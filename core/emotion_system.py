# core/emotion_system.py
import random
import logging
import math
from typing import Dict, Optional

import config
from database import DatabaseManager

class EmotionSystem:
    """管理寵物的所有情緒邏輯，包括離散情緒和核心情感模型。"""

    def __init__(self, db_manager: DatabaseManager, user_id: str, settings: Dict):
        self.db = db_manager
        self.user_id = user_id
        self.settings = settings
        self.emotions = self.db.load_emotions(self.user_id)
        
        # 如果是全新使用者或資料庫損毀，則用預設值重新初始化
        if not self.emotions or all(v == 0.5 for v in self.emotions.values()):
            self.emotions = config.EMOTIONS.copy()
            for name, val in self.emotions.items():
                self.db.save_emotion(self.user_id, name, val, trigger_event="initialization_or_reset")
            logging.info(f"Emotions initialized/reset for user {self.user_id}")
        
        # 核心情感狀態 (Valence-Arousal Model)
        self.core_affect = {"valence": 0.0, "arousal": 0.0}

    def get_current_emotions(self) -> Dict[str, float]:
        """返回當前的情緒字典的副本"""
        return self.emotions.copy()

    def get_dominant_emotion_for_display(self) -> str:
        """計算並返回用於UI顯示的主要情緒鍵名"""
        if not self.emotions:
            return "neutral"

        max_val = 0.0
        dominant_raw_emotion_name = "neutral"
        for emo, val in self.emotions.items():
            if val > max_val:
                max_val = val
                dominant_raw_emotion_name = emo
        
        if max_val < 0.35: # 如果最強烈的情緒也很微弱，則表現為中性
            return "neutral"

        # 將原始的複雜情緒映射到一組有限的、有對應圖片的顯示情緒
        if dominant_raw_emotion_name in ['joy', 'adoration', 'contentment', 'satisfaction', 'relief', 'hope', 'optimism', 'love', 'gratitude', 'amusement', 'triumph']:
            return "happy"
        if dominant_raw_emotion_name == 'excitement':
            return "excited"
        if dominant_raw_emotion_name in ['sadness', 'disappointment', 'empathetic_pain', 'regret', 'shame', 'guilt']:
            return "sad"
        if dominant_raw_emotion_name in ['anger', 'frustration', 'hatred', 'jealousy', 'disgust']:
            return "angry"
        if dominant_raw_emotion_name in ['anxiety', 'fear', 'horror', 'awkwardness', 'confusion', 'distrust']:
            return "anxious"
        if dominant_raw_emotion_name == 'boredom':
            return "bored"
            
        return "neutral"

    def decay_emotions(self, mood_stability: float):
        """根據情緒穩定度，使離散情緒值向中性(0.5)衰減"""
        decay_rate = self.settings.get(config.SETTING_DECAY_RATE, 0.02)
        decay_factor = 1.0 - mood_stability # 穩定度越高，衰減因子越小
        effective_decay_rate = decay_rate * decay_factor
        
        for name, value in self.emotions.items():
            if name == 'neutral': continue
            prev_value = value
            diff_from_neutral = value - 0.5
            new_value = value - (diff_from_neutral * effective_decay_rate * random.uniform(0.8, 1.2))
            
            # 確保不會衰減超過中性點
            if diff_from_neutral > 0: new_value = max(0.5, new_value)
            else: new_value = min(0.5, new_value)

            if abs(new_value - prev_value) > 0.001:
                self.emotions[name] = max(0.0, min(1.0, new_value))
                self.db.save_emotion(self.user_id, name, self.emotions[name], prev_value, "decay")
        
        logging.debug("Discrete emotions decayed.")

    def decay_core_affect(self, is_sleeping: bool):
        """使核心情感狀態向中性水平衰減"""
        target_arousal = 0.05 if is_sleeping else 0.1
        target_valence = 0.0
        arousal_decay_rate = 0.15 if is_sleeping else 0.08
        valence_decay_rate = 0.03 if is_sleeping else 0.02

        prev_valence = self.core_affect["valence"]
        prev_arousal = self.core_affect["arousal"]

        # Arousal decay
        self.core_affect["arousal"] = max(target_arousal, self.core_affect["arousal"] - arousal_decay_rate * (self.core_affect["arousal"] - target_arousal))
        # Valence decay
        if self.core_affect["valence"] > target_valence:
            self.core_affect["valence"] = max(target_valence, self.core_affect["valence"] - valence_decay_rate * (self.core_affect["valence"] - target_valence))
        else:
            self.core_affect["valence"] = min(target_valence, self.core_affect["valence"] + valence_decay_rate * (target_valence - self.core_affect["valence"]))

        if abs(self.core_affect["valence"] - prev_valence) > 0.001 or abs(self.core_affect["arousal"] - prev_arousal) > 0.001:
            logging.debug(f"Core affect decayed: V:{self.core_affect['valence']:.2f}, A:{self.core_affect['arousal']:.2f}")
            # 核心情感衰減後，重新映射到離散情緒
            self._map_core_affect_to_discrete_emotions("core_affect_decay")

    def apply_random_fluctuations(self, mood_stability: float):
        """對情緒施加微小的隨機波動"""
        sensitivity = self.settings.get(config.SETTING_EMO_SENSITIVITY, 1.0)
        num_to_change = random.randint(1, 3)
        
        for _ in range(num_to_change):
            emotion_name = random.choice(list(config.EMOTIONS.keys()))
            if emotion_name == "neutral": continue

            fluctuation_factor = (1.0 - mood_stability * 0.8) * (sensitivity * 0.5 + 0.5)
            change = random.uniform(-0.05, 0.05) * fluctuation_factor
            
            prev_value = self.emotions.get(emotion_name, 0.5)
            new_value = max(0.0, min(1.0, prev_value + change))

            if abs(new_value - prev_value) > 0.005:
                self.emotions[emotion_name] = new_value
                self.db.save_emotion(self.user_id, emotion_name, new_value, prev_value, "fluctuation")
        
        logging.debug("Applied random mood fluctuations.")

    def update_emotions_from_appraisals(self, appraisal_scores: Dict, character_traits: Dict, effective_sensitivity: float):
        """根據LLM的評價維度分數更新核心情感和離散情緒"""
        if not appraisal_scores: return

        # 1. 更新核心情感 (Valence-Arousal)
        valence_target = (appraisal_scores.get("pleasantness", 0.0) * 0.7 + appraisal_scores.get("goal_conduciveness", 0.0) * 0.3)
        
        novelty = appraisal_scores.get("novelty", 0.0)
        urgency = appraisal_scores.get("urgency", 0.0)
        event_intensity = (abs(appraisal_scores.get("pleasantness", 0.0)) + abs(appraisal_scores.get("goal_conduciveness", 0.0))) / 2.0
        arousal_target_increase = (novelty * 0.4 + urgency * 0.3 + event_intensity * 0.3) * effective_sensitivity

        # ... 此處可加入更複雜的來自原檔案的計算邏輯 ...

        blend_rate = 0.2 * effective_sensitivity
        self.core_affect["valence"] = self.core_affect["valence"] * (1 - blend_rate) + valence_target * blend_rate
        self.core_affect["arousal"] += arousal_target_increase
        self.core_affect["valence"] = max(-1.0, min(1.0, self.core_affect["valence"]))
        self.core_affect["arousal"] = max(0.0, min(1.0, self.core_affect["arousal"]))
        
        logging.info(f"Core affect updated from appraisals: V:{self.core_affect['valence']:.2f}, A:{self.core_affect['arousal']:.2f}")

        # 2. 將更新後的核心情感映射到離散情緒
        self._map_core_affect_to_discrete_emotions("appraisal_reaction", effective_sensitivity, character_traits)

    def _map_core_affect_to_discrete_emotions(self, trigger: str, sensitivity: float = 1.0, traits: Optional[Dict] = None):
        """根據當前的核心情感狀態，調整離散情緒"""
        if traits is None: traits = {}
        valence = self.core_affect["valence"]
        arousal = self.core_affect["arousal"]

        # 這是一個簡化的映射，完整的映射規則應從原始檔案的
        # _map_core_affect_to_discrete_emotions 方法中遷移過來。
        # 例如：
        if valence > 0.3 and arousal > 0.4: # V+, A+ -> Joy, Excitement
            self._adjust_discrete_emotion('joy', (valence + arousal) / 2, trigger, sensitivity)
            self._adjust_discrete_emotion('excitement', arousal, trigger, sensitivity)
        elif valence < -0.3 and arousal > 0.4: # V-, A+ -> Anger, Fear, Anxiety
            self._adjust_discrete_emotion('anxiety', (abs(valence) + arousal) / 2, trigger, sensitivity)
        # ... 其他映射規則 ...

        # 壓制不符合當前核心情感的離散情緒
        if valence > 0.5:
            for emo in config.NEGATIVE_EMOTIONS: self._adjust_discrete_emotion(emo, 0.1, trigger, 0.5)
        elif valence < -0.5:
            for emo in config.POSITIVE_EMOTIONS: self._adjust_discrete_emotion(emo, 0.1, trigger, 0.5)

    def _adjust_discrete_emotion(self, name: str, target: float, trigger: str, sensitivity_mod: float):
        """輔助函式，以一定速率調整單個離散情緒值"""
        if name not in self.emotions: return
        
        prev_val = self.emotions[name]
        blend_rate = 0.18 * sensitivity_mod * random.uniform(0.9, 1.1)
        new_val = prev_val * (1 - blend_rate) + target * blend_rate
        new_val = max(0.0, min(1.0, new_val))
        
        if abs(new_val - prev_val) > 0.01:
            self.emotions[name] = new_val
            self.db.save_emotion(self.user_id, name, new_val, prev_val, f"{trigger}_va_map")