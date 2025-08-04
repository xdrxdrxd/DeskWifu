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
from datetime import datetime

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
        
        # --- [新增] 模擬神經化學狀態 ---
        self.sim_neuro_state = {
            "motivation": 0.5,     # 類比多巴胺: 影響主動性、對獎勵的反應
            "mood_balance": 0.5,   # 類比血清素: 影響情緒穩定性、對負面刺激的緩衝
            "stress_level": 0.1,   # 類比皮質醇: 壓力水平 (0=無壓力, 1=極高壓力)
            "social_warmth": 0.5   # 類比催產素: 影響社交連結感、信任、共情
        }
        # --- [新增] 動態計算的行為參數 ---
        self.effective_mood_stability: float = 0.3
        self.effective_emo_sensitivity: float = 1.0
        self.effective_proactive_freq_modifier: float = 1.0
        self._apply_sim_neuro_effects() # 首次計算
        
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
        parts = []
        culture = self.demographics.get(config.SETTING_DEMO_CULTURE)
        age_group = self.demographics.get(config.SETTING_DEMO_AGE_GROUP)
        gender = self.demographics.get(config.SETTING_DEMO_GENDER)
        if culture: parts.append(f"你的文化背景設定為「{culture}」。")
        if age_group: parts.append(f"你的年齡層設定為「{age_group}」。")
        if gender: parts.append(f"你的性別認同設定為「{gender}」。")
        if not parts: return "你目前沒有特定的背景設定。"
        return " ".join(parts) + " 這些背景會影響你的說話方式和觀點。"

    def get_attachment_description_for_llm(self) -> str:
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
        hints = []
        general = self.self_efficacy.get("general", 0.5)
        social = self.self_efficacy.get("social", 0.5)
        task_eff = self.self_efficacy.get("task_management", 0.5)
        info_eff = self.self_efficacy.get("info_retrieval", 0.5)
        if general > 0.75: hints.append("你對自己整體的能力非常有信心。")
        elif general < 0.3: hints.append("你最近對自己整體的能力可能有點懷疑。")
        if social > 0.75: hints.append("在社交互動方面，你感覺非常自在且遊刃有餘。")
        elif social < 0.3: hints.append("在社交互動方面，你可能會非常謹慎或退縮。")
        if task_eff > 0.75: hints.append("對於管理和提醒任務，你覺得自己做得非常出色。")
        elif task_eff < 0.3: hints.append("在任務管理方面，你可能覺得非常吃力。")
        if self.settings.get(config.SETTING_SEARCH_API_ENABLED, 0):
            if info_eff > 0.75: hints.append("如果需要查找資訊，你對自己能找到準確結果非常有把握。")
            elif info_eff < 0.3: hints.append("在查找資訊方面，你感到非常不確定，擔心提供錯誤資訊。")
        if not hints: return ""
        return "關於你目前的「自我效能感」：「" + " ".join(hints) + "」這會影響你的自信程度和主動性。"

    # --- [新增] 模擬神經化學狀態的LLM提示 ---
    def get_neuro_state_description_for_llm(self) -> str:
        """根據模擬神經化學狀態產生給LLM的行為指導"""
        neuro_state_desc_parts = []
        motivation = self.sim_neuro_state.get("motivation", 0.5)
        stress = self.sim_neuro_state.get("stress_level", 0.1)
        mood_bal = self.sim_neuro_state.get("mood_balance", 0.5)
        
        if motivation > 0.75: neuro_state_desc_parts.append("你目前感覺精力非常充沛，充滿探索欲和動力！")
        elif motivation < 0.3: neuro_state_desc_parts.append("你目前感覺有點缺乏動力，也許提不起勁。")
        if stress > 0.7: neuro_state_desc_parts.append("你最近感到壓力很大，可能容易疲憊、緊張或煩躁。")
        elif stress < 0.1: neuro_state_desc_parts.append("你目前感覺非常輕鬆自在，沒什麼壓力。")
        if mood_bal < 0.3: neuro_state_desc_parts.append("你的心情似乎非常低落或很不穩定。")
        elif mood_bal > 0.75: neuro_state_desc_parts.append("你的心情整體非常平穩愉悅，充滿正能量。")

        if not neuro_state_desc_parts: return ""
        return "關於你當前的內在狀態：「" + " ".join(neuro_state_desc_parts) + "」這會強烈影響你的想法和行為。"

    def get_characteristics_description_for_llm(self) -> str:
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
        prev_score = self.attachment_score
        delta = 0.0
        event_deltas = {
            "positive_interaction": 0.0025, "negative_interaction": -0.0035,
            "user_praised_pet_event": 0.018, "user_scolded_pet_event": -0.025,
            "shared_positive_emotion": 0.006, "task_completed_help": 0.012,
            "proactive_positive_user_response": 0.004, "proactive_ignored_or_negative": -0.0025,
            "long_user_absence_tick": -0.0002, "user_returned_after_absence": 0.015,
            "app_start_bonus": 0.001, "explicit_user_affection": 0.030,
            "explicit_user_dislike_or_rejection": -0.040,
        }
        base_delta = event_deltas.get(event_type, 0.0)
        delta = base_delta * magnitude_factor
        if delta > 0: delta *= ((1.0 - prev_score) ** 1.2)
        elif delta < 0: delta *= (prev_score ** 1.2)
        self.attachment_score = max(0.0, min(1.0, prev_score + delta))
        if abs(self.attachment_score - prev_score) > 0.0001:
            self._save_character_data()
            logging.info(f"Attachment score updated: {prev_score:.4f} -> {self.attachment_score:.4f} (Event: '{event_type}')")

    def update_self_efficacy(self, domain: str, success_delta: float = 0.0, failure_delta: float = 0.0):
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
        
        # --- [新增] 事件觸發神經化學狀態更新 ---
        self._update_sim_neuro_state(event_type, intensity=strength_modifier)
        
        return emotion_boost_effects if (emotion_boost_effects["positive"] > 0 or emotion_boost_effects["negative"] > 0) else None

    def add_or_update_characteristic(self, trait_type: str, trait_key: str, trait_value: Any, source: str, initial_relevance_base: float = 0.6, relevance_increment_base: float = 0.15):
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
    
    # --- [替換/新增] 模擬神經化學的完整邏輯 ---
    def _update_sim_neuro_state(self, event_type, intensity=0.1):
        """根據事件更新模擬的神經化學狀態"""
        neuroticism = self.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        extraversion = self.character_traits.get(config.SETTING_OCEAN_EXTRAVERSION, 0.5)
        agreeableness = self.character_traits.get(config.SETTING_OCEAN_AGREEABLENESS, 0.5)
        
        # Motivation (Dopamine-like)
        motivation_change = 0.0
        if event_type in ["user_praised_pet", "explicit_user_affection", "task_completed_one", "successful_search"]:
            motivation_change = 0.05 + (intensity * 0.15) * (1 + (extraversion - 0.5) * 0.3)
        elif event_type in ["task_failed_or_ignored", "negative_interaction", "user_scolded_pet_critical"]:
            motivation_change = -(0.03 + intensity * 0.10)
        if motivation_change != 0:
            prev_val = self.sim_neuro_state["motivation"]
            self.sim_neuro_state["motivation"] = max(0.05, min(0.95, prev_val + motivation_change))
            if abs(self.sim_neuro_state["motivation"] - prev_val) > 0.001:
                logging.info(f"SimNeuro: Motivation {prev_val:.3f} -> {self.sim_neuro_state['motivation']:.3f} (Event: {event_type})")

        # Mood Balance (Serotonin-like)
        mood_balance_change = 0.0
        if event_type in ["shared_positive_emotion", "user_returned_after_absence"]:
            mood_balance_change = 0.02 + (intensity * 0.08) * (1 + (agreeableness - 0.5) * 0.2)
        elif event_type in ["user_scolded_pet_critical", "prolonged_strong_negative_complex"]:
            mood_balance_change = -(0.03 + intensity * 0.12) * (1 + (neuroticism - 0.5) * 0.4)
        if mood_balance_change != 0:
            prev_val = self.sim_neuro_state["mood_balance"]
            self.sim_neuro_state["mood_balance"] = max(0.1, min(0.9, prev_val + mood_balance_change))
            if abs(self.sim_neuro_state["mood_balance"] - prev_val) > 0.001:
                logging.info(f"SimNeuro: Mood Balance {prev_val:.3f} -> {self.sim_neuro_state['mood_balance']:.3f} (Event: {event_type})")

        # Stress Level (Cortisol-like)
        stress_change = 0.0
        if event_type in ["negative_interaction", "user_scolded_pet_critical", "task_failed_or_ignored"]:
            stress_change = 0.05 + (intensity * 0.20) * (1 + (neuroticism - 0.5) * 0.5)
        elif event_type in ["successful_self_regulation", "task_completed_one", "user_praised_pet"]:
            stress_change = -(0.03 + intensity * 0.15)
        if stress_change != 0:
            prev_val = self.sim_neuro_state["stress_level"]
            self.sim_neuro_state["stress_level"] = max(0.0, min(1.0, prev_val + stress_change))
            if abs(self.sim_neuro_state["stress_level"] - prev_val) > 0.001:
                logging.info(f"SimNeuro: Stress Level {prev_val:.3f} -> {self.sim_neuro_state['stress_level']:.3f} (Event: {event_type})")

        # Social Warmth (Oxytocin-like)
        social_warmth_change = 0.0
        if event_type in ["explicit_user_affection", "shared_positive_emotion", "user_returned_after_absence"]:
            social_warmth_change = 0.04 + (intensity * 0.12) * (0.8 + self.attachment_score * 0.4)
        elif event_type in ["explicit_user_dislike_or_rejection", "proactive_ignored_or_negative"]:
            social_warmth_change = -(0.05 + intensity * 0.15)
        if social_warmth_change != 0:
            prev_val = self.sim_neuro_state["social_warmth"]
            self.sim_neuro_state["social_warmth"] = max(0.05, min(0.95, prev_val + social_warmth_change))
            if abs(self.sim_neuro_state["social_warmth"] - prev_val) > 0.001:
                logging.info(f"SimNeuro: Social Warmth {prev_val:.3f} -> {self.sim_neuro_state['social_warmth']:.3f} (Event: {event_type})")

        self._apply_sim_neuro_effects()

    def _apply_sim_neuro_effects(self):
        """將模擬神經化學狀態應用到行為參數"""
        motivation = self.sim_neuro_state.get("motivation", 0.5)
        mood_balance = self.sim_neuro_state.get("mood_balance", 0.5)
        stress_level = self.sim_neuro_state.get("stress_level", 0.1)
        
        # 影響情緒穩定度和敏感度
        self.effective_mood_stability = float(self.settings.get(config.SETTING_MOOD_STABILITY, 0.3)) + (mood_balance - 0.5) * 0.20
        self.effective_mood_stability = max(0.05, min(0.95, self.effective_mood_stability))

        self.effective_emo_sensitivity = float(self.settings.get(config.SETTING_EMO_SENSITIVITY, 1.0)) - (mood_balance - 0.5) * 0.4
        self.effective_emo_sensitivity *= (1.0 + stress_level * 0.3)
        self.effective_emo_sensitivity = max(0.2, min(2.5, self.effective_emo_sensitivity))
        
        # 影響主動行為頻率
        self.effective_proactive_freq_modifier = 1.0 + (motivation - 0.5) * 0.8 - stress_level * 0.5
        self.effective_proactive_freq_modifier = max(0.2, min(2.0, self.effective_proactive_freq_modifier))

    def _decay_sim_neuro_state(self):
        """定期衰減模擬神經化學狀態，使其趨向基線"""
        decay_rates = {"motivation": 0.015, "mood_balance": 0.01, "stress_level": 0.025, "social_warmth": 0.012}
        baselines = {"motivation": 0.45, "mood_balance": 0.5, "stress_level": 0.08, "social_warmth": 0.45}
        
        changed = False
        for state, value in self.sim_neuro_state.items():
            rate, baseline = decay_rates.get(state, 0.01), baselines.get(state, 0.5)
            prev_val = value
            new_value = value - rate * (value - baseline) * random.uniform(0.8, 1.2)
            self.sim_neuro_state[state] = max(0.0, min(1.0, new_value)) # Clamp
            if abs(self.sim_neuro_state[state] - prev_val) > 0.001:
                changed = True

        if changed:
            logging.debug(f"SimNeuro states decayed: {self.sim_neuro_state}")
            self._apply_sim_neuro_effects()

    def periodic_maintenance(self):
        """執行定期的特徵維護，如衰減和清理"""
        self.db.decay_characteristics_relevance(self.user_id, decay_amount=0.007, decay_interval_days=1.5)
        self.db.remove_low_relevance_characteristics(self.user_id, relevance_threshold=0.035, unused_days_threshold=35)
        self.load_characteristics_cache(min_relevance=0.01)
        self._decay_sim_neuro_state() # --- [新增] 定期衰減神經狀態 ---
        logging.info("Periodic personality characteristics maintenance performed.")

    def learn_from_user_text_async(self, text: str):
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
            analysis_prompt = self._construct_llm_analysis_prompt_for_user_text(text)
            analysis_config = {"temperature": 0.30, "max_output_tokens": 1000}
            
            response = self.llm.model.generate_content(analysis_prompt, generation_config=analysis_config)
            response_text = response.text.strip() if response.parts else ""
            
            if response_text:
                self._process_llm_analysis_response(response_text, text)
        except Exception as e:
            logging.error(f"WORKER: Error during LLM characteristic analysis: {e}", exc_info=True)
        finally:
            self.active_user_text_analysis_threads = max(0, self.active_user_text_analysis_threads - 1)

    def _construct_llm_analysis_prompt_for_user_text(self, user_text: str) -> str:
        # (此方法在新舊版本中已存在且相似，此處保持不變)
        categories_description = f"""...""" # 省略，與您提供的檔案相同
        prompt = f"""...""" # 省略
        return prompt.strip()

    def _process_llm_analysis_response(self, llm_response_text: str, original_user_text: str):
        # (此方法在新舊版本中已存在且相似，此處保持不變)
        pass

    def learn_from_pet_text_async(self, text: str):
        if not self.llm or not text or len(text) < 12: return
        if self.active_pet_text_analysis_threads >= self.MAX_CONCURRENT_PET_TEXT_ANALYSIS:
            logging.warning("Max concurrent pet text analysis calls reached. Skipping.")
            return
        logging.debug(f"Dispatching pet text analysis to worker for: '{text[:50]}...'")
        self.active_pet_text_analysis_threads += 1
        thread = threading.Thread(target=self._learn_from_pet_text_worker, args=(text,))
        thread.daemon = True
        thread.start()
        
    def _learn_from_pet_text_worker(self, text: str):
        # (此方法在新舊版本中已存在且相似，此處保持不變)
        pass

    # --- [替換] 內省式學習的完整邏輯 ---
    def reflect_on_thoughts_async(self):
        """非同步地觸發一次對內心思考的自我反思。"""
        if not self.llm:
            logging.warning("Cannot reflect on thoughts, LLM is not available.")
            return
        
        now_ts = time.time()
        if (now_ts - self._last_thought_reflection_time) < (12 * 3600 * random.uniform(0.8, 1.2)):
            return

        logging.info("Dispatching thought reflection to worker...")
        thread = threading.Thread(target=self._reflect_on_thoughts_worker)
        thread.daemon = True
        thread.start()

    def _reflect_on_thoughts_worker(self):
        """在背景執行緒中執行對內心思考的分析和學習。"""
        logging.info("WORKER: Starting reflection on recent internal thoughts.")
        all_recent_stm = self.db.load_memory(self.user_id, is_long_term=False, limit=50)
        
        internal_thoughts = []
        for mem in all_recent_stm:
            if str(mem.get('content', '')).startswith("小星思考:"):
                thought_text = str(mem.get('content', ''))[len("小星思考:"):].strip()
                if len(thought_text) > 10:
                    ts = datetime.fromtimestamp(mem['timestamp']).strftime('%Y-%m-%d %H:%M')
                    internal_thoughts.append(f"- \"{thought_text[:150]}...\" (記錄於: {ts})")
        
        if len(internal_thoughts) < 5:
            logging.info(f"WORKER: Insufficient thoughts ({len(internal_thoughts)}) for reflection.")
            self._last_thought_reflection_time = time.time()
            return
        
        reflection_prompt = (
            "你（小星）正在進行自我反思。以下是你最近的「內心思考」片段。\n"
            "請閱讀並歸納出：\n"
            "1. 反覆出現的關於「你自己」的看法或感受？\n"
            "2. 新興的「興趣點」或「好奇的方向」？\n"
            "3. 持續的「擔憂」或「目標」？\n\n"
            "請將分析總結為 1 到 3 個「自我洞察點」。\n"
            "對於每個洞察點，提供：\n"
            "  a. `insight_type`: 類型，從 [\"self_perception\", \"emerging_interest\", \"recurring_concern\"] 中選擇\n"
            "  b. `description`: 簡短描述。\n"
            "  c. `trait_suggestion`: 建議一個 `trait_type` (從 pet_self_concept, favorite_topic 中選擇) 和 `trait_value`。\n\n"
            "內心思考記錄：\n"
            "```\n" + "\n".join(internal_thoughts) + "\n```\n\n"
            "請以 JSON 陣列的格式輸出，若無則空陣列 `[]`。請只輸出JSON。"
        )

        try:
            response = self.llm.model.generate_content(
                reflection_prompt,
                generation_config={"temperature": 0.4, "max_output_tokens": 600}
            )
            response_text = response.text.strip() if response.parts else ""
            if not response_text:
                return

            json_match = re.search(r"```json\s*(\[[\s\S]*?\])\s*```|(\[[\s\S]*?\])", response_text, re.DOTALL)
            if not json_match: return
            
            insights = json.loads(json_match.group(1) or json_match.group(2))
            if not isinstance(insights, list): return

            learned_count = 0
            for insight in insights:
                suggestion = insight.get("trait_suggestion")
                if isinstance(suggestion, dict) and suggestion.get("trait_type") and suggestion.get("trait_value"):
                    self.add_or_update_characteristic(
                        trait_type=suggestion["trait_type"],
                        trait_key=f"{suggestion['trait_type']}_{suggestion['trait_value'][:15].replace(' ','_')}",
                        trait_value=suggestion["trait_value"],
                        source=config.SOURCE_PET_OBSERVATION,
                        initial_relevance_base=0.6
                    )
                    learned_count += 1
            if learned_count > 0:
                logging.info(f"WORKER: Learned {learned_count} new traits from self-reflection.")
                self.load_characteristics_cache()
                self.handle_significant_event("pet_self_learned_pattern", strength_modifier=0.1 * learned_count)
        except Exception as e:
            logging.error(f"WORKER: Error during thought reflection: {e}", exc_info=True)
        finally:
            self._last_thought_reflection_time = time.time()
