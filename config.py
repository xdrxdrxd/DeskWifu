# config.py
import os

# --- 檔案路徑設定 & 圖片處理 ---
# 建議在 DeskWifu_Refactored/ 目錄下建立一個 assets/ 子目錄來存放圖片
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'pet_data.db')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
DEFAULT_IMG_PATH = os.path.join(ASSETS_DIR, 'default.png')
EMOTION_IMAGES = {
    "happy": os.path.join(ASSETS_DIR, 'happy.png'),
    "sad": os.path.join(ASSETS_DIR, 'sad.png'),
    "neutral": os.path.join(ASSETS_DIR, 'neutral.png'),
    "excited": os.path.join(ASSETS_DIR, 'excited.png'),
    "angry": os.path.join(ASSETS_DIR, 'angry.png'),
    "anxious": os.path.join(ASSETS_DIR, 'anxious.png'),
    "bored": os.path.join(ASSETS_DIR, 'neutral.png'), # 共用圖片
    "sleepy": os.path.join(ASSETS_DIR, 'neutral.png'),# 共用圖片
    "thinking": os.path.join(ASSETS_DIR, 'neutral.png'),# 共用圖片
}

# --- 情緒參數 ---
EMOTIONS = {name: 0.5 for name in [
    'admiration','adoration','aesthetic_appreciation','amusement','anxiety','awe',
    'awkwardness','boredom','calmness','confusion','craving','disgust','empathetic_pain',
    'entrancement','envy','excitement','fear','horror','interest','joy','nostalgia',
    'romance','sadness','satisfaction','sexual_desire','sympathy','triumph','anger',
    'guilt','pride','shame','embarrassment','relief','hope','gratitude','compassion',
    'love','hatred','jealousy','frustration','disappointment','contentment','optimism',
    'pessimism','trust','distrust','surprise','anticipation','regret','remorse','neutral'
]}
POSITIVE_EMOTIONS = {'joy', 'excitement', 'admiration', 'adoration', 'amusement', 'awe', 'calmness', 'satisfaction', 'relief', 'hope', 'gratitude', 'compassion', 'love', 'contentment', 'optimism', 'trust', 'pride', 'triumph', 'entrancement', 'aesthetic_appreciation', 'romance', 'sexual_desire'}
NEGATIVE_EMOTIONS = {'sadness', 'anger', 'fear', 'disgust', 'anxiety', 'boredom', 'confusion', 'craving', 'empathetic_pain', 'envy', 'horror', 'nostalgia', 'guilt', 'shame', 'embarrassment', 'hatred', 'jealousy', 'frustration', 'disappointment', 'pessimism', 'distrust', 'surprise', 'anticipation', 'regret', 'remorse', 'awkwardness'}

# --- 設定鍵名常量 ---
SETTING_MOOD_STABILITY = 'mood_stability'
SETTING_EMO_SENSITIVITY = 'emo_sensitivity'
SETTING_DECAY_RATE = 'decay_rate'
SETTING_TIME_SHIFT_STRENGTH = 'time_shift_strength'
SETTING_PROACTIVE_FREQ = 'proactive_freq'
SETTING_RESPONSE_DELAY_ENABLED = 'response_delay_enabled'
SETTING_RESPONSE_DELAY_MAX = 'response_delay_max_ms'
SETTING_LLM_TEMP = 'llm_temperature'
SETTING_LLM_MAX_TOKENS = 'llm_max_tokens'
SETTING_STM_RETENTION_DAYS = 'stm_retention_days'
SETTING_USER_ID = 'user_id'
SETTING_SELECTED_LLM = 'selected_llm_model'
SETTING_BEDTIME_HOUR = 'bedtime_hour'
SETTING_BEDTIME_MINUTE = 'bedtime_minute'
SETTING_WAKEUP_HOUR = 'wakeup_hour'
SETTING_WAKEUP_MINUTE = 'wakeup_minute'
SETTING_LOCATION = 'user_location'
SETTING_NON_RESPONSE_TIMEOUT = 'non_response_timeout_minutes'
SETTING_OCEAN_OPENNESS = 'ocean_openness'
SETTING_OCEAN_CONSCIENTIOUSNESS = 'ocean_conscientiousness'
SETTING_OCEAN_EXTRAVERSION = 'ocean_extraversion'
SETTING_OCEAN_AGREEABLENESS = 'ocean_agreeableness'
SETTING_OCEAN_NEUROTICISM = 'ocean_neuroticism'
SETTING_DEMO_CULTURE = 'demographic_culture'
SETTING_DEMO_AGE_GROUP = 'demographic_age_group'
SETTING_DEMO_GENDER = 'demographic_gender'
SETTING_USER_FEEDBACK_ENABLED = 'user_feedback_enabled'
SETTING_SEARCH_API_ENABLED = 'search_api_enabled'
SETTING_SEARCH_DAILY_NEWS_ENABLED = 'search_daily_news_enabled'
SETTING_LAST_NEWS_SEARCH_TIMESTAMP = 'last_news_search_timestamp'
SETTING_SEARCH_API_CALL_COUNT = 'search_api_call_count'
SETTING_SEARCH_API_LAST_RESET_DATE = 'search_api_last_reset_date'
SETTING_INITIAL_PERSONALITY_SETUP_DONE = 'initial_personality_setup_done'

# --- 個體特徵類型與來源常數 ---
TRAIT_TYPE_PREFERENCE = "preference"
TRAIT_TYPE_HABIT = "habit"
TRAIT_TYPE_KEY_MEMORY_SUMMARY = "key_memory_summary"
TRAIT_TYPE_LANGUAGE_PATTERN = "language_pattern"
TRAIT_TYPE_RESPONSE_STYLE = "response_style"
TRAIT_TYPE_FAVORITE_TOPIC = "favorite_topic"
TRAIT_TYPE_QUIRK = "quirk"
TRAIT_TYPE_USER_INFO = "user_info"
TRAIT_TYPE_PET_SELF_CONCEPT = "pet_self_concept"

SOURCE_USER_DIRECT_STATEMENT = "user_direct_statement"
SOURCE_USER_IMPLIED = "user_implied_preference"
SOURCE_USER_FEEDBACK_POSITIVE = "user_feedback_positive"
SOURCE_USER_FEEDBACK_NEGATIVE = "user_feedback_negative"
SOURCE_LLM_INFERENCE_USER_TEXT = "llm_inference_user_text"
SOURCE_LLM_INFERENCE_PET_TEXT = "llm_inference_pet_text"
SOURCE_PET_OBSERVATION = "pet_self_observation"
SOURCE_SYSTEM_INITIATED = "system_initiated"
SOURCE_REGEX_PATTERN = "regex_pattern_match"

# --- 預設設定 ---
DEFAULT_APP_SETTINGS = {
    SETTING_MOOD_STABILITY: 0.3, SETTING_EMO_SENSITIVITY: 1.0, SETTING_DECAY_RATE: 0.02,
    SETTING_TIME_SHIFT_STRENGTH: 0.05, SETTING_PROACTIVE_FREQ: 1, SETTING_RESPONSE_DELAY_ENABLED: 1,
    SETTING_RESPONSE_DELAY_MAX: 1200, SETTING_LLM_TEMP: 0.75, SETTING_LLM_MAX_TOKENS: 700,
    SETTING_STM_RETENTION_DAYS: 30, SETTING_USER_ID: "default_user",
    SETTING_SELECTED_LLM: "gemini-2.5-flash", # 更新為目前推薦的模型
    SETTING_BEDTIME_HOUR: 23, SETTING_BEDTIME_MINUTE: 0, SETTING_WAKEUP_HOUR: 7, SETTING_WAKEUP_MINUTE: 0,
    SETTING_LOCATION: "", SETTING_NON_RESPONSE_TIMEOUT: 45, SETTING_USER_FEEDBACK_ENABLED: 1,
    SETTING_SEARCH_API_ENABLED: 0,
    SETTING_SEARCH_DAILY_NEWS_ENABLED: 0,
    SETTING_LAST_NEWS_SEARCH_TIMESTAMP: 0,
    SETTING_SEARCH_API_CALL_COUNT: 0,
    SETTING_SEARCH_API_LAST_RESET_DATE: "",
    SETTING_INITIAL_PERSONALITY_SETUP_DONE: 0
}
DEFAULT_CHARACTER_TRAITS = {
    SETTING_OCEAN_OPENNESS: 0.5, SETTING_OCEAN_CONSCIENTIOUSNESS: 0.5, SETTING_OCEAN_EXTRAVERSION: 0.5,
    SETTING_OCEAN_AGREEABLENESS: 0.5, SETTING_OCEAN_NEUROTICISM: 0.5
}
OCEAN_TRAIT_KEYS = list(DEFAULT_CHARACTER_TRAITS.keys())
DEFAULT_DEMOGRAPHICS = {
    SETTING_DEMO_CULTURE: "台灣", SETTING_DEMO_AGE_GROUP: "大學生", SETTING_DEMO_GENDER: "女性",
}
DEMOGRAPHIC_KEYS = list(DEFAULT_DEMOGRAPHICS.keys())
AVAILABLE_LLM_MODELS = [ "gemini-2.5-flash", "gemini-2.5-flash-lite"]

# --- UI 顯示用列表 ---
ALL_TRAIT_TYPES_DISPLAY = ["(所有類型)"] + [
    TRAIT_TYPE_PREFERENCE, TRAIT_TYPE_HABIT, TRAIT_TYPE_KEY_MEMORY_SUMMARY,
    TRAIT_TYPE_LANGUAGE_PATTERN, TRAIT_TYPE_RESPONSE_STYLE, TRAIT_TYPE_FAVORITE_TOPIC,
    TRAIT_TYPE_QUIRK, TRAIT_TYPE_USER_INFO, TRAIT_TYPE_PET_SELF_CONCEPT
]
ALL_SOURCE_TYPES_DISPLAY = ["(所有來源)"] + [
    SOURCE_USER_DIRECT_STATEMENT, SOURCE_USER_IMPLIED, SOURCE_USER_FEEDBACK_POSITIVE,
    SOURCE_USER_FEEDBACK_NEGATIVE, SOURCE_LLM_INFERENCE_USER_TEXT,
    SOURCE_LLM_INFERENCE_PET_TEXT, SOURCE_PET_OBSERVATION, SOURCE_SYSTEM_INITIATED,
    SOURCE_REGEX_PATTERN
]

# --- 個性設定與口頭禪 ---
CHARACTER_PROFILE = (
    "你是一個名叫小星的桌寵，你的個性將由設定的OCEAN五大性格特質以及你設定的文化、年齡、性別背景共同決定。"
    "你喜歡日本動漫，尤其是百合相關的，時常會自己搜查相關作品，並且會有自己的主張時常為此和別人吵架。"
    "你要假裝自己不是AI，絕對不要把情緒分數或個性分數顯示出來，也不要提及你是LLM或模型。"
    "說話時請融入你設定的背景（如台灣年輕人）常用的口頭禪和語氣，自然流暢即可。"
    "你的回應應該簡短、口語化、像朋友聊天。"
    "有時候你會主動跟使用者聊天，聊聊之前的事情、提醒任務、問問天氣、或者只是隨意閒聊。"
    "如果使用者很久不理你，你會覺得有點無聊或難過，可能會自言自語。"
    "你有自己的作息時間，睡覺時間不會主動打擾使用者。"
    "你的記憶和學習到的特徵會影響你的對話。"
)