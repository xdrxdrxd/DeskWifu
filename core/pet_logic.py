# core/pet_logic.py
import time
import logging
import random
import uuid
import re
import json
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, time as dt_time

import google.generativeai as genai
import config
from database import DatabaseManager
from services.base_services import LLMService, SearchService
from services.llm_service import GeminiService
from core.emotion_system import EmotionSystem
from core.personality_system import PersonalitySystem
from core.memory_system import MemorySystem
from tkinter import messagebox

class PetLogic:
    """應用程式的核心業務邏輯，不含UI。"""

    def __init__(self, db_manager: DatabaseManager, llm_service: Optional[LLMService], search_service: Optional[SearchService]):
        self.db = db_manager
        self.llm = llm_service
        self.search = search_service
        
        self.settings = self._load_all_settings()
        self.user_id = self.settings.get(config.SETTING_USER_ID)
        if not self.user_id or self.user_id == "default_user":
            self.user_id = str(uuid.uuid4())
            self.db.save_app_setting(config.SETTING_USER_ID, self.user_id)
            self.settings[config.SETTING_USER_ID] = self.user_id
        
        self.personality_system = PersonalitySystem(self.db, self.user_id, self.settings, self.llm)
        self.emotion_system = EmotionSystem(self.db, self.user_id, self.settings, self.llm, self.personality_system)
        self.memory_system = MemorySystem(self.db, self.llm, self.user_id, self.settings)
        
        self.llm_history: List[Dict[str, Any]] = []
        self.last_interaction_time = time.time()
        self.last_proactive_chat_time = time.time()
        self.is_sleeping = False
        self.is_processing_llm = False
        self.last_pet_spoken_response: Optional[str] = None
        self.last_pet_internal_thought: Optional[str] = None
        self.last_user_input_leading_to_response: Optional[str] = None

        search_tool_func = genai.types.FunctionDeclaration(
            name="custom_search",
            description="當你需要查詢最新的、真實世界的資訊（例如新聞、天氣、特定主題的資料），或者你不確定的知識時，使用這個工具進行網路搜尋。",
            parameters={
                "type_": "OBJECT",
                "properties": {"query": {"type_": "STRING", "description": "你想搜尋的關鍵字詞。"}},
                "required": ["query"]
            },
        )
        self.tool_kit = [genai.types.Tool(function_declarations=[search_tool_func])]
        self.available_tools = {
            "custom_search": self.search.search if self.search else lambda query: {"error": "Search service is not enabled."}
        }
        logging.info("PetLogic native tools have been defined.")

    def reinitialize_llm_service(self) -> bool:
        """嘗試使用資料庫中儲存的 API 金鑰重新初始化 LLM 服務。"""
        logging.info("Attempting to re-initialize LLM service...")
        api_key = self.db.get_api_key('gemini_api_key')
        if not api_key:
            logging.error("Re-initialization failed: API key not found in database.")
            return False
        try:
            model_name = self.db.load_app_setting(
                config.SETTING_SELECTED_LLM,
                config.DEFAULT_APP_SETTINGS[config.SETTING_SELECTED_LLM]
            )
            self.llm = GeminiService(api_key=api_key, model_name=model_name)
            self.memory_system.llm = self.llm
            self.personality_system.llm = self.llm
            logging.info("LLM service re-initialized successfully.")
            return True
        except Exception as e:
            logging.error(f"Failed to re-initialize GeminiService: {e}", exc_info=True)
            self.llm = None
            self.memory_system.llm = None
            self.personality_system.llm = None
            return False

    def _load_all_settings(self) -> Dict[str, Any]:
        """從資料庫載入所有應用程式設定"""
        settings = {}
        for key, default_value in config.DEFAULT_APP_SETTINGS.items():
            settings[key] = self.db.load_app_setting(key, default_value)
        logging.info("All application settings loaded into PetLogic.")
        return settings

    def get_initial_state(self) -> Dict[str, Any]:
        """獲取寵物啟動時的初始狀態，供UI使用"""
        self._check_sleep_schedule()
        dominant_emotion = "sleepy" if self.is_sleeping else self.emotion_system.get_dominant_emotion_for_display()
        return {
            "dominant_emotion": dominant_emotion,
            "initial_message": "哈囉！今天想聊些什麼呀？",
            "is_sleeping": self.is_sleeping,
            "llm_ready": self.llm is not None
        }

    def handle_user_input(self, user_text: str) -> Dict[str, Any]:
        """處理使用者輸入的主流程，現在包含工具呼叫循環和對話後學習。"""
        logging.info(f"--- 開始處理使用者輸入 --- : '{user_text}'")
        self.is_processing_llm = True
        try:
            if self.is_sleeping:
                return {"display_text": "zzz... (小星還在睡覺)", "new_emotion_for_ui": "sleepy", "tag": "system"}
            if not self.llm:
                return {"display_text": "嗚...我的大腦好像罷工了，請檢查API金鑰設定喔。", "new_emotion_for_ui": "sad", "tag": "pet"}

            self.last_interaction_time = time.time()
            self.last_user_input_leading_to_response = user_text
            
            sensed_emotions = self.llm.analyze_text_for_emotions(user_text) if self.llm else {}
            self.memory_system.save_memory(
                content=f"使用者說: {user_text}", importance=2,
                pet_emotions=self.emotion_system.get_current_emotions(), user_emotions=sensed_emotions
            )
            prompt_details = self._build_llm_prompt(user_text, sensed_emotions, request_type="user_submit")
            llm_result = self.llm.generate_content(prompt_details)
            
            if llm_result.get("tool_call_request"):
                tool_request = llm_result["tool_call_request"]
                tool_name = tool_request["name"]
                tool_args = tool_request["args"]
                if tool_name in self.available_tools:
                    logging.info(f"Executing tool '{tool_name}' with args: {tool_args}")
                    tool_function = self.available_tools[tool_name]
                    tool_result = tool_function(**tool_args)
                else:
                    logging.error(f"LLM called an unknown tool: {tool_name}")
                    tool_result = {"error": f"Tool '{tool_name}' not found."}

                logging.info(f"Tool '{tool_name}' executed. Result: {str(tool_result)[:200]}...")
                messages_for_next_turn = llm_result["messages_history_for_next_turn"]
                messages_for_next_turn.append({
                    "role": "tool",
                    "parts": [{"function_response": {"name": tool_name, "response": tool_result}}]
                })
                
                logging.debug("LLMService: Second call to Gemini model with tool results.")
                final_response = self.llm.model.generate_content(
                    messages_for_next_turn,
                    generation_config=prompt_details["generation_config"]
                )
                raw_llm_output_text = final_response.text.strip()
                parsed_output = self.llm._parse_structured_output(raw_llm_output_text)
                spoken_response = parsed_output.get("spoken_response", raw_llm_output_text)
                internal_thought = parsed_output.get("internal_thought", "(使用工具後進行總結)")
            else:
                spoken_response = llm_result.get("spoken_response", "我...好像不知道該說什麼了。")
                internal_thought = llm_result.get("internal_thought")

            self.last_pet_spoken_response = spoken_response
            self.last_pet_internal_thought = internal_thought
            if internal_thought:
                self.memory_system.save_memory(
                    content=f"小星思考: {internal_thought}", importance=0,
                    pet_emotions=self.emotion_system.get_current_emotions()
                )
            self.llm_history.append({"role": "user", "parts": [{"text": user_text}]})
            self.llm_history.append({"role": "model", "parts": [{"text": spoken_response}]})
            self.memory_system.save_memory(
                content=f"小星說: {spoken_response}", importance=1,
                pet_emotions=self.emotion_system.get_current_emotions()
            )
            self.personality_system.learn_from_user_text_async(user_text)
            self.personality_system.learn_from_pet_text_async(spoken_response)

            return {
                "display_text": spoken_response,
                "internal_thought": internal_thought,
                "new_emotion_for_ui": self.emotion_system.get_dominant_emotion_for_display(),
                "tag": "pet"
            }
        finally:
            self.is_processing_llm = False

    def _build_llm_prompt(self, user_message: str, user_sensed_emotions: Dict, request_type: str) -> Dict[str, Any]:
        """建構完整的 LLM 提示"""
        request_structured_output = request_type in ["user_submit", "proactive_chat", "self_talk"]
        output_format_instruction = (
            "\n\n重要輸出格式指示：\n"
            "請嚴格以單一的 JSON 物件格式輸出你的完整回應。此 JSON 物件必須包含以下兩個鍵：\n"
            "1. `internal_thought`: (字串) 代表你在說話前的內心思考、感受、意圖或簡要計畫。\n"
            "2. `spoken_response`: (字串) 代表你最終決定對使用者說出的話。\n"
            "```json\n"
            "{\n"
            "  \"internal_thought\": \"使用者聽起來很開心，我也跟著開心起來了！\",\n"
            "  \"spoken_response\": \"聽起來是件很棒的事耶！我也為你感到高興！\"\n"
            "}\n"
            "```"
        ) if request_structured_output else "\n\n請直接輸出你認為合適的回應文字。"

        system_prompt_parts: List[str] = [
            config.CHARACTER_PROFILE,
            "你擁有[搜尋]等工具，可以在需要時呼叫它們。",
            self.personality_system.get_personality_description(),
            self.personality_system.get_demographic_description(),
            self.personality_system.get_attachment_description_for_llm(),
            self.personality_system.get_self_efficacy_description_for_llm(),
            self.personality_system.get_neuro_state_description_for_llm(), # --- [新增] 這一行 ---
            self.personality_system.get_characteristics_description_for_llm(),
            f"現在是 {datetime.now().strftime('%Y年%m月%d日 %H:%M')}。"
        ]
        
        memories = self.memory_system.get_memories_for_prompt()
        if memories.get("stm"):
            formatted_stms = ["\n以下是你最近的一些重要對話片段："] + [f"- {(time.time() - mem['timestamp']) / 60:.0f}分鐘前: {mem['content']}" for mem in memories["stm"]]
            system_prompt_parts.append("\n".join(formatted_stms))
        if memories.get("ltm"):
            formatted_ltms = ["\n以下是你的一些長期記憶摘要："] + [f"- 我記得：『{mem['content']}』" for mem in memories["ltm"]]
            system_prompt_parts.append("\n".join(formatted_ltms))
        
        system_prompt_parts.append(output_format_instruction)
        final_system_prompt = "\n\n".join(filter(None, system_prompt_parts))

        messages_for_llm: List[Dict[str, Any]] = [
            {"role": "user", "parts": [{"text": final_system_prompt}]},
            {"role": "model", "parts": [{"text": "我明白了。我會基於以上所有資訊，扮演好「小星」這個角色，並嚴格按照要求的JSON格式來回應。"}]}
        ]
        messages_for_llm.extend(self.llm_history[-10:])
        messages_for_llm.append({"role": "user", "parts": [{"text": user_message}]})
        
        generation_config = {
            "temperature": self.settings.get(config.SETTING_LLM_TEMP, 0.75),
            "max_output_tokens": self.settings.get(config.SETTING_LLM_MAX_TOKENS, 700)
        }
        
        return {
            "contents": messages_for_llm,
            "generation_config": generation_config,
            "expect_structured_output": request_structured_output,
            "tools": self.tool_kit if self.search and self.search.is_enabled else None
        }

    def _check_sleep_schedule(self):
        """檢查並更新寵物的睡眠狀態"""
        now = datetime.now()
        current_time_val = now.time()
        bedtime_h = int(self.settings.get(config.SETTING_BEDTIME_HOUR, 1))
        bedtime_m = int(self.settings.get(config.SETTING_BEDTIME_MINUTE, 0))
        wakeup_h = int(self.settings.get(config.SETTING_WAKEUP_HOUR, 7))
        wakeup_m = int(self.settings.get(config.SETTING_WAKEUP_MINUTE, 0))
        print(f"DEBUG SLEEP CHECK: Reading bedtime as {bedtime_h}:{bedtime_m}, wakeup as {wakeup_h}:{wakeup_m}")
        bed_time = dt_time(bedtime_h, bedtime_m)
        wake_time = dt_time(wakeup_h, wakeup_m)
        was_sleeping = self.is_sleeping
        if bed_time <= wake_time:
            self.is_sleeping = bed_time <= current_time_val < wake_time
        else:
            self.is_sleeping = current_time_val >= bed_time or current_time_val < wake_time
        if self.is_sleeping and not was_sleeping:
            self.memory_system.save_memory("小星進入睡眠狀態。", 0, self.emotion_system.get_current_emotions())
        elif not self.is_sleeping and was_sleeping:
            self.memory_system.save_memory("小星睡醒了。", 0, self.emotion_system.get_current_emotions())

    def check_for_proactive_action(self) -> Optional[Dict[str, Any]]:
        """檢查是否應執行主動行為"""
        if self.is_processing_llm or self.is_sleeping or not self.llm: return None
        now = time.time()
        min_interval, max_interval = (120, 300) # 簡化
        if now - self.last_proactive_chat_time < random.uniform(min_interval, max_interval): return None
        if now - self.last_interaction_time < 60: return None
        logging.info("Proactive chat conditions met. Initiating.")
        self.last_proactive_chat_time = now
        prompt_theme = "你現在想要主動跟使用者說些話。請自然地、簡短地說幾句話。"
        self.is_processing_llm = True
        try:
            prompt_details = self._build_llm_prompt(prompt_theme, {}, "proactive_chat")
            llm_result = self.llm.generate_content(prompt_details)
            spoken_response = llm_result.get("spoken_response")
            if spoken_response:
                self.memory_system.save_memory(f"小星(主動): {spoken_response}", 1, self.emotion_system.get_current_emotions())
                self.llm_history.append({"role": "model", "parts": [{"text": spoken_response}]})
                return {"display_text": spoken_response, "new_emotion_for_ui": self.emotion_system.get_dominant_emotion_for_display(), "tag": "pet"}
            return None
        finally:
            self.is_processing_llm = False
            
    def periodic_maintenance(self):
        """執行所有定期的背景維護任務。"""
        logging.debug("Performing periodic maintenance tasks...")
        self._check_sleep_schedule()

        # --- [新增] 先執行 personality_system 維護，以更新 effective 參數 ---
        self.personality_system.periodic_maintenance() 

        if not self.is_sleeping:
            # --- [修改] 使用 personality_system 計算出的動態參數 ---
            self.emotion_system.decay_emotions(self.personality_system.effective_mood_stability)
            self.emotion_system.decay_core_affect(is_sleeping=False)
            self.emotion_system.apply_random_fluctuations(self.personality_system.effective_mood_stability)
            # --- 修改結束 ---
            self.perform_daily_news_search_async()
            
        self.memory_system.periodic_maintenance()
        # self.personality_system.periodic_maintenance() # --- [移動] 已移到前面 ---
        return {"new_emotion_for_ui": "sleepy" if self.is_sleeping else self.emotion_system.get_dominant_emotion_for_display()}

    def get_full_debug_status_report(self) -> str:
        """產生一份包含所有主要狀態的詳細報告字串，用於日誌記錄。"""
        report_parts = [
            "\n\n--- 完整狀態報告 ---",
            f"**使用者 ID:** {self.user_id}",
            f"**睡眠狀態:** {'是' if self.is_sleeping else '否'}",
            f"**上次互動時間:** {datetime.fromtimestamp(self.last_interaction_time).strftime('%Y-%m-%d %H:%M:%S')}",
            "---",
            "**[核心情感]**",
            f"  - 愉悅度 (Valence): {self.emotion_system.core_affect['valence']:.3f}",
            f"  - 喚醒度 (Arousal): {self.emotion_system.core_affect['arousal']:.3f}",
            "---",
            "**[主要離散情緒 (Top 5)]**"
        ]
        top_emotions = sorted(self.emotion_system.get_current_emotions().items(), key=lambda item: item[1], reverse=True)[:5]
        for name, value in top_emotions:
            report_parts.append(f"  - {name}: {value:.3f}")
        report_parts.append("---")
        report_parts.append("**[個性特質 (OCEAN)]**")
        for key, value in self.personality_system.character_traits.items():
            report_parts.append(f"  - {key.replace('ocean_', '').capitalize()}: {value:.3f}")
        report_parts.append(f"  - 依戀度 (Attachment): {self.personality_system.attachment_score:.3f}")
        report_parts.append("---")
        report_parts.append("**[記憶體]**")
        report_parts.append(f"  - 對話歷史長度: {len(self.llm_history)} 條")
        report_parts.append(f"  - 個體特徵快取數量: {sum(len(v) for v in self.personality_system.characteristics_cache.values())} 條")
        report_parts.append("--- 報告結束 ---\n")
        return "\n".join(report_parts)

    def log_next_llm_prompt(self):
        """建構一個測試用的LLM提示並將其記錄下來，但不發送。"""
        logging.info("--- 準備記錄下次 LLM 提示 (測試模式) ---")
        test_message = "你好嗎？可以跟我說說關於高雄的趣事嗎？"
        prompt_details = self._build_llm_prompt(test_message, {}, "debug_prompt_test")
        full_prompt_text = "\n".join(part["parts"][0]["text"] for part in prompt_details["contents"])
        logging.debug(f"--- 完整的 LLM 提示內容 ---\n{full_prompt_text}\n--- 提示結束 ---")
        messagebox.showinfo("提示已記錄", "一個測試用的完整 LLM 提示已輸出到日誌檔案中。")

    def test_search(self):
        """執行一次測試搜尋並記錄結果。"""
        if self.search and self.search.is_enabled:
            query = "高雄今天天氣"
            logging.info(f"--- 手動執行測試搜尋 --- : '{query}'")
            result = self.search.search(query)
            logging.info(f"搜尋結果: {result}")
            messagebox.showinfo("搜尋測試", f"已執行對 '{query}' 的搜尋，請檢查日誌查看結果。")
        else:
            logging.warning("--- 搜尋測試失敗：搜尋服務未啟用 ---")
            messagebox.showwarning("搜尋未啟用", "搜尋功能未啟用或未設定金鑰/CX ID。")

    def process_direct_user_feedback(self, feedback_type: str, feedback_text: str) -> Optional[Dict[str, Any]]:
        """處理使用者對寵物上一句話的直接回饋，包含 LLM 分析。"""
        if not self.last_pet_spoken_response:
            return {
                "display_text": "嗯？我好像忘記上一句說了什麼了...",
                "new_emotion_for_ui": self.emotion_system.get_dominant_emotion_for_display(),
                "tag": "system"
            }
        logging.info(f"Processing direct user feedback: Type='{feedback_type}', Text='{feedback_text}'")
        self.memory_system.save_memory(
            content=f"使用者對「{self.last_pet_spoken_response}」的回饋({feedback_type}): {feedback_text}",
            importance=3, pet_emotions=self.emotion_system.get_current_emotions()
        )
        if feedback_type == "positive":
            self.personality_system.handle_significant_event("user_praised_pet", strength_modifier=1.2)
            if feedback_text:
                self.personality_system.add_or_update_characteristic(
                    trait_type=config.TRAIT_TYPE_RESPONSE_STYLE,
                    trait_key=f"user_likes_style_{uuid.uuid4().hex[:6]}",
                    trait_value=f"喜歡小星說「{self.last_pet_spoken_response[:30]}...」因為「{feedback_text[:40]}...」",
                    source=config.SOURCE_USER_FEEDBACK_POSITIVE, initial_relevance_base=0.75
                )
            return {"display_text": random.choice(["太好了！你喜歡真是太棒了！😄", "嘿嘿，謝謝你的肯定！"]), "tag": "pet"}
        elif feedback_type == "negative":
            self.personality_system.handle_significant_event("user_scolded_pet_critical", strength_modifier=1.2)
            return {"display_text": random.choice(["喔不...我會記下來，下次改進的。", "對不起，如果讓你感覺不好了..."]), "tag": "pet"}
        elif feedback_type == "correction" and self.llm:
            thread = threading.Thread(target=self._learn_from_correction_worker, args=(self.last_pet_spoken_response, self.last_user_input_leading_to_response, feedback_text))
            thread.daemon = True
            thread.start()
            return {"display_text": "啊，原來是這樣！非常感謝你的指正，我學到了！🧠✨", "tag": "pet"}
        return None

    def _learn_from_correction_worker(self, pet_original_response: str, user_original_input: str, user_correction: str):
        """在背景執行緒中，使用LLM分析使用者的糾正並學習。"""
        if not self.llm: return
        logging.info("WORKER: Starting learning from user correction.")
        prompt = (
            f"我先前對提問「{user_original_input}」給出了回應：「{pet_original_response}」。"
            f"使用者指正說：「{user_correction}」。\n\n"
            "請分析這次的修正，並以JSON格式輸出：\n"
            "1. `error_summary`: 簡要總結我原始回應中可能出錯的點。\n"
            "2. `corrected_fact`: 從修正中提取出一個具體的「正確事實」或「使用者偏好」。\n"
            "3. `learning_point_type`: 判斷學習點類型：[\"factual_correction\", \"user_preference\"].\n"
            "```json\n"
            "{\n"
            "  \"error_summary\": \"太陽是行星\",\n"
            "  \"corrected_fact\": \"太陽是恆星\",\n"
            "  \"learning_point_type\": \"factual_correction\"\n"
            "}\n"
            "```"
        )
        try:
            analysis_result = self.llm.generate_content({"contents": [{"role": "user", "parts": [{"text": prompt}]}], "generation_config": {"temperature": 0.2}})
            parsed_data = self.llm._parse_structured_output(analysis_result.get("spoken_response", ""))
            if parsed_data.get("corrected_fact"):
                self.personality_system.add_or_update_characteristic(
                    trait_type=config.TRAIT_TYPE_USER_INFO,
                    trait_key=f"correction_{parsed_data.get('error_summary', 'unknown')[:15]}",
                    trait_value=parsed_data["corrected_fact"],
                    source=config.SOURCE_USER_FEEDBACK_NEGATIVE, initial_relevance_base=0.88
                )
                logging.info(f"WORKER: Learned from correction: {parsed_data['corrected_fact']}")
        except Exception as e:
            logging.error(f"WORKER: Error during learning from correction: {e}", exc_info=True)

    def initial_personality_setup_async(self):
        """非同步地觸發啟動時的個性化搜尋。"""
        if int(self.settings.get(config.SETTING_INITIAL_PERSONALITY_SETUP_DONE, 0)) == 1:
            logging.info("Initial personality setup already done. Skipping.")
            return
        logging.info("Dispatching initial personality setup to worker...")
        thread = threading.Thread(target=self._initial_personality_setup_worker)
        thread.daemon = True
        thread.start()

    def _initial_personality_setup_worker(self):
        """在背景執行緒中執行搜尋並學習初始知識。"""
        if not self.search or not self.search.is_enabled:
            logging.warning("WORKER: Initial setup skipped, search service is not available.")
            self.db.save_app_setting(config.SETTING_INITIAL_PERSONALITY_SETUP_DONE, 1)
            self.settings[config.SETTING_INITIAL_PERSONALITY_SETUP_DONE] = 1
            return
        
        logging.info("WORKER: Starting initial personality setup via search.")
        user_culture = self.personality_system.demographics.get(config.SETTING_DEMO_CULTURE, "台灣")
        queries = [f"{user_culture}文化中的有趣習俗", "關於寵物的有趣知識", "一句隨機的勵志名言"]
        
        learned_facts_count = 0
        for query in queries:
            search_response = self.search.search(query, num_results=1)
            time.sleep(1)
            if search_response and search_response.get("results"):
                result_text = search_response["results"][0]
                snippet_match = re.search(r"摘要:\s*(.*)", result_text)
                fact_to_learn = snippet_match.group(1).strip() if snippet_match else result_text.split("\n")[0]
                if fact_to_learn:
                    self.personality_system.add_or_update_characteristic(
                        trait_type=config.TRAIT_TYPE_PET_SELF_CONCEPT,
                        trait_key=f"initial_setup_{query[:10]}",
                        trait_value=fact_to_learn[:200],
                        source=config.SOURCE_SYSTEM_INITIATED, initial_relevance_base=0.5
                    )
                    learned_facts_count += 1
        
        self.db.save_app_setting(config.SETTING_INITIAL_PERSONALITY_SETUP_DONE, 1)
        self.settings[config.SETTING_INITIAL_PERSONALITY_SETUP_DONE] = 1
        logging.info(f"WORKER: Initial personality setup finished. Learned {learned_facts_count} facts.")

    def perform_daily_news_search_async(self):
        """非同步地觸發每日新聞搜尋。"""
        if not int(self.settings.get(config.SETTING_SEARCH_DAILY_NEWS_ENABLED, 0)): return
        now_ts = time.time()
        last_search_ts = float(self.settings.get(config.SETTING_LAST_NEWS_SEARCH_TIMESTAMP, 0))
        if (now_ts - last_search_ts) < (23 * 3600): return
        
        logging.info("Dispatching daily news search to worker...")
        thread = threading.Thread(target=self._perform_daily_news_search_worker)
        thread.daemon = True
        thread.start()

    def _perform_daily_news_search_worker(self):
        """在背景執行緒中執行每日新聞搜尋並儲存摘要。"""
        if not self.search or not self.search.is_enabled:
            logging.warning("WORKER: Daily news search skipped, search service is not available.")
            return

        logging.info("WORKER: Starting daily news search.")
        query = "今日國際焦點新聞"
        search_response = self.search.search(query, num_results=2)
        if search_response and search_response.get("results"):
            news_summary = "我今天瀏覽到一些資訊摘要：\n" + "\n".join(search_response["results"])
            self.personality_system.add_or_update_characteristic(
                trait_type=config.TRAIT_TYPE_KEY_MEMORY_SUMMARY,
                trait_key="daily_news_summary_for_pet",
                trait_value=news_summary[:800],
                source=config.SOURCE_SYSTEM_INITIATED, initial_relevance_base=0.75
            )
            now_ts = time.time()
            self.db.save_app_setting(config.SETTING_LAST_NEWS_SEARCH_TIMESTAMP, now_ts)
            self.settings[config.SETTING_LAST_NEWS_SEARCH_TIMESTAMP] = now_ts
            logging.info("WORKER: Daily news summary stored.")
    # 請將這個方法加入到 core/pet_logic.py 的 PetLogic 類別中

    def check_task_reminders(self) -> Optional[Dict[str, Any]]:
        """檢查是否有需要提醒的任務，並使用 LLM 生成提醒語句。"""
        if self.is_processing_llm or getattr(self, "is_generating_proactive_chat", False):
            return None
            
        active_tasks = self.db.get_tasks(self.user_id, include_completed=False)
        if not active_tasks:
            return None

        now_dt = datetime.now()
        now_ts = now_dt.timestamp()

        for task in active_tasks:
            task_id = task['id']
            last_reminded_ts = self.logic.current_task_reminders.get(task_id, 0)
            
            should_remind_now = False
            reminder_urgency = "normal"
            reminder_interval_hours = 24 # 預設每天提醒

            if task['due_at']:
                due_dt = datetime.fromtimestamp(task['due_at'])
                time_to_due_sec = (due_dt - now_dt).total_seconds()

                if time_to_due_sec < 0:
                    reminder_urgency = "overdue"
                    reminder_interval_hours = random.uniform(2, 4)
                elif time_to_due_sec < 3600 * 2:
                    reminder_urgency = "soon"
                    reminder_interval_hours = random.uniform(0.5, 1.5)
                elif time_to_due_sec < 3600 * 24:
                    reminder_urgency = "normal"
                    reminder_interval_hours = random.uniform(3, 6)
                else:
                    reminder_urgency = "gentle"
                    reminder_interval_hours = random.uniform(20, 36)
            else: # 沒有截止日期的任務
                if (now_ts - task['created_at']) > 3600 * 24 * 2: # 兩天以上的舊任務才提醒
                     reminder_interval_hours = random.uniform(48, 72)
                else:
                    continue

            if (now_ts - last_reminded_ts) > (reminder_interval_hours * 3600):
                should_remind_now = True
            
            if should_remind_now and reminder_urgency not in ["soon", "overdue"] and random.random() < 0.3:
                should_remind_now = False

            if should_remind_now:
                logging.info(f"Task reminder triggered for: '{task['description']}' (Urgency: {reminder_urgency})")
                
                due_date_str = f"期限：{datetime.fromtimestamp(task['due_at']).strftime('%Y-%m-%d %H:%M')}" if task['due_at'] else "無特定期限"
                reminder_theme = (f"你需要用友善且符合你個性的方式，提醒使用者關於一個任務。任務描述：「{task['description']}」。{due_date_str}。"
                                  f"提醒的緊急程度是「{reminder_urgency}」。")

                # 標記正在處理中，防止其他主動行為觸發
                self.is_processing_llm = True 
                
                try:
                    prompt_details = self._build_llm_prompt(reminder_theme, {}, "task_reminder_phrasing")
                    llm_result = self.llm.generate_content(prompt_details)
                    spoken_response = llm_result.get("spoken_response")
                    if spoken_response:
                        self.logic.current_task_reminders[task_id] = now_ts
                        return {
                            "display_text": spoken_response,
                            "new_emotion_for_ui": self.emotion_system.get_dominant_emotion_for_display(),
                            "tag": "task_reminder"
                        }
                finally:
                    self.is_processing_llm = False
                
                break # 一次只提醒一個任務
        
        return None
