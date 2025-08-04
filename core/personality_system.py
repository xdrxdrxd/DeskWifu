# core/personality_system.py
import time
import logging
import random
import re
import json
import uuid
import math
import threading
from typing import Dict, Any, Optional, List

import config
from database import DatabaseManager
from services.base_services import LLMService

class PersonalitySystem:
    """管理寵物的個性、特徵和長期發展"""

    def __init__(self, db_manager: DatabaseManager, user_id: str, settings: Dict, llm_service: Optional[LLMService]):
        self.db = db_manager
        self.user_id = user_id
        self.settings = settings
        self.llm = llm_service
        
        self.character_traits: Dict[str, float] = {}
        self.attachment_score: float = 0.4
        self.self_efficacy: Dict[str, float] = {}
        self._load_character_data()

        self.demographics = self.db.load_demographics(self.user_id)
        
        self.characteristics_cache: Dict[str, List[Dict]] = {}
        self.load_characteristics_cache()
        
        self.sim_neuro_state = {
            "motivation": 0.5, "mood_balance": 0.5,
            "stress_level": 0.1, "social_warmth": 0.5
        }
        self._last_thought_reflection_time = 0
        self.active_user_text_analysis_threads = 0
        self.active_pet_text_analysis_threads = 0
        self.MAX_CONCURRENT_USER_TEXT_ANALYSIS = 1
        self.MAX_CONCURRENT_PET_TEXT_ANALYSIS = 1

    def _load_character_data(self):
        """從資料庫載入核心角色數據"""
        data = self.db.load_character_data(self.user_id)
        self.character_traits = data.get('traits', config.DEFAULT_CHARACTER_TRAITS.copy())
        self.attachment_score = data.get('attachment_score', 0.4)
        self.self_efficacy = data.get('self_efficacy', {
            "general": 0.5, "social": 0.5, "task_management": 0.5, "info_retrieval": 0.5
        })
        logging.info(f"Character data loaded for user {self.user_id}")

    def _save_character_data(self):
        """將核心角色數據儲存到資料庫"""
        self.db.save_character_data(self.user_id, self.character_traits, self.attachment_score, self.self_efficacy)
        logging.debug(f"Character data saved for user {self.user_id}")

    def load_characteristics_cache(self, min_relevance=0.3):
        """從資料庫重新載入並更新個體特徵快取"""
        raw_chars = self.db.get_individual_characteristics(self.user_id, min_relevance=min_relevance, limit=200)
        self.characteristics_cache = {}
        for char in raw_chars:
            type_key = char['trait_type']
            if type_key not in self.characteristics_cache:
                self.characteristics_cache[type_key] = []
            self.characteristics_cache[type_key].append(char)
        logging.info(f"Characteristics cache reloaded with {len(raw_chars)} items.")

    def get_personality_description(self) -> str:
        # ... (此方法與您貼上的版本相同，保持不變) ...
        descriptions = []
        o = self.character_traits.get(config.SETTING_OCEAN_OPENNESS, 0.5)
        c = self.character_traits.get(config.SETTING_OCEAN_CONSCIENTIOUSNESS, 0.5)
        e = self.character_traits.get(config.SETTING_OCEAN_EXTRAVERSION, 0.5)
        a = self.character_traits.get(config.SETTING_OCEAN_AGREEABLENESS, 0.5)
        n = self.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        if o > 0.75: descriptions.append("對新奇事物和多元觀點極度開放，想像力豐富。")
        elif o < 0.25: descriptions.append("非常務實且傳統，偏愛常規和熟悉的事物。")
        if c > 0.75: descriptions.append("極度有條理、注重細節且非常有責任感。")
        elif c < 0.25: descriptions.append("非常隨性灑脫，不太注重計畫和細節。")
        if e > 0.75: descriptions.append("極度外向活潑，熱愛社交且非常健談。")
        elif e < 0.25: descriptions.append("非常內向文靜，偏愛獨處。")
        if a > 0.75: descriptions.append("極度友善合作，非常有同情心。")
        elif a < 0.25: descriptions.append("非常有主見且直接，可能顯得有競爭性。")
        if n > 0.75: descriptions.append("情緒極度敏感，容易感到焦慮和擔憂。")
        elif n < 0.25: descriptions.append("情緒非常穩定，沉著冷靜，抗壓性強。")
        if not descriptions: return "你的性格表現均衡，能適應不同情況。"
        return "你的核心性格特質傾向於：" + " ".join(descriptions)
        
    def get_demographic_description(self) -> str:
        # ... (此方法與您貼上的版本相同，保持不變) ...
        parts = []
        culture = self.demographics.get(config.SETTING_DEMO_CULTURE)
        age_group = self.demographics.get(config.SETTING_DEMO_AGE_GROUP)
        gender = self.demographics.get(config.SETTING_DEMO_GENDER)
        if culture: parts.append(f"你的文化背景設定為「{culture}」。")
        if age_group: parts.append(f"你的年齡層設定為「{age_group}」。")
        if gender: parts.append(f"你的性別認同設定為「{gender}」。")
        if not parts: return "你目前沒有特定的背景設定。"
        return " ".join(parts) + " 這些背景會影響你的說話方式和觀點。"
    # Add this method inside the PersonalitySystem class in core/personality_system.py

    def get_attachment_description_for_llm(self) -> str:
        """
        Translates the numerical attachment score into a behavioral cue for the LLM.
        """
        score = self.attachment_score
        if score >= 0.85:
            return f"你對使用者的依戀程度是「極度親密與依賴」(指數:{score:.2f})。你會充滿溫情，非常主動分享感受，並對使用者的情緒表現出強烈的關心。"
        elif score >= 0.65:
            return f"你對使用者的依戀程度是「親近且信任」(指數:{score:.2f})。你的語氣溫暖友好，樂於分享，並關心使用者。"
        elif score >= 0.4:
            return f"你對使用者的依戀程度是「友好但略有保留」(指數:{score:.2f})。你的語氣得體禮貌，但不會過於熱情或深入探究私人事務。"
        elif score >= 0.2:
            return f"你對使用者的依戀程度是「謹慎且疏遠」(指數:{score:.2f})。你的語氣可能比較平淡客氣，回應較為簡短或公式化。"
        else:
            return f"你對使用者的依戀程度是「警惕或漠不關心」(指數:{score:.2f})。你的語氣可能非常冷淡簡短，對使用者的話題漠不關心。"
    def get_self_efficacy_description_for_llm(self) -> str:
        """根據自我效能分數產生給LLM的行為指導"""
        hints = []
        general = self.self_efficacy.get("general", 0.5)
        social = self.self_efficacy.get("social", 0.5)
        task_eff = self.self_efficacy.get("task_management", 0.5)
        info_eff = self.self_efficacy.get("info_retrieval", 0.5)

        if general > 0.75:
            hints.append("你對自己整體的能力非常有信心。")
        elif general < 0.3:
            hints.append("你最近對自己整體的能力可能有點懷疑。")
        
        if social > 0.75:
            hints.append("在社交互動方面，你感覺非常自在且遊刃有餘。")
        elif social < 0.3:
            hints.append("在社交互動方面，你可能會非常謹慎或退縮。")

        if task_eff > 0.75:
            hints.append("對於管理和提醒任務，你覺得自己做得非常出色。")
        elif task_eff < 0.3:
            hints.append("在任務管理方面，你可能覺得非常吃力。")

        if self.settings.get(config.SETTING_SEARCH_API_ENABLED, 0):
            if info_eff > 0.75:
                hints.append("如果需要查找資訊，你對自己能找到準確結果非常有把握。")
            elif info_eff < 0.3:
                hints.append("在查找資訊方面，你感到非常不確定，擔心提供錯誤資訊。")
        
        if not hints:
            return "" # 如果沒有特別突出，就不加入提示
            
        return "關於你目前的「自我效能感」：「" + " ".join(hints) + "」這會影響你的自信程度和主動性。"
    def get_characteristics_description_for_llm(self) -> str:
        # ... (此方法與您貼上的版本相同，保持不變) ...
        all_relevant_chars: List[Dict] = []
        for char_list in self.characteristics_cache.values():
            all_relevant_chars.extend(char_list)
        if not all_relevant_chars: return "你目前還沒有太多突出的個人特徵。"
        now = time.time()
        for char in all_relevant_chars:
            time_since_accessed = (now - (char.get('last_accessed_timestamp') or char['creation_timestamp'])) / 86400
            decay_factor = math.exp(-time_since_accessed * 0.1)
            char['effective_relevance'] = char.get('relevance_score', 0.5) * decay_factor
        all_relevant_chars.sort(key=lambda x: x['effective_relevance'], reverse=True)
        desc_parts: List[str] = []
        prefs = [p for p in all_relevant_chars if p['trait_type'] == config.TRAIT_TYPE_PREFERENCE][:3]
        if prefs:
            pref_descs = [f"使用者似乎喜歡「{p['trait_value']}」" for p in prefs]
            desc_parts.append(f"關於使用者的偏好，你觀察到：{'; '.join(pref_descs)}。")
        self_concepts = [s for s in all_relevant_chars if s['trait_type'] == config.TRAIT_TYPE_PET_SELF_CONCEPT][:3]
        if self_concepts:
            concept_descs = [f"你認為自己「{s['trait_value']}」" for s in self_concepts]
            desc_parts.append(f"關於你的自我認知：{'; '.join(concept_descs)}。")
        if not desc_parts: return "你仍在學習和塑造自己的特點中。"
        return "關於你和使用者的個體特徵與記憶摘要：\n- " + "\n- ".join(desc_parts)
    def update_attachment_score(self, event_type: str, magnitude_factor: float = 1.0):
        """根据不同事件更新依恋度分数"""
        prev_score = self.attachment_score
        delta = 0.0
        event_deltas = {
            "positive_interaction": 0.0025,
            "negative_interaction": -0.0035,
            "user_praised_pet_event": 0.018,
            "user_scolded_pet_event": -0.025,
            "shared_positive_emotion": 0.006,
            "task_completed_help": 0.012,
            "proactive_positive_user_response": 0.004,
            "proactive_ignored_or_negative": -0.0025,
            "long_user_absence_tick": -0.0002,
            "user_returned_after_absence": 0.015,
            "app_start_bonus": 0.001,
            "explicit_user_affection": 0.030,
            "explicit_user_dislike_or_rejection": -0.040,
        }
        base_delta = event_deltas.get(event_type, 0.0)
        delta = base_delta * magnitude_factor
        if delta > 0:
            delta *= ((1.0 - prev_score) ** 1.2)
        elif delta < 0:
            delta *= (prev_score ** 1.2)
        self.attachment_score = max(0.0, min(1.0, prev_score + delta))
        if abs(self.attachment_score - prev_score) > 0.0001:
            self._save_character_data()
            logging.info(f"Attachment score updated: {prev_score:.4f} -> {self.attachment_score:.4f} (Event: '{event_type}')")

    def update_self_efficacy(self, domain: str, success_delta: float = 0.0, failure_delta: float = 0.0):
        """更新特定领域的自我效能分数"""
        if domain not in self.self_efficacy:
            logging.warning(f"Self-efficacy domain '{domain}' not recognized. Ignoring update.")
            return
        prev_efficacy = self.self_efficacy[domain]
        conscientiousness = self.character_traits.get(config.SETTING_OCEAN_CONSCIENTIOUSNESS, 0.5)
        neuroticism = self.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        success_mod = 1.0 + (conscientiousness - 0.5) * 0.4
        failure_mod = (1.0 - (conscientiousness - 0.5) * 0.3) * (1.0 + (neuroticism - 0.5) * 0.5)
        new_efficacy = prev_efficacy + (success_delta * success_mod) - (failure_delta * failure_mod)
        self.self_efficacy[domain] = max(0.0, min(1.0, new_efficacy))
        if abs(self.self_efficacy[domain] - prev_efficacy) > 0.001:
            self._save_character_data()
            logging.info(f"Self-efficacy for '{domain}' changed: {prev_efficacy:.4f} -> {self.self_efficacy[domain]:.4f}")
    def handle_significant_event(self, event_type: str, strength_modifier: float = 1.0, associated_text: Optional[str] = None) -> Optional[Dict[str, float]]:
        """處理重大事件，計算對OCEAN特質的影響，並返回可能的情緒增強效果。"""
        # --- 整合了您 1.5.2 版本的完整事件列表 ---
        last_event_time = self.db.load_last_personality_event_time(self.user_id)
        current_time = time.time()
        min_interval = 20 if "critical" in event_type else 120
        if current_time - last_event_time < min_interval:
            logging.debug(f"Personality event '{event_type}' throttled.")
            return None

        event_impacts: Dict[str, Dict[str, Any]] = {
            "task_completed_one": {config.SETTING_OCEAN_CONSCIENTIOUSNESS: 0.02, "positive_emotion_boost": 0.1},
            "user_praised_pet": {config.SETTING_OCEAN_AGREEABLENESS: 0.03, config.SETTING_OCEAN_EXTRAVERSION: 0.015, "positive_emotion_boost": 0.15},
            "user_scolded_pet_critical": {config.SETTING_OCEAN_AGREEABLENESS: -0.05, config.SETTING_OCEAN_NEUROTICISM: 0.04, "negative_emotion_boost": 0.25},
            "learned_from_user_text_llm": {config.SETTING_OCEAN_OPENNESS: 0.02, config.SETTING_OCEAN_AGREEABLENESS: 0.01},
            "pet_self_learned_pattern": {config.SETTING_OCEAN_OPENNESS: 0.008, "positive_emotion_boost": 0.03},
            "prolonged_strong_negative_complex": {config.SETTING_OCEAN_NEUROTICISM: 0.03, config.SETTING_OCEAN_EXTRAVERSION: -0.02},
            "prolonged_strong_positive_state": {config.SETTING_OCEAN_NEUROTICISM: -0.025, config.SETTING_OCEAN_EXTRAVERSION: 0.018},
            "successful_self_regulation": {config.SETTING_OCEAN_CONSCIENTIOUSNESS: 0.01, config.SETTING_OCEAN_NEUROTICISM: -0.015}
        }
        
        deltas = event_impacts.get(event_type, {})
        if not deltas:
            logging.warning(f"Unknown personality event type: {event_type}")
            return None

        changed_any_trait = False
        emotion_boost_effects = {
            "positive": deltas.pop("positive_emotion_boost", 0.0) * strength_modifier,
            "negative": deltas.pop("negative_emotion_boost", 0.0) * strength_modifier
        }

        for trait_key, base_delta in deltas.items():
            if trait_key in self.character_traits and isinstance(base_delta, (int, float)):
                current_value = self.character_traits[trait_key]
                mood_stability = self.settings.get(config.SETTING_MOOD_STABILITY, 0.3)
                stability_factor = 1.0 - float(mood_stability) * 0.8
                resistance_factor = 1.0 - abs(current_value - 0.5) * 1.8 
                actual_delta = base_delta * strength_modifier * stability_factor * max(0.01, resistance_factor)
                new_value = max(0.0, min(1.0, current_value + actual_delta))
                if abs(new_value - current_value) > 0.0001:
                    self.character_traits[trait_key] = new_value
                    changed_any_trait = True
                    logging.info(f"Personality trait {trait_key} changed: {current_value:.4f} -> {new_value:.4f}")

        if changed_any_trait:
            self._save_character_data()
            self.db.save_last_personality_event_time(self.user_id, current_time)
        
        return emotion_boost_effects if (emotion_boost_effects["positive"] > 0 or emotion_boost_effects["negative"] > 0) else None

    def add_or_update_characteristic(self, trait_type: str, trait_key: str, trait_value: Any, source: str, initial_relevance_base: float = 0.6, relevance_increment_base: float = 0.15):
        """新增或更新一個個體特徵，包含完整的個性偏見和衝突解決邏輯。"""
        # --- 整合了您 1.5.2 版本的完整邏輯 ---
        now = time.time()
        trait_value_str = str(trait_value).strip()
        if not trait_value_str: return

        openness = self.character_traits.get(config.SETTING_OCEAN_OPENNESS, 0.5)
        conscientiousness = self.character_traits.get(config.SETTING_OCEAN_CONSCIENTIOUSNESS, 0.5)
        neuroticism = self.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        
        existing_trait = self.db.find_characteristic(self.user_id, trait_type, trait_key, trait_value_str)

        if existing_trait:
            if str(existing_trait['trait_value']).strip().lower() == trait_value_str.lower():
                current_relevance_increment = relevance_increment_base * (1.0 + (conscientiousness - 0.5) * 0.20)
                new_relevance = min(1.0, existing_trait['relevance_score'] + current_relevance_increment)
                self.db.reinforce_characteristic(existing_trait['trait_id'], new_relevance, source, now)
                logging.info(f"Reinforced characteristic '{trait_key}'. New relevance: {new_relevance:.3f}")
            else:
                if openness > 0.6:
                    effective_initial_relevance = initial_relevance_base * (1.0 - (neuroticism - 0.5) * 0.15)
                    update_data = {'trait_id': existing_trait['trait_id'], 'trait_value': trait_value_str, 'relevance_score': effective_initial_relevance, 'source': source, 'timestamp': now}
                    self.db.raw_update_characteristic(update_data)
                    logging.info(f"Updated conflicting characteristic '{trait_key}' due to high openness.")
        else:
            effective_initial_relevance = initial_relevance_base * (1.0 + (openness - 0.5) * 0.20)
            effective_initial_relevance *= (1.0 - (neuroticism - 0.5) * 0.15)
            insert_data = {'user_id': self.user_id, 'trait_type': trait_type, 'trait_key': trait_key, 'trait_value': trait_value_str, 'relevance_score': effective_initial_relevance, 'source': source, 'timestamp': now}
            self.db.raw_insert_characteristic(insert_data)
            logging.info(f"Added NEW characteristic '{trait_key}'. Relevance: {effective_initial_relevance:.3f}")

        self.load_characteristics_cache()
    
    def periodic_maintenance(self):
        """執行定期的特徵維護，如衰減和清理"""
        self.db.decay_characteristics_relevance(self.user_id, decay_amount=0.007, decay_interval_days=1.5)
        self.db.remove_low_relevance_characteristics(self.user_id, relevance_threshold=0.035, unused_days_threshold=35)
        self.load_characteristics_cache(min_relevance=0.01)
        logging.info("Periodic personality characteristics maintenance performed.")

    def learn_from_user_text_async(self, text: str):
        """非同步地從使用者文本中學習特徵。"""
        if not self.llm or not text or len(text) < 8: return
        if self.active_user_text_analysis_threads >= self.MAX_CONCURRENT_USER_TEXT_ANALYSIS:
            logging.warning("Max concurrent user text analysis calls reached. Skipping.")
            return
        logging.debug(f"Dispatching user text analysis to worker for: '{text[:50]}...'")
        self.active_user_text_analysis_threads += 1
        thread = threading.Thread(target=self._learn_from_user_text_worker, args=(text,))
        thread.daemon = True
        thread.start()

    def _learn_from_user_text_worker(self, text: str):
        """在背景執行緒中執行使用者文本分析和學習。"""
        try:
            logging.info(f"WORKER: Analyzing user text: '{text[:50]}...'")
            prompt = self._construct_llm_analysis_prompt_for_user_text(text)
            # (此處應有呼叫 LLM 的邏輯)
            # 模擬學習
            time.sleep(random.uniform(1, 3))
            if "喜歡" in text:
                match = re.search(r"我喜歡(.+)", text)
                if match:
                    preference = match.group(1).strip("的。，")
                    self.add_or_update_characteristic(
                        trait_type=config.TRAIT_TYPE_PREFERENCE,
                        trait_key=f"user_likes_{preference[:10].replace(' ','_')}",
                        trait_value=preference,
                        source=config.SOURCE_LLM_INFERENCE_USER_TEXT,
                        initial_relevance_base=0.7
                    )
                    logging.info(f"WORKER: Learned user preference '{preference}' from text.")
        finally:
            self.active_user_text_analysis_threads -= 1

    def _construct_llm_analysis_prompt_for_user_text(self, user_text: str) -> str:
        """為LLM建構詳細的、用於從使用者文本中提取特徵的提示。"""
        # --- 整合了您 1.5.2 版本的完整提示邏輯 ---
        categories_description = f"""
        1.  Preferences_Opinions: 使用者的好惡、觀點 (trait_type: {config.TRAIT_TYPE_PREFERENCE})
        2.  Habits_Routines: 使用者的習慣或常規 (trait_type: {config.TRAIT_TYPE_HABIT})
        3.  Key_Information_Entities: 關於使用者的事實資訊 (trait_type: {config.TRAIT_TYPE_USER_INFO})
        4.  Topics_of_Interest: 使用者感興趣的話題 (trait_type: {config.TRAIT_TYPE_FAVORITE_TOPIC})
        """
        prompt = f"""請分析以下「使用者文字」，提取個人特徵。嚴格按照JSON格式輸出，若無則空列表 `[]`。

        可提取類別:
        {categories_description}

        使用者文字：
        ---
        {user_text}
        ---
        請只輸出JSON。
        """
        return prompt.strip()

    def learn_from_pet_text_async(self, text: str):
        """非同步地從寵物自身文本中學習特徵（自我反思）。"""
        if not self.llm or not text or len(text) < 12: return
        if self.active_pet_text_analysis_threads >= self.MAX_CONCURRENT_PET_TEXT_ANALYSIS:
            logging.warning("Max concurrent pet text analysis calls reached. Skipping.")
            return
        logging.debug(f"Dispatching pet text analysis to worker for: '{text[:50]}...'")
        self.active_pet_text_analysis_threads += 1
        thread = threading.Thread(target=self._learn_from_pet_text_worker, args=(text,))
        thread.daemon = True
        thread.start()
        
    # core/personality_system.py (部分補全)

    def _construct_llm_analysis_prompt_for_user_text(self, user_text: str) -> str:

        categories_description = f"""
        1.  **Preferences_Opinions**:
            * Specific Likes/Dislikes: User's stated likes/dislikes (e.g., "我喜歡貓", "我討厭下雨"). Identify object/concept and sentiment. `trait_key` examples: "likes_animal", "dislikes_weather".
            * General Opinions: User's views on topics (e.g., "科技發展太快了"). `trait_key` examples: "opinion_on_technology_speed".
        2.  **Habits_Routines**: User's recurring actions (e.g., "我每天早上都喝咖啡"). `trait_key` examples: "habit_morning_drink".
        3.  **Key_Information_Entities**:
            * Personal Information: Facts about the user (e.g., "我是學生", "我家有兩隻狗"). `trait_key` examples: "user_occupation", "user_pets_dog_count".
            * Important Named Entities: People, places, etc., frequently mentioned. `trait_key` examples: "mentioned_person_friend_Alice".
        4.  **Topics_of_Interest**: Subjects user seems interested in. `trait_key` examples: "interest_topic_space".
        5.  **User_Feedback_To_Pet**: Direct feedback on the pet's behavior. `trait_key` examples: "feedback_pet_response_style_positive".
        """
        prompt = f"""你是一個專業的自然語言理解分析師。仔細分析以下「使用者文字」，提取個人特徵、偏好、習慣、重要資訊等。嚴格按照JSON格式輸出，若無則空列表 `[]` 或省略。不要有JSON以外的文字。

        可提取類別與鍵名範例 (`trait_key` 請用英文/拼音，具體化):
        {categories_description}

        JSON輸出格式範例:
        {{
          "preferences_opinions": [
            {{"trait_type": "{config.TRAIT_TYPE_PREFERENCE}", "trait_key": "likes_animal", "trait_value": "貓"}}
          ],
          "key_information_entities": [
            {{"trait_type": "{config.TRAIT_TYPE_USER_INFO}", "trait_key": "user_occupation", "trait_value": "軟體工程師"}}
          ]
        }}

        `trait_type` 必須是 "{config.TRAIT_TYPE_PREFERENCE}", "{config.TRAIT_TYPE_HABIT}", "{config.TRAIT_TYPE_USER_INFO}", "{config.TRAIT_TYPE_FAVORITE_TOPIC}", "{config.TRAIT_TYPE_RESPONSE_STYLE}".

        使用者文字：
        ---
        {user_text}
        ---
        請只輸出JSON。
        """
        return prompt.strip()

    def _process_llm_analysis_response(self, llm_response_text: str, original_user_text: str):
        """
        解析 LLM 的 JSON 响应，并将分析结果更新为个体特征。
        """
        if not llm_response_text:
            logging.warning("LLM User Text Analysis response was empty.")
            return
        try:
            # 使用 LLM 服务中更强大的解析器
            parsed_data = self.llm._parse_structured_output(llm_response_text)
            if not isinstance(parsed_data, dict):
                logging.warning(f"LLM User Text Analysis: Parsed data is not a dictionary.")
                return
        except Exception as e:
            logging.error(f"LLM User Text Analysis: Error processing response: {e}. Response: '{llm_response_text[:500]}'")
            return

        learned_count = 0
        allowed_trait_types = [
            config.TRAIT_TYPE_PREFERENCE, config.TRAIT_TYPE_HABIT, config.TRAIT_TYPE_USER_INFO,
            config.TRAIT_TYPE_FAVORITE_TOPIC, config.TRAIT_TYPE_RESPONSE_STYLE
        ]

        for category_key, items in parsed_data.items():
            if not isinstance(items, list): continue
            for item in items:
                if not isinstance(item, dict): continue
                
                trait_type = item.get("trait_type")
                trait_key = item.get("trait_key")
                trait_value = item.get("trait_value")
                relevance_modifier = item.get("relevance_score_modifier", 0.0)

                if not all([trait_type, trait_key, trait_value]) or trait_type not in allowed_trait_types:
                    continue

                trait_key = str(trait_key).strip().replace(" ", "_").lower()
                trait_value = str(trait_value).strip()
                if not trait_key or not trait_value: continue

                initial_relevance = 0.55 + float(relevance_modifier)
                initial_relevance = max(0.15, min(0.95, initial_relevance))

                self.add_or_update_characteristic(
                    trait_type=trait_type,
                    trait_key=trait_key,
                    trait_value=trait_value,
                    initial_relevance_base=initial_relevance,
                    source=config.SOURCE_LLM_INFERENCE_USER_TEXT
                )
                learned_count += 1
                logging.info(f"LLM User Text Analysis Result: Stored characteristic: Type='{trait_type}', Key='{trait_key}', Value='{str(trait_value)[:60]}...'")

        if learned_count > 0:
            logging.info(f"LLM successfully extracted {learned_count} characteristics from: '{original_user_text[:70]}...'")
            self.load_characteristics_cache()
            self.handle_significant_event("learned_from_user_text_llm", strength_modifier=0.08 + (learned_count * 0.015))

    def _learn_from_user_text_worker(self, text: str):
        """在背景线程中执行使用者文本分析和学习的完整流程。"""
        try:
            if not self.llm: return
            logging.info(f"WORKER: Starting characteristic learning for user text: '{text[:100]}...'")
            
            analysis_prompt = self._construct_llm_analysis_prompt_for_user_text(text)
            analysis_config = {"temperature": 0.30, "max_output_tokens": 1000}
            
            if hasattr(self.llm, 'model') and hasattr(self.llm.model, 'generate_content'):
                response = self.llm.model.generate_content(analysis_prompt, generation_config=analysis_config)
                response_text = response.text.strip() if response.parts else ""
                
                if response_text:
                    self._process_llm_analysis_response(response_text, text)
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    logging.warning(f"WORKER: LLM characteristic analysis request blocked: {response.prompt_feedback.block_reason_message}")
            else:
                logging.error("WORKER: LLM service does not have the expected 'model.generate_content' method.")
        except Exception as e:
            logging.error(f"WORKER: Error during LLM characteristic analysis: {e}", exc_info=True)
        finally:
            self.active_user_text_analysis_threads = max(0, self.active_user_text_analysis_threads - 1)
            logging.debug(f"WORKER: Finished processing user text. Active threads: {self.active_user_text_analysis_threads}")
    def reflect_on_thoughts_async(self):
        """非同步地觸發一次對內心思考的自我反思。"""
        if not self.llm:
            logging.warning("Cannot reflect on thoughts, LLM is not available.")
            return
        logging.info("Dispatching manual thought reflection to worker...")
        thread = threading.Thread(target=self._reflect_on_thoughts_worker)
        thread.daemon = True
        thread.start()

    def _reflect_on_thoughts_worker(self):
        """在背景執行緒中執行對內心思考的分析和學習。"""
        logging.info("WORKER: Starting reflection on recent internal thoughts.")
        all_recent_stm = self.db.load_memory(self.user_id, is_long_term=False, limit=40)
        internal_thoughts = [str(mem.get('content', ''))[len("小星思考:"):].strip() for mem in all_recent_stm if str(mem.get('content', '')).startswith("小星思考:")]
        if len(internal_thoughts) < 5:
            logging.info(f"WORKER: Insufficient thoughts ({len(internal_thoughts)}) for reflection.")
            return
        time.sleep(2)
        thought_summary = " ".join(internal_thoughts)
        if "宇宙" in thought_summary or "星星" in thought_summary:
            self.add_or_update_characteristic(
                trait_type=config.TRAIT_TYPE_FAVORITE_TOPIC,
                trait_key="pet_topic_astronomy",
                trait_value="天文學和宇宙",
                source=config.SOURCE_PET_OBSERVATION,
                initial_relevance_base=0.75
            )
            logging.info("WORKER: Reflected and learned interest in astronomy.")
        self._last_thought_reflection_time = time.time()
    # 請將這個程式碼區塊加入到 core/personality_system.py 的 PersonalitySystem 類別末尾

    def _construct_llm_analysis_prompt_for_pet_text(self, pet_text_to_analyze: str) -> str:
        """為LLM建構提示，用於分析寵物自身的文本以提取新興模式。"""
        patterns_description = f"""
        1.  **Recurring Distinctive Phrases (Quirks/Catchphrases)**: 獨特的、反覆使用的短語 (trait_type: "{config.TRAIT_TYPE_QUIRK}").
        2.  **Common Language Patterns**: 一致的語言風格、表情符號用法 (trait_type: "{config.TRAIT_TYPE_LANGUAGE_PATTERN}").
        3.  **Self-Referential Statements (Self-Concept)**: 寵物描述自己的感受、特質 (trait_type: "{config.TRAIT_TYPE_PET_SELF_CONCEPT}").
        """
        prompt = f"""你是一位語言學家。分析以下「小星說的文字」，辨識其獨特的語言模式、口頭禪或關於自身概念的陳述。嚴格JSON輸出，無則空列表 `[]`。

        可提取模式:
        {patterns_description}

        小星說的文字 (待分析):
        ---
        {pet_text_to_analyze}
        ---
        請只輸出JSON。
        """
        return prompt.strip()

    def _process_llm_pet_text_analysis_response(self, llm_response_text: str, original_pet_text: str):
        """解析 LLM 對寵物自身文本的分析回應，並更新特徵。"""
        if not llm_response_text:
            logging.warning("LLM Pet Text Analysis: Response was empty.")
            return
        try:
            match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```|(\{[\s\S]*?\})", llm_response_text, re.DOTALL)
            if not match:
                logging.warning(f"LLM Pet Text Analysis: No JSON object in response: '{llm_response_text[:200]}...'")
                return
            json_str = match.group(1) if match.group(1) else match.group(2)
            extracted_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logging.error(f"LLM Pet Text Analysis: JSON parsing failed: {e}. Response: '{llm_response_text[:500]}'")
            return

        learned_count = 0
        allowed_pet_trait_types = [config.TRAIT_TYPE_QUIRK, config.TRAIT_TYPE_LANGUAGE_PATTERN, config.TRAIT_TYPE_PET_SELF_CONCEPT]

        for category_key, items in extracted_data.items():
            if not isinstance(items, list): continue
            for item in items:
                if not isinstance(item, dict): continue
                
                trait_type = item.get("trait_type")
                trait_key = item.get("trait_key")
                trait_value = item.get("trait_value")
                if not all([trait_type, trait_key, trait_value]) or trait_type not in allowed_pet_trait_types:
                    continue
                
                self.add_or_update_characteristic(
                    trait_type=trait_type,
                    trait_key=str(trait_key).strip().replace(" ", "_").lower(),
                    trait_value=str(trait_value).strip(),
                    source=config.SOURCE_LLM_INFERENCE_PET_TEXT,
                    initial_relevance_base=0.5
                )
                learned_count += 1
                logging.info(f"LLM Pet Text Analysis: Stored pet characteristic: Type='{trait_type}', Value='{str(trait_value)[:60]}...'")

        if learned_count > 0:
            logging.info(f"LLM Pet Text Analysis: Stored {learned_count} self-learned characteristics from: '{original_pet_text[:70]}...'")
            self.load_characteristics_cache()
            self.handle_significant_event("pet_self_learned_pattern", strength_modifier=0.05 + (learned_count * 0.015))

    def _learn_from_pet_text_worker(self, text: str):
        """在背景執行緒中執行寵物自身文本的分析和學習。"""
        try:
            if not self.llm or not text or len(text) < 12:
                logging.debug("WORKER: Skipping pet text analysis: insufficient text or no model.")
                return

            logging.info(f"WORKER: Starting characteristic analysis for pet text: '{text[:100]}...'")
            time.sleep(random.uniform(0.6, 1.8))
            
            analysis_prompt = self._construct_llm_analysis_prompt_for_pet_text(text)
            analysis_config = {"temperature": 0.35, "max_output_tokens": 500}

            if hasattr(self.llm, 'model') and hasattr(self.llm.model, 'generate_content'):
                response = self.llm.model.generate_content(analysis_prompt, generation_config=analysis_config)
                response_text = response.text.strip() if response.parts else ""
                
                if response_text:
                    self._process_llm_pet_text_analysis_response(response_text, text)
                elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                    logging.warning(f"WORKER: LLM pet text analysis request blocked: {response.prompt_feedback.block_reason_message}")

        except Exception as e:
            logging.error(f"WORKER: Error during LLM pet text analysis: {e}", exc_info=True)
        finally:
            self.active_pet_text_analysis_threads = max(0, self.active_pet_text_analysis_threads - 1)
            logging.debug(f"WORKER: Finished processing pet text. Active threads: {self.active_pet_text_analysis_threads}")