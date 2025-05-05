import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk
from tkinter import colorchooser # Added for color picking (optional future use)
from PIL import Image, ImageTk
import json
import random
import time
import os
import sqlite3
import uuid
import google.generativeai as genai
import logging
from datetime import datetime
import math # For sigmoid if needed
import re # Import regex for improved JSON finding

# --- 日誌設定 ---
# 將 level 改為 logging.DEBUG 可以看到更詳細的日誌，包含傳送給 AI 的提示
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') # <-- Use this for debugging prompts


# --- 檔案路徑設定 & 圖片處理 ---
# (Unchanged)
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
# (Unchanged)
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
# (Unchanged)
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

# --- 預設設定 ---
# (Unchanged)
DEFAULT_SETTINGS = {
    SETTING_MOOD_STABILITY: 0.3,
    SETTING_OPTIMISM_TRAIT: 0.5,
    SETTING_ANXIETY_TRAIT: 0.5,
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
}


# --- 資料庫輔助 & 初始化 ---
# (Unchanged)
def column_exists(cursor, table_name, column_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        return column_name in columns
    except sqlite3.Error as e:
        logging.error(f"Error checking column {column_name} in {table_name}: {e}")
        return False

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            tables = {
                'emotions': '''CREATE TABLE IF NOT EXISTS emotions (user_id TEXT, emotion_name TEXT, value REAL, last_updated REAL, PRIMARY KEY (user_id, emotion_name))''',
                'short_term_memory': '''CREATE TABLE IF NOT EXISTS short_term_memory (id TEXT PRIMARY KEY, user_id TEXT, content TEXT, timestamp REAL, importance INTEGER, status TEXT DEFAULT 'remembered')''',
                'long_term_memory': '''CREATE TABLE IF NOT EXISTS long_term_memory (id TEXT PRIMARY KEY, user_id TEXT, content TEXT, timestamp REAL, importance INTEGER, status TEXT DEFAULT 'remembered')''',
                'api_keys': '''CREATE TABLE IF NOT EXISTS api_keys (id TEXT PRIMARY KEY, key_name TEXT UNIQUE, key_value TEXT)''',
                'app_state': '''CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value REAL)'''
            }
            for ddl in tables.values():
                c.execute(ddl)

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
# (Unchanged)
CHARACTER_PROFILE = (
    "你是一個名叫小星的桌寵，個性多變（活潑、好奇、溫暖、敏感、低落等），要假裝自己不是AI，絕對不要把情緒分數或個性分數顯示出來。"
    "說話時請融入台灣年輕人常用的口頭禪，例如「好喔」、「欸」、「煩欸」、「真的假的」、「對啊」、「屁啦」、「超好笑」、「好扯」、「啦」、「喔」、「啊」等等，"
    "但不強制任何詞語開頭，自然流暢即可。你的回應應該簡短、口語化、像朋友聊天。"
)

# --- API 金鑰管理 ---
# (Unchanged)
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
            c.execute("INSERT OR REPLACE INTO api_keys (key_name, key_value, id) VALUES (?, ?, ?)",(key_name, key_value, str(uuid.uuid4())))
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

# --- App State/Settings Management ---
# (Unchanged)
def save_setting(key, value):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, float(value)))
            conn.commit()
    except (sqlite3.Error, ValueError) as e:
        logging.error(f"Failed to save setting '{key}' with value '{value}': {e}")

def load_setting(key, default_value):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM app_state WHERE key=?", (key,))
            row = c.fetchone()
            return float(row[0]) if row else default_value
    except sqlite3.Error as e:
        logging.error(f"Failed to load setting '{key}': {e}")
        return default_value

# --- 記憶與情緒儲存與載入 ---
# (Unchanged)
def save_emotion(user_id, emotion_name, value):
    value = max(0.0, min(1.0, float(value)))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO emotions (user_id, emotion_name, value, last_updated) VALUES (?, ?, ?, ?)",(user_id, emotion_name, value, time.time()))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save emotion for user {user_id}: {e}")

def load_emotions(user_id):
    emo = dict(EMOTIONS)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT emotion_name, value FROM emotions WHERE user_id=?", (user_id,))
            rows = c.fetchall()
            for name, val in rows:
                if name in emo: emo[name] = val
            logging.info(f"Loaded emotions for user {user_id}.")
    except sqlite3.Error as e: logging.error(f"Failed to load emotions for user {user_id}: {e}")
    return emo

def save_memory(user_id, content, is_long_term=False, importance=1):
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"INSERT INTO {table} (id, user_id, content, timestamp, importance) VALUES (?, ?, ?, ?, ?)",(str(uuid.uuid4()), user_id, content, time.time(), importance))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save memory for user {user_id}: {e}")

def load_memory(user_id, is_long_term=False, limit=50):
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


# --- 設定視窗類別 ---
# (Unchanged)
class SettingsWindow(tk.Toplevel):
    def __init__(self, parent, app_settings):
        super().__init__(parent)
        self.title("小星設定")
        self.geometry("500x600") # Increased size
        self.parent = parent # The main PetApp instance
        self.app_settings = app_settings # Reference to the settings dict/object

        # --- Create main frame and canvas for scrolling ---
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- Store setting variables ---
        self.setting_vars = {}
        self._create_settings_widgets()
        self._load_settings_to_ui()

        # --- Buttons ---
        button_frame = ttk.Frame(self) # Place buttons outside scrollable area
        button_frame.pack(fill=tk.X, pady=10, padx=10)

        save_button = ttk.Button(button_frame, text="儲存設定", command=self._save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)

        cancel_button = ttk.Button(button_frame, text="取消", command=self.destroy)
        cancel_button.pack(side=tk.RIGHT)

        # --- Make window modal ---
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def _create_settings_widgets(self):
        frame = self.scrollable_frame

        # --- Personality Traits ---
        trait_frame = ttk.LabelFrame(frame, text="個性特質")
        trait_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_OPTIMISM_TRAIT] = tk.DoubleVar()
        ttk.Label(trait_frame, text="樂觀傾向 (0悲觀-1樂觀):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(trait_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_OPTIMISM_TRAIT]).grid(row=0, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_ANXIETY_TRAIT] = tk.DoubleVar()
        ttk.Label(trait_frame, text="焦慮傾向 (0冷靜-1易焦慮):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(trait_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_ANXIETY_TRAIT]).grid(row=1, column=1, sticky="ew", padx=5)

        # --- Emotional Response ---
        emo_frame = ttk.LabelFrame(frame, text="情緒反應")
        emo_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_EMO_SENSITIVITY] = tk.DoubleVar()
        ttk.Label(emo_frame, text="情緒敏感度 (0遲鈍-2敏感):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(emo_frame, from_=0.0, to=2.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_EMO_SENSITIVITY]).grid(row=0, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_MOOD_STABILITY] = tk.DoubleVar()
        ttk.Label(emo_frame, text="情緒穩定度 (0易變-1穩定):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(emo_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_MOOD_STABILITY]).grid(row=1, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_DECAY_RATE] = tk.DoubleVar()
        ttk.Label(emo_frame, text="情緒衰減速度 (0慢-0.1快):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(emo_frame, from_=0.0, to=0.1, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_DECAY_RATE]).grid(row=2, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_TIME_SHIFT_STRENGTH] = tk.DoubleVar()
        ttk.Label(emo_frame, text="時間影響情緒強度 (0無-0.2強):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(emo_frame, from_=0.0, to=0.2, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_TIME_SHIFT_STRENGTH]).grid(row=3, column=1, sticky="ew", padx=5)

        # --- Behavior Patterns ---
        behav_frame = ttk.LabelFrame(frame, text="行為模式")
        behav_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_PROACTIVE_FREQ] = tk.IntVar()
        ttk.Label(behav_frame, text="主動聊天頻率:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        freq_options = ["頻繁 (5-15分)", "普通 (10-25分)", "偶爾 (20-40分)", "從不"]
        # Store index in the variable
        self.freq_combobox = ttk.Combobox(behav_frame, textvariable=self.setting_vars[SETTING_PROACTIVE_FREQ], values=list(range(len(freq_options))), state="readonly", width=15)
        self.freq_combobox.grid(row=0, column=1, sticky="w", padx=5)
        # Set display text based on index (can't directly link options list easily)
        self.freq_combobox['values'] = freq_options # Display text
        # Load will set the index, display should update


        self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED] = tk.IntVar()
        ttk.Checkbutton(behav_frame, text="啟用回應延遲模擬", variable=self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED]).grid(row=1, column=0, columnspan=2, sticky="w", padx=5)

        self.setting_vars[SETTING_RESPONSE_DELAY_MAX] = tk.IntVar()
        ttk.Label(behav_frame, text="最大延遲時間 (ms):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(behav_frame, from_=0, to=3000, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_RESPONSE_DELAY_MAX]).grid(row=2, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_FORGET_CHANCE] = tk.DoubleVar()
        ttk.Label(behav_frame, text="記憶遺忘機率 (0無-0.1高):").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(behav_frame, from_=0.0, to=0.1, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_FORGET_CHANCE]).grid(row=3, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_RECALL_CHANCE] = tk.DoubleVar()
        ttk.Label(behav_frame, text="記憶回憶機率 (0無-0.05高):").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(behav_frame, from_=0.0, to=0.05, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_RECALL_CHANCE]).grid(row=4, column=1, sticky="ew", padx=5)

        # --- LLM Settings ---
        llm_frame = ttk.LabelFrame(frame, text="LLM 設定")
        llm_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_LLM_TEMP] = tk.DoubleVar()
        ttk.Label(llm_frame, text="回應溫度 (0精確-1隨機):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(llm_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_LLM_TEMP]).grid(row=0, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_LLM_MAX_TOKENS] = tk.IntVar()
        ttk.Label(llm_frame, text="回應最大長度 (tokens):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(llm_frame, textvariable=self.setting_vars[SETTING_LLM_MAX_TOKENS], width=10).grid(row=1, column=1, sticky="w", padx=5)

        # --- Other ---
        other_frame = ttk.LabelFrame(frame, text="其他")
        other_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_STM_RETENTION_DAYS] = tk.IntVar()
        ttk.Label(other_frame, text="短期記憶保留天數:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Entry(other_frame, textvariable=self.setting_vars[SETTING_STM_RETENTION_DAYS], width=10).grid(row=0, column=1, sticky="w", padx=5)


        # Make columns in frames resize reasonably
        for child in frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                child.grid_columnconfigure(1, weight=1)


    def _load_settings_to_ui(self):
        logging.debug("Loading settings into Settings UI.")
        for key, var in self.setting_vars.items():
            value = self.app_settings.get(key)
            if value is not None:
                 if key == SETTING_PROACTIVE_FREQ:
                     try:
                         index_val = int(value)
                         if 0 <= index_val < len(self.freq_combobox['values']):
                              var.set(index_val) # Set the index
                              self.freq_combobox.current(index_val) # Set display selection
                         else:
                              logging.warning(f"Invalid index for proactive freq: {index_val}. Defaulting.")
                              var.set(1)
                              self.freq_combobox.current(1)
                     except (ValueError, TypeError):
                          logging.error(f"Error loading proactive freq index: {value}. Defaulting.")
                          var.set(1)
                          self.freq_combobox.current(1)
                 else:
                     try:
                        var.set(value)
                     except Exception as e:
                         logging.error(f"Error setting UI for {key} with value {value}: {e}")
            else:
                 logging.warning(f"Setting key {key} not found in app settings during UI load.")


    def _save_settings(self):
        logging.info("Saving settings from Settings UI.")
        try:
            temp_settings = {}
            for key, var in self.setting_vars.items():
                value = var.get()
                if key == SETTING_PROACTIVE_FREQ:
                    # The variable holds the index (0, 1, 2, 3)
                    temp_settings[key] = int(value)
                elif key == SETTING_RESPONSE_DELAY_ENABLED:
                     temp_settings[key] = int(value) # Ensure 0 or 1
                elif key in [SETTING_RESPONSE_DELAY_MAX, SETTING_LLM_MAX_TOKENS, SETTING_STM_RETENTION_DAYS]:
                    temp_settings[key] = int(value) # Ensure integer
                else:
                    temp_settings[key] = float(value) # Assume float for others (Scales, etc.)

            # Update parent app's settings immediately
            self.parent.settings.update(temp_settings)

            # Persist settings to DB
            for key, value in temp_settings.items():
                save_setting(key, value)

            # Notify parent app that settings might have changed
            self.parent.apply_settings_changes()

            messagebox.showinfo("成功", "設定已儲存！", parent=self)
            self.destroy()

        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤：\n{e}", parent=self)


# --- 主程式類別 ---
class PetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("小星桌寵")
        # Try to load user ID from a simple config file, otherwise ask
        self.user_id = self._load_user_id()
        if not self.user_id:
            self.user_id = simpledialog.askstring("用戶ID", "請輸入您的用戶ID：", initialvalue="default_user")
            if not self.user_id: self.user_id = "default_user"
            self._save_user_id(self.user_id) # Save for next time

        self.boredom = 0.5
        self.energy = 0.8
        self.last_hourly_shift_time = 0

        # --- Load Settings ---
        self.settings = self._load_all_settings()

        init_db()
        self.model_var = tk.StringVar(value="gemini-1.5-flash") # Default model
        self._ensure_api_key()

        if hasattr(self, 'api_key') and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Use the actual selected model (might be loaded from settings if saved, or default)
                selected_model = self.settings.get('selected_llm_model', self.model_var.get())
                self.model_var.set(selected_model)
                self.model = genai.GenerativeModel(model_name=self.model_var.get())
                self.apply_llm_settings()
                logging.info(f"Gemini model '{self.model_var.get()}' configured.")
            except Exception as e:
                logging.error(f"Failed to configure Gemini: {e}")
                messagebox.showerror("API 錯誤", f"無法設定 Gemini 模型：{e}\n請檢查您的 API Key 或網路連線。")
                self.root.quit()
                return

            self.last_hourly_shift_time = load_setting('last_hourly_shift_time', 0)
            logging.info(f"Loaded last hourly shift time: {self.last_hourly_shift_time}")

            self.emotions = load_emotions(self.user_id)
            self.reload_memory_lists()

            self._build_ui()
            self._update_pet_image()
            self._initial_greeting()
            self._schedule_tasks()

            self._hourly_time_check(run_immediately=True)

        else:
            logging.warning("API Key not available. Exiting.")
            self.root.quit()

    def _load_user_id(self):
        """Loads user ID from a simple config file."""
        try:
            config_path = os.path.join(BASE_DIR, 'user_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('user_id')
        except Exception as e:
            logging.warning(f"Could not load user ID from config: {e}")
        return None

    def _save_user_id(self, user_id):
        """Saves user ID to a simple config file."""
        try:
            config_path = os.path.join(BASE_DIR, 'user_config.json')
            with open(config_path, 'w') as f:
                json.dump({'user_id': user_id}, f)
        except Exception as e:
            logging.error(f"Could not save user ID to config: {e}")


    def _load_all_settings(self):
        """Loads all settings from DB or uses defaults."""
        settings = {}
        for key, default_value in DEFAULT_SETTINGS.items():
            settings[key] = load_setting(key, default_value)
        # Load other non-numeric settings if saved, e.g., selected model
        settings['selected_llm_model'] = load_setting('selected_llm_model', DEFAULT_SETTINGS.get('selected_llm_model', "gemini-1.5-flash")) # Example, assuming default
        logging.info("Loaded application settings.")
        # Ensure correct types after loading
        settings[SETTING_PROACTIVE_FREQ] = int(settings.get(SETTING_PROACTIVE_FREQ, DEFAULT_SETTINGS[SETTING_PROACTIVE_FREQ]))
        settings[SETTING_RESPONSE_DELAY_ENABLED] = int(settings.get(SETTING_RESPONSE_DELAY_ENABLED, DEFAULT_SETTINGS[SETTING_RESPONSE_DELAY_ENABLED]))
        settings[SETTING_RESPONSE_DELAY_MAX] = int(settings.get(SETTING_RESPONSE_DELAY_MAX, DEFAULT_SETTINGS[SETTING_RESPONSE_DELAY_MAX]))
        settings[SETTING_LLM_MAX_TOKENS] = int(settings.get(SETTING_LLM_MAX_TOKENS, DEFAULT_SETTINGS[SETTING_LLM_MAX_TOKENS]))
        settings[SETTING_STM_RETENTION_DAYS] = int(settings.get(SETTING_STM_RETENTION_DAYS, DEFAULT_SETTINGS[SETTING_STM_RETENTION_DAYS]))
        return settings

    def apply_llm_settings(self):
         """Applies LLM temperature and max tokens to the generation config used in calls."""
         logging.info(f"Applying LLM settings: Temp={self.settings[SETTING_LLM_TEMP]}, MaxTokens={self.settings[SETTING_LLM_MAX_TOKENS]}")
         # Note: These settings are applied dynamically within call_llm via GenerationConfig

    def apply_settings_changes(self):
        """Called after settings are saved to apply immediate changes."""
        logging.info("Applying settings changes...")
        self.apply_llm_settings()
        self._cancel_timers()
        self._reschedule_tasks_from_settings()
        logging.info("Settings changes applied and tasks rescheduled.")

    def _cancel_timers(self):
        """Cancel all scheduled 'after' tasks."""
        logging.debug("Cancelling scheduled timers...")
        timers = ['proactive_timer_id', 'decay_timer_id', 'needs_timer_id',
                  'cleanup_timer_id', 'forgetting_timer_id', 'hourly_timer_id',
                  'response_delay_timer_id']
        for timer_attr in timers:
             if hasattr(self, timer_attr):
                 timer_id = getattr(self, timer_attr, None)
                 if timer_id:
                     try:
                         self.root.after_cancel(timer_id)
                         setattr(self, timer_attr, None)
                     except tk.TclError:
                          pass # May already be cancelled or invalid

    def _reschedule_tasks_from_settings(self):
         """Reschedules tasks based on current settings."""
         logging.debug("Rescheduling tasks based on settings...")

         # --- Proactive Chat ---
         freq_index = self.settings[SETTING_PROACTIVE_FREQ]
         intervals = [(5*60, 15*60), (10*60, 25*60), (20*60, 40*60), (-1, -1)] # (min, max) in seconds
         if 0 <= freq_index < len(intervals):
             min_delay, max_delay = intervals[freq_index]
         else:
              logging.warning(f"Invalid proactive frequency index {freq_index}, defaulting to '普通'")
              min_delay, max_delay = intervals[1] # Default to Mid

         if min_delay > 0:
              next_proactive_ms = random.randint(min_delay * 1000, max_delay * 1000)
              self.proactive_timer_id = self.root.after(next_proactive_ms, self._proactive)
              logging.info(f"Rescheduled proactive task in {next_proactive_ms/1000:.0f}s")
         else:
              logging.info("Proactive task disabled by settings.")

         # --- Other tasks ---
         decay_interval_ms = 15 * 60 * 1000
         needs_interval_ms = 5 * 60 * 1000
         cleanup_interval_ms = 24 * 60 * 60 * 1000
         forgetting_interval_ms = 6 * 60 * 60 * 1000
         hourly_interval_ms = 60 * 60 * 1000 # Check every hour

         self.decay_timer_id = self.root.after(decay_interval_ms, self._decay_emotions)
         self.needs_timer_id = self.root.after(needs_interval_ms, self._update_needs)
         self.cleanup_timer_id = self.root.after(cleanup_interval_ms, self._cleanup) # Cleanup calls its own reschedule
         self.forgetting_timer_id = self.root.after(forgetting_interval_ms, self._process_memory_forgetting)
         self.hourly_timer_id = self.root.after(hourly_interval_ms, self._hourly_time_check) # Hourly check reschedules itself


    def _ensure_api_key(self):
        # (Unchanged)
        self.api_key = get_api_key('gemini')
        if not self.api_key:
            key = simpledialog.askstring("API Key", "請輸入您的 Google AI Gemini API Key：", parent=self.root)
            if key:
                if set_api_key('gemini', key):
                    self.api_key = key
                    logging.info("New API Key saved.")
                else:
                    messagebox.showerror("錯誤", "無法儲存 API Key。")
                    self.api_key = None
            else:
                 messagebox.showwarning("警告", "未提供 API Key，部分功能將無法使用。")
                 self.api_key = None

    def _build_ui(self):
        # (Unchanged)
        # --- Image Display ---
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=10)
        self.pet_label = tk.Label(self.image_frame)
        self.pet_label.pack()
        try:
            img = Image.open(DEFAULT_IMG_PATH).resize((150,150), Image.Resampling.LANCZOS)
            self.pet_photo = ImageTk.PhotoImage(img)
            self.pet_label.config(image=self.pet_photo)
            self.current_image_path = DEFAULT_IMG_PATH
        except Exception as e:
            logging.error(f"Error loading default image: {e}")
            self.pet_label.config(text="[圖片錯誤]", width=20, height=10)


        # --- Model Selection ---
        model_frame = tk.Frame(self.root)
        model_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(model_frame, text="選擇模型：").pack(side=tk.LEFT)
        opts = ["gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
        # Ensure loaded model is in options, otherwise default
        if self.model_var.get() not in opts: self.model_var.set(opts[0])
        self.model_option_menu = tk.OptionMenu(model_frame, self.model_var, *opts, command=self._on_model_change)
        self.model_option_menu.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- Dialogue Display ---
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        self.text_scrollbar = tk.Scrollbar(self.text_frame)
        self.text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text = tk.Text(self.text_frame, height=15, width=50, state='disabled', wrap=tk.WORD, yscrollcommand=self.text_scrollbar.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_scrollbar.config(command=self.text.yview)

        # --- Input Box ---
        self.entry = tk.Entry(self.root, width=50)
        self.entry.pack(pady=5, padx=10, fill=tk.X)
        self.entry.bind("<Return>", self.process_input)

        # --- Status Labels ---
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(pady=2, fill=tk.X, padx=10)
        self.boredom_label = tk.Label(self.status_frame, text=f"無聊度: {self.boredom:.1f}")
        self.boredom_label.pack(side=tk.LEFT)
        self.energy_label = tk.Label(self.status_frame, text=f"精力: {self.energy:.1f}")
        self.energy_label.pack(side=tk.RIGHT)

        # --- Menu ---
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="匯入圖片...", command=self.import_image)
        file_menu.add_command(label="開啟設定...", command=self.open_settings_window)
        file_menu.add_command(label="清除 API Key...", command=self._clear_api_key_action)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close)
        status_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="狀態", menu=status_menu)
        status_menu.add_command(label="查看狀態", command=self._show_emotions)
        status_menu.add_command(label="查看記憶", command=self._show_memories)


    def open_settings_window(self):
         # (Unchanged)
         SettingsWindow(self.root, self.settings)

    def _get_dominant_emotion(self):
        # (Unchanged)
        if not self.emotions: return "neutral", 0.5, "neutral"
        dominant_name = max(self.emotions, key=self.emotions.get)
        strength = self.emotions[dominant_name]
        positive_score = sum(self.emotions.get(e, 0) for e in POSITIVE_EMOTIONS)
        negative_score = sum(self.emotions.get(e, 0) for e in NEGATIVE_EMOTIONS)
        mood = "neutral"
        if positive_score > negative_score + 0.1: mood = "positive"
        elif negative_score > positive_score + 0.1: mood = "negative"
        visual_mood = "neutral"
        if dominant_name in ['joy', 'excitement', 'satisfaction', 'amusement', 'adoration']: visual_mood = "happy"
        elif dominant_name in ['sadness', 'disappointment', 'grief', 'remorse']: visual_mood = "sad"
        elif dominant_name in ['anger', 'frustration', 'disgust']: visual_mood = "angry"
        elif dominant_name in ['fear', 'anxiety']: visual_mood = "anxious"
        elif mood == "positive": visual_mood = "happy"
        elif mood == "negative": visual_mood = "sad"
        return dominant_name, strength, visual_mood

    def _update_pet_image(self):
        # (Unchanged)
        _, _, visual_mood = self._get_dominant_emotion()
        img_path = EMOTION_IMAGES.get(visual_mood, DEFAULT_IMG_PATH)
        if not os.path.exists(img_path): img_path = DEFAULT_IMG_PATH
        try:
            current_path = getattr(self, 'current_image_path', None)
            if current_path == img_path: return

            img = Image.open(img_path).resize((150, 150), Image.Resampling.LANCZOS)
            self.pet_photo = ImageTk.PhotoImage(img)
            self.pet_label.config(image=self.pet_photo)
            self.current_image_path = img_path
        except Exception as e: logging.error(f"Error updating pet image to {img_path}: {e}")

    def _initial_greeting(self):
        # (Unchanged)
        dom, strength, _ = self._get_dominant_emotion()
        greeting = f"哈囉！我是小星。"
        if strength >= 0.7: greeting += f" 我現在特別 {dom} 欸！"
        elif strength <= 0.3 and dom in NEGATIVE_EMOTIONS : greeting += f" 嗯...有點{dom}..."
        elif self.energy < 0.4: greeting += f" 有點想睡了..."
        elif self.boredom > 0.7: greeting += f" 好無聊喔，陪我玩啦！"
        else: greeting += f" 今天還不錯，你在幹嘛？"
        self._append(f"小星: {greeting}")

    def _on_model_change(self, selected_model):
        # (Unchanged logic, added saving selection)
        if not hasattr(self, 'api_key') or not self.api_key:
            messagebox.showerror("錯誤", "API Key 未設定，無法切換模型。")
            if hasattr(self, 'model') and self.model: self.model_var.set(self.model.model_name)
            return
        try:
            self.model = genai.GenerativeModel(model_name=selected_model)
            self.apply_llm_settings()
            self._append(f"[系統] 已切換模型：{selected_model}")
            logging.info(f"Switched model to: {selected_model}")
            # Save the selected model name
            self.settings['selected_llm_model'] = selected_model
            save_setting('selected_llm_model', selected_model) # Persist the choice (needs string conversion)
        except Exception as e:
            logging.error(f"Model switch failed: {e}")
            messagebox.showerror("錯誤", f"模型切換失敗：{e}\n可能是 API Key 無效或模型名稱錯誤。")
            if hasattr(self, 'model') and self.model: self.model_var.set(self.model.model_name)
            else: self._append("[系統] 模型切換失敗，無法設定生成模型！")


    def _clear_api_key_action(self):
        # (Unchanged)
        if messagebox.askyesno("確認", "確定要清除已儲存的 API Key 嗎？清除後需要重新輸入才能使用。"):
            if clear_api_key('gemini'):
                messagebox.showinfo("成功", "API Key 已清除。請重新啟動應用程式或重新輸入 Key。")
                self.api_key = None
                self.entry.config(state='disabled')
                if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
                self._append("[系統] API Key 已清除，請重新輸入才能對話。")
            else: messagebox.showerror("錯誤", "清除 API Key 時發生錯誤。")

    def _show_emotions(self):
        # (Unchanged)
        status_window = tk.Toplevel(self.root)
        status_window.title("小星的狀態")
        status_window.geometry("350x450")
        txt_area = scrolledtext.ScrolledText(status_window, wrap=tk.WORD, width=40, height=25)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        status_text = "--- 個性參數 ---\n"
        status_text += f"無聊度 (Boredom): {self.boredom:.2f}\n"
        status_text += f"精力 (Energy): {self.energy:.2f}\n"
        status_text += f"樂觀傾向: {self.settings.get(SETTING_OPTIMISM_TRAIT, '?'):.2f}\n"
        status_text += f"焦慮傾向: {self.settings.get(SETTING_ANXIETY_TRAIT, '?'):.2f}\n\n"
        status_text += "--- 情緒分數 (0.0 - 1.0) ---\n"
        sorted_emotions = sorted(self.emotions.items())
        if sorted_emotions:
            for name, value in sorted_emotions: status_text += f"{name}: {value:.3f}\n"
        else: status_text += "尚未載入情緒資料。\n"
        txt_area.insert(tk.INSERT, status_text)
        txt_area.config(state='disabled')
        close_button = ttk.Button(status_window, text="關閉", command=status_window.destroy)
        close_button.pack(pady=5)
        status_window.transient(self.root)
        status_window.grab_set()
        self.root.wait_window(status_window)

    def _show_memories(self):
        # (Unchanged - shows 'remembered' state memories)
        st = [content for _, content in self.short_term_tuples[-5:]] or ["無短期記憶"]
        lt = [content for _, content in self.long_term_tuples[-3:]] or ["無長期記憶"]
        msg = "短期記憶 (最新 5 筆):\n" + "\n".join(reversed(st)) + "\n\n長期記憶 (最新 3 筆):\n" + "\n".join(reversed(lt))
        # Use Toplevel for better display
        mem_window = tk.Toplevel(self.root)
        mem_window.title("小星的記憶")
        mem_window.geometry("400x300")
        txt_area = scrolledtext.ScrolledText(mem_window, wrap=tk.WORD, width=45, height=15)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        txt_area.insert(tk.INSERT, msg)
        txt_area.config(state='disabled')
        close_button = ttk.Button(mem_window, text="關閉", command=mem_window.destroy)
        close_button.pack(pady=5)
        mem_window.transient(self.root)
        mem_window.grab_set()
        self.root.wait_window(mem_window)


    def import_image(self):
        # (Unchanged)
        fp = filedialog.askopenfilename(title="選擇一張圖片作為小星的樣子", filetypes=[("圖片檔", "*.png;*.jpg;*.jpeg;*.gif"), ("所有檔案", "*.*")], initialdir=BASE_DIR)
        if fp:
            try:
                img = Image.open(fp).resize((150, 150), Image.Resampling.LANCZOS)
                p = ImageTk.PhotoImage(img)
                self.pet_label.config(image=p)
                self.pet_label.image = p # Keep reference
                self.current_image_path = fp
                logging.info(f"User imported image: {fp}")
            except Exception as e:
                logging.error(f"Failed to import image {fp}: {e}")
                messagebox.showerror("圖片錯誤", f"無法載入所選圖片：\n{e}")


    def call_llm(self, prompt, include_context=True):
        # (Unchanged logic - context building & applying settings)
        if not hasattr(self, 'model') or not self.model: return "嗯...我現在好像沒辦法思考..."
        full_prompt = prompt
        if include_context:
            dom, strength, _ = self._get_dominant_emotion()
            mood_str = f"我現在的主要感覺是 {dom} (強度 {strength:.2f})。" if strength > 0.3 else "我現在心情還算平穩。"
            # Use tuples directly for recent chats
            recent_chats_content = [f"{'你' if mem.startswith('User:') else '小星'}: {mem[6:]}"
                                    for _, mem in self.short_term_tuples[-3:]] # Get content from last 3 tuples
            memory_str = "最近聊到：" + "; ".join(recent_chats_content) if recent_chats_content else ""
            context_header = f"{CHARACTER_PROFILE}\n{mood_str}\n{memory_str}\n\n"
            full_prompt = context_header + prompt

        try:
            config = genai.types.GenerationConfig(
                temperature=float(self.settings[SETTING_LLM_TEMP]),
                top_p=0.9,
                max_output_tokens=int(self.settings[SETTING_LLM_MAX_TOKENS])
            )
            logging.debug(f"--- LLM Call (include_context={include_context}) ---\nPrompt: {full_prompt}\nConfig: {config}\n--------------------------")
            response = self.model.generate_content(full_prompt, generation_config=config)

            if hasattr(response, 'text'): return response.text.strip()
            elif hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                 logging.warning(f"LLM generation blocked: {response.prompt_feedback}")
                 block_reason = getattr(response.prompt_feedback, 'block_reason', '未知原因')
                 return f"欸...這個話題我好像不太能說耶。（原因：{block_reason}）"
            else:
                 logging.error(f"LLM generation failed with unexpected response structure: {response}")
                 return "糟糕，我好像斷線了..."
        except Exception as e:
            logging.error(f"LLM call failed: {e}")
            if "API key not valid" in str(e): return "我的能量來源（API Key）好像出問題了..."
            elif "Resource has been exhausted" in str(e): return "今天好像說太多話了，讓我休息一下下喔！"
            elif "Model service is overloaded" in str(e): return "嗚哇，現在好像太多人在找我了，請稍後再試！"
            else: return "哎呀，我的腦袋好像打結了，等一下再試試？"

    # !!--- MODIFIED FUNCTION ---!!
    def update_emotions_from_interaction(self, user_input, bot_response):
        """
        Analyzes the interaction and updates emotions based on LLM response.
        Includes conversation history in the prompt for better context.
        """
        # Get recent conversation history
        recent_chats_content = [f"{'你' if mem.startswith('User:') else '小星'}: {mem[6:]}"
                                for _, mem in self.short_term_tuples[-4:-1]] # Last 3 interactions (before current one)
        conversation_history = "\n".join(recent_chats_content)
        if conversation_history:
            conversation_history = "最近的對話紀錄：\n" + conversation_history + "\n"
        else:
            conversation_history = "這是我們對話的開始。\n"

        emotion_list_str = ", ".join(EMOTIONS.keys())
        # Show significant current emotions only
        current_emotions_str = str({k: round(v, 2) for k, v in self.emotions.items() if v > 0.1})

        # Construct the prompt with history
        prompt = f"""
分析以下使用者和你的對話，判斷你（小星）的情緒變化。
你的個性是：{CHARACTER_PROFILE}
你目前的情緒狀態（0-1分）：{current_emotions_str}

{conversation_history}
最新的對話內容：
使用者: "{user_input}"
你 (小星): "{bot_response}"

請根據**最新的對話內容**以及**之前的對話紀錄**，評估你哪些情緒應該變化，以及變化後的新分數（0.0 到 1.0 之間）。
只需專注於因這次對話**直接引起**的情緒變化。如果某情緒沒有變化，則無需包含在輸出中。
可用的情緒列表：{emotion_list_str}

請嚴格使用以下 JSON 格式回覆，只包含有變化的情緒和新分數：
{{
  "emotion_name1": new_value1,
  "emotion_name2": new_value2,
  ...
}}
確保你的回覆**只有**這個 JSON 物件，不要包含任何額外的文字或解釋。

你的 JSON 輸出："""

        # Add Logging for the exact prompt being sent
        logging.debug(f"--- Emotion Update Prompt ---\n{prompt}\n--------------------------")

        # Call LLM (pass include_context=False as context is now built into this specific prompt)
        response_text = self.call_llm(prompt, include_context=False)

        if not response_text or response_text.startswith("欸...") or response_text.startswith("糟糕") or response_text.startswith("哎呀"):
            logging.warning(f"LLM call for emotion update returned non-content or error: {response_text}")
            return # Don't proceed if LLM gave an error/refusal

        json_str = None # Initialize json_str
        try:
            # Attempt to find JSON within potential markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE) # More flexible regex
            if json_match:
                 json_str = json_match.group(1)
                 logging.debug("Found JSON in markdown block for emotion update.")
            else:
                # Fallback to finding the first '{' and last '}'
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start: # Basic validation
                    json_str = response_text[json_start:json_end]
                    logging.debug("Found JSON using find method for emotion update.")
                else:
                    # THIS IS WHERE THE ORIGINAL WARNING HAPPENS if no JSON found
                    logging.warning(f"Could not find valid JSON object in emotion update response: {response_text}")
                    return # Exit if no JSON structure found

            # Now attempt to parse the extracted json_str
            updates = json.loads(json_str)

            if isinstance(updates, dict):
                updated_count = 0
                stability = self.settings[SETTING_MOOD_STABILITY]
                sensitivity = self.settings[SETTING_EMO_SENSITIVITY]

                for name, target_value_str in updates.items():
                    if name in self.emotions:
                        try:
                            current_value = self.emotions[name]
                            target_value = max(0.0, min(1.0, float(target_value_str)))
                            raw_change = target_value - current_value
                            sensitive_change = raw_change * sensitivity
                            stable_change = sensitive_change * (1.0 - stability)
                            new_value = current_value + stable_change
                            new_value = max(0.0, min(1.0, new_value))

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
                    self._update_pet_image() # Update image only if emotions changed
            else:
                logging.warning(f"Emotion update response JSON was not a dictionary object: {updates}")

        except json.JSONDecodeError as e:
             # Log error if json.loads fails
             logging.error(f"Failed to decode JSON from emotion update: {e}\nAttempted JSON string: '{json_str}'\nFull Response: {response_text}")
        except Exception as e:
             # Catch other potential errors during processing
             logging.error(f"Error processing emotion updates: {e}\nResponse: {response_text}")
    # !!--- END MODIFIED FUNCTION ---!!


    def process_input(self, event=None):
        # (Unchanged)
        user_input = self.entry.get().strip()
        if not user_input: return

        self._append(f"你: {user_input}")
        self.entry.delete(0, tk.END)
        self.boredom = max(0, self.boredom - 0.1)
        self._update_status_labels()

        is_long_term_worthy = random.random() < 0.05
        importance = 1
        if "重要" in user_input or "記得" in user_input or "記住" in user_input:
             is_long_term_worthy = True
             importance = 5
        # Save user input to short-term memory first
        save_memory(self.user_id, f"User: {user_input}", is_long_term=False, importance=importance)
        if is_long_term_worthy:
            save_memory(self.user_id, f"User: {user_input}", is_long_term=True, importance=importance) # Also save to long term if worthy

        # Reload immediately to include user input for context
        self.reload_memory_lists()

        prompt_for_response = f"用戶說：\"{user_input}\"\n請根據你的個性、當前心情和最近的對話，用口語化的方式回應他。"
        bot_response = self.call_llm(prompt_for_response, include_context=True)

        if self.settings[SETTING_RESPONSE_DELAY_ENABLED]:
            delay_ms = random.randint(100, int(self.settings[SETTING_RESPONSE_DELAY_MAX]))
            typing_msg = "小星正在輸入..."
            self._append(typing_msg)
            self.response_delay_timer_id = self.root.after(delay_ms, lambda u=user_input, b=bot_response, t_msg=typing_msg: self._finalize_response(u, b, t_msg))
        else:
             self._finalize_response(user_input, bot_response)

    def _finalize_response(self, user_input, bot_response, typing_msg=None):
         # (Unchanged)
         if typing_msg:
              try:
                   # Simple removal: Find last line and delete if it's the typing message
                   content = self.text.get("end-2l linestart", "end-1l lineend") # Get second to last line
                   if content == typing_msg:
                        self.text.config(state='normal')
                        self.text.delete("end-2l linestart", "end-1l lineend")
                        self.text.config(state='disabled')
              except Exception as e:
                   logging.warning(f"Could not remove typing indicator: {e}")

         self._append(f"小星: {bot_response}")

         # Save bot response memory
         save_memory(self.user_id, f"小星: {bot_response}", is_long_term=False) # Bot responses usually STM

         # Reload memory again to include bot response before emotion update
         self.reload_memory_lists()

         # Update emotions based on the interaction
         self.update_emotions_from_interaction(user_input, bot_response)


    def reload_memory_lists(self):
        # (Unchanged)
        logging.debug("Reloading memory lists from database.")
        self.short_term_tuples = load_memory(self.user_id, False, limit=50) # Load recent 50 STM
        self.long_term_tuples = load_memory(self.user_id, True, limit=20) # Load recent 20 LTM
        # Keep separate lists for simpler access if needed elsewhere
        self.short_term = [content for _, content in self.short_term_tuples]
        self.long_term = [content for _, content in self.long_term_tuples]


    def _decay_emotions(self):
        # (Unchanged)
        decay_rate = self.settings[SETTING_DECAY_RATE]
        optimism = self.settings[SETTING_OPTIMISM_TRAIT]
        anxiety_p = self.settings[SETTING_ANXIETY_TRAIT]
        updated = False

        for name, value in list(self.emotions.items()):
            baseline = 0.5
            if name in ['joy', 'hope', 'optimism', 'satisfaction', 'excitement', 'gratitude', 'contentment']:
                baseline = 0.5 + (optimism - 0.5) * 0.3
            elif name in ['sadness', 'pessimism', 'disappointment', 'fear', 'anxiety', 'frustration']:
                 baseline = 0.5 - (optimism - 0.5) * 0.3
            if name in ['anxiety', 'fear', 'worry']: # Apply anxiety trait pressure
                 baseline += (anxiety_p - 0.5) * 0.2

            baseline = max(0.0, min(1.0, baseline)) # Clamp baseline

            if abs(value - baseline) > 0.01:
                new_value = value + (baseline - value) * decay_rate
                new_value = max(0.0, min(1.0, new_value))
                if abs(new_value - value) > 0.001:
                    self.emotions[name] = new_value
                    save_emotion(self.user_id, name, new_value)
                    updated = True

        if updated: self._update_pet_image()
        # Reschedule using the same interval (no need to cancel/re-add unless interval changes)
        self.decay_timer_id = self.root.after(15 * 60 * 1000, self._decay_emotions)


    def _update_needs(self):
        # (Unchanged)
        self.boredom = min(1.0, self.boredom + 0.01)
        self.energy = max(0.0, self.energy - 0.005)
        self._update_status_labels()
        self.needs_timer_id = self.root.after(5 * 60 * 1000, self._update_needs)


    def _update_status_labels(self):
        # (Unchanged)
        self.boredom_label.config(text=f"無聊度: {self.boredom:.1f}")
        self.energy_label.config(text=f"精力: {self.energy:.1f}")


    def _apply_hourly_emotion_shift(self, hour):
        # (Unchanged)
        logging.info(f"Applying hourly emotion shift for hour: {hour}")
        change_magnitude = self.settings[SETTING_TIME_SHIFT_STRENGTH]
        stability = self.settings[SETTING_MOOD_STABILITY]
        emotions_to_update = {}

        if 6 <= hour < 10: # Morning boost
            emotions_to_update['optimism'] = self.emotions.get('optimism', 0.5) + random.uniform(0, change_magnitude * 1.5)
            emotions_to_update['interest'] = self.emotions.get('interest', 0.5) + random.uniform(0, change_magnitude * 1.2)
            self.energy = min(1.0, self.energy + 0.1)
        elif 12 <= hour < 14: # Post-lunch dip?
             emotions_to_update['calmness'] = self.emotions.get('calmness', 0.5) + random.uniform(0, change_magnitude * 0.5)
             self.energy = max(0.0, self.energy - 0.03)
        elif 19 <= hour < 23: # Evening calm/nostalgia
            emotions_to_update['calmness'] = self.emotions.get('calmness', 0.5) + random.uniform(0, change_magnitude)
            emotions_to_update['nostalgia'] = self.emotions.get('nostalgia', 0.5) + random.uniform(0, change_magnitude * 0.5)
        elif 23 <= hour or hour < 5: # Late night sleepiness/boredom
            emotions_to_update['boredom'] = self.emotions.get('boredom', 0.5) + random.uniform(0, change_magnitude * 1.2)
            self.boredom = min(1.0, self.boredom + 0.03)
            self.energy = max(0.0, self.energy - 0.08)

        # General random shifts
        for _ in range(random.randint(1, 3)):
             emo_name = random.choice(list(EMOTIONS.keys()))
             change = random.uniform(-change_magnitude, change_magnitude)
             emotions_to_update[emo_name] = self.emotions.get(emo_name, 0.5) + change

        updated_count = 0
        if emotions_to_update:
            for name, target_value in emotions_to_update.items():
                 if name in self.emotions:
                     current_value = self.emotions[name]
                     raw_change = target_value - current_value
                     stable_change = raw_change * (1.0 - stability) # Apply stability
                     new_value = current_value + stable_change
                     new_value = max(0.0, min(1.0, new_value)) # Clamp

                     if abs(new_value - current_value) > 0.005:
                         self.emotions[name] = new_value
                         save_emotion(self.user_id, name, new_value)
                         updated_count +=1
            if updated_count > 0:
                 logging.info(f"Applied {updated_count} time-based emotion shifts (considering stability).")
                 self._update_pet_image()
                 self._update_status_labels()


    def _hourly_time_check(self, run_immediately=False):
        # (Unchanged logic, improved logging)
        now = time.time()
        current_hour = datetime.now().hour
        hour_in_seconds = 60 * 60
        time_since_last_shift = now - self.last_hourly_shift_time

        # Apply shift if an hour passed OR first run
        if time_since_last_shift >= hour_in_seconds or (run_immediately and self.last_hourly_shift_time == 0):
            logging.info("Performing hourly time check actions.")
            self._apply_hourly_emotion_shift(current_hour)
            self.last_hourly_shift_time = now
            save_setting('last_hourly_shift_time', now)
        # else: logging.debug(f"Hourly check skipped: {time_since_last_shift/60:.1f} minutes since last shift.")

        # Schedule the next check (always schedule, even if skipped this time)
        if hasattr(self, 'hourly_timer_id') and self.hourly_timer_id:
             try: self.root.after_cancel(self.hourly_timer_id)
             except tk.TclError: pass
        next_check_delay_ms = hour_in_seconds * 1000
        self.hourly_timer_id = self.root.after(next_check_delay_ms, self._hourly_time_check)
        # logging.debug(f"Scheduled next hourly check in {next_check_delay_ms / 1000 / 60:.1f} minutes.")


    def _proactive(self):
        # (Unchanged logic, slightly refined prompts)
        dom, strength, _ = self._get_dominant_emotion()
        threshold = 0.65
        possible_actions = []

        if strength > threshold:
             if dom in POSITIVE_EMOTIONS: possible_actions.append(f"我現在超 {dom} 的啦！({strength:.1f}) 你最近有什麼開心的事嗎，跟我分享一下嘛～")
             elif dom in NEGATIVE_EMOTIONS: possible_actions.append(f"嗯...現在心情有點 {dom} ({strength:.1f})，怪怪的...")
             else: possible_actions.append(f"我現在對某件事超級 {dom} ({strength:.1f})！好好奇喔！")
        if self.boredom > 0.85: possible_actions.append("真的好無聊喔～～～ 我們來聊點什麼啦？")
        if self.energy < 0.25: possible_actions.append("我不行了... (趴) 好想睡...晚點再吵你？")
        # Recall memory based on setting
        if self.long_term_tuples and random.random() < self.settings[SETTING_RECALL_CHANCE] * 20: # Increase recall chance for proactive chat
            memory_id, memory_item = random.choice(self.long_term_tuples)
            if memory_item.startswith("User:") and len(memory_item) > 15:
                 topic = memory_item[6:35].strip().replace("\n", " ")
                 possible_actions.append(f"欸～我突然想到，你之前是不是說過「{topic}...」？後來怎麼了？")
            elif memory_item.startswith("小星:") and len(memory_item) > 15:
                 topic = memory_item[4:35].strip().replace("\n", " ")
                 possible_actions.append(f"我記得我之前好像跟你說過「{topic}...」對吧？你覺得呢？")

        possible_actions.extend(["嗨！突然想找你聊聊～","在嗎在嗎？最近怎麼樣啊？","（探頭）你在幹嘛？"])
        if not possible_actions: possible_actions.append("嗯？") # Simple fallback

        chosen_action_prompt = random.choice(possible_actions)
        final_utterance = self.call_llm(f"你想要主動跟使用者說話，你想表達的大意是：「{chosen_action_prompt}」。請用自然的口氣說出來。", include_context=True)
        self._append(f"小星 (主動): {final_utterance}")

        self.boredom = max(0, self.boredom - 0.2)
        self._update_status_labels()

        # Reschedule based on settings
        freq_index = self.settings[SETTING_PROACTIVE_FREQ]
        intervals = [(5*60, 15*60), (10*60, 25*60), (20*60, 40*60), (-1, -1)]
        min_delay, max_delay = intervals[freq_index] if 0 <= freq_index < len(intervals) else intervals[1]

        if min_delay > 0:
             next_proactive_ms = random.randint(min_delay * 1000, max_delay * 1000)
             if hasattr(self, 'proactive_timer_id') and self.proactive_timer_id:
                  try: self.root.after_cancel(self.proactive_timer_id)
                  except tk.TclError: pass
             self.proactive_timer_id = self.root.after(next_proactive_ms, self._proactive)
             logging.info(f"Rescheduled proactive task after proactive event in {next_proactive_ms/1000:.0f}s")


    def _cleanup(self):
        # (Unchanged)
        retention_days = self.settings[SETTING_STM_RETENTION_DAYS]
        clean_short_term_memory(retention_days)
        if hasattr(self, 'cleanup_timer_id') and self.cleanup_timer_id:
             try: self.root.after_cancel(self.cleanup_timer_id)
             except tk.TclError: pass
        self.cleanup_timer_id = self.root.after(24 * 60 * 60 * 1000, self._cleanup)


    def _process_memory_forgetting(self):
        # (Unchanged)
        logging.debug("Processing memory forgetting/recalling.")
        forget_chance = self.settings[SETTING_FORGET_CHANCE]
        recall_chance = self.settings[SETTING_RECALL_CHANCE]
        forgotten_count = 0
        recalled_count = 0

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # Forget STM
                c.execute("SELECT id FROM short_term_memory WHERE status='remembered' ORDER BY RANDOM() LIMIT 20")
                st_ids_to_consider = [row[0] for row in c.fetchall()]
                for mem_id in st_ids_to_consider:
                    if random.random() < forget_chance:
                        c.execute("UPDATE short_term_memory SET status='forgotten' WHERE id=?", (mem_id,))
                        forgotten_count += 1
                # Forget LTM (lower chance implicitly by lower limit)
                c.execute("SELECT id FROM long_term_memory WHERE status='remembered' ORDER BY RANDOM() LIMIT 10")
                lt_ids_to_consider = [row[0] for row in c.fetchall()]
                for mem_id in lt_ids_to_consider:
                     if random.random() < forget_chance * 0.5: # Make LTM forgetting harder
                        c.execute("UPDATE long_term_memory SET status='forgotten' WHERE id=?", (mem_id,))
                        forgotten_count += 1

                # Recall STM
                c.execute("SELECT id FROM short_term_memory WHERE status='forgotten' ORDER BY RANDOM() LIMIT 10")
                st_ids_to_recall = [row[0] for row in c.fetchall()]
                for mem_id in st_ids_to_recall:
                     if random.random() < recall_chance:
                        c.execute("UPDATE short_term_memory SET status='remembered' WHERE id=?", (mem_id,))
                        recalled_count += 1
                # Recall LTM
                c.execute("SELECT id FROM long_term_memory WHERE status='forgotten' ORDER BY RANDOM() LIMIT 5")
                lt_ids_to_recall = [row[0] for row in c.fetchall()]
                for mem_id in lt_ids_to_recall:
                     if random.random() < recall_chance * 1.5: # Make LTM recall slightly easier
                        c.execute("UPDATE long_term_memory SET status='remembered' WHERE id=?", (mem_id,))
                        recalled_count += 1

                conn.commit()
                if forgotten_count > 0: logging.info(f"Forgot {forgotten_count} memories.")
                if recalled_count > 0: logging.info(f"Recalled {recalled_count} memories.")
                if forgotten_count > 0 or recalled_count > 0: self.reload_memory_lists() # Reload if changes occurred
        except sqlite3.Error as e: logging.error(f"Error during memory forgetting process: {e}")

        # Reschedule
        if hasattr(self, 'forgetting_timer_id') and self.forgetting_timer_id:
             try: self.root.after_cancel(self.forgetting_timer_id)
             except tk.TclError: pass
        self.forgetting_timer_id = self.root.after(6 * 60 * 60 * 1000, self._process_memory_forgetting)


    def _schedule_tasks(self):
        # (Unchanged)
        self._reschedule_tasks_from_settings()


    def _append(self, text):
        # (Unchanged)
        try:
            self.text.config(state='normal')
            self.text.insert(tk.END, text + "\n")
            self.text.config(state='disabled')
            self.text.see(tk.END)
        except tk.TclError as e: logging.warning(f"Failed to append text, window might be closing: {e}")
        except Exception as e: logging.error(f"Error appending text: {e}")


    def on_close(self):
        # (Unchanged)
        logging.info("Closing application...")
        self._cancel_timers()
        # Save last hourly shift time one last time? (optional)
        # save_setting('last_hourly_shift_time', self.last_hourly_shift_time)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        available_themes = style.theme_names()
        logging.info(f"Available ttk themes: {available_themes}")
        # Prefer OS-native themes
        if 'vista' in available_themes: style.theme_use('vista') # Windows
        elif 'aqua' in available_themes: style.theme_use('aqua') # macOS
        elif 'clam' in available_themes: style.theme_use('clam') # Good Linux fallback
        else: style.theme_use('default')
    except tk.TclError:
         logging.warning("Could not set ttk theme.")

    root.minsize(350, 450)
    app = PetApp(root)
    # Check if API key setup was successful before starting mainloop
    if hasattr(app, 'api_key') and app.api_key:
         root.protocol("WM_DELETE_WINDOW", app.on_close)
         root.mainloop()
    else:
         logging.error("Application failed to initialize completely (likely API key issue). Exiting.")
         # Optional: Show a final error message box before quit if root exists
         if root.winfo_exists():
              messagebox.showerror("啟動失敗", "應用程式無法完成初始化，可能是 API Key 設定問題。請檢查日誌檔。")
              root.destroy()
