# core/memory_system.py
import time
import logging
import json
import re
from typing import Dict, Optional, List
from datetime import datetime

import config
from database import DatabaseManager
from services.base_services import LLMService

class MemorySystem:
    """管理寵物的短期和長期記憶"""

    def __init__(self, db_manager: DatabaseManager, llm_service: Optional[LLMService], user_id: str, settings: Dict):
        self.db = db_manager
        self.llm = llm_service
        self.user_id = user_id
        self.settings = settings

    def _extract_keywords(self, text_content: str) -> Optional[str]:
        """從文本中提取關鍵字"""
        if not text_content or not isinstance(text_content, str):
            return None
        
        # 匹配中文或英文單詞
        words = re.findall(r'\b[a-zA-Z\u4e00-\u9fff]{3,}\b', text_content.lower())
        
        stopwords = {"的", "了", "是", "我", "你", "他", "她", "它", "也", "嗎", "呢", "吧", "呀",
                     "the", "a", "is", "to", "in", "it", "and", "that", "this", "you", "i"}
        
        valid_keywords = [w for w in words if w not in stopwords and not w.isdigit()]
        
        if not valid_keywords:
            return None
        
        # 優先取較長的詞
        unique_keywords = sorted(list(set(valid_keywords)), key=len, reverse=True)
        return ",".join(unique_keywords[:5]) if unique_keywords else None

    def save_memory(self, content: str, importance: int, pet_emotions: Dict, user_emotions: Optional[Dict] = None, is_long_term: bool = False, status: str = 'remembered'):
        """將一條記憶儲存到資料庫，自動計算衍生欄位"""
        pet_emotions_json: Optional[str] = None
        user_emotions_json: Optional[str] = None
        emotional_intensity = 0.0

        # 處理寵物情緒快照和情緒強度
        if pet_emotions and isinstance(pet_emotions, dict):
            significant_pet_emotions = {k: round(v, 3) for k, v in pet_emotions.items() if v > 0.15}
            if significant_pet_emotions:
                pet_emotions_json = json.dumps(significant_pet_emotions, ensure_ascii=False)
                if significant_pet_emotions.values():
                    top_emo_values = sorted(significant_pet_emotions.values(), reverse=True)[:3]
                    emotional_intensity = sum(top_emo_values) / len(top_emo_values)
                    # 對高喚醒度情緒給予加權
                    if any(emo in significant_pet_emotions and significant_pet_emotions[emo] > 0.6 for emo in ['excitement', 'fear', 'anger', 'anxiety', 'surprise']):
                        emotional_intensity *= 1.15
            else:
                emotional_intensity = 0.05 # 非常平淡的基礎值

        # 處理使用者情緒快照
        if user_emotions and isinstance(user_emotions, dict):
            significant_user_emotions = {k: round(v, 3) for k, v in user_emotions.items() if v > 0.2}
            if significant_user_emotions:
                user_emotions_json = json.dumps(significant_user_emotions, ensure_ascii=False)
        
        emotional_intensity = max(0.0, min(1.0, emotional_intensity))
        
        # 關鍵字提取
        keywords = self._extract_keywords(content) if not is_long_term and len(content) > 10 else None
        
        self.db.save_memory(
            user_id=self.user_id,
            content=content,
            is_long_term=is_long_term,
            importance=importance,
            status=status,
            pet_emotions_json=pet_emotions_json,
            user_emotions_json=user_emotions_json,
            keywords=keywords,
            emotional_intensity=emotional_intensity
        )

    def get_memories_for_prompt(self, stm_limit: int = 6, ltm_limit: int = 2) -> Dict[str, List[Dict]]:
        """獲取最近的、經過篩選的短期和長期記憶，用於LLM提示"""
        # 這裡可以實現原檔案 get_llm_prompt 中更複雜的情緒關聯篩選邏輯
        recent_stms = self.db.load_memory(self.user_id, is_long_term=False, limit=stm_limit, status_filter='remembered')
        recent_ltms = self.db.load_memory(self.user_id, is_long_term=True, limit=ltm_limit, status_filter='summarized_from_stm')
        
        return {"stm": recent_stms, "ltm": recent_ltms}

    def periodic_maintenance(self):
        """執行定期的記憶體維護"""
        # 1. 清理舊的 STM
        retention_days = self.settings.get(config.SETTING_STM_RETENTION_DAYS, 30)
        self.db.clean_short_term_memory(
            self.user_id,
            retention_days=int(retention_days),
            importance_threshold_for_archive=2,
            emotional_intensity_threshold_for_archive=0.65
        )
        logging.info("Short-term memory cleanup check performed.")

        # 2. 將待歸檔的 STM 總結成 LTM (這是一個耗時操作)
        self._summarize_stm_to_ltm()

    def _summarize_stm_to_ltm(self):
        """
        使用LLM將'to_be_archived'的STM總結成LTM。
        應在背景執行緒中謹慎呼叫。
        """
        if not self.llm:
            logging.warning("LTM Summarization skipped: LLM service not available.")
            return

        stms_to_process = self.db.load_memory(self.user_id, status_filter='to_be_archived', limit=5)
        if not stms_to_process:
            return
            
        logging.info(f"Found {len(stms_to_process)} STMs to summarize into LTM.")
        
        # 建構提示
        stm_content_for_prompt = []
        for stm in stms_to_process:
            ts = datetime.fromtimestamp(stm['timestamp']).strftime('%H:%M')
            stm_content_for_prompt.append(f"[{ts}] {stm['content']}")

        # ... 此處應包含原檔案中 _process_memories_for_ltm 的完整 summarization_prompt ...
        summarization_prompt = (
            "請將以下短期記憶片段總結成一段流暢、簡潔的長期記憶... \n"
            "短期記憶片段：\n" + "\n".join(stm_content_for_prompt) +
            "\n請以JSON格式輸出，包含 'summary' 和 'dominant_emotion_of_summary' 兩個鍵。"
        )
        
        # 呼叫LLM服務
        # 注意：llm_service 應該要有一個專門處理這種請求的方法
        # 這裡我們假設 generate_content 可以處理
        prompt_details = {
            "contents": [{"role": "user", "parts": [{"text": summarization_prompt}]}],
            "generation_config": {"temperature": 0.5, "max_output_tokens": 300},
            "expect_structured_output": True # 假設我們需要結構化輸出
        }
        
        summary_result = self.llm.generate_content(prompt_details)
        
        if summary_result and not summary_result.get("error"):
            summary_text = summary_result.get("spoken_response") # 假設 spoken_response 就是 summary
            if summary_text:
                # 儲存新的LTM
                self.save_memory(
                    content=summary_text,
                    importance=sum(s['importance'] for s in stms_to_process) // len(stms_to_process),
                    pet_emotions={}, # LTM的情緒可以從摘要中重新分析，或留空
                    is_long_term=True,
                    status='summarized_from_stm'
                )
                
                # 更新被處理過的STM的狀態
                processed_ids = [s['id'] for s in stms_to_process]
                self.db.update_stms_status(processed_ids, 'summarized_to_ltm')
                logging.info(f"Successfully summarized {len(processed_ids)} STMs into one LTM.")