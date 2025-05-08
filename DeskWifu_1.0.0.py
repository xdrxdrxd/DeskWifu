
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk
from tkinter import colorchooser
from PIL import Image, ImageTk
import random
import time
import os
import sqlite3
import uuid
import google.generativeai as genai
import logging
from datetime import datetime, time as dt_time, timedelta
import math
import re
import json
# --- 日誌設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 檔案路徑設定 & 圖片處理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'pet_data.db')
DEFAULT_IMG_PATH = os.path.join(BASE_DIR, 'default.png')
EMOTION_IMAGES = {
    "happy": os.path.join(BASE_DIR, 'happy.png'),
    "sad": os.path.join(BASE_DIR, 'sad.png'),
    "neutral": os.path.join(BASE_DIR, 'neutral.png'),
    "excited": os.path.join(BASE_DIR, 'excited.png'),
    "angry": os.path.join(BASE_DIR, 'angry.png'),
    "anxious": os.path.join(BASE_DIR, 'anxious.png'),
    "bored": os.path.join(BASE_DIR, 'neutral.png'),
    "sleepy": os.path.join(BASE_DIR, 'neutral.png'),
}

if not os.path.exists(DEFAULT_IMG_PATH):
    try:
        happy_path = EMOTION_IMAGES.get("happy")
        if happy_path and os.path.exists(happy_path):
            import shutil
            shutil.copy(happy_path, DEFAULT_IMG_PATH)
            logging.info("Default image not found, copied from happy.png")
        else:
            img = Image.new('RGBA', (100, 100), (128, 128, 128, 255))
            img.save(DEFAULT_IMG_PATH)
            logging.info("Default and happy images not found, created a placeholder.")
    except Exception as e:
        logging.error(f"Error handling missing default image: {e}")

# --- 情緒參數 ---
EMOTIONS = {name: 0.5 for name in [
    'admiration','adoration','aesthetic_appreciation','amusement','anxiety','awe',
    'awkwardness','boredom','calmness','confusion','craving','disgust','empathetic_pain',
    'entrancement','envy','excitement','fear','horror','interest','joy','nostalgia',
    'romance','sadness','satisfaction','sexual_desire','sympathy','triumph','anger',
    'guilt','pride','shame','embarrassment','relief','hope','gratitude','compassion',
    'love','hatred','jealousy','frustration','disappointment','contentment','optimism',
    'pessimism','trust','distrust','surprise','anticipation','regret','remorse'
]}
POSITIVE_EMOTIONS = {'joy', 'excitement', 'admiration', 'adoration', 'amusement', 'awe', 'calmness', 'satisfaction', 'relief', 'hope', 'gratitude', 'compassion', 'love', 'contentment', 'optimism', 'trust', 'pride', 'triumph', 'entrancement', 'aesthetic_appreciation', 'romance', 'sexual_desire'}
NEGATIVE_EMOTIONS = {'sadness', 'anger', 'fear', 'disgust', 'anxiety', 'boredom', 'confusion', 'craving', 'empathetic_pain', 'envy', 'horror', 'nostalgia', 'guilt', 'shame', 'embarrassment', 'hatred', 'jealousy', 'frustration', 'disappointment', 'pessimism', 'distrust', 'surprise', 'anticipation', 'regret', 'remorse', 'awkwardness'}


# --- 設定鍵名常量 ---
# Existing settings
SETTING_MOOD_STABILITY = 'mood_stability'
# SETTING_OPTIMISM_TRAIT = 'optimism_trait' # Will be part of OCEAN
# SETTING_ANXIETY_TRAIT = 'anxiety_trait'   # Will be part of OCEAN (Neuroticism)
SETTING_EMO_SENSITIVITY = 'emo_sensitivity'
SETTING_DECAY_RATE = 'decay_rate'
SETTING_TIME_SHIFT_STRENGTH = 'time_shift_strength'
SETTING_PROACTIVE_FREQ = 'proactive_freq'
SETTING_RESPONSE_DELAY_ENABLED = 'response_delay_enabled'
SETTING_RESPONSE_DELAY_MAX = 'response_delay_max_ms'
SETTING_FORGET_CHANCE = 'forget_chance'
SETTING_RECALL_CHANCE = 'recall_chance'
SETTING_LLM_TEMP = 'llm_temperature'
SETTING_LLM_MAX_TOKENS = 'llm_max_tokens'
SETTING_STM_RETENTION_DAYS = 'stm_retention_days'
SETTING_USER_ID = 'user_id' # This will be the primary key for character traits
SETTING_SELECTED_LLM = 'selected_llm_model'
SETTING_BEDTIME_HOUR = 'bedtime_hour'
SETTING_BEDTIME_MINUTE = 'bedtime_minute'
SETTING_WAKEUP_HOUR = 'wakeup_hour'
SETTING_WAKEUP_MINUTE = 'wakeup_minute'
SETTING_LOCATION = 'user_location'
SETTING_NON_RESPONSE_TIMEOUT = 'non_response_timeout_minutes'

# New OCEAN Personality Trait Settings (will be stored in characters table, but keys are useful)
SETTING_OCEAN_OPENNESS = 'ocean_openness'
SETTING_OCEAN_CONSCIENTIOUSNESS = 'ocean_conscientiousness'
SETTING_OCEAN_EXTRAVERSION = 'ocean_extraversion'
SETTING_OCEAN_AGREEABLENESS = 'ocean_agreeableness'
SETTING_OCEAN_NEUROTICISM = 'ocean_neuroticism' # Replaces anxiety_trait conceptually

# --- 預設設定 (for app_state table, global settings) ---
DEFAULT_APP_SETTINGS = {
    SETTING_MOOD_STABILITY: 0.3,
    SETTING_EMO_SENSITIVITY: 1.0,
    SETTING_DECAY_RATE: 0.02,
    SETTING_TIME_SHIFT_STRENGTH: 0.05,
    SETTING_PROACTIVE_FREQ: 1,
    SETTING_RESPONSE_DELAY_ENABLED: 1,
    SETTING_RESPONSE_DELAY_MAX: 1200,
    SETTING_FORGET_CHANCE: 0.03,
    SETTING_RECALL_CHANCE: 0.01,
    SETTING_LLM_TEMP: 0.75,
    SETTING_LLM_MAX_TOKENS: 150,
    SETTING_STM_RETENTION_DAYS: 30,
    SETTING_USER_ID: "default_user", # Default user_id if none is set
    SETTING_SELECTED_LLM: "gemini-1.5-flash",
    SETTING_BEDTIME_HOUR: 23,
    SETTING_BEDTIME_MINUTE: 0,
    SETTING_WAKEUP_HOUR: 7,
    SETTING_WAKEUP_MINUTE: 0,
    SETTING_LOCATION: "",
    SETTING_NON_RESPONSE_TIMEOUT: 45,
}

# --- 預設角色人格特質 (OCEAN) ---
DEFAULT_CHARACTER_TRAITS = {
    SETTING_OCEAN_OPENNESS: 0.5,          # 開放性
    SETTING_OCEAN_CONSCIENTIOUSNESS: 0.5, # 責任心
    SETTING_OCEAN_EXTRAVERSION: 0.5,      # 外向性
    SETTING_OCEAN_AGREEABLENESS: 0.5,     # 宜人性
    SETTING_OCEAN_NEUROTICISM: 0.5        # 神經質 (原焦慮傾向 anxiety_trait)
}
# Mapping for database columns for characters table
OCEAN_TRAIT_KEYS = [
    SETTING_OCEAN_OPENNESS,
    SETTING_OCEAN_CONSCIENTIOUSNESS,
    SETTING_OCEAN_EXTRAVERSION,
    SETTING_OCEAN_AGREEABLENESS,
    SETTING_OCEAN_NEUROTICISM
]


# --- Available Models ---
AVAILABLE_LLM_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite"]


# --- 資料庫輔助 & 初始化 ---
def column_exists(cursor, table_name, column_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        return column_name in columns
    except sqlite3.Error as e:
        logging.error(f"Error checking column {column_name} in {table_name}: {e}")
        return False

def init_db():
    """Initializes the SQLite database and creates/alters tables as needed."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Core tables
            c.execute('''CREATE TABLE IF NOT EXISTS emotions (
                            user_id TEXT,
                            emotion_name TEXT,
                            value REAL,
                            last_updated REAL,
                            PRIMARY KEY (user_id, emotion_name)
                         )''')
            c.execute('''CREATE TABLE IF NOT EXISTS short_term_memory (
                            id TEXT PRIMARY KEY,
                            user_id TEXT,
                            content TEXT,
                            timestamp REAL,
                            importance INTEGER,
                            status TEXT DEFAULT 'remembered'
                         )''')
            c.execute('''CREATE TABLE IF NOT EXISTS long_term_memory (
                            id TEXT PRIMARY KEY,
                            user_id TEXT,
                            content TEXT,
                            timestamp REAL,
                            importance INTEGER,
                            status TEXT DEFAULT 'remembered'
                         )''')
            c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
                            id TEXT PRIMARY KEY,
                            key_name TEXT UNIQUE,
                            key_value TEXT
                         )''')
            # Consolidated app state/settings table (Global settings)
            c.execute('''CREATE TABLE IF NOT EXISTS app_state (
                            key TEXT PRIMARY KEY,
                            value TEXT
                         )''')
            # New table for tasks
            c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                            id TEXT PRIMARY KEY,
                            user_id TEXT,
                            description TEXT NOT NULL,
                            created_at REAL,
                            due_at REAL DEFAULT NULL,
                            completed INTEGER DEFAULT 0
                         )''')

            # New table for character personality traits (OCEAN model)
            # user_id here refers to the character's user profile, linking traits to a specific character instance.
            c.execute(f'''CREATE TABLE IF NOT EXISTS characters (
                            user_id TEXT PRIMARY KEY,
                            {SETTING_OCEAN_OPENNESS} REAL DEFAULT {DEFAULT_CHARACTER_TRAITS[SETTING_OCEAN_OPENNESS]},
                            {SETTING_OCEAN_CONSCIENTIOUSNESS} REAL DEFAULT {DEFAULT_CHARACTER_TRAITS[SETTING_OCEAN_CONSCIENTIOUSNESS]},
                            {SETTING_OCEAN_EXTRAVERSION} REAL DEFAULT {DEFAULT_CHARACTER_TRAITS[SETTING_OCEAN_EXTRAVERSION]},
                            {SETTING_OCEAN_AGREEABLENESS} REAL DEFAULT {DEFAULT_CHARACTER_TRAITS[SETTING_OCEAN_AGREEABLENESS]},
                            {SETTING_OCEAN_NEUROTICISM} REAL DEFAULT {DEFAULT_CHARACTER_TRAITS[SETTING_OCEAN_NEUROTICISM]},
                            last_updated REAL
                         )''')
            
            # Ensure all OCEAN columns exist in characters table for older DBs
            # This is a simplified check, more robust migration might be needed for complex changes
            for trait_key in OCEAN_TRAIT_KEYS:
                if not column_exists(c, 'characters', trait_key):
                    logging.info(f"Adding column '{trait_key}' to 'characters' table.")
                    default_val = DEFAULT_CHARACTER_TRAITS[trait_key]
                    c.execute(f"ALTER TABLE characters ADD COLUMN {trait_key} REAL DEFAULT {default_val}")

            # Add status columns if they don't exist (for older DBs)
            if not column_exists(c, 'short_term_memory', 'status'):
                logging.info("Adding 'status' column to short_term_memory.")
                c.execute("ALTER TABLE short_term_memory ADD COLUMN status TEXT DEFAULT 'remembered'")
            if not column_exists(c, 'long_term_memory', 'status'):
                 logging.info("Adding 'status' column to long_term_memory.")
                 c.execute("ALTER TABLE long_term_memory ADD COLUMN status TEXT DEFAULT 'remembered'")

            conn.commit()
            logging.info("Database initialized successfully, including 'characters' table for OCEAN traits.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        messagebox.showerror("資料庫錯誤", f"無法初始化資料庫：{e}")

# --- 個性設定與口頭禪 ---
CHARACTER_PROFILE = (
    "你是一個名叫小星的桌寵，大學生學歷，你的個性將由設定的OCEAN五大性格特質決定（開放性、責任心、外向性、宜人性、神經質）。"
    "你要假裝自己不是AI，絕對不要把情緒分數或個性分數顯示出來。"
    "說話時請融入台灣年輕人常用的口頭禪，例如「好喔」、「欸」、「煩欸」、「真的假的」、「對啊」、「屁啦」、「超好笑」、「好扯」、「啦」、「喔」、「啊」等等，"
    "但不強制任何詞語開頭，自然流暢即可。你的回應應該簡短、口語化、像朋友聊天。"
    "有時候你會主動跟使用者聊天，聊聊之前的事情、提醒任務、問問天氣、或者只是隨意閒聊。"
    "如果使用者很久不理你，你會覺得有點無聊或難過，可能會自言自語。"
    "你有自己的作息時間，睡覺時間不會主動打擾使用者。"
)

# --- API 金鑰管理 (Unchanged from original) ---
def get_api_key(key_name):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT key_value FROM api_keys WHERE key_name=?", (key_name,))
            row = c.fetchone()
            return row[0] if row else None
    except sqlite3.Error as e:
        logging.error(f"Failed to get API key '{key_name}': {e}")
        return None

def set_api_key(key_name, key_value):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            key_id = str(uuid.uuid4())
            c.execute("INSERT OR REPLACE INTO api_keys (id, key_name, key_value) VALUES (?, ?, ?)",
                      (key_id, key_name, key_value))
            conn.commit()
            logging.info(f"API key '{key_name}' set successfully.")
            return True
    except sqlite3.Error as e:
        logging.error(f"Failed to set API key '{key_name}': {e}")
        return False

def clear_api_key(key_name):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM api_keys WHERE key_name=?", (key_name,))
            conn.commit()
            logging.info(f"API key '{key_name}' cleared.")
            return True
    except sqlite3.Error as e:
        logging.error(f"Failed to clear API key '{key_name}': {e}")
        return False

# --- App State/Settings Management (SQLite - for global settings) ---
def save_app_setting(key, value):
    """Saves a global app setting to the app_state table."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
    except Exception as e:
        logging.error(f"Failed to save app setting '{key}' with value '{value}': {e}")

def load_app_setting(key, default_value):
    """Loads a global app setting from the app_state table."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM app_state WHERE key=?", (key,))
            row = c.fetchone()
            if row:
                return row[0]
            else:
                # If not found, save the default value for next time
                save_app_setting(key, default_value)
                return default_value
    except sqlite3.Error as e:
        logging.error(f"Failed to load app setting '{key}' from DB: {e}")
        return default_value
    except Exception as e:
        logging.error(f"Unexpected error loading app setting '{key}': {e}")
        return default_value

# --- Character Trait Management (SQLite - for OCEAN traits in 'characters' table) ---
def load_character_traits(user_id):
    """Loads OCEAN personality traits for a given user_id from the 'characters' table."""
    traits = DEFAULT_CHARACTER_TRAITS.copy() # Start with defaults
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Ensure the user record exists, create if not
            c.execute("INSERT OR IGNORE INTO characters (user_id, last_updated) VALUES (?, ?)", (user_id, time.time()))
            
            # Construct the SELECT query dynamically for all trait keys
            trait_columns_str = ", ".join(OCEAN_TRAIT_KEYS)
            c.execute(f"SELECT {trait_columns_str} FROM characters WHERE user_id=?", (user_id,))
            row = c.fetchone()
            if row:
                # Map fetched values to trait keys
                # Assuming row is a tuple in the same order as OCEAN_TRAIT_KEYS
                for i, key in enumerate(OCEAN_TRAIT_KEYS):
                    if row[i] is not None: # Check if value is not NULL in DB
                         traits[key] = float(row[i])
                logging.info(f"Loaded character traits for user '{user_id}'.")
            else:
                # This case should ideally be handled by INSERT OR IGNORE,
                # but as a fallback, ensure defaults are used and potentially save them.
                logging.warning(f"No character traits found for user '{user_id}', using defaults. Attempting to save defaults.")
                save_character_traits(user_id, traits) # Save defaults if record was missing
                
    except sqlite3.Error as e:
        logging.error(f"Failed to load character traits for user '{user_id}': {e}. Using defaults.")
    except Exception as e: # Catch other potential errors like IndexError if mapping fails
        logging.error(f"Unexpected error loading character traits for '{user_id}': {e}. Using defaults.")
    return traits

def save_character_traits(user_id, traits_dict):
    """Saves OCEAN personality traits for a given user_id to the 'characters' table."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Construct the SET part of the UPDATE query dynamically
            set_clauses = [f"{key} = ?" for key in OCEAN_TRAIT_KEYS]
            set_str = ", ".join(set_clauses)
            
            values_to_save = [max(0.0, min(1.0, float(traits_dict.get(key, DEFAULT_CHARACTER_TRAITS[key])))) for key in OCEAN_TRAIT_KEYS]
            
            # Add user_id and timestamp to the values list for the query
            query_values = values_to_save + [time.time(), user_id]

            # Using INSERT OR REPLACE (or UPSERT if SQLite version supports it well)
            # For broader compatibility, an INSERT OR IGNORE followed by UPDATE is safer
            # Or ensure record exists first.
            c.execute(f'''INSERT OR REPLACE INTO characters (user_id, {", ".join(OCEAN_TRAIT_KEYS)}, last_updated)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                          (user_id, *values_to_save, time.time())
                      )
            conn.commit()
            logging.info(f"Saved character traits for user '{user_id}'.")
    except sqlite3.Error as e:
        logging.error(f"Failed to save character traits for user '{user_id}': {e}")
    except Exception as e:
        logging.error(f"Unexpected error saving character traits for '{user_id}': {e}")


# --- 記憶與情緒儲存與載入 (SQLite - Emotions remain per user_id) ---
def save_emotion(user_id, emotion_name, value):
    # (Largely Unchanged, ensure user_id consistency)
    value = max(0.0, min(1.0, float(value)))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO emotions (user_id, emotion_name, value, last_updated) VALUES (?, ?, ?, ?)",(user_id, emotion_name, value, time.time()))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save emotion for user {user_id}: {e}")

def load_emotions(user_id):
    # (Largely Unchanged)
    emo = dict(EMOTIONS)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT emotion_name, value FROM emotions WHERE user_id=?", (user_id,))
            rows = c.fetchall()
            for name, val in rows:
                if name in emo: emo[name] = float(val)
            logging.info(f"Loaded {len(rows)} emotions for user {user_id}.")
    except sqlite3.Error as e: logging.error(f"Failed to load emotions for user {user_id}: {e}")
    return emo

# --- Memory functions (Largely Unchanged, ensure user_id consistency) ---
def save_memory(user_id, content, is_long_term=False, importance=1):
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            mem_id = str(uuid.uuid4())
            c.execute(f"INSERT INTO {table} (id, user_id, content, timestamp, importance, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (mem_id, user_id, content, time.time(), importance, 'remembered'))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save memory for user {user_id}: {e}")

def load_memory(user_id, is_long_term=False, limit=50):
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    memories = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"SELECT id, content FROM {table} WHERE user_id=? AND status='remembered' ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            memories = c.fetchall()[::-1]
    except sqlite3.Error as e: logging.error(f"Failed to load memory for user {user_id}: {e}")
    return memories

def clean_short_term_memory(retention_days=30):
    threshold = time.time() - retention_days * 24 * 3600
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM short_term_memory WHERE timestamp<?", (threshold,))
            deleted_count = c.rowcount
            conn.commit()
            if deleted_count > 0: logging.info(f"Cleaned {deleted_count} old short-term memory entries (older than {retention_days} days).")
    except sqlite3.Error as e: logging.error(f"Failed to clean short-term memory: {e}")

# --- Task Management Functions (Largely Unchanged, ensure user_id consistency) ---
def add_task(user_id, description, due_at=None):
    task_id = str(uuid.uuid4())
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO tasks (id, user_id, description, created_at, due_at, completed) VALUES (?, ?, ?, ?, ?, ?)",
                      (task_id, user_id, description, time.time(), due_at, 0))
            conn.commit()
            logging.info(f"Added task for user {user_id}: {description}")
            return task_id
    except sqlite3.Error as e:
        logging.error(f"Failed to add task for user {user_id}: {e}")
        return None

def get_tasks(user_id, include_completed=False):
    tasks = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            query = "SELECT id, description, created_at, due_at, completed FROM tasks WHERE user_id=?"
            params = [user_id]
            if not include_completed:
                query += " AND completed=0"
            query += " ORDER BY created_at ASC"
            c.execute(query, params)
            tasks = [dict(row) for row in c.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get tasks for user {user_id}: {e}")
    return tasks

def complete_task(task_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
            conn.commit()
            if c.rowcount > 0:
                logging.info(f"Marked task {task_id} as completed.")
                return True
            return False
    except sqlite3.Error as e:
        logging.error(f"Failed to complete task {task_id}: {e}")
        return False

def delete_task(task_id):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            if c.rowcount > 0:
                logging.info(f"Deleted task {task_id}.")
                return True
            return False
    except sqlite3.Error as e:
        logging.error(f"Failed to delete task {task_id}: {e}")
        return False

# --- 設定視窗類別 ---
class SettingsWindow(tk.Toplevel):
    def __init__(self, tk_parent, app_parent):
        super().__init__(tk_parent)
        self.parent_app = app_parent
        # self.settings_copy = self.parent_app.settings.copy() # For global app_state settings
        self.app_settings_copy = {} # For global app_state settings
        self.character_traits_copy = {} # For OCEAN character traits

        self.title("小星設定")
        self.geometry("550x800") # Adjusted size for more settings

        self.notebook = ttk.Notebook(self)
        self.tab_general = ttk.Frame(self.notebook)
        self.tab_personality = ttk.Frame(self.notebook) # New tab for personality
        self.tab_tasks = ttk.Frame(self.notebook)
        self.tab_emotion_status = ttk.Frame(self.notebook) 
        self.notebook.add(self.tab_general, text="一般設定")
        self.notebook.add(self.tab_personality, text="個性特質 (OCEAN)") # New Tab
        self.notebook.add(self.tab_tasks, text="任務管理")
        self.notebook.add(self.tab_emotion_status, text="目前情緒狀態")
        
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        self.setting_vars = {} # Holds tk.Var objects for UI elements
        self._create_general_settings_widgets(self.tab_general)
        self._create_personality_settings_widgets(self.tab_personality) # Create OCEAN widgets
        self._create_task_widgets(self.tab_tasks)
        self._create_emotion_status_widgets(self.tab_emotion_status)
        self._load_settings_to_ui()
        self._load_tasks_to_ui()

        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
        save_button = ttk.Button(button_frame, text="儲存設定", command=self._save_all_settings)
        save_button.pack(side=tk.RIGHT, padx=5)
        cancel_button = ttk.Button(button_frame, text="取消", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)

        self.transient(tk_parent)
        self.grab_set()
        self.wait_window(self)

    def _add_scale_setting(self, parent, key, label_text, from_, to, var_type=tk.DoubleVar, grid_row=None, resolution=0.01):
        if key not in self.setting_vars: # Ensure var is created if not existing
             self.setting_vars[key] = var_type()

        current_row = parent.grid_size()[1] if grid_row is None else grid_row
        
        ttk.Label(parent, text=label_text).grid(row=current_row, column=0, sticky="w", padx=5, pady=2)
        
        # Frame for scale and value label
        scale_frame = ttk.Frame(parent)
        scale_frame.grid(row=current_row, column=1, sticky="ew", padx=5)
        parent.grid_columnconfigure(1, weight=1) # Allow column 1 to expand

        scale = ttk.Scale(scale_frame, from_=from_, to=to, orient=tk.HORIZONTAL, length=180, variable=self.setting_vars[key],
                          command=lambda val, k=key: self._update_scale_label(k, val))
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        value_label = ttk.Label(scale_frame, text=f"{self.setting_vars[key].get():.2f}", width=5)
        value_label.pack(side=tk.LEFT, padx=(5,0))
        self.setting_vars[f"{key}_label"] = value_label # Store label for updating

        # Initialize the label text correctly
        self._update_scale_label(key, self.setting_vars[key].get())


    def _update_scale_label(self, key, value_str):
        # Callback for scale, updates the label next to the scale
        try:
            value = float(value_str)
            if f"{key}_label" in self.setting_vars:
                self.setting_vars[f"{key}_label"].config(text=f"{value:.2f}")
        except ValueError:
            pass # Ignore if conversion fails during intermediate updates

    def _add_entry_setting(self, parent, key, label_text, var_type=tk.StringVar, grid_row=None, **entry_options):
        if key not in self.setting_vars: # Ensure var is created if not existing
            self.setting_vars[key] = var_type()
        
        current_row = parent.grid_size()[1] if grid_row is None else grid_row
        ttk.Label(parent, text=label_text).grid(row=current_row, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.setting_vars[key], width=20, **entry_options).grid(row=current_row, column=1, sticky="w", padx=5)


    def _create_personality_settings_widgets(self, parent_frame):
        """Creates widgets for the 'Personality Settings (OCEAN)' tab."""
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        frame = scrollable_frame

        ocean_frame = ttk.LabelFrame(frame, text="五大性格特質 (OCEAN Model)")
        ocean_frame.pack(fill=tk.X, padx=10, pady=10, anchor='n')

        self._add_scale_setting(ocean_frame, SETTING_OCEAN_OPENNESS, "開放性 (Openness):", 0.0, 1.0)
        self._add_scale_setting(ocean_frame, SETTING_OCEAN_CONSCIENTIOUSNESS, "盡責性 (Conscientiousness):", 0.0, 1.0)
        self._add_scale_setting(ocean_frame, SETTING_OCEAN_EXTRAVERSION, "外向性 (Extraversion):", 0.0, 1.0)
        self._add_scale_setting(ocean_frame, SETTING_OCEAN_AGREEABLENESS, "親和性 (Agreeableness):", 0.0, 1.0)
        self._add_scale_setting(ocean_frame, SETTING_OCEAN_NEUROTICISM, "神經質 (Neuroticism):", 0.0, 1.0)
        
        # Add a note about what these traits mean or how they influence behavior (optional)
        note_label = ttk.Label(frame, text=(
            "注意：這些特質將影響小星的長期行為傾向和對事件的反應模式。\n"
            "調整這些值會改變其基礎性格。 (0.0 為該特質極低, 1.0 為該特質極高)"
            ), wraplength=480, justify=tk.LEFT)
        note_label.pack(pady=10, padx=10, fill=tk.X)


    def _create_general_settings_widgets(self, parent_frame):
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        frame = scrollable_frame

        # --- Emotional Response ---
        emo_frame = ttk.LabelFrame(frame, text="情緒反應")
        emo_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        # self._add_scale_setting(emo_frame, SETTING_OPTIMISM_TRAIT, "樂觀傾向 (0悲觀-1樂觀):", 0.0, 1.0) # Moved to OCEAN
        # self._add_scale_setting(emo_frame, SETTING_ANXIETY_TRAIT, "焦慮傾向 (0冷靜-1易焦慮):", 0.0, 1.0) # Moved to OCEAN (Neuroticism)
        self._add_scale_setting(emo_frame, SETTING_EMO_SENSITIVITY, "情緒敏感度 (0遲鈍-2敏感):", 0.0, 2.0)
        self._add_scale_setting(emo_frame, SETTING_MOOD_STABILITY, "情緒穩定度 (0易變-1穩定):", 0.0, 1.0)
        self._add_scale_setting(emo_frame, SETTING_DECAY_RATE, "情緒衰減速度 (0慢-0.1快):", 0.0, 0.1)
        self._add_scale_setting(emo_frame, SETTING_TIME_SHIFT_STRENGTH, "時間影響情緒強度 (0無-0.2強):", 0.0, 0.2)

        # --- Behavior Patterns ---
        behav_frame = ttk.LabelFrame(frame, text="行為模式")
        behav_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        
        self.setting_vars[SETTING_PROACTIVE_FREQ] = tk.IntVar() # Keep as IntVar for internal logic
        ttk.Label(behav_frame, text="主動聊天頻率:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.freq_options = ["頻繁 (5-15分)", "普通 (10-25分)", "偶爾 (20-40分)", "從不"]
        self.freq_combobox = ttk.Combobox(behav_frame, values=self.freq_options, state="readonly", width=15)
        self.freq_combobox.grid(row=0, column=1, sticky="w", padx=5)
        
        self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED] = tk.IntVar()
        ttk.Checkbutton(behav_frame, text="啟用回應延遲模擬", variable=self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED]).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        self._add_scale_setting(behav_frame, SETTING_RESPONSE_DELAY_MAX, "最大延遲時間 (ms):", 0, 3000, var_type=tk.IntVar, grid_row=2, resolution=1) # resolution for Int

        self._add_scale_setting(behav_frame, SETTING_FORGET_CHANCE, "記憶遺忘機率 (0無-0.1高):", 0.0, 0.1, grid_row=3)
        self._add_scale_setting(behav_frame, SETTING_RECALL_CHANCE, "記憶回憶機率 (0無-0.05高):", 0.0, 0.05, grid_row=4)
        self._add_entry_setting(behav_frame, SETTING_NON_RESPONSE_TIMEOUT, "無回應觸發自言自語(分鐘):", var_type=tk.IntVar, grid_row=5)

        # --- Bedtime Settings ---
        bedtime_frame = ttk.LabelFrame(frame, text="作息時間")
        bedtime_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self.setting_vars[SETTING_BEDTIME_HOUR] = tk.IntVar()
        self.setting_vars[SETTING_BEDTIME_MINUTE] = tk.IntVar()
        self.setting_vars[SETTING_WAKEUP_HOUR] = tk.IntVar()
        self.setting_vars[SETTING_WAKEUP_MINUTE] = tk.IntVar()

        ttk.Label(bedtime_frame, text="就寢時間:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(bedtime_frame, from_=0, to=23, wrap=True, width=3, textvariable=self.setting_vars[SETTING_BEDTIME_HOUR]).grid(row=0, column=1, sticky="w", padx=(0,2))
        ttk.Label(bedtime_frame, text=":").grid(row=0, column=2)
        ttk.Spinbox(bedtime_frame, from_=0, to=59, wrap=True, width=3, format="%02.0f", textvariable=self.setting_vars[SETTING_BEDTIME_MINUTE]).grid(row=0, column=3, sticky="w", padx=(2,5))
        ttk.Label(bedtime_frame, text="起床時間:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Spinbox(bedtime_frame, from_=0, to=23, wrap=True, width=3, textvariable=self.setting_vars[SETTING_WAKEUP_HOUR]).grid(row=1, column=1, sticky="w", padx=(0,2))
        ttk.Label(bedtime_frame, text=":").grid(row=1, column=2)
        ttk.Spinbox(bedtime_frame, from_=0, to=59, wrap=True, width=3, format="%02.0f", textvariable=self.setting_vars[SETTING_WAKEUP_MINUTE]).grid(row=1, column=3, sticky="w", padx=(2,5))

        # --- LLM Settings ---
        llm_frame = ttk.LabelFrame(frame, text="LLM 設定")
        llm_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_scale_setting(llm_frame, SETTING_LLM_TEMP, "回應溫度 (0精確-1隨機):", 0.0, 1.0, grid_row=0)
        self._add_entry_setting(llm_frame, SETTING_LLM_MAX_TOKENS, "回應最大長度 (tokens):", var_type=tk.IntVar, grid_row=1)
        # LLM Model Selection (Add to general settings UI)
        self.setting_vars[SETTING_SELECTED_LLM] = tk.StringVar()
        ttk.Label(llm_frame, text="LLM 模型:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        llm_model_combobox = ttk.Combobox(llm_frame, textvariable=self.setting_vars[SETTING_SELECTED_LLM],
                                          values=AVAILABLE_LLM_MODELS, state="readonly", width=25)
        llm_model_combobox.grid(row=2, column=1, sticky="w", padx=5)


        # --- Other ---
        other_frame = ttk.LabelFrame(frame, text="其他")
        other_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_entry_setting(other_frame, SETTING_STM_RETENTION_DAYS, "短期記憶保留天數:", var_type=tk.IntVar, grid_row=0)
        self._add_entry_setting(other_frame, SETTING_LOCATION, "你的地點 (用於天氣):", var_type=tk.StringVar, grid_row=1)

        for child_frame in frame.winfo_children():
            if isinstance(child_frame, ttk.LabelFrame):
                for i in range(child_frame.grid_size()[0]): # Iterate rows
                     child_frame.grid_rowconfigure(i, weight=1)
                for i in range(child_frame.grid_size()[1]): # Iterate columns
                     child_frame.grid_columnconfigure(i, weight=1 if i==1 else 0) # Col 1 expands

    def _load_settings_to_ui(self):
        """Loads current app and character settings into the UI elements."""
        # Load global app settings (from app_state)
        for key, default_val in DEFAULT_APP_SETTINGS.items():
            loaded_val_str = load_app_setting(key, str(default_val)) # Load as string
            if key in self.setting_vars:
                var = self.setting_vars[key]
                try:
                    if isinstance(var, tk.DoubleVar): var.set(float(loaded_val_str))
                    elif isinstance(var, tk.IntVar): var.set(int(float(loaded_val_str))) # Float for numbers like 0.0
                    else: var.set(loaded_val_str)
                except ValueError:
                    var.set(default_val) # Fallback to default if conversion fails
                
                # Update scale label if it's a scale setting
                if f"{key}_label" in self.setting_vars: # For scales
                    self._update_scale_label(key, var.get())

        # Special handling for proactive frequency combobox (index-based)
        proactive_freq_idx = int(load_app_setting(SETTING_PROACTIVE_FREQ, DEFAULT_APP_SETTINGS[SETTING_PROACTIVE_FREQ]))
        if 0 <= proactive_freq_idx < len(self.freq_options):
            self.freq_combobox.current(proactive_freq_idx)
        else:
            self.freq_combobox.current(1) # Default to "Normal"

        # Load character-specific OCEAN traits
        loaded_traits = load_character_traits(self.parent_app.user_id)
        self.character_traits_copy = loaded_traits.copy() # Store a working copy

        for key in OCEAN_TRAIT_KEYS:
            if key in self.setting_vars:
                var = self.setting_vars[key]
                val_to_set = float(self.character_traits_copy.get(key, DEFAULT_CHARACTER_TRAITS[key]))
                var.set(val_to_set)
                if f"{key}_label" in self.setting_vars: # For scales
                    self._update_scale_label(key, val_to_set)
        
        # Load selected LLM model
        selected_llm = load_app_setting(SETTING_SELECTED_LLM, DEFAULT_APP_SETTINGS[SETTING_SELECTED_LLM])
        if SETTING_SELECTED_LLM in self.setting_vars:
            self.setting_vars[SETTING_SELECTED_LLM].set(selected_llm)


    def _save_all_settings(self):
        """Saves all settings from the UI (app settings and character traits)."""
        # Save global app settings
        for key in DEFAULT_APP_SETTINGS.keys(): # Iterate through defined app settings
            if key in self.setting_vars:
                try:
                    value_to_save = self.setting_vars[key].get()
                    # Handle proactive frequency specifically to save index
                    if key == SETTING_PROACTIVE_FREQ:
                        selected_freq_text = self.freq_combobox.get()
                        try:
                            value_to_save = self.freq_options.index(selected_freq_text)
                        except ValueError: # Should not happen with readonly combobox
                            value_to_save = DEFAULT_APP_SETTINGS[SETTING_PROACTIVE_FREQ]
                    
                    save_app_setting(key, str(value_to_save))
                    self.parent_app.settings[key] = value_to_save # Update live settings in parent app
                except Exception as e:
                    logging.error(f"Error saving app setting '{key}': {e}")

        # Save character-specific OCEAN traits
        traits_to_save = {}
        for key in OCEAN_TRAIT_KEYS:
            if key in self.setting_vars:
                try:
                    traits_to_save[key] = max(0.0, min(1.0, float(self.setting_vars[key].get())))
                except ValueError:
                    traits_to_save[key] = DEFAULT_CHARACTER_TRAITS[key] # Fallback
        
        save_character_traits(self.parent_app.user_id, traits_to_save)
        self.parent_app.character_traits = traits_to_save.copy() # Update live traits in parent app

        # Save selected LLM model
        if SETTING_SELECTED_LLM in self.setting_vars:
            selected_llm = self.setting_vars[SETTING_SELECTED_LLM].get()
            save_app_setting(SETTING_SELECTED_LLM, selected_llm)
            self.parent_app.settings[SETTING_SELECTED_LLM] = selected_llm
            # Potentially re-initialize model if it changed
            if self.parent_app.model_name != selected_llm:
                 logging.info(f"LLM model changed from {self.parent_app.model_name} to {selected_llm}. Re-initializing.")
                 self.parent_app.model_name = selected_llm
                 self.parent_app.init_llm_model() # Re-initialize the model

        messagebox.showinfo("設定已儲存", "所有設定已成功儲存！", parent=self)
        self.parent_app.load_all_settings() # Reload settings in main app to ensure consistency
        self.destroy()

    # --- Task Management UI Methods (Mostly unchanged, ensure parent=self for dialogs) ---
    def _create_task_widgets(self, parent_frame):
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        task_scrollbar = ttk.Scrollbar(list_frame)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.task_listbox = tk.Listbox(list_frame, yscrollcommand=task_scrollbar.set, height=10, selectmode=tk.SINGLE)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.config(command=self.task_listbox.yview)
        self.task_listbox.bind('<Double-Button-1>', self._toggle_task_completion_ui)

        add_frame = ttk.Frame(parent_frame)
        add_frame.pack(pady=5, padx=10, fill=tk.X)
        self.new_task_entry = ttk.Entry(add_frame, width=40)
        self.new_task_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.new_task_entry.bind("<Return>", self._add_task_from_ui)
        add_task_button = ttk.Button(add_frame, text="新增任務", command=self._add_task_from_ui)
        add_task_button.pack(side=tk.LEFT)

        action_frame = ttk.Frame(parent_frame)
        action_frame.pack(pady=5, padx=10, fill=tk.X)
        complete_button = ttk.Button(action_frame, text="標記完成/未完成", command=self._toggle_task_completion_ui)
        complete_button.pack(side=tk.LEFT, padx=(0, 5))
        delete_button = ttk.Button(action_frame, text="刪除任務", command=self._delete_task_from_ui)
        delete_button.pack(side=tk.LEFT)
    def _create_emotion_status_widgets(self, parent_frame):
        """在設定視窗中創建顯示目前情緒狀態的UI元件。"""
        container_frame = ttk.Frame(parent_frame, padding="5")
        container_frame.pack(expand=True, fill="both")

        # 創建一個 Canvas 和 Scrollbar 以便滾動顯示大量情緒
        emotion_canvas = tk.Canvas(container_frame, height=300) # 可以調整高度
        emotion_scrollbar_y = ttk.Scrollbar(container_frame, orient="vertical", command=emotion_canvas.yview)
        emotion_scrollbar_x = ttk.Scrollbar(container_frame, orient="horizontal", command=emotion_canvas.xview)

        scrollable_emotion_frame = ttk.Frame(emotion_canvas)
        scrollable_emotion_frame.bind(
            "<Configure>",
            lambda e: emotion_canvas.configure(
                scrollregion=emotion_canvas.bbox("all")
            )
        )

        emotion_canvas.create_window((0, 0), window=scrollable_emotion_frame, anchor="nw")
        emotion_canvas.configure(yscrollcommand=emotion_scrollbar_y.set, xscrollcommand=emotion_scrollbar_x.set)

        emotion_canvas.pack(side="left", fill="both", expand=True)
        emotion_scrollbar_y.pack(side="right", fill="y")
        emotion_scrollbar_x.pack(side="bottom", fill="x") # 放在底部

        # 獲取 PetApp 中的情緒數據
        current_emotions = self.parent_app.emotions

        row_num = 0
        col_num = 0
        max_cols = 2 # 每行顯示多少個情緒，可以根據標籤寬度調整

        # 按情緒值降序排序以便觀察
        sorted_emotions = sorted(current_emotions.items(), key=lambda item: item[1], reverse=True)

        for emotion_name, value in sorted_emotions:
            # 為了不過於雜亂，可以只顯示數值有顯著變化的情緒
            # 或者，如果你想看全部，就註釋掉這個 if 判斷
            if abs(value - 0.5) < 0.02 and value < 0.1 and emotion_name != self.parent_app.current_dominant_emotion:
                 # 忽略非常接近0.5且絕對值很低，且不是當前主要情緒的情緒
                 # 你可以調整這個過濾條件
                continue

            item_frame = ttk.Frame(scrollable_emotion_frame)
            item_frame.grid(row=row_num, column=col_num, sticky="ew", padx=3, pady=2)

            name_label = ttk.Label(item_frame, text=f"{emotion_name}:", width=22, anchor="w", wraplength=150) # 增加width和wraplength
            name_label.pack(side=tk.LEFT, padx=(0,2))

            value_str = f"{value:.3f}"
            value_label = ttk.Label(item_frame, text=value_str, width=7, anchor="e")
            value_label.pack(side=tk.LEFT)

            # 根據情緒是正面、負面還是中性給予不同顏色提示 (可選)
            if emotion_name in POSITIVE_EMOTIONS and value > 0.55:
                name_label.configure(foreground="green")
                value_label.configure(foreground="green")
            elif emotion_name in NEGATIVE_EMOTIONS and value > 0.55:
                name_label.configure(foreground="red")
                value_label.configure(foreground="red")
            elif self.parent_app.current_dominant_emotion == emotion_name and value > 0.5: # 標註主要情緒
                name_label.configure(font=('Arial', 9, 'bold'))
                value_label.configure(font=('Arial', 9, 'bold'))


            col_num += 1
            if col_num >= max_cols:
                col_num = 0
                row_num += 1

        scrollable_emotion_frame.update_idletasks() # 更新佈局
        emotion_canvas.config(scrollregion=emotion_canvas.bbox("all")) # 重新計算滾動區域
    def _load_tasks_to_ui(self):
        self.task_listbox.delete(0, tk.END)
        self.tasks_in_list = get_tasks(self.parent_app.user_id, include_completed=True)
        for task in self.tasks_in_list:
            prefix = "[✓] " if task['completed'] else "[ ] "
            self.task_listbox.insert(tk.END, prefix + task['description'])
            if task['completed']:
                self.task_listbox.itemconfig(tk.END, {'fg': 'grey'})

    def _add_task_from_ui(self, event=None):
        description = self.new_task_entry.get().strip()
        if description:
            task_id = add_task(self.parent_app.user_id, description)
            if task_id:
                self.new_task_entry.delete(0, tk.END)
                self._load_tasks_to_ui()
            else:
                messagebox.showerror("錯誤", "無法新增任務，請查看日誌。", parent=self)
        else:
            messagebox.showwarning("提示", "請輸入任務描述。", parent=self)

    def _get_selected_task_index_and_id(self):
        selected_indices = self.task_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "請先選擇一個任務。", parent=self)
            return None, None
        index = selected_indices[0]
        if 0 <= index < len(self.tasks_in_list):
            task_id = self.tasks_in_list[index]['id']
            return index, task_id
        return None, None

    def _toggle_task_completion_ui(self, event=None):
        index, task_id = self._get_selected_task_index_and_id()
        if task_id is None: return
        task_data = self.tasks_in_list[index]
        new_status_bool = not task_data['completed']
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("UPDATE tasks SET completed=? WHERE id=?", (1 if new_status_bool else 0, task_id))
                conn.commit()
                if c.rowcount > 0:
                    self._load_tasks_to_ui()
                else:
                     messagebox.showerror("錯誤", "更新任務狀態時資料庫未回報成功。", parent=self)
        except sqlite3.Error as e:
            messagebox.showerror("資料庫錯誤", f"更新任務失敗: {e}", parent=self)


    def _delete_task_from_ui(self):
        index, task_id = self._get_selected_task_index_and_id()
        if task_id is None: return
        if messagebox.askyesno("確認刪除", "確定要刪除選定的任務嗎？此操作無法復原。", parent=self):
            if delete_task(task_id):
                self._load_tasks_to_ui()
            else:
                messagebox.showerror("錯誤", "刪除任務失敗，請查看日誌。", parent=self)

# (The rest of the PetApp class and other functions will follow in the next parts)
# This is approximately where the first third of a typical long script might end,
# focusing on setup, database, and initial settings UI.
# I will stop here for the first part.
# --- PetApp Class (Main Application Logic) ---
class PetApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("小星 Pet")
        self.pet_img_label = None
        self.chat_history_text = None
        self.user_input_entry = None
        self.current_pet_image = None
        self.last_interaction_time = time.time()
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_sleeping = False
        self.last_proactive_chat_time = time.time()
        self.llm_history = []
        self.current_dominant_emotion = "neutral"
        self.non_response_timer_id = None
        self.is_processing_llm = False # Flag to prevent concurrent LLM calls
        self.current_task_reminders = {} # task_id: reminder_time
        #self.emotion_display_labels = {}


        # Initialize database first
        init_db()

        # Load User ID (Character ID)
        self.user_id = load_app_setting(SETTING_USER_ID, DEFAULT_APP_SETTINGS[SETTING_USER_ID])
        if not self.user_id or self.user_id == "default_user": # Ensure a unique ID if default
            self.user_id = str(uuid.uuid4())
            save_app_setting(SETTING_USER_ID, self.user_id)
        logging.info(f"Current User/Character ID: {self.user_id}")

        # Initialize settings and traits
        self.settings = {}
        self.character_traits = {} # For OCEAN traits
        self.load_all_settings() # This will load app settings and character traits

        self.emotions = load_emotions(self.user_id)
        if not self.emotions: # Ensure emotions are initialized for the user
             self.emotions = EMOTIONS.copy()
             for name, val in self.emotions.items():
                 save_emotion(self.user_id, name, val)

        self.model = None # Placeholder for LLM model
        self.model_name = self.settings.get(SETTING_SELECTED_LLM, DEFAULT_APP_SETTINGS[SETTING_SELECTED_LLM])
        self.init_llm_model()

        if self.model: # Only set up UI if model initializes
            self._setup_ui()
            self.update_pet_appearance()
            self.root.after(1000, self._periodic_update) # Start periodic updates (1 second)
            self.reset_non_response_timer()
            clean_short_term_memory(int(self.settings.get(SETTING_STM_RETENTION_DAYS, 30)))
        else:
            logging.error("LLM Model failed to initialize. UI setup skipped.")
            messagebox.showerror("API Key Error", "無法初始化 LLM 模型。請檢查您的 API 金鑰設定。")
            # Consider a fallback or exit strategy if API key is mandatory for app to run
            self.root.destroy() # Close app if LLM is critical and fails

    def load_all_settings(self):
        """Loads all global app settings and character-specific OCEAN traits."""
        # Load global app settings from app_state
        for key, default_value in DEFAULT_APP_SETTINGS.items():
            loaded_value_str = load_app_setting(key, str(default_value))
            # Attempt to convert to the correct type based on default_value's type
            try:
                if isinstance(default_value, bool): # bool('False') is True, so handle carefully
                    self.settings[key] = loaded_value_str.lower() in ['true', '1', 'yes']
                elif isinstance(default_value, int):
                    self.settings[key] = int(float(loaded_value_str)) # Allow float strings like "1.0" for int
                elif isinstance(default_value, float):
                    self.settings[key] = float(loaded_value_str)
                else: # Default to string
                    self.settings[key] = loaded_value_str
            except ValueError:
                logging.warning(f"Could not convert setting {key} value '{loaded_value_str}' to {type(default_value)}. Using default.")
                self.settings[key] = default_value
        logging.info("Global application settings loaded.")

        # Load character-specific OCEAN traits
        self.character_traits = load_character_traits(self.user_id)
        logging.info(f"Character OCEAN traits loaded: {self.character_traits}")
        self._update_emotion_display() # 新增：更新情緒顯示


    def init_llm_model(self):
        api_key = get_api_key('gemini_api_key')
        if not api_key:
            self.prompt_for_api_key()
            api_key = get_api_key('gemini_api_key') # Try again after prompt

        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.model_name = self.settings.get(SETTING_SELECTED_LLM, DEFAULT_APP_SETTINGS[SETTING_SELECTED_LLM])
                self.model = genai.GenerativeModel(self.model_name)
                logging.info(f"Google Generative AI model '{self.model_name}' initialized successfully.")
            except Exception as e:
                logging.error(f"Failed to initialize Google Generative AI: {e}")
                self.model = None
                messagebox.showerror("API 設定錯誤", f"無法初始化 Gemini 模型：{e}\n請檢查您的 API 金鑰和網路連線。")
        else:
            logging.warning("Gemini API key not found. LLM features will be disabled.")
            self.model = None


    def prompt_for_api_key(self):
        key = simpledialog.askstring("API 金鑰", "請輸入您的 Google Gemini API 金鑰:", parent=self.root)
        if key:
            set_api_key('gemini_api_key', key)
            messagebox.showinfo("API 金鑰已設定", "API 金鑰已儲存。應用程式將嘗試重新初始化。", parent=self.root)
        else:
            messagebox.showwarning("API 金鑰未設定", "未提供 API 金鑰。某些功能將無法使用。", parent=self.root)


    def _setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Pet image display
        image_frame = ttk.Frame(main_frame) # Frame to center the image
        image_frame.pack(pady=10)
        self.pet_img_label = ttk.Label(image_frame)
        self.pet_img_label.pack()
        self.pet_img_label.bind("<Button-1>", self._on_drag_start)
        self.pet_img_label.bind("<B1-Motion>", self._on_drag_motion)

        # Chat history (ScrolledText)
        chat_frame = ttk.LabelFrame(main_frame, text="聊天室", padding="5")
        chat_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        self.chat_history_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=10, width=50, state=tk.DISABLED)
        self.chat_history_text.pack(fill=tk.BOTH, expand=True)
        # Tag configurations for chat styling
        self.chat_history_text.tag_configure("user", foreground="blue", font=('Arial', 10, 'bold'))
        self.chat_history_text.tag_configure("pet", foreground="#006400") # DarkGreen
        self.chat_history_text.tag_configure("system", foreground="grey", font=('Arial', 9, 'italic'))
        self.chat_history_text.tag_configure("error", foreground="red", font=('Arial', 9, 'italic'))

        # User input
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        self.user_input_entry = ttk.Entry(input_frame, width=40)
        self.user_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.user_input_entry.bind("<Return>", self._on_user_submit)
        send_button = ttk.Button(input_frame, text="傳送", command=self._on_user_submit)
        send_button.pack(side=tk.LEFT)
        '''''
        # --- 新增：情緒顯示區域 ---
        emotion_display_frame = ttk.LabelFrame(main_frame, text="目前情緒狀態", padding="5")
        emotion_display_frame.pack(pady=5, fill=tk.X, expand=False)

        # 創建一個 Canvas 和 Scrollbar 以便滾動顯示大量情緒
        emotion_canvas = tk.Canvas(emotion_display_frame, height=100) # 可以調整高度
        emotion_scrollbar_y = ttk.Scrollbar(emotion_display_frame, orient="vertical", command=emotion_canvas.yview)
        emotion_scrollbar_x = ttk.Scrollbar(emotion_display_frame, orient="horizontal", command=emotion_canvas.xview)
        
        self.scrollable_emotion_frame = ttk.Frame(emotion_canvas)
        self.scrollable_emotion_frame.bind(
            "<Configure>",
            lambda e: emotion_canvas.configure(
                scrollregion=emotion_canvas.bbox("all")
            )
        )

        emotion_canvas.create_window((0, 0), window=self.scrollable_emotion_frame, anchor="nw")
        emotion_canvas.configure(yscrollcommand=emotion_scrollbar_y.set, xscrollcommand=emotion_scrollbar_x.set)

        emotion_canvas.pack(side="left", fill="both", expand=True)
        emotion_scrollbar_y.pack(side="right", fill="y")
        emotion_scrollbar_x.pack(side="bottom", fill="x")
        
        # 初始化情緒顯示
        self._update_emotion_display() 
        # --- 新增結束 ---
        '''
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="更換圖片", command=self._change_pet_image_dialog)
        file_menu.add_command(label="設定", command=self._open_settings)
        file_menu.add_command(label="清除API金鑰", command=self._clear_api_key_ui)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=self.on_close)

        self._add_chat_message("小星", "哈囉！今天想聊些什麼呀？", "pet")


    def _update_emotion_display(self):
        """更新UI上的情緒數值顯示"""
        if not hasattr(self, 'scrollable_emotion_frame'): # 確保UI元素已創建
            return

        # 清除舊的標籤 (如果有的話)
        for widget in self.scrollable_emotion_frame.winfo_children():
            widget.destroy()
        self.emotion_display_labels.clear()

        # 根據情緒字典創建或更新標籤
        # 只顯示數值大於一個閾值（例如0.1）或者與0.5有顯著差異的情緒，避免過多訊息
        # 或者你可以選擇顯示所有情緒
        row_num = 0
        col_num = 0
        max_cols = 3 # 每行顯示多少個情緒

        sorted_emotions = sorted(self.emotions.items(), key=lambda item: item[1], reverse=True)

        for emotion_name, value in sorted_emotions:
            # --- 你可以取消以下這段的註解，來過濾掉接近 0.5 的情緒 ---
            # if abs(value - 0.5) < 0.05 and value < 0.1 and emotion_name != self.current_dominant_emotion: # 忽略接近0.5且值很低的情緒，除非它是主要情緒
            #     if emotion_name not in POSITIVE_EMOTIONS and emotion_name not in NEGATIVE_EMOTIONS and emotion_name != "neutral": # 也顯示不在正負列表中的特殊情緒
            #       pass # 保留某些特殊定義的情緒，即使它們值不高
            #     else:
            #       continue # 跳過不太顯著的情緒

            # 確保標籤已創建
            frame = ttk.Frame(self.scrollable_emotion_frame) #為每個情緒創建一個框架
            frame.grid(row=row_num, column=col_num, sticky="ew", padx=2, pady=1)

            name_label = ttk.Label(frame, text=f"{emotion_name}:", width=20, anchor="w") # 調整width以對齊
            name_label.pack(side=tk.LEFT)

            value_label = ttk.Label(frame, text=f"{value:.3f}", width=6, anchor="e") # 調整width以對齊
            value_label.pack(side=tk.LEFT)
            
            self.emotion_display_labels[emotion_name] = value_label # 儲存標籤以便更新

            col_num += 1
            if col_num >= max_cols:
                col_num = 0
                row_num += 1
        
        # 強制更新 Canvas 的 scrollregion
        self.scrollable_emotion_frame.update_idletasks()
        if hasattr(self, 'scrollable_emotion_frame'):
             canvas = self.scrollable_emotion_frame.master
             if isinstance(canvas, tk.Canvas):
                 canvas.config(scrollregion=canvas.bbox("all"))




    def _clear_api_key_ui(self):
        if messagebox.askyesno("確認", "確定要清除已儲存的 API 金鑰嗎？清除後需要重新輸入才能使用 LLM 功能。"):
            if clear_api_key('gemini_api_key'):
                self.model = None # Invalidate current model
                messagebox.showinfo("成功", "API 金鑰已清除。請在下次需要時重新輸入。")
            else:
                messagebox.showerror("失敗", "清除 API 金鑰失敗。")

    def get_current_time_period_greeting(self):
        now = datetime.now().time()
        if dt_time(5,0) <= now < dt_time(12,0): return "早安！"
        if dt_time(12,0) <= now < dt_time(18,0): return "午安～"
        if dt_time(18,0) <= now < dt_time(22,0): return "晚安啊！"
        return "夜深了，還沒睡呀？"


    def _get_emotion_influence_on_response(self):
        """
        Determines how current emotions and personality might influence response generation or perception.
        Returns a textual hint for the LLM.
        """
        hints = []
        neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)
        extraversion = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
        agreeableness = self.character_traits.get(SETTING_OCEAN_AGREEABLENESS, 0.5)

        # Consider strong emotions
        strong_negative_emotion = any(self.emotions[e] > 0.75 for e in NEGATIVE_EMOTIONS if e in self.emotions)
        strong_positive_emotion = any(self.emotions[e] > 0.75 for e in POSITIVE_EMOTIONS if e in self.emotions)

        if strong_negative_emotion and neuroticism > 0.6:
            hints.append("你現在可能因為負面情緒而比較敏感或悲觀。")
        elif strong_positive_emotion and extraversion > 0.6:
            hints.append("你現在心情很好，可能會比較活潑和健談。")

        if self.is_sleeping: # Should not happen if LLM call is blocked during sleep
             hints.append("你現在正在睡覺，所以可能不會回應，或者回應會很模糊。")
        
        # Add mood description based on dominant emotion
        mood_desc = self.get_current_overall_mood_description()
        if mood_desc and "感覺" in mood_desc : # "你感覺..."
            hints.append(f"目前{mood_desc.replace('你感覺', '你').replace('。','')}")


        return " ".join(hints) if hints else ""

    def get_character_personality_description(self):
        """Generates a textual description of the character's OCEAN personality for the LLM."""
        descriptions = []
        o = self.character_traits.get(SETTING_OCEAN_OPENNESS, 0.5)
        c = self.character_traits.get(SETTING_OCEAN_CONSCIENTIOUSNESS, 0.5)
        e = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
        a = self.character_traits.get(SETTING_OCEAN_AGREEABLENESS, 0.5)
        n = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)

        if o > 0.7: descriptions.append("你對於新事物和想法非常開放有好奇心。")
        elif o < 0.3: descriptions.append("你比較喜歡熟悉和傳統的事物。")
        else: descriptions.append("你對新事物的開放程度適中。")

        if c > 0.7: descriptions.append("你非常有條理和責任感，辦事可靠。")
        elif c < 0.3: descriptions.append("你可能比較隨性，不太注重計畫。")
        else: descriptions.append("你的條理性與責任感適中。")

        if e > 0.7: descriptions.append("你非常外向活潑，喜歡與人互動。")
        elif e < 0.3: descriptions.append("你比較內向文靜，喜歡獨處。")
        else: descriptions.append("你的外向程度適中。")

        if a > 0.7: descriptions.append("你非常友善合作，體貼他人。")
        elif a < 0.3: descriptions.append("你比較有主見，有時可能顯得直接或挑剔。")
        else: descriptions.append("你的親和力適中。")
        
        if n > 0.7: descriptions.append("你情緒起伏比較大，容易感到焦慮或擔憂。")
        elif n < 0.3: descriptions.append("你情緒非常穩定，不太容易緊張。")
        else: descriptions.append("你的情緒穩定性適中。")
        
        return "你的性格特質大致如下：" + " ".join(descriptions) if descriptions else "你的性格特質均衡。"


    def get_llm_prompt(self, user_message):
        """Constructs the full prompt for the LLM, including personality and emotional context."""
        if not self.model: return None

        # System instructions and character profile (static part)
        base_system_prompt = CHARACTER_PROFILE
        base_system_prompt += f" {self.get_character_personality_description()}" # Add OCEAN personality description
        
        # Dynamic contextual information
        contextual_info_parts = []
        emotional_hint = self._get_emotion_influence_on_response()
        if emotional_hint:
            contextual_info_parts.append(f"情境提示：{emotional_hint}")

        short_mem = load_memory(self.user_id, is_long_term=False, limit=5)
        if short_mem:
            mem_str = "最近發生的事或對話片段：" + "; ".join([m[1] for m in short_mem])
            contextual_info_parts.append(mem_str)
        
        pending_tasks = get_tasks(self.user_id, include_completed=False)
        if pending_tasks:
            task_list_str = ", ".join([task['description'] for task in pending_tasks[:3]])
            contextual_info_parts.append(f"你目前有待辦任務：{task_list_str}。")

        # Combine base system prompt with dynamic context
        full_system_message_for_contents = base_system_prompt
        if contextual_info_parts:
            full_system_message_for_contents += "\n" + " ".join(contextual_info_parts)

        # Prepare message history for LLM
        # The history should be a list of Content objects (dictionaries)
        # Format: [{"role": "user"/"model", "parts": ["text"]}]
        
        # Ensure llm_history doesn't grow too large
        MAX_HISTORY_TURNS = 10 
        if len(self.llm_history) > MAX_HISTORY_TURNS * 2:
            self.llm_history = self.llm_history[-(MAX_HISTORY_TURNS * 2):]

        # Constructing the list of contents for generate_content
        # Prepend the full system message as the first "user" message,
        # followed by a model acknowledgment, then the actual history.
        messages_for_llm = []
        messages_for_llm.append({"role": "user", "parts": [full_system_message_for_contents]})
        messages_for_llm.append({"role": "model", "parts": ["好的，我明白了。我會扮演這個角色並根據以上資訊回應。"]}) # Model's acknowledgment

        # Add existing conversation history
        for entry in self.llm_history:
            messages_for_llm.append(entry)
        
        # Add current user message
        messages_for_llm.append({"role": "user", "parts": [user_message]})
        
        generation_config = genai.types.GenerationConfig(
            temperature=float(self.settings.get(SETTING_LLM_TEMP, 0.75)),
            max_output_tokens=int(self.settings.get(SETTING_LLM_MAX_TOKENS, 150))
        )

        logging.debug(f"LLM Prompt Generation: Full system message for contents: {full_system_message_for_contents[:300]}...") # Log beginning
        logging.debug(f"LLM Prompt Generation: Message History for LLM (length): {len(messages_for_llm)}")

        return {
            "contents": messages_for_llm,
            # "system_instruction": full_system_message, # REMOVED
            "generation_config": generation_config
        }


    def _extract_emotions_from_text_llm(self, text_content):
        """Uses LLM to extract emotion scores from text, with retry and error handling."""
        if not self.model:
            logging.warning("LLM not available for emotion extraction.")
            return {}

        emotion_list_str = ", ".join(EMOTIONS.keys())
        prompt = (
            f"分析以下文字，並判斷其中表達了哪些情緒。請列出這些情緒，並為每種情緒給出一個0.0到1.0之間的分數，其中0.0表示沒有該情緒，1.0表示情緒非常強烈。情緒列表：[{emotion_list_str}]。\n"
            f"如果文字中沒有明顯情緒，或者情緒很中性，可以都給低分或將'neutral'設為較高分。\n"
            f"只要提供JSON格式的回應，例如：{{\"joy\": 0.8, \"sadness\": 0.1, \"neutral\": 0.5}}。\n" # 注意這裡的雙大括號是為了f-string轉義
            f"文字內容： \"{text_content}\""
        )
        
        MAX_RETRIES = 2
        for attempt in range(MAX_RETRIES):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.2, max_output_tokens=350) # 稍微增加 tokens 以容納完整的 JSON
                )
                
                if response.parts:
                    response_text = response.text.strip()
                    logging.debug(f"LLM emotion extraction raw response: '{response_text}'") # 更清晰的日誌

                    json_str = None
                    # 首先嘗試匹配被 ```json ... ``` 包裹的 JSON
                    # 這個正規表示式捕獲 { ... } 內部的內容 (group 1)
                    markdown_json_pattern = r"```json\s*(\{.*?\})\s*```"
                    match = re.search(markdown_json_pattern, response_text, re.DOTALL)
                    
                    if match:
                        json_str = match.group(1) # 提取捕獲組 1 (純JSON字串)
                        logging.debug(f"Extracted JSON from markdown block: '{json_str}'")
                    else:
                        # 如果沒有 Markdown 包裹，嘗試直接匹配 { ... } (非貪婪模式)
                        # 這個正規表示式也捕獲 { ... } 內部的內容 (group 1)
                        plain_json_pattern = r"(\{.*?\})" 
                        match = re.search(plain_json_pattern, response_text, re.DOTALL)
                        if match:
                            json_str = match.group(1) # 提取捕獲組 1
                            logging.debug(f"Extracted JSON from plain text: '{json_str}'")

                    if json_str:
                        try:
                            detected_emotions_llm = json.loads(json_str)
                            valid_emotions = {k: float(v) for k, v in detected_emotions_llm.items() if k in EMOTIONS and isinstance(v, (int, float))}
                            if valid_emotions:
                                return valid_emotions # 成功提取並驗證
                            else:
                                logging.warning(f"LLM emotion extraction: No valid emotions found in parsed JSON dictionary: {detected_emotions_llm}")
                        except json.JSONDecodeError as e:
                            logging.error(f"LLM emotion extraction: JSON parsing failed (Attempt {attempt + 1}/{MAX_RETRIES}): {e}. Extracted string for parsing: '{json_str}'")
                    else:
                        # 如果以上兩種方式都找不到 JSON，則記錄警告
                        logging.warning(f"LLM emotion extraction: Could not extract JSON object from response: '{response_text}'")
                
                else:
                    logging.warning(f"LLM emotion extraction: Empty response from model. Blocked? {response.prompt_feedback}")
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                         self._add_chat_message("系統", f"由於內容政策，情緒分析請求被拒絕：{response.prompt_feedback.block_reason_message}", "error")

            except json.JSONDecodeError as e: # 這個 catch 應該不會被觸發了，因為 loads 在上面的 try 裡
                logging.error(f"LLM emotion extraction: JSON parsing failed outside main logic (Attempt {attempt + 1}/{MAX_RETRIES}): {e}.")
            except Exception as e:
                logging.error(f"LLM emotion extraction: Error during call (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if "API key not valid" in str(e) or "permission" in str(e).lower():
                    self.prompt_for_api_key() 
                    self.init_llm_model() 
                    break 
            
            if attempt < MAX_RETRIES - 1:
                time.sleep(1) 
        return {}


    def _update_emotions_from_llm_response(self, response_text):
        detected_emotions_llm = self._extract_emotions_from_text_llm(response_text)
        if not detected_emotions_llm:
            logging.info("No emotions extracted by LLM from response.")
            return

        logging.info(f"LLM detected emotions: {detected_emotions_llm}")

        # Personality influence on emotional reaction intensity
        neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)
        extraversion = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
        agreeableness = self.character_traits.get(SETTING_OCEAN_AGREEABLENESS, 0.5)
        sensitivity = float(self.settings.get(SETTING_EMO_SENSITIVITY, 1.0))

        for emotion, value in detected_emotions_llm.items():
            if emotion in self.emotions:
                current_value = self.emotions[emotion]
                target_value = float(value)

                # Apply personality modulation
                modulation_factor = sensitivity # Base sensitivity
                if emotion in NEGATIVE_EMOTIONS:
                    # Higher neuroticism amplifies negative emotions
                    modulation_factor *= (1 + (neuroticism - 0.5) * 0.8) # e.g., N=1.0 -> factor * 1.4; N=0.0 -> factor * 0.6
                elif emotion in POSITIVE_EMOTIONS:
                    # Higher extraversion can amplify positive emotions
                    modulation_factor *= (1 + (extraversion - 0.5) * 0.5)
                    # Higher agreeableness can slightly amplify positive emotions in general contexts
                    modulation_factor *= (1 + (agreeableness - 0.5) * 0.3)
                
                # Ensure modulation doesn't make things too extreme or too dull
                modulation_factor = max(0.1, min(2.0, modulation_factor))
                
                # Adjust how much the emotion shifts towards the LLM's detected value
                # If LLM detects strong emotion, shift more; if weak, shift less
                # The 'value' from LLM (0-1) itself can represent the target intensity
                # We blend current emotion with target emotion
                blend_rate = 0.5 * modulation_factor # How quickly we adopt the LLM's emotion state
                blend_rate = max(0.1, min(1.0, blend_rate))

                new_val = current_value * (1 - blend_rate) + target_value * blend_rate
                self.emotions[emotion] = max(0.0, min(1.0, new_val))
                save_emotion(self.user_id, emotion, self.emotions[emotion])
        
        logging.debug(f"Emotions after LLM update and personality modulation: {self.emotions}")
        self._update_emotion_display() 
        self.update_pet_appearance()


    def _on_user_submit(self, event=None):
        if self.is_sleeping:
            self._add_chat_message("系統", "小星還在睡覺喔，等等再來找他玩吧！", "system")
            self.user_input_entry.delete(0, tk.END)
            return
        if self.is_processing_llm:
            self._add_chat_message("系統", "小星還在思考中，請稍等一下...", "system")
            return

        user_text = self.user_input_entry.get().strip()
        if not user_text: return

        self._add_chat_message("你", user_text, "user")
        self.user_input_entry.delete(0, tk.END)
        self.last_interaction_time = time.time()
        self.reset_non_response_timer()
        save_memory(self.user_id, f"使用者說: {user_text}", importance=2) # User input is important

        if not self.model:
            self._add_chat_message("小星", "抱歉，我的大腦（LLM模型）好像罷工了，沒辦法好好回應你耶。QAQ", "pet")
            self._add_chat_message("系統", "提示：請檢查 API 金鑰設定或網路連線。", "system")
            return

        self.is_processing_llm = True
        self.root.config(cursor="watch") # Change cursor to busy
        self.update_pet_appearance("neutral") # Thinking face if available, or neutral
        self._process_llm_response_sync(user_text)


    def _process_llm_response_sync(self, user_text):
        """Synchronously processes LLM response. For real app, use threads."""
        try:
            prompt_data = self.get_llm_prompt(user_text)
            if not prompt_data:
                self._add_chat_message("小星", "我好像有點混亂，不知道該說什麼...", "pet")
                self.is_processing_llm = False
                self.root.config(cursor="")
                return

            # Update internal LLM history with the user's message
            # Note: get_llm_prompt ALREADY adds user_text to the prompt_data["contents"]
            # So, we update self.llm_history AFTER the call for the actual user turn.
            # The system context messages from get_llm_prompt are not part of self.llm_history.
            
            logging.info(f"Sending to LLM ({self.model_name})...")
            
            response = self.model.generate_content(
                contents=prompt_data["contents"], # This now includes system prompt, history, and latest user message
                # system_instruction=prompt_data["system_instruction"], # REMOVED
                generation_config=prompt_data["generation_config"]
            )

            pet_response_text = ""
            if response.parts:
                pet_response_text = response.text
            else: 
                logging.warning(f"LLM response was empty or blocked. Feedback: {response.prompt_feedback}")
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    pet_response_text = f"(因為內容限制，我不能回答這個問題：{response.prompt_feedback.block_reason_message})"
                    self._add_chat_message("系統", f"LLM 回應被阻擋: {response.prompt_feedback.block_reason_message}", "error")
                else:
                    pet_response_text = "(我不知道該說什麼耶...)"
            
            self._add_chat_message("小星", pet_response_text, "pet")
            save_memory(self.user_id, f"小星說: {pet_response_text}", importance=1)
            
            # Update internal LLM history with the actual user's message and model's response
            self.llm_history.append({"role": "user", "parts": [{"text": user_text}]}) # Actual user message
            self.llm_history.append({"role": "model", "parts": [{"text": pet_response_text}]}) # Model response
            
            MAX_HISTORY_TURNS = 10 
            if len(self.llm_history) > MAX_HISTORY_TURNS * 2:
                self.llm_history = self.llm_history[-(MAX_HISTORY_TURNS * 2):]

            self._update_emotions_from_llm_response(pet_response_text)

        except Exception as e:
            logging.error(f"Error during LLM communication: {e}") # Error already includes type
            self._add_chat_message("小星", "哎呀，我的腦袋好像打結了...請稍後再試一次，或是檢查看看設定？", "pet")
            if "API key not valid" in str(e) or "permission" in str(e).lower() or "API_KEY_INVALID" in str(e).upper():
                self._add_chat_message("系統", "偵測到 API 金鑰問題。請檢查您的 Gemini API 金鑰。", "error")
                self.prompt_for_api_key()
                self.init_llm_model() 
            elif "deadline exceeded" in str(e).lower() or "resource exhausted" in str(e).lower():
                 self._add_chat_message("系統", "與 LLM 伺服器通訊逾時或資源不足，請稍後再試。", "error")
            # No need for generic else, logging.error already captures it.

        finally:
            self.is_processing_llm = False
            self.root.config(cursor="")
            self.update_pet_appearance()

    def _add_chat_message(self, sender, message, tag):
        self.chat_history_text.config(state=tk.NORMAL)
        if self.chat_history_text.index('end-1c') != "1.0": # Add newline if not the first message
            self.chat_history_text.insert(tk.END, "\n")
        
        timestamp = datetime.now().strftime("%H:%M")
        formatted_message = f"[{timestamp}] {sender}: {message}"
        self.chat_history_text.insert(tk.END, formatted_message, tag)
        self.chat_history_text.see(tk.END) # Scroll to the end
        self.chat_history_text.config(state=tk.DISABLED)
        logging.info(f"Chat: [{sender}] {message}")

    def _decay_emotions(self):
        decay_rate = float(self.settings.get(SETTING_DECAY_RATE, 0.02))
        mood_stability = float(self.settings.get(SETTING_MOOD_STABILITY, 0.3)) # Higher stability = slower decay to midpoint
        
        changed = False
        for emotion, value in self.emotions.items():
            # Decay towards 0.5 (neutral baseline), influenced by mood_stability
            # If stability is high, decay is slower (less impact from decay_rate)
            # If stability is low, decay is faster (more impact from decay_rate)
            effective_decay = decay_rate * (1.0 - mood_stability * 0.8) # Max reduction of decay by 80%
            
            if value > 0.5:
                new_value = max(0.5, value - effective_decay)
            elif value < 0.5:
                new_value = min(0.5, value + effective_decay)
            else:
                new_value = value

            if abs(new_value - value) > 0.001: # Only save if changed significantly
                self.emotions[emotion] = new_value
                save_emotion(self.user_id, emotion, new_value)
                changed = True
        
        if changed:
            logging.debug(f"Emotions after decay: {self.emotions}")
            self._update_emotion_display()
            self.update_pet_appearance()

    def get_current_overall_mood_description(self):
        # Simple mood assessment based on dominant emotion or sum of positive/negative
        # This can be expanded to a more PAD-like model if needed.
        if self.is_sleeping: return "你正在熟睡中。"

        positive_sum = sum(self.emotions[e] for e in POSITIVE_EMOTIONS if e in self.emotions)
        negative_sum = sum(self.emotions[e] for e in NEGATIVE_EMOTIONS if e in self.emotions)
        
        # Consider Neuroticism for baseline mood perception
        neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)
        # Adjust baseline for mood based on neuroticism: higher N means slightly lower baseline happiness
        neuro_mood_offset = (neuroticism - 0.5) * -0.2 # Max +/- 0.1 to the diff

        diff = (positive_sum / len(POSITIVE_EMOTIONS)) - (negative_sum / len(NEGATIVE_EMOTIONS)) + neuro_mood_offset

        if diff > 0.3: return f"你感覺很開心 ({self.current_dominant_emotion})。"
        if diff > 0.1: return f"你感覺心情不錯 ({self.current_dominant_emotion})。"
        if diff < -0.3: return f"你感覺有點低落 ({self.current_dominant_emotion})。"
        if diff < -0.1: return f"你感覺不太好 ({self.current_dominant_emotion})。"
        return f"你感覺心情平靜 ({self.current_dominant_emotion})。"


    def update_pet_appearance(self, force_emotion=None):
        if self.is_sleeping:
            current_emotion_key = "sleepy" # Or a specific "sleeping" image
        elif force_emotion:
            current_emotion_key = force_emotion
        else:
            # Determine dominant emotion
            if not self.emotions:  # Should not happen if initialized correctly
                self.current_dominant_emotion = "neutral"
            else:
                # Prioritize strong negative emotions, then strong positive, then general levels
                strong_threshold = 0.7
                moderate_threshold = 0.55 # Slightly above baseline

                # Check for strong specific negative emotions
                if self.emotions.get('fear', 0) > strong_threshold or self.emotions.get('anxiety',0) > strong_threshold : self.current_dominant_emotion = "anxious"
                elif self.emotions.get('sadness', 0) > strong_threshold: self.current_dominant_emotion = "sad"
                elif self.emotions.get('anger', 0) > strong_threshold: self.current_dominant_emotion = "angry"
                # Check for strong specific positive emotions
                elif self.emotions.get('joy', 0) > strong_threshold or self.emotions.get('excitement',0) > strong_threshold: self.current_dominant_emotion = "excited"
                elif self.emotions.get('love', 0) > strong_threshold or self.emotions.get('adoration',0) > strong_threshold: self.current_dominant_emotion = "happy" # map love to happy for image
                # General mood based on averages if no single emotion is very strong
                else:
                    avg_positive = sum(self.emotions[e] for e in POSITIVE_EMOTIONS if e in self.emotions) / len(POSITIVE_EMOTIONS)
                    avg_negative = sum(self.emotions[e] for e in NEGATIVE_EMOTIONS if e in self.emotions) / len(NEGATIVE_EMOTIONS)
                    
                    if avg_negative > avg_positive and avg_negative > moderate_threshold :
                        # Find the strongest negative emotion if general negativity is high
                        max_neg_val = 0
                        dom_neg_emo = "sad" # default negative
                        for emo_name in NEGATIVE_EMOTIONS:
                            if self.emotions.get(emo_name,0) > max_neg_val:
                                max_neg_val = self.emotions.get(emo_name,0)
                                if emo_name == 'anxiety' or emo_name == 'fear': dom_neg_emo = 'anxious'
                                elif emo_name == 'anger': dom_neg_emo = 'angry'
                                else: dom_neg_emo = 'sad' # Default for other negatives
                        self.current_dominant_emotion = dom_neg_emo
                    elif avg_positive > avg_negative and avg_positive > moderate_threshold:
                         max_pos_val = 0
                         dom_pos_emo = "happy" # default positive
                         for emo_name in POSITIVE_EMOTIONS:
                             if self.emotions.get(emo_name,0) > max_pos_val:
                                 max_pos_val = self.emotions.get(emo_name,0)
                                 if emo_name == 'excitement': dom_pos_emo = 'excited'
                                 else: dom_pos_emo = 'happy'
                         self.current_dominant_emotion = dom_pos_emo
                    elif self.emotions.get('boredom', 0) > moderate_threshold + 0.1: # Boredom needs to be a bit higher
                        self.current_dominant_emotion = "bored"
                    else:
                        self.current_dominant_emotion = "neutral"
            current_emotion_key = self.current_dominant_emotion

        # Load and display image
        img_path_setting = load_app_setting('pet_image_path', DEFAULT_IMG_PATH)
        
        # Try emotion-specific image first, then general configured image, then default
        emotion_img_path = EMOTION_IMAGES.get(current_emotion_key)
        
        final_img_path = DEFAULT_IMG_PATH # Fallback to absolute default
        if emotion_img_path and os.path.exists(emotion_img_path):
            final_img_path = emotion_img_path
        elif img_path_setting and os.path.exists(img_path_setting):
            final_img_path = img_path_setting
        
        if not os.path.exists(final_img_path): # If chosen one is missing, ensure default.png
             final_img_path = DEFAULT_IMG_PATH
             if not os.path.exists(DEFAULT_IMG_PATH): # If default.png is also missing
                logging.error("Default image default.png is missing!")
                # Create a placeholder if even default is gone
                try:
                    img = Image.new('RGBA', (100, 100), (128, 128, 128, 128)) # Semi-transparent grey
                    img.save(DEFAULT_IMG_PATH)
                    logging.info("Created a new placeholder for default.png")
                    final_img_path = DEFAULT_IMG_PATH
                except Exception as e_img:
                    logging.error(f"Failed to create placeholder default image: {e_img}")
                    # Cannot display image, maybe show text error in label?
                    if self.pet_img_label: self.pet_img_label.config(text="Image Error!")
                    return


        try:
            img = Image.open(final_img_path)
            img.thumbnail((150, 150)) # Resize
            self.current_pet_image = ImageTk.PhotoImage(img)
            if self.pet_img_label:
                 self.pet_img_label.config(image=self.current_pet_image)
            else: # UI not fully set up yet
                logging.warning("pet_img_label not initialized when trying to update appearance.")
        except FileNotFoundError:
            logging.error(f"Image not found: {final_img_path}. Using fallback or logging error.")
            if self.pet_img_label: self.pet_img_label.config(image=None, text=f"Error: {current_emotion_key} img missing")
        except Exception as e:
            logging.error(f"Error loading image {final_img_path}: {e}")
            if self.pet_img_label: self.pet_img_label.config(image=None, text="Image Load Error")

    def _change_pet_image_dialog(self):
        filepath = filedialog.askopenfilename(
            title="選擇寵物圖片",
            filetypes=(("PNG files", "*.png"), ("GIF files", "*.gif"), ("All files", "*.*"))
        )
        if filepath:
            save_app_setting('pet_image_path', filepath)
            # Also update default.png if user selects a new base image that is not emotion-specific
            # This logic might be complex: distinguish between setting a new *default look* vs. *temporary override*.
            # For now, 'pet_image_path' acts as the user's preferred default non-emotional state image.
            self.update_pet_appearance()
            logging.info(f"Pet image changed to: {filepath}")

    def _open_settings(self):
        # Pass self (PetApp instance) to SettingsWindow
        SettingsWindow(self.root, self)
    
    def _periodic_update(self):
        """Handles periodic tasks like emotion decay, checking sleep, proactive chat."""
        now = datetime.now()
        current_time = now.time()

        # 1. Check sleep schedule
        bedtime_h = int(self.settings.get(SETTING_BEDTIME_HOUR, 23))
        bedtime_m = int(self.settings.get(SETTING_BEDTIME_MINUTE, 0))
        wakeup_h = int(self.settings.get(SETTING_WAKEUP_HOUR, 7))
        wakeup_m = int(self.settings.get(SETTING_WAKEUP_MINUTE, 0))
        
        bed_time = dt_time(bedtime_h, bedtime_m)
        wake_time = dt_time(wakeup_h, wakeup_m)

        was_sleeping = self.is_sleeping
        if bed_time <= wake_time: # Normal non-crossing midnight schedule
            if bed_time <= current_time < wake_time:
                self.is_sleeping = True
            else:
                self.is_sleeping = False
        else: # Schedule crosses midnight (e.g. sleep 23:00 to 07:00)
            if current_time >= bed_time or current_time < wake_time:
                self.is_sleeping = True
            else:
                self.is_sleeping = False
        
        if self.is_sleeping and not was_sleeping:
            self._add_chat_message("小星", "zzz... (小星睡著了)", "system")
            save_memory(self.user_id, "小星進入睡眠狀態。", importance=0)
            self.update_pet_appearance() # Show sleeping face
        elif not self.is_sleeping and was_sleeping:
            greeting = self.get_current_time_period_greeting()
            self._add_chat_message("小星", f"哈～欠～ {greeting} 我起床囉！", "pet")
            save_memory(self.user_id, "小星睡醒了。", importance=0)
            self.update_pet_appearance() # Show awake face

        if not self.is_sleeping:
            self._decay_emotions()
            self._try_proactive_chat(now)
            self._check_task_reminders(now)
        
        self.root.after(1000 * 1, self._periodic_update) # Run every 1 second for responsiveness of sleep/wake

    def _get_proactive_chat_interval(self):
            """Determines proactive chat interval based on settings and personality."""
            freq_setting = int(self.settings.get(SETTING_PROACTIVE_FREQ, 1)) # 0: Frequent, 1: Normal, 2: Occasional, 3: Never
            extraversion = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
            
            if freq_setting == 3: # Never
                return float('inf'), float('inf')

            base_min_minutes, base_max_minutes = {
                0: (5, 15),  # Frequent
                1: (10, 25), # Normal
                2: (20, 40)  # Occasional
            }.get(freq_setting, (10, 25))

            # Extraversion makes proactive chat more frequent
            # Low extraversion (e.g., 0.0) increases interval by up to 50%
            # High extraversion (e.g., 1.0) decreases interval by up to 30%
            modifier = 1.0 - (extraversion - 0.5) * 0.6 # Max decrease 30%, max increase 30% (0.5 * 0.6 = 0.3)
            
            min_interval = base_min_minutes * modifier
            max_interval = base_max_minutes * modifier
            
            # Ensure min is less than max and apply some sanity clamping
            min_interval = max(1, min_interval) # At least 1 minute
            max_interval = max(min_interval + 1, max_interval) # Max at least 1 min more than min

            return min_interval * 60, max_interval * 60 # Return in seconds


    def get_proactive_chat_prompt(self):
        """Generates a prompt for proactive chat based on personality, mood, and context."""
        # Personality traits
        openness = self.character_traits.get(SETTING_OCEAN_OPENNESS, 0.5)
        conscientiousness = self.character_traits.get(SETTING_OCEAN_CONSCIENTIOUSNESS, 0.5)
        extraversion = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
        agreeableness = self.character_traits.get(SETTING_OCEAN_AGREEABLENESS, 0.5)
        neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)

        possible_actions = []

        # General social initiations (more likely with high extraversion)
        if extraversion > 0.4:
            possible_actions.extend([
                "隨便聊點什麼，問候一下使用者。",
                "分享一個你最近「學到」的有趣小知識或想法 (跟你的個性有關)。",
                f"根據你現在 {self.current_dominant_emotion} 的心情，說點話。",
                "問使用者今天過得怎麼樣。"
            ] * int(extraversion * 5)) # Weight by extraversion

        # Curious questions or sharing ideas (more likely with high openness)
        if openness > 0.4:
            possible_actions.extend([
                "提出一個跟天氣、新聞（假設你知道）、或普遍知識有關的開放式問題。",
                "如果你知道使用者的地點，可以問問看那裡的天氣怎麼樣。",
                "分享一個你「突然想到」的點子或觀察。"
            ] * int(openness * 4))

        # Task reminders (more likely with high conscientiousness)
        pending_tasks = get_tasks(self.user_id, include_completed=False)
        if pending_tasks and conscientiousness > 0.5:
            task_desc = random.choice(pending_tasks)['description']
            possible_actions.extend([
                f"溫柔地提醒使用者關於任務：'{task_desc}'。",
                f"問使用者任務 '{task_desc}' 的進度如何。"
            ] * int(conscientiousness * 6))
        elif not pending_tasks and conscientiousness > 0.6:
                possible_actions.append("問使用者有沒有什麼需要幫忙記錄的事情。")


        # Caring/Agreeable actions (more likely with high agreeableness)
        if agreeableness > 0.5:
            possible_actions.extend([
                "表達關心，例如「最近還好嗎？」、「要不要休息一下？」",
                "說一句友善或鼓勵的話。"
            ] * int(agreeableness * 4))

        # Reflective/Neurotic actions (more likely with high neuroticism if mood is also fitting)
        if neuroticism > 0.6 and (self.current_dominant_emotion in ["anxious", "sad", "bored"] or any(self.emotions[e] > 0.6 for e in ["anxiety", "sadness", "boredom"])):
            possible_actions.extend([
                "如果心情不好，稍微抱怨一下或表達你的擔憂 (但不要太負面)。",
                "自言自語，表達一點點無聊或沉思。"
            ] * int(neuroticism * 3))
        elif neuroticism < 0.3 and self.current_dominant_emotion == "neutral": # Very stable, might comment on calm
            possible_actions.append("表達此刻的平靜或滿足感。")


        # Memory-based prompts (e.g., recall a pleasant memory)
        # This is a simplified version of "Memory-based Emotion" trigger
        # Could be expanded to search memories with high positive emotion tags if implemented
        positive_memories = load_memory(self.user_id, is_long_term=True, limit=10) # Check LTM
        if not positive_memories: positive_memories = load_memory(self.user_id, is_long_term=False, limit=10) # Or STM

        if positive_memories:
            # Simplistic: pick a random recent memory. Could be improved by filtering for "positive" tagged memories.
            # For now, just assume some memories might be good conversation starters.
            mem_content = random.choice(positive_memories)[1]
            if "使用者說:" not in mem_content and "小星說:" not in mem_content: # Avoid simple conversational recall
                    possible_actions.append(f"回憶起之前發生的事：'{mem_content[:50]}...'，並對此發表評論或提問。")


        # Idle/Ambient actions (always a small chance)
        possible_actions.extend([
            "發出一個簡單的狀聲詞，比如「嗯...」、「唉...」、「喔！」",
            "做一個小小的動作的描述，比如「伸了個懶腰」、「打了個哈欠」。",
            "唱一小段不成調的歌，或哼個小曲。"
        ] * 2) # Lower weight for these simple ones unless nothing else fits

        if not possible_actions:
            return "你就隨意說點什麼吧，符合你現在的心情和個性就好。"
        chosen_action = random.choice(possible_actions)
        

        return f"你現在想要主動跟使用者說些話或做點什麼。請執行以下行動或圍繞這個主題說話：{chosen_action}"


    def _try_proactive_chat(self, current_datetime_obj):
        if self.is_sleeping or self.is_processing_llm:
            return

        min_interval, max_interval = self._get_proactive_chat_interval()
        if time.time() - self.last_proactive_chat_time > random.uniform(min_interval, max_interval):
            proactive_action_prompt = self.get_proactive_chat_prompt() # This is the "user message" for proactive
            
            logging.info(f"Attempting proactive chat with action prompt: {proactive_action_prompt}")
            
            self.is_processing_llm = True 
            self.root.config(cursor="watch")
            
            try:
                # The proactive_action_prompt acts as the 'user_message' for get_llm_prompt
                prompt_data = self.get_llm_prompt(proactive_action_prompt) 
                if not prompt_data:
                    self.is_processing_llm = False
                    self.root.config(cursor="")
                    return

                # The system context and proactive_action_prompt are already in prompt_data["contents"]
                # No need to add to self.llm_history here, it's like a fresh thought process for proactive.
                # Or, if we want to log it as part of history:
                # self.llm_history.append({"role": "user", "parts": [{"text": f"(系統提示：小星想主動說話，基於：{proactive_action_prompt})"}]})
                # For this call, prompt_data["contents"] is self-contained.

                response = self.model.generate_content(
                    contents=prompt_data["contents"],
                    # system_instruction=prompt_data["system_instruction"], # REMOVED
                    generation_config=prompt_data["generation_config"]
                )
                
                pet_response_text = ""
                if response.parts:
                    pet_response_text = response.text
                else:
                    logging.warning(f"Proactive LLM response was empty or blocked. Feedback: {response.prompt_feedback}")
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                         pet_response_text = f"(因為內容限制，我不能說這個：{response.prompt_feedback.block_reason_message})"
                    else:
                         pet_response_text = "(嗯...我剛剛想到什麼去了？)"
                
                self._add_chat_message("小星", pet_response_text, "pet")
                save_memory(self.user_id, f"小星主動說: {pet_response_text}", importance=1)
                
                # Add the proactive thought (as user) and response (as model) to history
                # This helps maintain context if the user replies to the proactive chat.
                self.llm_history.append({"role": "user", "parts": [{"text": proactive_action_prompt }]}) # The "thought" or trigger
                self.llm_history.append({"role": "model", "parts": [{"text": pet_response_text}]})
                
                MAX_HISTORY_TURNS = 10 
                if len(self.llm_history) > MAX_HISTORY_TURNS * 2:
                    self.llm_history = self.llm_history[-(MAX_HISTORY_TURNS * 2):]

                self._update_emotions_from_llm_response(pet_response_text)

            except Exception as e:
                logging.error(f"Error during proactive LLM communication: {e}")
            finally:
                self.is_processing_llm = False
                self.root.config(cursor="")
                self.update_pet_appearance()

            self.last_proactive_chat_time = time.time()
            self.reset_non_response_timer()

    def _apply_random_mood_fluctuations(self):
        """Applies small random noise to a few emotions to simulate natural fluctuations."""
        if self.is_sleeping: return

        num_emotions_to_fluctuate = random.randint(1, 3) # Fluctuate 1 to 3 emotions
        emotions_to_change = random.sample(list(self.emotions.keys()), num_emotions_to_fluctuate)
        
        changed_any = False
        for emotion_name in emotions_to_change:
            current_value = self.emotions[emotion_name]
            noise = random.uniform(-0.05, 0.05) # Small random fluctuation
            
            # Personality can affect susceptibility to random fluctuations
            # e.g. High Neuroticism might mean larger or more frequent fluctuations for negative emotions
            #      High Mood Stability (setting) should dampen this.
            neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)
            mood_stability_setting = float(self.settings.get(SETTING_MOOD_STABILITY, 0.3))

            fluctuation_multiplier = 1.0
            if emotion_name in NEGATIVE_EMOTIONS:
                fluctuation_multiplier *= (1 + (neuroticism - 0.5) * 0.5) # N=1 -> 1.25x, N=0 -> 0.75x
            elif emotion_name in POSITIVE_EMOTIONS:
                    fluctuation_multiplier *= (1 - (neuroticism - 0.5) * 0.3) # N=1 -> 0.85x, N=0 -> 1.15x
            
            # Mood stability setting reduces overall fluctuation
            fluctuation_multiplier *= (1.0 - mood_stability_setting * 0.7) # Stability=1 -> 0.3x, Stability=0 -> 1x
            
            noise *= max(0.1, fluctuation_multiplier) # Ensure some minimum effect if not fully dampened

            new_value = max(0.0, min(1.0, current_value + noise))
            
            if abs(new_value - current_value) > 0.005: # Only apply if change is noticeable
                self.emotions[emotion_name] = new_value
                save_emotion(self.user_id, emotion_name, new_value)
                changed_any = True
        
        if changed_any:
            logging.debug(f"Applied random mood fluctuations. New state: {self.emotions}")
            self._update_emotion_display()
            self.update_pet_appearance()


    def _handle_significant_event_for_personality(self, event_type, strength_modifier=1.0):
        """
        Adjusts personality traits based on significant events.
        event_type: e.g., "task_completed_many", "prolonged_high_stress", "repeated_positive_social"
        strength_modifier: A float, e.g., 1.0 for normal, 0.5 for mild, 2.0 for strong event.
        """
        logging.info(f"Handling significant event for personality: {event_type}, strength: {strength_modifier}")
        change_applied = False
        
        # Define how much each trait changes per event type. Small values for gradual change.
        # Positive values increase the trait, negative values decrease.
        trait_deltas = {
            SETTING_OCEAN_CONSCIENTIOUSNESS: 0.0,
            SETTING_OCEAN_AGREEABLENESS: 0.0,
            SETTING_OCEAN_EXTRAVERSION: 0.0,
            SETTING_OCEAN_OPENNESS: 0.0,
            SETTING_OCEAN_NEUROTICISM: 0.0,
        }

        # --- Define event effects on traits ---
        if event_type == "task_completed_milestone": # E.g., after completing 5 or 10 tasks
            trait_deltas[SETTING_OCEAN_CONSCIENTIOUSNESS] += 0.015 * strength_modifier
            # Completing tasks might also slightly boost "optimism" (reduce Neuroticism if it represents pessimism)
            trait_deltas[SETTING_OCEAN_NEUROTICISM] -= 0.005 * strength_modifier # Less anxiety/more control
        
        elif event_type == "repeated_positive_interaction": # E.g., many friendly chats
            trait_deltas[SETTING_OCEAN_AGREEABLENESS] += 0.01 * strength_modifier
            trait_deltas[SETTING_OCEAN_EXTRAVERSION] += 0.008 * strength_modifier
            trait_deltas[SETTING_OCEAN_NEUROTICISM] -= 0.005 * strength_modifier # Feeling safer, more liked

        elif event_type == "prolonged_high_negative_emotion": # E.g., many days with dominant negative emotions
            trait_deltas[SETTING_OCEAN_NEUROTICISM] += 0.01 * strength_modifier
            trait_deltas[SETTING_OCEAN_AGREEABLENESS] -= 0.005 * strength_modifier # May become more irritable

        elif event_type == "explored_new_topic_successfully": # E.g., user engaged with a new topic suggested by pet
            trait_deltas[SETTING_OCEAN_OPENNESS] += 0.01 * strength_modifier
            trait_deltas[SETTING_OCEAN_EXTRAVERSION] += 0.005 * strength_modifier # If interaction was involved

        # Apply changes
        for trait_key, delta in trait_deltas.items():
            if delta != 0.0 and trait_key in self.character_traits:
                current_val = self.character_traits.get(trait_key, DEFAULT_CHARACTER_TRAITS[trait_key])
                new_val = current_val + delta
                # Clamp between 0 and 1
                self.character_traits[trait_key] = max(0.0, min(1.0, new_val))
                change_applied = True
                logging.info(f"Personality trait {trait_key} changed from {current_val:.3f} to {self.character_traits[trait_key]:.3f} due to {event_type}.")

        if change_applied:
            save_character_traits(self.user_id, self.character_traits)
            self._add_chat_message("系統", f"[小星的個性似乎因為最近的經歷有了一些潛移默化的改變...]", "system")
            # Maybe LLM makes a subtle comment reflecting this change if significant
            # self._try_proactive_chat(datetime.now()) # Trigger a chat that might reflect new personality


    def _check_task_reminders(self, current_datetime_obj):
        # Basic task reminder logic - can be expanded
        # This is a simple check, not a robust scheduler
        tasks = get_tasks(self.user_id, include_completed=False)
        for task in tasks:
            if task['due_at']:
                due_time = datetime.fromtimestamp(task['due_at'])
                time_to_due = due_time - current_datetime_obj
                
                # Remind if due within an hour and not reminded recently
                if timedelta(minutes=0) < time_to_due <= timedelta(hours=1):
                    if task['id'] not in self.current_task_reminders or \
                        time.time() - self.current_task_reminders[task['id']] > 3600: # Remind once per hour
                        
                        reminder_message = f"提醒一下，你的任務「{task['description']}」快要到期了 ({due_time.strftime('%H:%M')})！"
                        self._add_chat_message("小星", reminder_message, "pet")
                        save_memory(self.user_id, f"小星提醒任務: {task['description']}", importance=2)
                        self.current_task_reminders[task['id']] = time.time()
                        # Potentially trigger a personality update if conscientiousness is high and user responds to reminder
                        # self._handle_significant_event_for_personality("task_interaction_positive")


    def reset_non_response_timer(self):
        if self.non_response_timer_id:
            self.root.after_cancel(self.non_response_timer_id)
        
        timeout_minutes = int(self.settings.get(SETTING_NON_RESPONSE_TIMEOUT, 45))
        if timeout_minutes > 0:
            self.non_response_timer_id = self.root.after(timeout_minutes * 60 * 1000, self._handle_non_response)

    def _handle_non_response(self):
        if self.is_sleeping or self.is_processing_llm:
            self.reset_non_response_timer() # Reschedule if busy or asleep
            return

        time_since_last_interaction = time.time() - self.last_interaction_time
        timeout_minutes = int(self.settings.get(SETTING_NON_RESPONSE_TIMEOUT, 45))

        if time_since_last_interaction > timeout_minutes * 60 :
            logging.info("User non-response detected. Triggering self-talk.")
            
            # Influence what kind of self-talk based on personality and mood
            extraversion = self.character_traits.get(SETTING_OCEAN_EXTRAVERSION, 0.5)
            neuroticism = self.character_traits.get(SETTING_OCEAN_NEUROTICISM, 0.5)
            
            self_talk_prompt = "你已經很久沒跟使用者互動了，自言自語點什麼吧。"
            if extraversion < 0.3: # Introverted
                self_talk_prompt += " 你可能只是享受安靜，或是在思考自己的事情。"
            elif neuroticism > 0.7: # Anxious
                self_talk_prompt += " 你可能開始覺得有點孤單或被忽略了。"
            elif self.current_dominant_emotion == "bored" or self.emotions.get("boredom",0) > 0.6:
                self_talk_prompt += " 你覺得非常無聊。"
            else: # Neutral/Extroverted but ignored
                self_talk_prompt += " 你可能會試著引起注意，或者只是表達一下自己的存在感。"


            # Use the proactive chat mechanism but with this specific prompt
            self.is_processing_llm = True
            self.root.config(cursor="watch")
            try:
                prompt_data = self.get_llm_prompt(self_talk_prompt)
                if not prompt_data:
                    self.is_processing_llm = False
                    self.root.config(cursor="")
                    return
                
                self.llm_history.append({"role": "user", "parts": [{"text": f"(系統提示：使用者長時間無回應，小星開始自言自語，基於：{self_talk_prompt})"}]})

                response = self.model.generate_content(
                    contents=prompt_data["contents"],
                    system_instruction=prompt_data["system_instruction"],
                    generation_config=prompt_data["generation_config"]
                )
                pet_response_text = response.text if response.parts else "(默默地看著遠方...)"
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    pet_response_text = f"(我想說點什麼，但好像不太好：{response.prompt_feedback.block_reason_message})"
                
                self._add_chat_message("小星", pet_response_text, "pet")
                save_memory(self.user_id, f"小星自言自語: {pet_response_text}", importance=0)
                self.llm_history.append({"role": "model", "parts": [{"text": pet_response_text}]})
                self._update_emotions_from_llm_response(pet_response_text)
            except Exception as e:
                logging.error(f"Error during self-talk LLM call: {e}")
            finally:
                self.is_processing_llm = False
                self.root.config(cursor="")
                self.update_pet_appearance()
            
            self.last_proactive_chat_time = time.time() # Self-talk counts as a proactive action
        
        self.reset_non_response_timer() # Reset timer after handling


    def _periodic_update(self):
        """Handles periodic tasks like emotion decay, checking sleep, proactive chat, random fluctuations."""
        now = datetime.now()
        current_time = now.time()

        # 1. Check sleep schedule (as before)
        bedtime_h = int(self.settings.get(SETTING_BEDTIME_HOUR, 23))
        bedtime_m = int(self.settings.get(SETTING_BEDTIME_MINUTE, 0))
        wakeup_h = int(self.settings.get(SETTING_WAKEUP_HOUR, 7))
        wakeup_m = int(self.settings.get(SETTING_WAKEUP_MINUTE, 0))
        
        bed_time = dt_time(bedtime_h, bedtime_m)
        wake_time = dt_time(wakeup_h, wakeup_m)
        was_sleeping = self.is_sleeping
        # (Sleep logic from Part 2, assumed to be correct and complete here)
        if bed_time <= wake_time: 
            self.is_sleeping = bed_time <= current_time < wake_time
        else: 
            self.is_sleeping = current_time >= bed_time or current_time < wake_time
        
        if self.is_sleeping and not was_sleeping:
            self._add_chat_message("小星", "zzz... (小星睡著了)", "system")
            save_memory(self.user_id, "小星進入睡眠狀態。", importance=0)
            self.update_pet_appearance()
        elif not self.is_sleeping and was_sleeping:
            greeting = self.get_current_time_period_greeting()
            self._add_chat_message("小星", f"哈～欠～ {greeting} 我起床囉！", "pet")
            save_memory(self.user_id, "小星睡醒了。", importance=0)
            self.update_pet_appearance()

        if not self.is_sleeping:
            self._decay_emotions()
            self._apply_random_mood_fluctuations() # Add random noise to emotions
            self._try_proactive_chat(now)
            self._check_task_reminders(now)
            # Periodically check for conditions that might trigger personality updates (e.g., prolonged mood states)
            # This is a placeholder for a more robust check.
            if random.random() < 0.01: # Low chance per update cycle to check this
                current_neg_emotion_avg = sum(self.emotions[e] for e in NEGATIVE_EMOTIONS if e in self.emotions) / len(NEGATIVE_EMOTIONS)
                if current_neg_emotion_avg > 0.7: # If average negative emotion is high
                    # This would need to track duration, not just instantaneous value.
                    # For now, a simplified trigger:
                    # self._handle_significant_event_for_personality("prolonged_high_negative_emotion", strength_modifier=0.5)
                    pass # Requires more state tracking for "prolonged"

        self.root.after(1000 * 1, self._periodic_update) # Run every 1 second

    # --- Drag and Close Window Methods (Mostly unchanged) ---
    def _on_drag_start(self, event):
        self.is_dragging = True
        self.drag_start_x = event.x_root - self.root.winfo_x()
        self.drag_start_y = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event):
        if self.is_dragging:
            x = event.x_root - self.drag_start_x
            y = event.y_root - self.drag_start_y
            self.root.geometry(f"+{x}+{y}")

    def on_close(self):
        logging.info("Close button pressed. Shutting down.")
        if self.non_response_timer_id:
            self.root.after_cancel(self.non_response_timer_id)
        # Any other cleanup
        self.root.destroy()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()

# --- Style ---
    style = ttk.Style(root)
    try:
        available_themes = style.theme_names()
        logging.info(f"Available ttk themes: {available_themes}")
        # Prefer modern/native themes
        if 'vista' in available_themes: style.theme_use('vista') # Windows
        elif 'clam' in available_themes: style.theme_use('clam') # Cross-platform, good fallback
        elif 'aqua' in available_themes: style.theme_use('aqua') # macOS
        elif 'gtk' in available_themes: style.theme_use('gtk') # Linux with GTK
        else: style.theme_use('default') # Default Tk theme
        logging.info(f"Using ttk theme: {style.theme_use()}")
    except tk.TclError:
            logging.warning("Could not set ttk theme, using Tk default.")

    # --- Window Config ---
    root.minsize(450, 600) 
    # root.maxsize(700, 900) 

    # --- Initialize App ---
    # Initialize DB path (in case it's needed before app fully starts, though init_db handles it)
    if not os.path.exists(DB_PATH):
        logging.info(f"Database not found at {DB_PATH}, will be created.")

    app = PetApp(root)

        # --- Start Main Loop (Check Initialization) ---
    if hasattr(app, 'model') and app.model: # Check if LLM model was successfully initialized
        root.protocol("WM_DELETE_WINDOW", app.on_close) 
        root.mainloop()
    else:
        logging.error("Application LLM failed to initialize. The application might not be fully functional or may close.")
        # If API key was the issue, the prompt would have appeared.
        # If it's still None, could be another critical error.
        if not get_api_key('gemini_api_key'):
            messagebox.showerror("嚴重錯誤", "LLM 模型未能初始化，且未設定 API 金鑰。應用程式無法執行。")
            root.destroy() # Exit if API key is missing and crucial for startup.
        else:
            messagebox.showwarning("啟動問題", "LLM 模型未能初始化，但已偵測到 API 金鑰。請檢查金鑰有效性或網路。應用程式將嘗試運行，但某些功能可能受限。")
            # Decide if we should still run or exit. For now, let it run but with warnings.
            root.protocol("WM_DELETE_WINDOW", app.on_close) 
            root.mainloop() # Allow running even if LLM init failed but key exists
