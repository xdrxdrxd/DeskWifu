import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk
from tkinter import colorchooser # Added for color picking (optional future use)
from PIL import Image, ImageTk
import json # No longer needed for user_config or settings
import random
import time
import os
import sqlite3
import uuid
import google.generativeai as genai
import logging
from datetime import datetime, time as dt_time, timedelta
import math # For sigmoid if needed
import re # Import regex for improved JSON finding

# --- 日誌設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # <-- Use this for debugging prompts

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
    # Add more mappings as needed
    "bored": os.path.join(BASE_DIR, 'neutral.png'), # Example: map bored to neutral visually
    "sleepy": os.path.join(BASE_DIR, 'neutral.png'), # Example: map sleepy to neutral visually
}
# Create default image if missing
if not os.path.exists(DEFAULT_IMG_PATH):
    try:
        happy_path = EMOTION_IMAGES.get("happy")
        if happy_path and os.path.exists(happy_path):
            import shutil
            shutil.copy(happy_path, DEFAULT_IMG_PATH)
            logging.info("Default image not found, copied from happy.png")
        else:
            # Create a simple placeholder if happy.png is also missing
            img = Image.new('RGBA', (100, 100), (128, 128, 128, 255)) # Grey placeholder
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
SETTING_MOOD_STABILITY = 'mood_stability'
SETTING_OPTIMISM_TRAIT = 'optimism_trait'
SETTING_ANXIETY_TRAIT = 'anxiety_trait'
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
SETTING_USER_ID = 'user_id'
SETTING_SELECTED_LLM = 'selected_llm_model'
SETTING_BEDTIME_HOUR = 'bedtime_hour'
SETTING_BEDTIME_MINUTE = 'bedtime_minute'
SETTING_WAKEUP_HOUR = 'wakeup_hour'
SETTING_WAKEUP_MINUTE = 'wakeup_minute'
SETTING_LOCATION = 'user_location' # Added for weather
SETTING_NON_RESPONSE_TIMEOUT = 'non_response_timeout_minutes' # Added for inactivity detection


# --- 預設設定 ---
DEFAULT_SETTINGS = {
    SETTING_MOOD_STABILITY: 0.3,
    SETTING_OPTIMISM_TRAIT: 0.5,
    SETTING_ANXIETY_TRAIT: 0.5,
    SETTING_EMO_SENSITIVITY: 1.0,
    SETTING_DECAY_RATE: 0.02,
    SETTING_TIME_SHIFT_STRENGTH: 0.05,
    SETTING_PROACTIVE_FREQ: 1, # Index for "Normal"
    SETTING_RESPONSE_DELAY_ENABLED: 1,
    SETTING_RESPONSE_DELAY_MAX: 1200,
    SETTING_FORGET_CHANCE: 0.03,
    SETTING_RECALL_CHANCE: 0.01,
    SETTING_LLM_TEMP: 0.75,
    SETTING_LLM_MAX_TOKENS: 150,
    SETTING_STM_RETENTION_DAYS: 30,
    SETTING_USER_ID: "default_user",
    SETTING_SELECTED_LLM: "gemini-1.5-flash", # Updated default model
    SETTING_BEDTIME_HOUR: 23,
    SETTING_BEDTIME_MINUTE: 0,
    SETTING_WAKEUP_HOUR: 7,
    SETTING_WAKEUP_MINUTE: 0,
    SETTING_LOCATION: "", # Default empty location
    SETTING_NON_RESPONSE_TIMEOUT: 45, # Default non-response timeout in minutes
}

# --- Available Models ---
AVAILABLE_LLM_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-lite"] # Updated list


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
                            status TEXT DEFAULT 'remembered' -- remembered, forgotten
                         )''')
            c.execute('''CREATE TABLE IF NOT EXISTS long_term_memory (
                            id TEXT PRIMARY KEY,
                            user_id TEXT,
                            content TEXT,
                            timestamp REAL,
                            importance INTEGER,
                            status TEXT DEFAULT 'remembered' -- remembered, forgotten
                         )''')
            c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
                            id TEXT PRIMARY KEY,
                            key_name TEXT UNIQUE,
                            key_value TEXT
                         )''')
            # Consolidated app state/settings table
            c.execute('''CREATE TABLE IF NOT EXISTS app_state (
                            key TEXT PRIMARY KEY,
                            value TEXT -- Store all as TEXT for flexibility, convert on load/save
                         )''')
            # New table for tasks
            c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                            id TEXT PRIMARY KEY,
                            user_id TEXT,
                            description TEXT NOT NULL,
                            created_at REAL,
                            due_at REAL DEFAULT NULL, -- Optional due date/time timestamp
                            completed INTEGER DEFAULT 0 -- 0=incomplete, 1=complete
                         )''')

            # Add status columns if they don't exist (for older DBs)
            if not column_exists(c, 'short_term_memory', 'status'):
                logging.info("Adding 'status' column to short_term_memory.")
                c.execute("ALTER TABLE short_term_memory ADD COLUMN status TEXT DEFAULT 'remembered'")
            if not column_exists(c, 'long_term_memory', 'status'):
                 logging.info("Adding 'status' column to long_term_memory.")
                 c.execute("ALTER TABLE long_term_memory ADD COLUMN status TEXT DEFAULT 'remembered'")

            conn.commit()
            logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        messagebox.showerror("資料庫錯誤", f"無法初始化資料庫：{e}")

# --- 個性設定與口頭禪 ---
CHARACTER_PROFILE = (
    "你是一個名叫小星的桌寵，個性多變（活潑、好奇、溫暖、敏感、低落等），要假裝自己不是AI，絕對不要把情緒分數或個性分數顯示出來。"
    "說話時請融入台灣年輕人常用的口頭禪，例如「好喔」、「欸」、「煩欸」、「真的假的」、「對啊」、「屁啦」、「超好笑」、「好扯」、「啦」、「喔」、「啊」等等，"
    "但不強制任何詞語開頭，自然流暢即可。你的回應應該簡短、口語化、像朋友聊天。"
    "有時候你會主動跟使用者聊天，聊聊之前的事情、提醒任務、問問天氣、或者只是隨意閒聊。"
    "如果使用者很久不理你，你會覺得有點無聊或難過，可能會自言自語。"
    "你有自己的作息時間，睡覺時間不會主動打擾使用者。"
)

# --- API 金鑰管理 ---
def get_api_key(key_name):
    # (Unchanged)
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
    # (Unchanged)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Generate UUID for the primary key if needed
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
    # (Unchanged)
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

# --- App State/Settings Management (SQLite) ---
def save_setting(key, value):
    """Saves a setting to the app_state table, storing as TEXT."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Store all values as strings in the database
            c.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
            # logging.debug(f"Saved setting '{key}' with value '{value}' (stored as string)")
    except Exception as e:
        logging.error(f"Failed to save setting '{key}' with value '{value}': {e}")

def load_setting(key, default_value):
    """Loads a setting from the app_state table. Returns the raw value (usually string) or default."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM app_state WHERE key=?", (key,))
            row = c.fetchone()
            # Return the raw value from the database if it exists
            if row:
                # logging.debug(f"Loaded setting '{key}', raw value: '{row[0]}'")
                return row[0]
            else:
                # logging.debug(f"Setting '{key}' not found, returning default: '{default_value}'")
                return default_value
    except sqlite3.Error as e:
        logging.error(f"Failed to load setting '{key}' from DB: {e}")
        return default_value
    except Exception as e: # Catch other potential errors
        logging.error(f"Unexpected error loading setting '{key}': {e}")
        return default_value

# --- 記憶與情緒儲存與載入 (SQLite) ---
def save_emotion(user_id, emotion_name, value):
    # (Unchanged)
    value = max(0.0, min(1.0, float(value)))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO emotions (user_id, emotion_name, value, last_updated) VALUES (?, ?, ?, ?)",(user_id, emotion_name, value, time.time()))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save emotion for user {user_id}: {e}")

def load_emotions(user_id):
    # (Unchanged)
    emo = dict(EMOTIONS)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT emotion_name, value FROM emotions WHERE user_id=?", (user_id,))
            rows = c.fetchall()
            for name, val in rows:
                if name in emo: emo[name] = float(val) # Convert loaded value to float
            logging.info(f"Loaded {len(rows)} emotions for user {user_id}.")
    except sqlite3.Error as e: logging.error(f"Failed to load emotions for user {user_id}: {e}")
    return emo

def save_memory(user_id, content, is_long_term=False, importance=1):
    # (Unchanged)
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
    # (Unchanged)
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    memories = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Load only 'remembered' memories
            c.execute(f"SELECT id, content FROM {table} WHERE user_id=? AND status='remembered' ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            memories = c.fetchall()[::-1] # Reverse to get chronological order
    except sqlite3.Error as e: logging.error(f"Failed to load memory for user {user_id}: {e}")
    return memories

def clean_short_term_memory(retention_days=30):
    # (Unchanged)
    threshold = time.time() - retention_days * 24 * 3600
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Delete entries older than the threshold (regardless of status)
            c.execute("DELETE FROM short_term_memory WHERE timestamp<?", (threshold,))
            deleted_count = c.rowcount
            conn.commit()
            if deleted_count > 0: logging.info(f"Cleaned {deleted_count} old short-term memory entries (older than {retention_days} days).")
    except sqlite3.Error as e: logging.error(f"Failed to clean short-term memory: {e}")

# --- Task Management Functions (SQLite) ---
def add_task(user_id, description, due_at=None):
    """Adds a new task to the database."""
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
    """Retrieves tasks for a user."""
    tasks = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row # Return rows as dict-like objects
            c = conn.cursor()
            query = "SELECT id, description, created_at, due_at, completed FROM tasks WHERE user_id=?"
            params = [user_id]
            if not include_completed:
                query += " AND completed=0"
            query += " ORDER BY created_at ASC" # Show oldest first
            c.execute(query, params)
            tasks = [dict(row) for row in c.fetchall()] # Convert Row objects to dicts
    except sqlite3.Error as e:
        logging.error(f"Failed to get tasks for user {user_id}: {e}")
    return tasks

def complete_task(task_id):
    """Marks a task as completed."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
            conn.commit()
            if c.rowcount > 0:
                logging.info(f"Marked task {task_id} as completed.")
                return True
            else:
                logging.warning(f"Attempted to complete non-existent task ID: {task_id}")
                return False
    except sqlite3.Error as e:
        logging.error(f"Failed to complete task {task_id}: {e}")
        return False

def delete_task(task_id):
    """Deletes a task from the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            if c.rowcount > 0:
                logging.info(f"Deleted task {task_id}.")
                return True
            else:
                logging.warning(f"Attempted to delete non-existent task ID: {task_id}")
                return False
    except sqlite3.Error as e:
        logging.error(f"Failed to delete task {task_id}: {e}")
        return False


# --- 設定視窗類別 ---
class SettingsWindow(tk.Toplevel):
    def __init__(self, tk_parent, app_parent):
        super().__init__(tk_parent)
        self.parent_app = app_parent # Reference to the main PetApp instance
        self.settings_copy = self.parent_app.settings.copy() # Work on a copy

        self.title("小星設定")
        self.geometry("550x750") # Increased size for tasks

        # --- Use Notebook for Tabs ---
        self.notebook = ttk.Notebook(self)
        self.tab_general = ttk.Frame(self.notebook)
        self.tab_tasks = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_general, text="一般設定")
        self.notebook.add(self.tab_tasks, text="任務管理")
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # --- Store setting variables ---
        self.setting_vars = {}
        self._create_general_settings_widgets(self.tab_general)
        self._create_task_widgets(self.tab_tasks) # Create task tab UI

        self._load_settings_to_ui()
        self._load_tasks_to_ui() # Load tasks into the task tab

        # --- Buttons ---
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)

        save_button = ttk.Button(button_frame, text="儲存設定", command=self._save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = ttk.Button(button_frame, text="取消", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)

        # --- Make window modal ---
        self.transient(tk_parent)
        self.grab_set()
        self.wait_window(self)

# 在 SettingsWindow class 裡面
    def _create_general_settings_widgets(self, parent_frame):
        """Creates widgets for the 'General Settings' tab."""
        # --- Canvas for Scrolling ---
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame = scrollable_frame # Use this frame for placing widgets

        # --- Personality Traits ---
        trait_frame = ttk.LabelFrame(frame, text="個性特質")
        trait_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_scale_setting(trait_frame, SETTING_OPTIMISM_TRAIT, "樂觀傾向 (0悲觀-1樂觀):", 0.0, 1.0)
        self._add_scale_setting(trait_frame, SETTING_ANXIETY_TRAIT, "焦慮傾向 (0冷靜-1易焦慮):", 0.0, 1.0)

        # --- Emotional Response ---
        emo_frame = ttk.LabelFrame(frame, text="情緒反應")
        emo_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_scale_setting(emo_frame, SETTING_EMO_SENSITIVITY, "情緒敏感度 (0遲鈍-2敏感):", 0.0, 2.0)
        self._add_scale_setting(emo_frame, SETTING_MOOD_STABILITY, "情緒穩定度 (0易變-1穩定):", 0.0, 1.0)
        self._add_scale_setting(emo_frame, SETTING_DECAY_RATE, "情緒衰減速度 (0慢-0.1快):", 0.0, 0.1)
        self._add_scale_setting(emo_frame, SETTING_TIME_SHIFT_STRENGTH, "時間影響情緒強度 (0無-0.2強):", 0.0, 0.2)

        # --- Behavior Patterns ---
        behav_frame = ttk.LabelFrame(frame, text="行為模式")
        behav_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')

        # ---> 修改 Combobox 相關部分 <---
        # 保留 IntVar 但主要用於載入時暫存值，不直接綁定 Combobox 的讀取
        self.setting_vars[SETTING_PROACTIVE_FREQ] = tk.IntVar()
        ttk.Label(behav_frame, text="主動聊天頻率:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        # 將選項儲存為實例變數，以便後續查找索引
        self.freq_options = ["頻繁 (5-15分)", "普通 (10-25分)", "偶爾 (20-40分)", "從不"]
        # Combobox 直接使用顯示文字列表，移除 textvariable 參數
        self.freq_combobox = ttk.Combobox(behav_frame,
                                          values=self.freq_options,
                                          state="readonly",
                                          width=15)
        self.freq_combobox.grid(row=0, column=1, sticky="w", padx=5)
        # ---> 修改結束 <---

        self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED] = tk.IntVar()
        ttk.Checkbutton(behav_frame, text="啟用回應延遲模擬", variable=self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED]).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
        self._add_scale_setting(behav_frame, SETTING_RESPONSE_DELAY_MAX, "最大延遲時間 (ms):", 0, 3000, var_type=tk.IntVar, grid_row=2)

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
        bed_h_spin = ttk.Spinbox(bedtime_frame, from_=0, to=23, wrap=True, width=3, textvariable=self.setting_vars[SETTING_BEDTIME_HOUR])
        bed_h_spin.grid(row=0, column=1, sticky="w", padx=(0, 2))
        ttk.Label(bedtime_frame, text=":").grid(row=0, column=2)
        bed_m_spin = ttk.Spinbox(bedtime_frame, from_=0, to=59, wrap=True, width=3, format="%02.0f", textvariable=self.setting_vars[SETTING_BEDTIME_MINUTE])
        bed_m_spin.grid(row=0, column=3, sticky="w", padx=(2, 5))

        ttk.Label(bedtime_frame, text="起床時間:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        wake_h_spin = ttk.Spinbox(bedtime_frame, from_=0, to=23, wrap=True, width=3, textvariable=self.setting_vars[SETTING_WAKEUP_HOUR])
        wake_h_spin.grid(row=1, column=1, sticky="w", padx=(0, 2))
        ttk.Label(bedtime_frame, text=":").grid(row=1, column=2)
        wake_m_spin = ttk.Spinbox(bedtime_frame, from_=0, to=59, wrap=True, width=3, format="%02.0f", textvariable=self.setting_vars[SETTING_WAKEUP_MINUTE])
        wake_m_spin.grid(row=1, column=3, sticky="w", padx=(2, 5))


        # --- LLM Settings ---
        llm_frame = ttk.LabelFrame(frame, text="LLM 設定")
        llm_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_scale_setting(llm_frame, SETTING_LLM_TEMP, "回應溫度 (0精確-1隨機):", 0.0, 1.0, grid_row=0)
        self._add_entry_setting(llm_frame, SETTING_LLM_MAX_TOKENS, "回應最大長度 (tokens):", var_type=tk.IntVar, grid_row=1)


        # --- Other ---
        other_frame = ttk.LabelFrame(frame, text="其他")
        other_frame.pack(fill=tk.X, padx=10, pady=5, anchor='n')
        self._add_entry_setting(other_frame, SETTING_STM_RETENTION_DAYS, "短期記憶保留天數:", var_type=tk.IntVar, grid_row=0)
        self._add_entry_setting(other_frame, SETTING_LOCATION, "你的地點 (用於天氣):", var_type=tk.StringVar, grid_row=1)


        # Make columns in frames resize reasonably
        for child in frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                child.grid_columnconfigure(1, weight=1)


    def _add_scale_setting(self, parent, key, label_text, from_, to, var_type=tk.DoubleVar, grid_row=None):
        """Helper to add a label and scale for a setting."""
        self.setting_vars[key] = var_type()
        if grid_row is None: # Auto-increment row if not specified
            grid_row = parent.grid_size()[1] # Next available row
        ttk.Label(parent, text=label_text).grid(row=grid_row, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(parent, from_=from_, to=to, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[key]).grid(row=grid_row, column=1, sticky="ew", padx=5)

    def _add_entry_setting(self, parent, key, label_text, var_type=tk.StringVar, grid_row=None, **entry_options):
        """Helper to add a label and entry for a setting."""
        self.setting_vars[key] = var_type()
        if grid_row is None:
            grid_row = parent.grid_size()[1]
        ttk.Label(parent, text=label_text).grid(row=grid_row, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(parent, textvariable=self.setting_vars[key], width=20, **entry_options).grid(row=grid_row, column=1, sticky="w", padx=5)

    def _create_task_widgets(self, parent_frame):
        """Creates widgets for the 'Task Management' tab."""
        # Frame for the listbox and scrollbar
        list_frame = ttk.Frame(parent_frame)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        task_scrollbar = ttk.Scrollbar(list_frame)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.task_listbox = tk.Listbox(list_frame, yscrollcommand=task_scrollbar.set, height=15, selectmode=tk.SINGLE)
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.config(command=self.task_listbox.yview)
        self.task_listbox.bind('<Double-Button-1>', self._toggle_task_completion_ui) # Double-click to toggle

        # Frame for entry and add button
        add_frame = ttk.Frame(parent_frame)
        add_frame.pack(pady=5, padx=10, fill=tk.X)

        self.new_task_entry = ttk.Entry(add_frame, width=40)
        self.new_task_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.new_task_entry.bind("<Return>", self._add_task_from_ui)

        add_task_button = ttk.Button(add_frame, text="新增任務", command=self._add_task_from_ui)
        add_task_button.pack(side=tk.LEFT)

        # Frame for action buttons (Complete/Delete)
        action_frame = ttk.Frame(parent_frame)
        action_frame.pack(pady=5, padx=10, fill=tk.X)

        complete_button = ttk.Button(action_frame, text="標記完成/未完成", command=self._toggle_task_completion_ui)
        complete_button.pack(side=tk.LEFT, padx=(0, 5))

        delete_button = ttk.Button(action_frame, text="刪除任務", command=self._delete_task_from_ui)
        delete_button.pack(side=tk.LEFT)


    def _load_tasks_to_ui(self):
        """Loads tasks from the database into the listbox."""
        self.task_listbox.delete(0, tk.END) # Clear existing items
        self.tasks_in_list = get_tasks(self.parent_app.user_id, include_completed=True) # Get all tasks

        for task in self.tasks_in_list:
            prefix = "[✓] " if task['completed'] else "[ ] "
            self.task_listbox.insert(tk.END, prefix + task['description'])
            if task['completed']:
                self.task_listbox.itemconfig(tk.END, {'fg': 'grey'}) # Style completed tasks


    def _add_task_from_ui(self, event=None):
        """Adds a task entered in the UI entry field."""
        description = self.new_task_entry.get().strip()
        if description:
            task_id = add_task(self.parent_app.user_id, description)
            if task_id:
                self.new_task_entry.delete(0, tk.END)
                self._load_tasks_to_ui() # Refresh the list
            else:
                messagebox.showerror("錯誤", "無法新增任務，請查看日誌。", parent=self)
        else:
             messagebox.showwarning("提示", "請輸入任務描述。", parent=self)


    def _get_selected_task_index_and_id(self):
        """Gets the index and ID of the selected task in the listbox."""
        selected_indices = self.task_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("提示", "請先選擇一個任務。", parent=self)
            return None, None
        index = selected_indices[0]
        if 0 <= index < len(self.tasks_in_list):
            task_id = self.tasks_in_list[index]['id']
            return index, task_id
        else:
            logging.error(f"Selected index {index} out of bounds for task list.")
            return None, None


    def _toggle_task_completion_ui(self, event=None):
        """Toggles the completion status of the selected task in the UI."""
        index, task_id = self._get_selected_task_index_and_id()
        if task_id is None:
            return

        task = self.tasks_in_list[index]
        new_status = not task['completed'] # Toggle status

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("UPDATE tasks SET completed=? WHERE id=?", (1 if new_status else 0, task_id))
                conn.commit()
                if c.rowcount > 0:
                    logging.info(f"Toggled completion status for task {task_id} to {new_status}.")
                    self._load_tasks_to_ui() # Refresh list
                else:
                     messagebox.showerror("錯誤", "更新任務狀態時出錯。", parent=self)
        except sqlite3.Error as e:
             logging.error(f"Failed to toggle task {task_id} completion: {e}")
             messagebox.showerror("資料庫錯誤", f"無法更新任務狀態：{e}", parent=self)


    def _delete_task_from_ui(self):
        """Deletes the selected task from the UI and database."""
        index, task_id = self._get_selected_task_index_and_id()
        if task_id is None:
            return

        if messagebox.askyesno("確認", f"確定要刪除任務「{self.tasks_in_list[index]['description']}」嗎？", parent=self):
            if delete_task(task_id):
                 self._load_tasks_to_ui() # Refresh list
            else:
                 messagebox.showerror("錯誤", "無法刪除任務，請查看日誌。", parent=self)


# 在 SettingsWindow class 裡面
    def _load_settings_to_ui(self):
        """Loads current settings from the settings_copy into the UI elements."""
        logging.debug("Loading settings into Settings UI.")
        for key, var in self.setting_vars.items():
            # Use the initial copy loaded from the main app
            # Get value from settings copy, fallback to default, ensure it's string for consistent processing initially
            value_str = str(self.settings_copy.get(key, DEFAULT_SETTINGS.get(key)))
            if value_str is None: # Should not happen with default fallback, but safety check
                 logging.warning(f"Setting key {key} could not be determined during UI load.")
                 continue # Skip this setting if value is None

            try:
                # ---> 修改 proactive_freq 的載入處理 <---
                if key == SETTING_PROACTIVE_FREQ:
                    # Ensure self.freq_options exists (should be set in _create_general_settings_widgets)
                    if not hasattr(self, 'freq_options'):
                         logging.error("freq_options not initialized before loading settings.")
                         continue # Skip if options list is missing

                    index_val = int(value_str) # Convert loaded value (string from DB or default int) to index
                    if 0 <= index_val < len(self.freq_options):
                        # Set the Combobox selection based on the index
                        self.freq_combobox.current(index_val)
                        # Optionally, update the associated IntVar if it's used elsewhere
                        # var.set(index_val)
                        logging.debug(f"Loaded proactive_freq index {index_val}, set Combobox to '{self.freq_options[index_val]}'")
                    else:
                        # Handle invalid index found in settings
                        logging.warning(f"Invalid index {index_val} loaded for proactive_freq. Defaulting to index 1.")
                        self.freq_combobox.current(1) # Default to "普通" display
                        # var.set(1) # Set IntVar to default index
                # ---> 修改結束 <---

                # Handle other variable types
                elif isinstance(var, tk.IntVar):
                    # Convert to float first then int for robustness (e.g., handles "1.0")
                    var.set(int(float(value_str)))
                elif isinstance(var, tk.DoubleVar):
                    var.set(float(value_str))
                elif isinstance(var, tk.StringVar):
                     var.set(value_str) # It's already a string
                else:
                    # Fallback for any unhandled variable types
                    logging.warning(f"Unhandled variable type for key {key}: {type(var)}. Setting as string.")
                    var.set(value_str) # Try setting directly as string

            except (ValueError, TypeError, tk.TclError, AttributeError) as e: # Added AttributeError for safety
                logging.error(f"Error setting UI for key '{key}' with loaded value '{value_str}': {e}. Using default.", exc_info=True)
                # Attempt to set default value if loading failed
                default_val = DEFAULT_SETTINGS.get(key)
                try:
                    if default_val is not None:
                        # Handle setting default value based on type
                         if key == SETTING_PROACTIVE_FREQ:
                             # Ensure self.freq_options exists before setting default
                             if hasattr(self, 'freq_options') and 0 <= int(default_val) < len(self.freq_options):
                                 self.freq_combobox.current(int(default_val))
                             else:
                                 self.freq_combobox.current(1) # Ultimate fallback default
                             # if isinstance(var, tk.IntVar): var.set(int(default_val)) # Update IntVar if needed

                         elif isinstance(var, tk.IntVar): var.set(int(float(default_val)))
                         elif isinstance(var, tk.DoubleVar): var.set(float(default_val))
                         elif isinstance(var, tk.StringVar): var.set(str(default_val))
                         else: var.set(str(default_val)) # Fallback default

                except Exception as e_def:
                    # Log error if setting the default value also fails
                    logging.error(f"Failed to set default value for key '{key}' after initial load error: {e_def}", exc_info=True)

# 在 SettingsWindow class 裡面
    def _save_settings(self):
        """Saves settings from UI to the parent app's settings and persists them."""
        logging.info("Attempting to save settings from Settings UI.")
        temp_settings = {} # Store validated settings before applying

        # --- Process General Settings (excluding proactive_freq) ---
        for key, var in self.setting_vars.items():
            # ---> 跳過 proactive_freq，將在迴圈後單獨處理 <---
            if key == SETTING_PROACTIVE_FREQ:
                continue
            # ---> --- <---

            actual_value = None # Initialize variable to store raw value
            try:
                actual_value = var.get() # Get the raw value from the UI variable

                # Log the raw value retrieved
                logging.debug(f"Processing setting: Key='{key}', Raw Value Retrieved='{actual_value}', Type={type(actual_value)}")

                value = actual_value # Use the retrieved value for the following logic

                # --- Type Validation/Conversion based on key ---
                # proactive_freq is handled separately after this loop
                if key in [SETTING_RESPONSE_DELAY_ENABLED,
                           SETTING_RESPONSE_DELAY_MAX, SETTING_LLM_MAX_TOKENS,
                           SETTING_STM_RETENTION_DAYS, SETTING_BEDTIME_HOUR, SETTING_BEDTIME_MINUTE,
                           SETTING_WAKEUP_HOUR, SETTING_WAKEUP_MINUTE, SETTING_NON_RESPONSE_TIMEOUT]:
                    temp_settings[key] = int(value) # Convert to integer

                elif key in [SETTING_OPTIMISM_TRAIT, SETTING_ANXIETY_TRAIT,
                             SETTING_EMO_SENSITIVITY, SETTING_MOOD_STABILITY,
                             SETTING_DECAY_RATE, SETTING_TIME_SHIFT_STRENGTH,
                             SETTING_FORGET_CHANCE, SETTING_RECALL_CHANCE,
                             SETTING_LLM_TEMP]:
                    temp_settings[key] = float(value) # Convert to float

                elif key in [SETTING_LOCATION]: # String settings
                     temp_settings[key] = str(value) # Ensure it's a string

                else:
                    # Log if a key wasn't explicitly handled (should not happen if all keys are covered)
                    logging.warning(f"Unhandled setting key '{key}' found during save loop. Storing as string.")
                    temp_settings[key] = str(value) # Default to storing as string

                # Log successful processing of the setting within the loop
                logging.debug(f"Successfully processed setting in loop: Key='{key}', Validated Value={temp_settings[key]} (Type: {type(temp_settings[key])})")

            except (ValueError, TypeError, tk.TclError) as e:
                # Log detailed error if validation/conversion fails
                logging.error(f"ERROR during setting validation for Key='{key}'. Operation Failed. Raw Value Retrieved='{actual_value}' (Type: {type(actual_value)}). Error: {e}", exc_info=True)
                # Show error message to the user
                messagebox.showerror("輸入錯誤", f"設定 '{key}' 的值 '{actual_value}' 無效。\n錯誤訊息: {e}\n請修正後再試。", parent=self)
                return # Stop the saving process immediately on error

        # --- Process proactive_freq separately AFTER the loop ---
        try:
            # Ensure freq_options and freq_combobox exist
            if not hasattr(self, 'freq_options') or not hasattr(self, 'freq_combobox'):
                 logging.error("Cannot save proactive_freq: freq_options or freq_combobox not initialized.")
                 messagebox.showerror("程式錯誤", "無法儲存主動聊天頻率設定 (元件未初始化)。", parent=self)
                 return # Stop saving

            selected_freq_string = self.freq_combobox.get() # Get the selected DISPLAY STRING from Combobox
            if selected_freq_string in self.freq_options:
                # Find the index corresponding to the selected string
                selected_index = self.freq_options.index(selected_freq_string)
                # Save the integer index
                temp_settings[SETTING_PROACTIVE_FREQ] = selected_index
                logging.debug(f"Saving proactive_freq: Selected String='{selected_freq_string}', Determined Index={selected_index}")
            else:
                # Handle unexpected case where Combobox string is not in options
                logging.warning(f"Invalid selection '{selected_freq_string}' found in freq_combobox during save. Saving default index 1.")
                temp_settings[SETTING_PROACTIVE_FREQ] = 1 # Default to index 1 ("普通")

        except Exception as e:
             # Catch any other errors during proactive_freq processing
             logging.error(f"Unexpected error processing proactive_freq saving: {e}", exc_info=True)
             messagebox.showerror("輸入錯誤", f"儲存 主動聊天頻率 時發生未知錯誤：{e}", parent=self)
             return # Stop saving if this crucial setting fails

        # Final check to ensure proactive_freq was added to settings to be saved
        if SETTING_PROACTIVE_FREQ not in temp_settings:
             logging.error("Critical error: SETTING_PROACTIVE_FREQ was not added to temp_settings before proceeding.")
             messagebox.showerror("程式錯誤", "無法處理主動聊天頻率設定值。", parent=self)
             return # Stop saving


        # --- Validate Bedtime/Wakeup Logic (Ensure times are not identical) ---
        try:
            # Retrieve potentially updated values from temp_settings
            bh = temp_settings[SETTING_BEDTIME_HOUR]
            bm = temp_settings[SETTING_BEDTIME_MINUTE]
            wh = temp_settings[SETTING_WAKEUP_HOUR]
            wm = temp_settings[SETTING_WAKEUP_MINUTE]
            # Check if bedtime and wakeup time are exactly the same
            if bh == wh and bm == wm:
                 messagebox.showwarning("提示", "就寢時間和起床時間不能設定為完全相同。", parent=self)
                 # Depending on desired behavior, you might 'return' here to prevent saving
                 # return
        except KeyError as e:
            # Handle cases where time settings might be missing (shouldn't happen if handled above)
            logging.error(f"Missing required setting for bedtime validation: {e}", exc_info=True)
            messagebox.showerror("設定錯誤", f"缺少必要的作息時間設定值: {e}", parent=self)
            return # Stop saving


        # --- Apply validated settings to parent app's dictionary ---
        self.parent_app.settings.update(temp_settings)
        logging.debug("Applied validated settings to parent application state.")

        # --- Persist all settings from temp_settings to the database ---
        save_count = 0
        fail_count = 0
        # Iterate through the validated settings we prepared
        for key, value_to_save in temp_settings.items():
            try:
                # Call the function to save the individual setting to the DB
                # save_setting internally converts the value to string for storage
                save_setting(key, value_to_save)
                save_count += 1
            except Exception as e_save:
                # Log error if saving to database fails for a specific key
                logging.error(f"Failed to save setting '{key}' (value: {value_to_save}) to database: {e_save}", exc_info=True)
                fail_count += 1

        logging.info(f"Database save attempt: Successful Saves={save_count}, Failed Saves={fail_count}")

        # Notify user if any settings failed to save to the database
        if fail_count > 0:
            messagebox.showwarning("儲存錯誤", f"有 {fail_count} 個設定無法成功儲存到資料庫。\n請檢查日誌檔以獲取詳細資訊。", parent=self)
            # Decide whether to proceed or stop if DB save fails partially
            # return # Optional: Stop if any DB save fails

        # --- Notify parent app to apply the changes (e.g., reschedule tasks) ---
        try:
            self.parent_app.apply_settings_changes()
            logging.debug("Notified parent application to apply setting changes.")
        except Exception as e_apply:
             logging.error(f"Error occurred when applying settings changes in parent app: {e_apply}", exc_info=True)
             messagebox.showerror("應用設定錯誤", f"儲存成功，但在應用設定時發生錯誤：{e_apply}", parent=self)
             # Settings are saved, but application might not reflect them immediately

        # --- Close the settings window if all saves were successful (or handled) ---
        # Close only if DB saves were fully successful. Adjust if partial saves are acceptable.
        if fail_count == 0:
            messagebox.showinfo("成功", "設定已成功儲存！", parent=self)
            self.destroy() # Close the settings window


# --- 主程式類別 ---
class PetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("小星桌寵")
        init_db() # Ensure DB and tables exist before loading anything

        # --- Load Settings FIRST ---
        self.settings = self._load_all_settings()
        self.user_id = self.settings.get(SETTING_USER_ID, DEFAULT_SETTINGS[SETTING_USER_ID])
        # Ask for User ID only if it's still the default and the DB setting wasn't loaded properly
        # This check is less critical now as user_id is unlikely to be default if DB exists
        # if self.user_id == "default_user" and load_setting(SETTING_USER_ID, None) is None:
        #      new_user_id = simpledialog.askstring("用戶ID", "請輸入您的用戶ID：", initialvalue="default_user", parent=self.root)
        #      if new_user_id:
        #          self.user_id = new_user_id
        #          self.settings[SETTING_USER_ID] = self.user_id
        #          save_setting(SETTING_USER_ID, self.user_id) # Save the new ID

        # --- Core State Variables ---
        self.emotions = {} # Initialize empty, load later if model is ready
        self.boredom = 0.5 # Temporary default, will sync with emotion dict
        self.energy = 0.8 # Keep energy separate for now
        self.last_hourly_shift_time = float(load_setting('last_hourly_shift_time', 0))
        self.last_user_interaction_time = time.time() # Initialize interaction time
        self.last_proactive_theme = None # Track last proactive theme to avoid repetition
        self.last_proactive_timestamp = 0 # Track time of last proactive message
        self.is_sleeping = False # Track sleep state
        self.just_woke_up = False # Flag for wake-up greeting
        self.short_term_tuples = [] # Initialize memory lists
        self.long_term_tuples = []

        # --- Model Selection Variable ---
        self.model_var = tk.StringVar()
        loaded_model = self.settings.get(SETTING_SELECTED_LLM, DEFAULT_SETTINGS[SETTING_SELECTED_LLM])
        if loaded_model not in AVAILABLE_LLM_MODELS:
             logging.warning(f"Loaded model '{loaded_model}' not in available list. Using default.")
             loaded_model = AVAILABLE_LLM_MODELS[0]
             self.settings[SETTING_SELECTED_LLM] = loaded_model
             save_setting(SETTING_SELECTED_LLM, loaded_model) # Save corrected default
        self.model_var.set(loaded_model)

        # --- Build UI FIRST --- (Essential change for dialog parenting)
        self._build_ui()

        # --- API Key and Model Initialization ---
        self._ensure_api_key() # Tries to get key from DB/env
        self.model = None # Initialize model attribute to None

        if hasattr(self, 'api_key') and self.api_key: # Checks if key was found by _ensure_api_key
            # Key FOUND in DB/env, try to configure Gemini
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(model_name=self.model_var.get()) # Sets self.model
                self.apply_llm_settings()
                logging.info(f"Gemini model '{self.model_var.get()}' configured using existing key.")
            except Exception as e:
                # Configuration failed even with a key
                logging.error(f"Failed to configure Gemini WITH key: {e}")
                messagebox.showerror("API 錯誤", f"使用已有的 API Key 設定 Gemini 模型失敗：{e}\n請檢查 Key 是否有效或網路連線。", parent=self.root)
                # Let self.model remain None, __main__ check will handle exit.
        else:
             # Key NOT FOUND by _ensure_api_key, prompt the user NOW that UI exists
             logging.warning("API Key not available. Prompting user...")
             self.prompt_for_api_key() # This function tries to set self.api_key and self.model

        # --- Post-Init Setup (Only if model initialized successfully) ---
        # Check if model is set *after* trying DB/env and potential prompt
        if self.model:
            # Model initialized successfully, proceed with full setup
            self.emotions = load_emotions(self.user_id)
            self.boredom = self.emotions.get('boredom', 0.5) # Sync boredom
            self.reload_memory_lists()
            self._update_pet_image()
            self._update_status_labels() # Show initial status
            self._initial_greeting_or_wakeup() # Handle initial state
            self._schedule_tasks() # Start background tasks
            self._hourly_time_check(run_immediately=True) # Run initial check
            self._check_non_response() # Start non-response check
            logging.info("PetApp initialized successfully with LLM.")
        else:
             # Model is STILL None (key not found/entered, or config failed)
             logging.warning("LLM Model remains uninitialized after init attempts.")
             # Display a message in the text area, UI is already built
             self._append("[系統] 核心對話模型初始化失敗。\n請透過選單 [檔案] -> [設定 API Key...] 輸入有效的 API Key。", tags=("system",))
             # Ensure UI elements requiring the model are disabled (prompt_for_api_key should handle this)
             self.entry.config(state='disabled')
             if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
             # No background tasks should be scheduled if the model failed.


    def _load_all_settings(self):
        """Loads all settings from DB using load_setting or uses defaults."""
        settings = {}
        # Load all settings defined in DEFAULT_SETTINGS
        for key, default_value in DEFAULT_SETTINGS.items():
            # load_setting returns the raw value (usually string) or default
            raw_value = load_setting(key, default_value)
            # Attempt to convert to the expected type based on default value type
            try:
                if isinstance(default_value, bool): # Handle potential booleans if added later
                    settings[key] = bool(int(raw_value))
                elif isinstance(default_value, int):
                    settings[key] = int(float(raw_value)) # Safest: str -> float -> int
                elif isinstance(default_value, float):
                    settings[key] = float(raw_value)
                else: # Assume string if not numeric or bool
                    settings[key] = str(raw_value)
            except (ValueError, TypeError) as e:
                 logging.warning(f"Could not convert loaded setting '{key}' (value: '{raw_value}') to type {type(default_value)}. Using default. Error: {e}")
                 settings[key] = default_value # Use default if conversion fails

        logging.info(f"Loaded application settings. User ID: {settings.get(SETTING_USER_ID)}")
        return settings


    def apply_llm_settings(self):
         """Applies LLM temperature and max tokens to the generation config used in calls."""
         # These settings are primarily used within call_llm via GenerationConfig
         temp = float(self.settings.get(SETTING_LLM_TEMP, DEFAULT_SETTINGS[SETTING_LLM_TEMP]))
         max_tokens = int(self.settings.get(SETTING_LLM_MAX_TOKENS, DEFAULT_SETTINGS[SETTING_LLM_MAX_TOKENS]))
         logging.info(f"Applying LLM settings: Temp={temp}, MaxTokens={max_tokens}")
         # No direct object update needed here, values are read during call_llm


    def apply_settings_changes(self):
        """Called after settings are saved to apply immediate changes."""
        logging.info("Applying settings changes...")
        self.user_id = self.settings.get(SETTING_USER_ID)
        self.apply_llm_settings()

        # Check if model needs to be re-initialized
        current_model_name = self.model.model_name if self.model else None
        selected_model_name = self.settings.get(SETTING_SELECTED_LLM)
        if self.api_key and selected_model_name and current_model_name != selected_model_name:
             logging.info(f"Model changed in settings from {current_model_name} to {selected_model_name}. Re-initializing.")
             self._on_model_change(selected_model_name) # Use existing function

        # Cancel and Reschedule tasks only if the model is active
        if self.model:
            self._cancel_timers() # Cancel existing timers
            self._schedule_tasks() # Reschedule based on new settings
            self._hourly_time_check(run_immediately=True) # Force immediate check
            self._check_non_response() # Reschedule non-response check

        self._update_status_labels() # Update UI
        self._update_pet_image() # Update image

        logging.info("Settings changes applied and tasks rescheduled (if model active).")


    def _cancel_timers(self):
        """Cancel all scheduled 'after' tasks."""
        logging.debug("Cancelling scheduled timers...")
        timers = ['proactive_timer_id', 'decay_timer_id', 'needs_timer_id',
                  'cleanup_timer_id', 'forgetting_timer_id', 'hourly_timer_id',
                  'response_delay_timer_id', 'non_response_timer_id']
        for timer_attr in timers:
             timer_id = getattr(self, timer_attr, None)
             if timer_id:
                 try:
                     self.root.after_cancel(timer_id)
                 except tk.TclError:
                     logging.debug(f"Timer {timer_attr} (ID: {timer_id}) already cancelled or invalid.")
                 except Exception as e:
                     logging.warning(f"Error cancelling timer {timer_attr}: {e}")
                 finally:
                    setattr(self, timer_attr, None) # Clear the stored ID regardless


    def _schedule_tasks(self):
         """Schedules all recurring background tasks based on current settings."""
         # Ensure model is ready before scheduling tasks that rely on it or state
         if not self.model:
              logging.warning("Skipping task scheduling: Model not initialized.")
              return
         logging.debug("Scheduling background tasks...")
         self._schedule_proactive_task()
         self._schedule_decay_task()
         self._schedule_needs_update_task()
         self._schedule_cleanup_task()
         self._schedule_forgetting_task()
         self._schedule_hourly_check_task()
         # Non-response check is scheduled separately


    def _schedule_proactive_task(self):
         if hasattr(self, 'proactive_timer_id') and self.proactive_timer_id: return # Already scheduled
         freq_index = int(self.settings.get(SETTING_PROACTIVE_FREQ, 1))
         intervals = [(5*60, 15*60), (10*60, 25*60), (20*60, 40*60), (-1, -1)] # (min, max) in seconds
         if 0 <= freq_index < len(intervals):
             min_delay, max_delay = intervals[freq_index]
         else:
             min_delay, max_delay = intervals[1]

         if min_delay > 0:
              now = time.time()
              min_time_since_last = 3 * 60
              time_since_last = now - self.last_proactive_timestamp
              base_delay_s = random.randint(min_delay, max_delay)
              actual_delay_s = max(min_time_since_last - time_since_last, 0) + base_delay_s

              next_proactive_ms = int(actual_delay_s * 1000)
              self.proactive_timer_id = self.root.after(next_proactive_ms, self._proactive)
              logging.info(f"Scheduled proactive task in {next_proactive_ms/1000:.0f}s")
         else:
              logging.info("Proactive task disabled by settings.")
              self.proactive_timer_id = None


    def _schedule_decay_task(self):
        if hasattr(self, 'decay_timer_id') and self.decay_timer_id: return
        decay_interval_ms = 15 * 60 * 1000 # 15 minutes
        self.decay_timer_id = self.root.after(decay_interval_ms, self._decay_emotions)

    def _schedule_needs_update_task(self):
        if hasattr(self, 'needs_timer_id') and self.needs_timer_id: return
        needs_interval_ms = 5 * 60 * 1000 # 5 minutes
        self.needs_timer_id = self.root.after(needs_interval_ms, self._update_needs)

    def _schedule_cleanup_task(self):
        if hasattr(self, 'cleanup_timer_id') and self.cleanup_timer_id: return
        cleanup_interval_ms = 24 * 60 * 60 * 1000 # 24 hours
        self.cleanup_timer_id = self.root.after(cleanup_interval_ms, self._cleanup)

    def _schedule_forgetting_task(self):
        if hasattr(self, 'forgetting_timer_id') and self.forgetting_timer_id: return
        forgetting_interval_ms = 6 * 60 * 60 * 1000 # 6 hours
        self.forgetting_timer_id = self.root.after(forgetting_interval_ms, self._process_memory_forgetting)

    def _schedule_hourly_check_task(self):
        if hasattr(self, 'hourly_timer_id') and self.hourly_timer_id: return
        # Schedule to run near the start of the next 15-min interval
        now = datetime.now()
        minutes_past_hour = now.minute
        minutes_to_next_quarter = 15 - (minutes_past_hour % 15)
        next_quarter = now.replace(second=5, microsecond=0) + timedelta(minutes=minutes_to_next_quarter) # 5s past quarter hour
        delay_ms = int((next_quarter - now).total_seconds() * 1000)
        if delay_ms < 5000: delay_ms += 15 * 60 * 1000 # Ensure minimum 5 sec delay, aim for next quarter

        self.hourly_timer_id = self.root.after(delay_ms, self._hourly_time_check)
        logging.debug(f"Scheduled next hourly/sleep check in {delay_ms / 1000 / 60:.1f} minutes.")


    def _ensure_api_key(self):
        """Tries to load API key from DB or environment, sets self.api_key."""
        self.api_key = get_api_key('gemini')
        if not self.api_key:
            self.api_key = os.environ.get('GEMINI_API_KEY')
            if self.api_key:
                 logging.info("Loaded API Key from environment variable.")
                 # Optionally save it to the database for persistence
                 set_api_key('gemini', self.api_key)
            # else: self.api_key remains None


    def prompt_for_api_key(self):
        """Prompts the user for the API key and attempts to initialize the model."""
        key = simpledialog.askstring("API Key Required",
                                     "找不到 Gemini API Key。\n請輸入您的 Google AI Gemini API Key：",
                                     parent=self.root) # Use self.root as parent
        if key:
            if set_api_key('gemini', key):
                self.api_key = key
                logging.info("New API Key saved.")
                # Try to initialize model immediately
                try:
                    genai.configure(api_key=self.api_key)
                    selected_model = self.model_var.get()
                    if selected_model not in AVAILABLE_LLM_MODELS:
                        selected_model = AVAILABLE_LLM_MODELS[0]
                        self.model_var.set(selected_model)
                        # Also update settings dict and save if corrected
                        self.settings[SETTING_SELECTED_LLM] = selected_model
                        save_setting(SETTING_SELECTED_LLM, selected_model)

                    self.model = genai.GenerativeModel(model_name=selected_model)
                    self.apply_llm_settings()
                    logging.info(f"Gemini model '{selected_model}' configured after key entry.")
                    self._append("[系統] API Key 已設定，模型已載入！", tags=("system",))
                    # ---> Re-enable UI on success <---
                    self.entry.config(state='normal')
                    if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='normal')
                    # Perform post-init steps ONLY if they haven't run yet
                    if not self.emotions: # Check if emotions dict is still empty
                        logging.info("Performing post-model-init setup...")
                        self.emotions = load_emotions(self.user_id)
                        self.boredom = self.emotions.get('boredom', 0.5)
                        self.reload_memory_lists()
                        self._update_pet_image()
                        self._update_status_labels()
                        self._initial_greeting_or_wakeup()
                        self._schedule_tasks() # Start background tasks now
                        self._hourly_time_check(run_immediately=True)
                        self._check_non_response()

                except Exception as e:
                    logging.error(f"Failed to configure Gemini after key entry: {e}")
                    messagebox.showerror("API 錯誤", f"設定 Gemini 模型失敗：{e}\n請檢查 Key 是否有效。", parent=self.root)
                    self.api_key = None # Clear invalid key
                    self.model = None # Ensure model is None
                    # ---> Keep UI disabled on failure <---
                    self.entry.config(state='disabled')
                    if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
            else:
                messagebox.showerror("錯誤", "無法儲存 API Key。", parent=self.root)
                self.api_key = None; self.model = None
                self.entry.config(state='disabled')
                if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
        else:
             messagebox.showwarning("警告", "未提供 API Key，將無法使用對話功能。", parent=self.root)
             self.api_key = None; self.model = None
             self.entry.config(state='disabled')
             if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')


    def _build_ui(self):
        # --- Image Display ---
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=10)
        self.pet_label = tk.Label(self.image_frame)
        self.pet_label.pack()

        # --- Model Selection ---
        model_frame = tk.Frame(self.root)
        model_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(model_frame, text="選擇模型：").pack(side=tk.LEFT)
        self.model_option_menu = tk.OptionMenu(model_frame, self.model_var, *AVAILABLE_LLM_MODELS, command=self._on_model_change)
        self.model_option_menu.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.model_option_menu.config(state='normal') # Start enabled

        # --- Dialogue Display ---
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.text_scrollbar = tk.Scrollbar(self.text_frame)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(self.text_frame, height=15, width=50, state='disabled', wrap=tk.WORD, yscrollcommand=self.text_scrollbar.set, font=("Arial", 10))
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_scrollbar.config(command=self.text.yview)
        self.text.tag_configure("user", foreground="blue")
        self.text.tag_configure("pet", foreground="green")
        self.text.tag_configure("system", foreground="grey", font=("Arial", 9, "italic"))
        self.text.tag_configure("proactive", foreground="#800080") # Purple
        self.text.tag_configure("selftalk", foreground="#FFA500", font=("Arial", 10, "italic")) # Orange italic

        # --- Input Box ---
        self.entry = tk.Entry(self.root, width=50, font=("Arial", 10))
        self.entry.pack(pady=5, padx=10, fill=tk.X)
        self.entry.bind("<Return>", self.process_input)
        self.entry.config(state='normal') # Start enabled

        # --- Status Labels ---
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(pady=2, fill=tk.X, padx=10)
        self.boredom_label = tk.Label(self.status_frame, text="無聊度: -", width=15, anchor='w')
        self.boredom_label.pack(side=tk.LEFT)
        self.energy_label = tk.Label(self.status_frame, text="精力: -", width=15, anchor='e')
        self.energy_label.pack(side=tk.RIGHT)
        self.sleep_status_label = tk.Label(self.status_frame, text="", width=10, anchor='center')
        self.sleep_status_label.pack(side=tk.LEFT, expand=True, fill=tk.X) # Allow to fill space

        # --- Menu ---
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="開啟設定...", command=self.open_settings_window)
        file_menu.add_command(label="設定 API Key...", command=self.prompt_for_api_key) # Use revised prompt
        file_menu.add_command(label="清除 API Key...", command=self._clear_api_key_action)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        status_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="狀態", menu=status_menu)
        status_menu.add_command(label="查看狀態", command=self._show_emotions)
        status_menu.add_command(label="查看記憶", command=self._show_memories)
        status_menu.add_command(label="查看任務", command=self._show_tasks_popup)


    def open_settings_window(self):
         """Opens the settings window."""
         SettingsWindow(self.root, self) # Pass self (PetApp instance)

    def _map_emotion_to_visual(self, emotion_name):
        EMOTION_VISUAL_MAP = {
            "happy": ["joy", "amusement", "adoration", "satisfaction", "gratitude", "hope", "optimism", "contentment"],
            "sad": ["sadness", "disappointment", "remorse", "guilt", "shame", "empathetic_pain", "pessimism"],
            "angry": ["anger", "frustration", "disgust", "hatred", "jealousy"],
            "excited": ["excitement", "interest", "surprise", "anticipation", "awe", "triumph"],
            "anxious": ["anxiety", "fear", "horror", "awkwardness", "confusion"],
            "neutral": ["neutral", "calmness", "nostalgia", "sympathy", "trust"],
        }
        for visual, group in EMOTION_VISUAL_MAP.items():
            if emotion_name in group:
                return visual
        return "neutral"
    def _get_dominant_emotion(self):
        """Determines the dominant emotion and visual state (one of 6 fixed types)."""
        if not self.emotions:
            return "neutral", 0.5, "neutral"

        current_energy = self.energy
        current_boredom = self.emotions.get('boredom', 0.5)

        if self.is_sleeping:
            return "sleepy", 1.0, "neutral"  # Use neutral visual for sleep

        # 優先狀態（疲勞、極度無聊）
        if current_energy < 0.15:
            return "sleepy", 1.0 - current_energy, "neutral"
        if current_boredom > 0.9:
            return "bored", current_boredom, "neutral"

        # 顯著單一情緒優先判斷
        priority_thresholds = {
            "anger": 0.75,
            "sadness": 0.75,
            "joy": 0.8,
            "excitement": 0.8,
            "anxiety": 0.7,
        }
        for emo, threshold in priority_thresholds.items():
            value = self.emotions.get(emo, 0)
            if value > threshold:
                visual_mood = self._map_emotion_to_visual(emo)
                return emo, value, visual_mood

        # 尋找最強情緒
        filtered = {k: v for k, v in self.emotions.items() if v > 0.3 and k != "boredom"}
        if not filtered:
            dominant_name = "neutral"
            strength = 0.5
        else:
            dominant_name = max(filtered, key=filtered.get)
            strength = filtered[dominant_name]

        visual_mood = self._map_emotion_to_visual(dominant_name)

        # 可選：考慮與上一次情緒的差異
        if hasattr(self, '_last_emotion'):
            delta = abs(strength - getattr(self, '_last_strength', 0))
            if self._last_emotion != dominant_name and delta > 0.4:
                dominant_name = "anxiety"
                strength = 1.0
                visual_mood = "anxious"

        self._last_emotion = dominant_name
        self._last_strength = strength

        return dominant_name, strength, visual_mood


    def _update_pet_image(self):
        """Updates the pet's image based on the dominant visual mood."""
        _, _, visual_mood = self._get_dominant_emotion()
        img_path = EMOTION_IMAGES.get(visual_mood, DEFAULT_IMG_PATH)

        if not os.path.exists(img_path):
            logging.warning(f"Image path not found for mood '{visual_mood}': {img_path}. Using default.")
            img_path = DEFAULT_IMG_PATH

        current_path = getattr(self, 'current_image_path', None)
        if current_path == img_path: return # No change needed

        try:
            img = Image.open(img_path).resize((150, 150), Image.Resampling.LANCZOS)
            self.pet_photo = ImageTk.PhotoImage(img)
            self.pet_label.config(image=self.pet_photo)
            self.current_image_path = img_path
            logging.debug(f"Updated pet image to: {os.path.basename(img_path)} (Visual Mood: {visual_mood})")
        except Exception as e:
            logging.error(f"Error updating pet image to {img_path}: {e}")
            self.pet_label.config(image=None, text="[圖片錯誤]", width=20, height=10)
            self.current_image_path = None


    def _initial_greeting_or_wakeup(self):
        """Handles the first message when the app starts or wakes up."""
        # Check if model is ready before attempting greeting
        if not self.model:
            logging.warning("Skipping initial greeting: Model not ready.")
            return

        if self.just_woke_up:
            self._append("小星: 早安啊！ 感覺睡得不錯～", tags=("pet", "proactive"))
            self.just_woke_up = False
            self.is_sleeping = False # Ensure awake state
            self._update_status_labels()
            self.last_proactive_timestamp = time.time()
        elif not self.is_sleeping:
             dom, strength, _ = self._get_dominant_emotion()
             greeting = f"哈囉！我是小星。"
             if strength >= 0.7 and dom in POSITIVE_EMOTIONS: greeting += f" 我現在超 {dom} 的欸！"
             elif strength >= 0.6 and dom in NEGATIVE_EMOTIONS: greeting += f" 嗯...有點{dom}..."
             elif self.energy < 0.4: greeting += f" 有點想睡了..."
             elif self.emotions.get('boredom', 0) > 0.7: greeting += f" 好無聊喔，陪我玩啦！"
             else: greeting += f" 你來啦，今天怎麼樣？" # Changed default greeting
             self._append(f"小星: {greeting}", tags=("pet",))
             self.last_proactive_timestamp = time.time()


    def _on_model_change(self, selected_model):
        """Handles model selection from the OptionMenu."""
        if not self.api_key:
            messagebox.showerror("錯誤", "API Key 未設定，無法切換模型。", parent=self.root)
            if self.model: self.model_var.set(self.model.model_name)
            else: self.model_var.set(AVAILABLE_LLM_MODELS[0])
            return

        if selected_model not in AVAILABLE_LLM_MODELS:
             messagebox.showerror("錯誤", f"無效的模型選擇: {selected_model}", parent=self.root)
             if self.model: self.model_var.set(self.model.model_name)
             return

        try:
            self.model = genai.GenerativeModel(model_name=selected_model)
            self.apply_llm_settings()
            self.settings[SETTING_SELECTED_LLM] = selected_model
            save_setting(SETTING_SELECTED_LLM, selected_model)
            self._append(f"[系統] 已切換模型：{selected_model}", tags=("system",))
            logging.info(f"Switched model to: {selected_model}")
        except Exception as e:
            logging.error(f"Model switch failed: {e}")
            messagebox.showerror("錯誤", f"模型切換失敗：{e}\n可能是 API Key 無效或模型名稱錯誤。", parent=self.root)
            if hasattr(self, 'model') and self.model: self.model_var.set(self.model.model_name)
            else: self.model_var.set(AVAILABLE_LLM_MODELS[0]); self.model = None


    def _clear_api_key_action(self):
        """Clears the stored API key."""
        if messagebox.askyesno("確認", "確定要清除已儲存的 API Key 嗎？清除後需要重新設定才能使用。", parent=self.root):
            if clear_api_key('gemini'):
                messagebox.showinfo("成功", "API Key 已清除。請透過選單重新設定。", parent=self.root)
                self.api_key = None
                self.model = None # Model is no longer valid
                self.entry.config(state='disabled')
                if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
                self._append("[系統] API Key 已清除，請重新設定才能對話。", tags=("system",))
                # Cancel background tasks as model is gone
                self._cancel_timers()
            else: messagebox.showerror("錯誤", "清除 API Key 時發生錯誤。", parent=self.root)


    def _show_emotions(self):
        """Displays current emotions and traits in a popup."""
        if not self.emotions: # Check if emotions are loaded
             messagebox.showinfo("狀態", "情緒資料尚未載入 (可能模型未初始化)。", parent=self.root)
             return

        status_window = tk.Toplevel(self.root)
        status_window.title("小星的狀態")
        status_window.geometry("350x500")
        txt_area = scrolledtext.ScrolledText(status_window, wrap=tk.WORD, width=40, height=30)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        status_text = "--- 狀態 & 個性 ---\n"
        status_text += f"精力 (Energy): {self.energy:.2f}\n"
        status_text += f"樂觀傾向: {float(self.settings.get(SETTING_OPTIMISM_TRAIT, '?')):.2f}\n"
        status_text += f"焦慮傾向: {float(self.settings.get(SETTING_ANXIETY_TRAIT, '?')):.2f}\n"
        status_text += f"睡眠狀態: {'睡覺中' if self.is_sleeping else '醒著'}\n\n"
        status_text += "--- 主要情緒 (0.0 - 1.0) ---\n"
        sorted_emotions = sorted(self.emotions.items(), key=lambda item: item[1], reverse=True)
        shown_count = 0
        for name, value in sorted_emotions:
             if value > 0.01 or shown_count < 15: # Show if value > 0.01 OR it's in the top 15
                status_text += f"{name}: {value:.3f}\n"
                shown_count += 1
        if shown_count == 0: status_text += "(無明顯情緒)\n"

        txt_area.insert(tk.INSERT, status_text)
        txt_area.config(state='disabled')
        close_button = ttk.Button(status_window, text="關閉", command=status_window.destroy)
        close_button.pack(pady=5)
        status_window.transient(self.root); status_window.grab_set(); self.root.wait_window(status_window)


    def _show_memories(self):
        """Displays recent memories in a popup."""
        st = [content for _, content in self.short_term_tuples[-5:]] or ["無短期記憶"]
        lt = [content for _, content in self.long_term_tuples[-3:]] or ["無長期記憶"]
        msg = "短期記憶 (最新 5 筆):\n" + "\n".join(reversed(st)) + "\n\n長期記憶 (最新 3 筆):\n" + "\n".join(reversed(lt))
        mem_window = tk.Toplevel(self.root)
        mem_window.title("小星的記憶")
        mem_window.geometry("400x300")
        txt_area = scrolledtext.ScrolledText(mem_window, wrap=tk.WORD, width=45, height=15)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        txt_area.insert(tk.INSERT, msg)
        txt_area.config(state='disabled')
        close_button = ttk.Button(mem_window, text="關閉", command=mem_window.destroy)
        close_button.pack(pady=5)
        mem_window.transient(self.root); mem_window.grab_set(); self.root.wait_window(mem_window)


    def _show_tasks_popup(self):
        """Displays current tasks in a separate popup window."""
        task_window = tk.Toplevel(self.root)
        task_window.title("小星的任務清單")
        task_window.geometry("400x350")
        list_frame = ttk.Frame(task_window); list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        task_scrollbar = ttk.Scrollbar(list_frame); task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        task_listbox = tk.Listbox(list_frame, yscrollcommand=task_scrollbar.set, height=15)
        task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); task_scrollbar.config(command=task_listbox.yview)
        tasks = get_tasks(self.user_id, include_completed=True)
        if tasks:
            for task in tasks:
                prefix = "[✓] " if task['completed'] else "[ ] "
                task_listbox.insert(tk.END, prefix + task['description'])
                if task['completed']: task_listbox.itemconfig(tk.END, {'fg': 'grey'})
        else:
            task_listbox.insert(tk.END, "(目前沒有任務)"); task_listbox.config(state='disabled')
        close_button = ttk.Button(task_window, text="關閉", command=task_window.destroy); close_button.pack(pady=5)
        task_window.transient(self.root); task_window.grab_set(); self.root.wait_window(task_window)


    def call_llm(self, prompt, include_context=True, purpose="generic"):
        """Calls the LLM with appropriate context and error handling."""
        if not self.model:
            logging.warning(f"LLM call ignored (Purpose: {purpose}): Model not initialized.")
            if purpose == "emotion_update": return None
            elif purpose == "self_talk": return "..."
            else: return "嗯...我現在好像沒辦法思考... (模型未載入)"

        full_prompt = prompt
        if include_context:
            dom, strength, _ = self._get_dominant_emotion()
            mood_str = f"我現在的主要感覺是 {dom} (強度 {strength:.2f})。" if strength > 0.3 else "我現在心情還算平穩。"
            if self.is_sleeping: mood_str = "我正在睡覺。"
            elif self.energy < 0.3: mood_str += " 感覺有點累..."

            recent_chats_tuples = self.short_term_tuples[-4:]
            recent_chats_content = []
            token_count = 0
            max_context_tokens = 200
            for _, mem in reversed(recent_chats_tuples):
                 mem_tokens = len(mem.split())
                 if token_count + mem_tokens < max_context_tokens:
                     speaker = "你" if mem.startswith("User:") else "小星"
                     content = mem[mem.find(":")+1:].strip()
                     recent_chats_content.append(f"{speaker}: {content}")
                     token_count += mem_tokens
                 else: break
            recent_chats_content.reverse()
            memory_str = "最近聊到：\n" + "\n".join(recent_chats_content) if recent_chats_content else "(對話剛開始)"

            task_summary = self._get_task_summary()
            context_header = f"{CHARACTER_PROFILE}\n\n[目前狀態]\n{mood_str}\n{task_summary}\n\n[最近對話紀錄]\n{memory_str}\n------\n"
            full_prompt = context_header + prompt

        try:
            config = genai.types.GenerationConfig(
                temperature=float(self.settings.get(SETTING_LLM_TEMP, DEFAULT_SETTINGS[SETTING_LLM_TEMP])),
                top_p=0.95,
                max_output_tokens=int(self.settings.get(SETTING_LLM_MAX_TOKENS, DEFAULT_SETTINGS[SETTING_LLM_MAX_TOKENS]))
            )
            logging.debug(f"--- LLM Call (Purpose: {purpose}, Context: {include_context}) ---\nPrompt Length: {len(full_prompt)} chars\nPrompt Preview: {full_prompt[:200]}...\nConfig: {config}\n--------------------------")

            response = self.model.generate_content(full_prompt, generation_config=config)

            if response.candidates and hasattr(response.candidates[0].content, 'parts'):
                 response_text = "".join(part.text for part in response.candidates[0].content.parts).strip()
                 if response_text:
                      logging.debug(f"LLM Response Text: {response_text}")
                      return response_text
                 else:
                      finish_reason = response.candidates[0].finish_reason.name
                      logging.warning(f"LLM response text empty. Finish Reason: {finish_reason}")
                      if finish_reason == 'SAFETY': return "欸...這個話題我好像不太能說耶。（安全設定）"
                      elif finish_reason == 'RECITATION': return "嗯...我好像不小心重複到一些受保護的內容了。"
                      elif finish_reason == 'MAX_TOKENS': return "我話好像說到一半...被打斷了欸。"
                      else: return "嗯？我好像不知道該說什麼了..."
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason.name
                 logging.warning(f"LLM prompt blocked. Reason: {block_reason}")
                 return f"欸...這個話題我好像不太能提耶。（原因：{block_reason}）"
            else:
                 logging.error(f"LLM generation failed with unexpected response structure: {response}")
                 return "糟糕，我好像斷線了..."

        except Exception as e:
            logging.error(f"LLM call failed: {e}", exc_info=True)
            err_str = str(e).lower()
            if "api key not valid" in err_str or "permission_denied" in err_str:
                self.api_key = None; self.model = None
                self.prompt_for_api_key()
                return "我的能量來源（API Key）好像出問題了...請檢查一下？"
            elif "resource has been exhausted" in err_str: return "今天好像說太多話了，我的能量用完了，明天再聊吧！"
            elif "model service is overloaded" in err_str or "503" in err_str: return "嗚哇，現在好像太多人在找我了，請稍後再試！"
            elif "deadline_exceeded" in err_str or "timeout" in err_str: return "嗯...網路好像有點慢，我的回應飛走了..."
            elif "content has been blocked" in err_str or "safety" in err_str: return "欸...這個話題我好像不太能說耶。（安全設定）"
            else: return "哎呀，我的腦袋好像打結了，等一下再試試？"


    def _get_task_summary(self):
        """Generates a short text summary of pending tasks for context."""
        # Check if model is active, otherwise no point generating summary
        if not self.model: return ""
        try:
            tasks = get_tasks(self.user_id, include_completed=False)
            if not tasks:
                return "目前沒有待辦任務。"
            elif len(tasks) == 1:
                 return f"你有 1 件待辦任務：\n- {tasks[0]['description'][:50]}{'...' if len(tasks[0]['description']) > 50 else ''}"
            else:
                summary = f"你有 {len(tasks)} 件待辦任務："
                for i, task in enumerate(tasks[:2]): # List first 2 only
                     summary += f"\n- {task['description'][:50]}{'...' if len(task['description']) > 50 else ''}"
                if len(tasks) > 2:
                     summary += "\n- ..."
                return summary
        except Exception as e:
             logging.error(f"Error generating task summary: {e}")
             return "(無法讀取任務)"


    # !!--- MODIFIED FUNCTION ---!! (Emotion Update - moved to top section)
    def update_emotions_from_interaction(self, user_input, bot_response):
        """
        Analyzes the interaction and updates emotions based on LLM response.
        (See implementation in the first half / earlier in the class definition)
        """
        if not self.model: return # Cannot update emotions without LLM

        # Get recent conversation history (more concise)
        recent_chats_content = [f"{'你' if mem.startswith('User:') else '小星'}: {mem[mem.find(':')+1:].strip()}"
                                for _, mem in self.short_term_tuples[-4:-1]] # Last 3 interactions (before current one)
        conversation_history = "\n".join(recent_chats_content)
        if conversation_history:
            conversation_history = "之前的對話紀錄：\n" + conversation_history + "\n"
        else:
            conversation_history = "這是我們對話的開始。\n"

        emotion_list_str = ", ".join(EMOTIONS.keys())
        current_emotions_str = str({k: round(v, 2) for k, v in self.emotions.items() if abs(v - 0.5) > 0.1})

        prompt = f"""
你的個性是：{CHARACTER_PROFILE}
你目前較明顯的情緒狀態（0-1分）：{current_emotions_str}

{conversation_history}
最新的對話互動：
使用者: "{user_input}"
你 (小星): "{bot_response}"

根據**最新的對話互動**以及你**當前的情緒**，分析你（小星）的情緒因此次互動產生了哪些變化，平均要影響6種情緒。
只需專注於因這次對話**直接引起**的情緒變化，並評估變化後的新分數（0.0 到 1.0 之間）。
如果某情緒沒有變化，則無需包含在輸出中。
可用的情緒列表：{emotion_list_str}

請嚴格使用以下 JSON 格式回覆，只包含有變化的情緒和它們的新分數：
{{
  "emotion_name1": new_value1,
  "emotion_name2": new_value2,
  ...
}}
確保你的回覆**只有**這個 JSON 物件，不要包含任何標記、註解或解釋。

你的 JSON 輸出："""

        logging.debug(f"--- Emotion Update Prompt ---\n{prompt}\n--------------------------")
        response_text = self.call_llm(prompt, include_context=False, purpose="emotion_update")

        if not response_text:
            logging.warning("LLM call for emotion update returned no response.")
            return

        json_str = None
        try:
            try: # Try direct parse
                 updates = json.loads(response_text)
                 if isinstance(updates, dict): json_str = response_text
            except json.JSONDecodeError: # Try markdown regex
                 json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
                 if json_match: json_str = json_match.group(1)
                 else: # Try fallback { } find
                     json_start = response_text.find('{'); json_end = response_text.rfind('}') + 1
                     if json_start != -1 and json_end > json_start: json_str = response_text[json_start:json_end]
                     else: logging.warning(f"Could not find valid JSON object in emotion update response: {response_text}"); return

            if json_str:
                updates = json.loads(json_str)
                if isinstance(updates, dict):
                    updated_count = 0
                    stability = float(self.settings.get(SETTING_MOOD_STABILITY, DEFAULT_SETTINGS[SETTING_MOOD_STABILITY]))
                    sensitivity = float(self.settings.get(SETTING_EMO_SENSITIVITY, DEFAULT_SETTINGS[SETTING_EMO_SENSITIVITY]))
                    for name, target_value_str in updates.items():
                        if name in self.emotions:
                            try:
                                current_value = self.emotions[name]
                                target_value = max(0.0, min(1.0, float(target_value_str)))
                                raw_change = target_value - current_value
                                sensitive_change = raw_change * sensitivity
                                stable_change = sensitive_change * (1.0 - stability)
                                new_value = max(0.0, min(1.0, current_value + stable_change))
                                if abs(new_value - current_value) > 0.005:
                                    self.emotions[name] = new_value
                                    save_emotion(self.user_id, name, new_value)
                                    updated_count += 1
                                    logging.debug(f"Updated emotion '{name}' from {current_value:.3f} to {new_value:.3f}")
                            except ValueError: logging.warning(f"Invalid value format for emotion '{name}': {target_value_str}")
                            except Exception as e_inner: logging.error(f"Error applying update for emotion '{name}': {e_inner}")
                        else: logging.warning(f"LLM returned unknown emotion '{name}' in update.")
                    if updated_count > 0:
                        logging.info(f"Applied {updated_count} emotion updates from interaction.")
                        # Sync boredom value after update
                        self.boredom = self.emotions.get('boredom', 0.5)
                        self._update_pet_image(); self._update_status_labels()
                else: logging.warning(f"Emotion update response JSON was not a dictionary object: {updates}")
        except json.JSONDecodeError as e: logging.error(f"Failed to decode JSON for emotion update: {e}\nAttempted JSON: '{json_str}'\nResponse: {response_text}")
        except Exception as e: logging.error(f"Error processing emotion updates: {e}\nResponse: {response_text}")


    def process_input(self, event=None):
        """Handles user input from the entry box."""
        if not self.model: # Don't process input if model not ready
             self._append("[系統] 抱歉，我還沒準備好接收訊息 (模型未載入)。", tags=("system",))
             return
        if self.is_sleeping:
             self._append("[系統] 小星睡著了，好像聽不到...", tags=("system",))
             self.entry.delete(0, tk.END)
             return

        user_input = self.entry.get().strip()
        if not user_input: return

        self.last_user_interaction_time = time.time()
        if hasattr(self, 'non_response_timer_id') and self.non_response_timer_id:
             self.root.after_cancel(self.non_response_timer_id); self.non_response_timer_id = None
        self._check_non_response() # Reschedule check

        self._append(f"你: {user_input}", tags=("user",))
        self.entry.delete(0, tk.END)

        self.emotions['boredom'] = max(0, self.emotions.get('boredom', 0.5) - 0.15) # More reduction
        save_emotion(self.user_id, 'boredom', self.emotions['boredom'])
        self.boredom = self.emotions['boredom'] # Sync variable
        self._update_status_labels()

        # --- Command Handling ---
        handled_as_command = False
        # Add Task Command
        if user_input.lower().startswith("新增任務") or user_input.lower().startswith("add task"):
             task_desc = user_input.split(maxsplit=1)[1].strip() if len(user_input.split()) > 1 else ""
             if task_desc:
                 if add_task(self.user_id, task_desc): self._append(f"小星: 好喔，幫你記下來了：「{task_desc}」", tags=("pet",))
                 else: self._append("小星: 哎呀，新增任務失敗了...", tags=("pet",))
                 handled_as_command = True
             else: self._append("小星: 要新增什麼任務呀？", tags=("pet",)); handled_as_command = True
        # Show Tasks Command
        elif user_input.lower() == "查看任務" or user_input.lower() == "show tasks":
            tasks = get_tasks(self.user_id, include_completed=False)
            if tasks:
                 response = "你還有這些事情要做喔：\n" + "\n".join([f"{i+1}. {t['description']}" for i, t in enumerate(tasks)])
                 self._append(f"小星: {response.strip()}", tags=("pet",))
            else: self._append("小星: 耶！目前沒有待辦任務喔！", tags=("pet",))
            handled_as_command = True
        # Complete Task Command
        elif user_input.lower().startswith("完成任務") or user_input.lower().startswith("complete task"):
            parts = user_input.split(maxsplit=1); task_identifier = parts[1].strip() if len(parts) > 1 else ""
            if task_identifier:
                tasks = get_tasks(self.user_id, include_completed=False); task_to_complete = None
                try: # Try index first
                    task_index = int(task_identifier) - 1
                    if 0 <= task_index < len(tasks): task_to_complete = tasks[task_index]
                except ValueError: # Try substring match
                    found = [t for t in tasks if task_identifier.lower() in t['description'].lower()]
                    if len(found) == 1: task_to_complete = found[0]
                    elif len(found) > 1: self._append(f"小星: 找到好幾個「{task_identifier}」任務，要完成哪個？", tags=("pet",)); handled_as_command = True
                if task_to_complete:
                     if complete_task(task_to_complete['id']): self._append(f"小星: 好棒！完成「{task_to_complete['description']}」了！", tags=("pet",))
                     else: self._append("小星: 嗯？完成任務時好像出錯了...", tags=("pet",))
                elif not handled_as_command: self._append(f"小星: 找不到叫做「{task_identifier}」的待辦任務耶。", tags=("pet",))
                handled_as_command = True
            else: self._append("小星: 要完成哪個任務呀？", tags=("pet",)); handled_as_command = True

        # --- LLM Response if not a command ---
        if not handled_as_command:
            is_long_term_worthy = random.random() < 0.05 or any(k in user_input for k in ["重要", "記得", "記住", "生日", "紀念日"])
            importance = 5 if is_long_term_worthy else 1
            save_memory(self.user_id, f"User: {user_input}", is_long_term=False, importance=importance)
            if is_long_term_worthy: save_memory(self.user_id, f"User: {user_input}", is_long_term=True, importance=importance)
            self.reload_memory_lists() # Include user input for context

            prompt_for_response = f"使用者說：\"{user_input}\"\n請根據你的個性、當前心情、待辦事項和最近的對話，用口語化的方式回應他。"
            bot_response = self.call_llm(prompt_for_response, include_context=True, purpose="response")

            delay_enabled = int(self.settings.get(SETTING_RESPONSE_DELAY_ENABLED, 1))
            if delay_enabled:
                max_delay = int(self.settings.get(SETTING_RESPONSE_DELAY_MAX, 1200))
                delay_ms = random.randint(100, max(101, max_delay))
                typing_indicator_line = self._append("小星正在輸入...", tags=("system",), get_line=True)
                self.response_delay_timer_id = self.root.after(delay_ms, lambda u=user_input, b=bot_response, t_line=typing_indicator_line: self._finalize_response(u, b, t_line))
            else:
                 self._finalize_response(user_input, bot_response)


    def _finalize_response(self, user_input, bot_response, typing_indicator_line=None):
         """Displays the bot's response, removes typing indicator, saves memory, and updates emotions."""
         if typing_indicator_line:
              try: # Try removing typing indicator
                   start_index = f"{typing_indicator_line}.0"
                   end_index = f"{typing_indicator_line}.end+1c" # Line end + newline
                   current_content = self.text.get(start_index, end_index)
                   if "小星正在輸入..." in current_content:
                       self.text.config(state='normal')
                       self.text.delete(start_index, end_index)
                       self.text.config(state='disabled')
              except tk.TclError as e: logging.debug(f"Could not remove typing indicator line {typing_indicator_line}: {e}")
              except Exception as e: logging.error(f"Error removing typing indicator: {e}")

         self._append(f"小星: {bot_response}", tags=("pet",))
         save_memory(self.user_id, f"小星: {bot_response}", is_long_term=False)
         self.reload_memory_lists() # Include bot response before emotion update
         self.update_emotions_from_interaction(user_input, bot_response)


    def reload_memory_lists(self):
        """Reloads memories from the database into instance lists."""
        logging.debug("Reloading memory lists from database.")
        self.short_term_tuples = load_memory(self.user_id, False, limit=50)
        self.long_term_tuples = load_memory(self.user_id, True, limit=20)


    def _decay_emotions(self):
        """Gradually returns emotions towards their baseline."""
        if not self.model or not self.emotions: return # Don't decay if not initialized
        decay_rate = float(self.settings.get(SETTING_DECAY_RATE, 0.02)) * (0.3 if self.is_sleeping else 1.0)
        optimism = float(self.settings.get(SETTING_OPTIMISM_TRAIT, 0.5))
        anxiety_p = float(self.settings.get(SETTING_ANXIETY_TRAIT, 0.5))
        updated = False

        for name, value in list(self.emotions.items()):
            baseline = 0.5
            if name in POSITIVE_EMOTIONS: baseline = 0.5 + (optimism - 0.5) * 0.4
            elif name in NEGATIVE_EMOTIONS: baseline = 0.5 - (optimism - 0.5) * 0.4
            if name in ['anxiety', 'fear']: baseline += (anxiety_p - 0.5) * 0.3
            if name == 'boredom': baseline = 0.3
            if name == 'interest': baseline = 0.6
            baseline = max(0.0, min(1.0, baseline))

            if abs(value - baseline) > 0.01:
                new_value = max(0.0, min(1.0, value + (baseline - value) * decay_rate))
                if abs(new_value - value) > 0.001:
                    self.emotions[name] = new_value
                    save_emotion(self.user_id, name, new_value)
                    updated = True

        if updated:
            self.boredom = self.emotions.get('boredom', 0.5) # Sync variable
            self._update_pet_image(); self._update_status_labels()

        # Reschedule
        if hasattr(self, 'decay_timer_id') and self.decay_timer_id:
            try: self.root.after_cancel(self.decay_timer_id)
            except: pass
        self.decay_timer_id = self.root.after(15 * 60 * 1000, self._decay_emotions)


    def _update_needs(self):
        """Updates basic needs like boredom and energy over time."""
        if not self.model or not self.emotions: return # Don't update if not initialized

        # Boredom increases over time
        time_since_interaction = time.time() - self.last_user_interaction_time
        boredom_increase = 0.01 + (time_since_interaction / 3600) * 0.05
        current_boredom = self.emotions.get('boredom', 0.5)
        new_boredom = min(1.0, current_boredom + boredom_increase * (0.5 if self.is_sleeping else 1.0)) # Slower increase during sleep
        if abs(new_boredom - current_boredom) > 0.001:
            self.emotions['boredom'] = new_boredom
            save_emotion(self.user_id, 'boredom', new_boredom)
            self.boredom = new_boredom # Sync variable

        # Energy changes
        energy_change = 0.002 if self.is_sleeping else -0.005
        if self.emotions.get('excitement', 0) > 0.7 and not self.is_sleeping: energy_change = -0.01
        self.energy = max(0.0, min(1.0, self.energy + energy_change))

        self._update_status_labels()

        # Reschedule
        if hasattr(self, 'needs_timer_id') and self.needs_timer_id:
            try: self.root.after_cancel(self.needs_timer_id)
            except: pass
        self.needs_timer_id = self.root.after(5 * 60 * 1000, self._update_needs)


    def _update_status_labels(self):
        """Updates the UI labels for boredom, energy, and sleep status."""
        try:
            boredom_val = self.emotions.get('boredom', self.boredom) # Use emotion dict if available
            self.boredom_label.config(text=f"無聊度: {boredom_val:.1f}")
            self.energy_label.config(text=f"精力: {self.energy:.1f}")
            if self.is_sleeping: self.sleep_status_label.config(text="[睡覺中😴]", fg="blue")
            else: self.sleep_status_label.config(text="")
        except Exception as e:
            logging.error(f"Error updating status labels: {e}")


    def _is_bedtime(self):
        """Checks if the current time is within the configured bedtime hours."""
        try:
            bed_hour = int(self.settings.get(SETTING_BEDTIME_HOUR, 23))
            bed_min = int(self.settings.get(SETTING_BEDTIME_MINUTE, 0))
            wake_hour = int(self.settings.get(SETTING_WAKEUP_HOUR, 7))
            wake_min = int(self.settings.get(SETTING_WAKEUP_MINUTE, 0))
            now = datetime.now().time()
            bed_time = dt_time(bed_hour, bed_min)
            wake_time = dt_time(wake_hour, wake_min)
            if bed_time > wake_time: return now >= bed_time or now < wake_time
            else: return bed_time <= now < wake_time
        except Exception as e:
            logging.error(f"Error checking bedtime: {e}")
            return False # Default to not being bedtime on error


    def _apply_hourly_emotion_shift(self, hour):
        """Applies mood changes based on the time of day."""
        if self.is_sleeping or not self.emotions: return

        logging.info(f"Applying hourly emotion shift for hour: {hour}")
        change_magnitude = float(self.settings.get(SETTING_TIME_SHIFT_STRENGTH, 0.05))
        stability = float(self.settings.get(SETTING_MOOD_STABILITY, 0.3))
        emotions_to_update = {} # Stores {emotion_name: change_amount}

        if 6 <= hour < 10: emotions_to_update.update({'optimism': random.uniform(0.1, change_magnitude * 1.5), 'interest': random.uniform(0.1, change_magnitude * 1.2), 'joy': random.uniform(0, change_magnitude * 0.8)}); self.energy = min(1.0, self.energy + 0.15)
        elif 12 <= hour < 14: emotions_to_update.update({'calmness': random.uniform(0, change_magnitude * 0.5), 'boredom': random.uniform(0, change_magnitude * 0.3)}); self.energy = max(0.0, self.energy - 0.05)
        elif 19 <= hour < 23: emotions_to_update.update({'calmness': random.uniform(0, change_magnitude), 'nostalgia': random.uniform(0, change_magnitude * 0.7), 'contentment': random.uniform(0, change_magnitude * 0.5)})
        # elif 23 <= hour or hour < 5: emotions_to_update['boredom'] = random.uniform(0, change_magnitude * 0.8) # Less shift late night

        for _ in range(random.randint(0, 1)): # Fewer random shifts
             emo_name = random.choice(list(EMOTIONS.keys())); change = random.uniform(-change_magnitude * 0.5, change_magnitude * 0.5)
             emotions_to_update[emo_name] = emotions_to_update.get(emo_name, 0) + change # Add random change

        updated_count = 0
        if emotions_to_update:
            for name, change in emotions_to_update.items():
                 if name in self.emotions:
                     stable_change = change * (1.0 - stability)
                     new_value = max(0.0, min(1.0, self.emotions[name] + stable_change))
                     if abs(new_value - self.emotions[name]) > 0.005:
                         self.emotions[name] = new_value; save_emotion(self.user_id, name, new_value); updated_count +=1
            if updated_count > 0:
                 logging.info(f"Applied {updated_count} time-based emotion shifts."); self.boredom = self.emotions.get('boredom', 0.5); self._update_pet_image(); self._update_status_labels()


    def _hourly_time_check(self, run_immediately=False):
        """ Checks time, applies hourly shifts, manages sleep state."""
        if not self.model: return # Don't run if model not ready

        now_dt = datetime.now(); current_hour = now_dt.hour; now_ts = now_dt.timestamp()
        currently_is_bedtime = self._is_bedtime()

        # --- Sleep State Management ---
        if currently_is_bedtime and not self.is_sleeping:
            self.is_sleeping = True; self.just_woke_up = False
            logging.info("Bedtime reached. Going to sleep."); self._append("[系統] 小星要去睡覺了...💤", tags=("system",))
            if hasattr(self, 'proactive_timer_id') and self.proactive_timer_id: self.root.after_cancel(self.proactive_timer_id); self.proactive_timer_id = None
            self._update_pet_image(); self._update_status_labels()
        elif not currently_is_bedtime and self.is_sleeping:
            self.is_sleeping = False; self.just_woke_up = True
            logging.info("Wake-up time reached. Waking up."); self._update_pet_image(); self._update_status_labels()
            self._initial_greeting_or_wakeup() # Trigger wake-up message
            self._schedule_proactive_task() # Reschedule proactive timer

        # --- Hourly Emotion Shift ---
        hour_in_seconds = 60 * 60
        time_since_last_shift = now_ts - self.last_hourly_shift_time
        if not self.is_sleeping and (time_since_last_shift >= hour_in_seconds - 120 or run_immediately): # Check slightly before hour mark
             self._apply_hourly_emotion_shift(current_hour)
             self.last_hourly_shift_time = now_ts; save_setting('last_hourly_shift_time', now_ts)

        # --- Reschedule ---
        if hasattr(self, 'hourly_timer_id') and self.hourly_timer_id:
            try: self.root.after_cancel(self.hourly_timer_id); self.hourly_timer_id = None
            except: pass
        # Schedule next check (every 15 minutes)
        now = datetime.now(); minutes_past_hour = now.minute; minutes_to_next_quarter = 15 - (minutes_past_hour % 15)
        next_quarter = now.replace(second=5, microsecond=0) + timedelta(minutes=minutes_to_next_quarter)
        delay_ms = int((next_quarter - now).total_seconds() * 1000)
        if delay_ms < 5000: delay_ms += 15 * 60 * 1000
        self.hourly_timer_id = self.root.after(delay_ms, self._hourly_time_check)


    def _proactive(self):
        """Initiates proactive interaction if conditions are met."""
        if self.is_sleeping or not self.model or not self.emotions:
             # logging.debug("Proactive cancelled: Sleeping or not ready.")
             return # Reschedule handled by hourly check when waking

        min_quiet_time = 4 * 60
        now = time.time()
        if (now - self.last_user_interaction_time < min_quiet_time) or (now - self.last_proactive_timestamp < min_quiet_time):
             logging.debug("Proactive cancelled: Too soon since last interaction.")
             self._schedule_proactive_task() # Reschedule normally
             return

        logging.info("Initiating proactive interaction.")
        self.last_proactive_timestamp = now
        proactive_message = self._generate_proactive_message()

        if proactive_message:
            self._append(f"小星 (主動): {proactive_message}", tags=("pet", "proactive"))
            self.emotions['boredom'] = max(0, self.emotions.get('boredom', 0.5) - 0.2)
            save_emotion(self.user_id, 'boredom', self.emotions['boredom'])
            self.boredom = self.emotions['boredom'] # Sync variable
            self._update_status_labels()
        else: logging.warning("Proactive message generation failed.")

        self._schedule_proactive_task() # Reschedule next check


    def _generate_proactive_message(self):
        """Selects a proactive theme and generates a message using LLM."""
        themes = ["greeting", "memory_recall", "task_reminder", "weather_inquiry", "chatter", "emotion_expression"]
        weights = [1.0, 1.5, 1.8, 0.8, 2.5, 1.2] # Base weights

        # Adjust weights based on state
        tasks_pending = get_tasks(self.user_id)
        if len(self.long_term_tuples) > 5: weights[1] *= 1.5 # memory_recall
        if tasks_pending: weights[2] *= 2.0 # task_reminder
        if not self.settings.get(SETTING_LOCATION): weights[3] *= 0.5 # weather_inquiry
        dom, strength, _ = self._get_dominant_emotion()
        if strength > 0.75: weights[5] *= 2.0 # emotion_expression
        if self.emotions.get('boredom', 0.5) > 0.8: weights[4] *= 2.0 # chatter

        if self.last_proactive_theme and self.last_proactive_theme in themes:
             try: weights[themes.index(self.last_proactive_theme)] *= 0.1
             except: pass

        possible_themes = []; possible_weights = []
        for i, theme in enumerate(themes):
             can_use = True
             if theme == "task_reminder" and not tasks_pending: can_use = False
             if theme == "memory_recall" and not self.long_term_tuples: can_use = False
             if can_use: possible_themes.append(theme); possible_weights.append(weights[i])

        if not possible_themes: selected_theme = "greeting"
        else: selected_theme = random.choices(possible_themes, weights=possible_weights, k=1)[0]

        self.last_proactive_theme = selected_theme
        logging.info(f"Selected proactive theme: {selected_theme}")

        # --- Generate message idea based on theme ---
        prompt_idea = ""
        theme_functions = {
            "greeting": self._proactive_greeting,
            "memory_recall": self._proactive_memory_recall,
            "task_reminder": self._proactive_task_reminder,
            "weather_inquiry": self._proactive_weather_inquiry,
            "emotion_expression": self._proactive_emotion_expression,
            "chatter": self._proactive_chatter
        }
        if selected_theme in theme_functions:
            prompt_idea = theme_functions[selected_theme]()
        else: # Fallback
             prompt_idea = self._proactive_chatter()

        if not prompt_idea: return None

        final_prompt = f"你想要主動跟使用者說話，你想表達的大意是：「{prompt_idea}」。請根據你的個性和目前狀態，用自然的口氣把這段話說出來，簡短一點。"
        final_utterance = self.call_llm(final_prompt, include_context=True, purpose="proactive_speak")
        return final_utterance


    def _proactive_greeting(self): return random.choice(["哈囉～ 突然想跟你打聲招呼！", "嘿！在嗎？ 最近怎麼樣啊？", "（探頭）你在忙嗎？", "嗨嗨～"])
    def _proactive_memory_recall(self):
        if not self.long_term_tuples: return None
        mems = self.long_term_tuples; chosen_mem = random.choice(mems)
        _, memory_item = chosen_mem; content = memory_item[memory_item.find(":")+1:].strip().replace("\n", " ")
        topic = content[:50] + ('...' if len(content) > 50 else '')
        return random.choice([f"欸～我突然想到，我們之前是不是聊過「{topic}」？", f"我記得你之前好像說過關於「{topic}」的事？", f"對了，上次講到「{topic}」，後來怎麼樣了啊？"])
    def _proactive_task_reminder(self):
        tasks = get_tasks(self.user_id, include_completed=False); task = random.choice(tasks) if tasks else None
        if not task: return None
        return random.choice([f"對了，別忘了還有「{task['description']}」這件事喔！", f"欸，那個「{task['description']}」做了沒啊？", f"溫馨提醒～ 記得要處理「{task['description']}」嘿！"])
    def _proactive_weather_inquiry(self):
        loc = self.settings.get(SETTING_LOCATION, "")
        if loc: return random.choice([f"你那邊 ({loc}) 現在天氣好嗎？", f"不知道 {loc} 今天天氣如何？", f"希望 {loc} 今天是個好天氣！"])
        else: return random.choice(["欸，好好奇你現在在哪裡喔？ 方不方便跟我說一下？", "不知道你那邊天氣怎麼樣？ 你在哪個城市啊？", "對了，一直忘了問，你通常都在哪個地區活動呀？"])
    def _proactive_emotion_expression(self):
        dom, strength, _ = self._get_dominant_emotion(); phrases = []
        if strength < 0.65: return self._proactive_chatter()
        if dom in POSITIVE_EMOTIONS: phrases = [f"跟你說喔，我現在超 {dom} 的啦！ ({strength:.1f})", f"嘿嘿，現在心情很好欸，感覺很 {dom}！"]
        elif dom in NEGATIVE_EMOTIONS: phrases = [f"嗯...跟你說喔，我現在心情有點 {dom} ({strength:.1f})...", f"不知道為什麼，感覺有點 {dom}，怪怪的..."]
        else: phrases = [f"我現在感覺超級 {dom} ({strength:.1f})！"]
        return random.choice(phrases) if phrases else self._proactive_chatter()
    def _proactive_chatter(self):
        topics = ["隨便聊聊嘛～ 最近有發生什麼有趣的事嗎？", "你在做什麼呀？ 好奇～", "最近有聽到什麼好聽的歌嗎？", "肚子餓了嗎？", "（伸懶腰）", "今天天氣感覺怎麼樣？", "好想出去玩喔～"]
        if self.energy < 0.4: topics.append("有點想睡覺了...")
        if self.emotions.get('boredom', 0) > 0.7: topics.append("真的好無聊喔...")
        return random.choice(topics)


    def _handle_non_response(self):
        """Triggered when user hasn't responded for a while."""
        if not self.model or not self.emotions: return
        logging.info("User inactivity detected. Triggering non-response behavior.")

        # 1. Adjust Mood
        sad_inc = random.uniform(0.02, 0.08); bored_inc = random.uniform(0.05, 0.15)
        opt = float(self.settings.get(SETTING_OPTIMISM_TRAIT, 0.5))
        self.emotions['sadness'] = min(1.0, self.emotions.get('sadness', 0.5) + sad_inc * (1.0 - opt))
        self.emotions['boredom'] = min(1.0, self.emotions.get('boredom', 0.5) + bored_inc)
        save_emotion(self.user_id, 'sadness', self.emotions['sadness'])
        save_emotion(self.user_id, 'boredom', self.emotions['boredom'])
        logging.info(f"Mood adjusted due to inactivity: Sadness -> {self.emotions['sadness']:.3f}, Boredom -> {self.emotions['boredom']:.3f}")
        self.boredom = self.emotions['boredom'] # Sync var
        self._update_pet_image(); self._update_status_labels()

        # 2. Generate Self-Talk
        dom, strength, _ = self._get_dominant_emotion()
        prompt = f"你因為使用者很久沒有回應，感到有點無聊和失落。請根據你的個性和目前的主要情緒 ({dom}={strength:.2f})，生成一句簡短的自言自語。"
        self_talk = self.call_llm(prompt, include_context=True, purpose="self_talk")
        if self_talk: self._append(f"小星 (自言自語): {self_talk}", tags=("pet", "selftalk"))
        else: logging.warning("Self-talk generation failed.")

        # 3. Reschedule next check (handled by _check_non_response calling itself)


    def _check_non_response(self):
        """Checks if user has been inactive and schedules the handler or next check."""
        if hasattr(self, 'non_response_timer_id') and self.non_response_timer_id:
            try: self.root.after_cancel(self.non_response_timer_id); self.non_response_timer_id = None
            except: pass

        if self.is_sleeping or not self.model: # Don't check when sleeping or no model
             # logging.debug("Non-response check skipped: Sleeping or model not ready.")
             return

        timeout_minutes = int(self.settings.get(SETTING_NON_RESPONSE_TIMEOUT, 45))
        if timeout_minutes <= 0: return # Feature disabled

        time_since_last = time.time() - self.last_user_interaction_time
        timeout_seconds = timeout_minutes * 60

        if time_since_last >= timeout_seconds:
            self._handle_non_response() # Handle it now
            # _handle_non_response should ideally reschedule, but let's reschedule here too for safety
            next_delay_ms = int(timeout_seconds * 1000 * random.uniform(1.1, 1.5)) # Longer delay after self-talk
        else:
            # Schedule the check for when the timeout WILL occur
            remaining_time_sec = timeout_seconds - time_since_last
            next_delay_ms = int(remaining_time_sec * 1000) + random.randint(1000, 5000) # Add jitter

        self.non_response_timer_id = self.root.after(max(5000, next_delay_ms), self._check_non_response) # Minimum 5 sec delay


    def _cleanup(self):
        """Cleans old short-term memory entries."""
        if not self.model: return
        retention_days = int(self.settings.get(SETTING_STM_RETENTION_DAYS, 30))
        clean_short_term_memory(retention_days)
        # Reschedule
        if hasattr(self, 'cleanup_timer_id') and self.cleanup_timer_id:
            try: self.root.after_cancel(self.cleanup_timer_id); self.cleanup_timer_id = None
            except: pass
        self.cleanup_timer_id = self.root.after(24 * 60 * 60 * 1000, self._cleanup)


    def _process_memory_forgetting(self):
        """Simulates forgetting and recalling memories based on probabilities."""
        if self.is_sleeping or not self.model: return

        logging.debug("Processing memory forgetting/recalling.")
        forget_chance = float(self.settings.get(SETTING_FORGET_CHANCE, 0.03))
        recall_chance = float(self.settings.get(SETTING_RECALL_CHANCE, 0.01))
        forgotten_count = 0; recalled_count = 0

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # Simplified: Randomly select some to potentially forget/recall
                # Forget STM
                c.execute("UPDATE short_term_memory SET status='forgotten' WHERE status='remembered' AND RANDOM() < ?", (forget_chance,))
                forgotten_count += c.rowcount
                # Forget LTM (harder)
                c.execute("UPDATE long_term_memory SET status='forgotten' WHERE status='remembered' AND RANDOM() < ?", (forget_chance * 0.3,))
                forgotten_count += c.rowcount
                # Recall STM
                c.execute("UPDATE short_term_memory SET status='remembered' WHERE status='forgotten' AND RANDOM() < ?", (recall_chance,))
                recalled_count += c.rowcount
                # Recall LTM (easier)
                c.execute("UPDATE long_term_memory SET status='remembered' WHERE status='forgotten' AND RANDOM() < ?", (recall_chance * 1.5,))
                recalled_count += c.rowcount
                conn.commit()

                if forgotten_count > 0: logging.info(f"Forgot {forgotten_count} memories.")
                if recalled_count > 0: logging.info(f"Recalled {recalled_count} memories.")
                if forgotten_count > 0 or recalled_count > 0: self.reload_memory_lists()
        except sqlite3.Error as e: logging.error(f"Error during memory forgetting process: {e}")

        # Reschedule
        if hasattr(self, 'forgetting_timer_id') and self.forgetting_timer_id:
            try: self.root.after_cancel(self.forgetting_timer_id); self.forgetting_timer_id = None
            except: pass
        self.forgetting_timer_id = self.root.after(6 * 60 * 60 * 1000, self._process_memory_forgetting)


    def _append(self, text, tags=None, get_line=False):
        """Appends text to the dialogue display with optional tags. Can return line index."""
        line_index = None
        try:
            if get_line: line_index = self.text.index("end-1c").split('.')[0]
            self.text.config(state='normal')
            if tags: self.text.insert(tk.END, text + "\n", tags)
            else: self.text.insert(tk.END, text + "\n")
            self.text.config(state='disabled')
            self.text.see(tk.END)
            return line_index if get_line else None
        except tk.TclError as e: logging.warning(f"Failed to append text, window might be closing: {e}")
        except Exception as e: logging.error(f"Error appending text: {e}")
        return None


    def on_close(self):
        """Handles application closing actions."""
        logging.info("Closing application...")
        self._cancel_timers() # Stop all scheduled tasks cleanly
        if self.model: # Save final state only if model was active
            save_setting('last_hourly_shift_time', self.last_hourly_shift_time)
            # Maybe save emotions one last time?
            # for name, value in self.emotions.items(): save_emotion(self.user_id, name, value)
        logging.info("小星 says goodbye!")
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
        if 'vista' in available_themes: style.theme_use('vista')
        elif 'clam' in available_themes: style.theme_use('clam')
        elif 'aqua' in available_themes: style.theme_use('aqua') # macOS
        else: style.theme_use('default')
        logging.info(f"Using ttk theme: {style.theme_use()}")
    except tk.TclError:
         logging.warning("Could not set ttk theme.")

    # --- Window Config ---
    root.minsize(400, 550) # Adjusted min size
    root.maxsize(600, 800) # Optional max size

    # --- Initialize App ---
    app = PetApp(root)

    # --- Start Main Loop (Check Initialization) ---
    # Check if the model was successfully initialized (implies API key was valid or entered)
    if hasattr(app, 'model') and app.model:
         root.protocol("WM_DELETE_WINDOW", app.on_close) # Handle window close button
         root.mainloop()
    else:
         logging.error("Application failed to initialize LLM. Exiting.")
         # Show final error message if API key prompt didn't already cover it
         if root.winfo_exists(): # Check if window still exists
              messagebox.showerror("啟動失敗", "無法初始化核心對話模型 (Gemini)。\n請檢查您的 API Key 設定與網路連線。\n應用程式即將關閉。", parent=root)
              root.destroy()
