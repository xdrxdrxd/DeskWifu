# services/llm_service.py
import google.generativeai as genai
import logging
import re
import json
from typing import Dict, Any

import config
from services.base_services import LLMService

class GeminiService(LLMService):
    """使用 Google Gemini API 的 LLM 服務"""
    def __init__(self, api_key: str, model_name: str):
        if not api_key:
            raise ValueError("API key for GeminiService cannot be empty.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        # 建立一個專門用於分析任務的模型，可以使用較輕量的模型
        self.analysis_model = genai.GenerativeModel("gemini-1.5-flash-latest") 
        logging.info(f"GeminiService initialized with model: {model_name}")

    def generate_content(self, prompt_details: Dict[str, Any]) -> Dict[str, Any]:
        """根據結構化的提示詳情生成內容，包含工具呼叫邏輯"""
        try:
            messages_history = prompt_details["contents"]
            tools = prompt_details.get("tools")
            generation_config = prompt_details.get("generation_config")
            expect_structured_output = prompt_details.get("expect_structured_output", False)

            # 第一次呼叫模型
            logging.debug("LLMService: Initial call to Gemini model.")
            response = self.model.generate_content(
                messages_history,
                generation_config=generation_config,
                tools=tools
            )

            response_part = response.candidates[0].content.parts[0]

            # 檢查模型是否要求呼叫工具
            if response_part.function_call:
                function_call = response_part.function_call
                function_name = function_call.name
                
                logging.info(f"LLM requested a tool call: {function_name} with args: {function_call.args}")
                
                # 將模型的「工具呼叫請求」加到歷史紀錄中
                messages_history.append(response.candidates[0].content)

                # 返回一個特殊的字典，通知 PetLogic 需要執行工具
                return {
                    "tool_call_request": {
                        "name": function_name,
                        "args": dict(function_call.args)
                    },
                    "messages_history_for_next_turn": messages_history, # 傳遞更新後的歷史
                    "error": None
                }
            else:
                # 模型沒有要求呼叫工具，直接給出了文字回答
                raw_llm_output_text = response.text.strip()
                if expect_structured_output:
                    parsed_output = self._parse_structured_output(raw_llm_output_text)
                    return {
                        "internal_thought": parsed_output.get("internal_thought", "(未提供思考)"),
                        "spoken_response": parsed_output.get("spoken_response", raw_llm_output_text),
                        "error": None
                    }
                else:
                    return {"spoken_response": raw_llm_output_text, "error": None}

        except Exception as e:
            logging.error(f"Gemini API error during content generation: {e}", exc_info=True)
            return {
                "internal_thought": f"(API 錯誤: {e})",
                "spoken_response": "哎呀，我的思考迴路短路了...",
                "error": str(e)
            }

    def analyze_text_for_emotions(self, text: str) -> Dict[str, float]:
        """分析給定文本，返回一個包含情緒及其分數的字典"""
        if not text or len(text) < 5:
            return {}

        emotion_list_str = ", ".join(config.EMOTIONS.keys())
        prompt = (
            f"請只用繁體中文回答。仔細分析以下文字，判斷其主要表達了哪些情緒。\n"
            f"可參考的情緒列表：[{emotion_list_str}]。\n"
            f"僅提供JSON格式的回應，不要有任何其他文字，例如：{{\"joy\": 0.8, \"neutral\": 0.2}}。\n"
            f"待分析的文字： \"{text}\""
        )
        try:
            response = self.analysis_model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 500}
            )
            parsed_json = self._parse_structured_output(response.text)
            
            # 驗證返回的資料
            valid_emotions = {
                k: float(v) for k, v in parsed_json.items()
                if k in config.EMOTIONS and isinstance(v, (int, float))
            }
            return valid_emotions
        except Exception as e:
            logging.error(f"Gemini API error during emotion analysis: {e}", exc_info=True)
            return {}

    def appraise_event(self, event_text: str) -> Dict[str, float]:
        """根據評價理論分析事件文本"""
        if not event_text or len(event_text) < 3:
            return {}
            
        # ... 此處應包含原檔案中 _appraise_event_with_llm 的完整 appraisal_prompt ...
        prompt = f"""
        請根據以下維度對事件進行評估，並以 JSON 格式返回分數。
        評價維度: "novelty", "pleasantness", "goal_conduciveness", "coping_potential", "urgency".
        事件文本: "{event_text}"
        請只輸出 JSON。
        """
        try:
            response = self.analysis_model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 200}
            )
            parsed_json = self._parse_structured_output(response.text)
            
            # 驗證並轉換為浮點數
            valid_appraisals = {k: float(v) for k, v in parsed_json.items() if isinstance(v, (int, float))}
            return valid_appraisals
        except Exception as e:
            logging.error(f"Gemini API error during event appraisal: {e}", exc_info=True)
            return {}

    def _parse_structured_output(self, raw_text: str) -> Dict:
        """
        更強大的 JSON 解析器：從LLM的原始回應中安全地提取JSON物件。
        能夠處理 markdown 標記和字串中的換行符。
        """
        logging.debug(f"LLM Raw Output to be parsed:\n---\n{raw_text}\n---")
        
        # 尋找被 ```json ... ``` 包圍的區塊或裸露的JSON物件
        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*?\})", raw_text, re.DOTALL)
        
        if match:
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                # 關鍵修正：使用 strict=False 來允許字串中的控制字元，例如換行符
                data = json.loads(json_str, strict=False)
                if isinstance(data, dict):
                    logging.info("Successfully parsed structured JSON output.")
                    return data
                else:
                    logging.warning(f"Parsed JSON is not a dictionary. Type: {type(data)}")
                    return {"spoken_response": str(data), "internal_thought": "(JSON解析結果非字典)"}
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse extracted JSON. Error: {e}. Trying to fix...")
                # 嘗試修復常見的錯誤，例如結尾多餘的逗號
                fixed_json_str = re.sub(r',\s*([\}\]])', r'\1', json_str)
                try:
                    data = json.loads(fixed_json_str, strict=False)
                    logging.info("Successfully parsed JSON after auto-fixing.")
                    return data
                except json.JSONDecodeError:
                    logging.error(f"Auto-fixing JSON failed. Final attempt failed for string: '{json_str[:250]}...'")
                    return {"spoken_response": raw_text, "internal_thought": "(JSON 提取後解析失敗)"}
        
        logging.warning(f"No valid JSON object found in LLM response.")
        return {"spoken_response": raw_text, "internal_thought": "(未找到有效的JSON物件)"}