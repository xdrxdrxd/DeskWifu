import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk # Added ttk
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

# --- 日誌設定 ---
# (Unchanged)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- 檔案路徑設定 & 圖片處理 ---
# (Unchanged)
# ... (BASE_DIR, DB_PATH, DEFAULT_IMG_PATH, EMOTION_IMAGES handling) ...
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
if not os.path.exists(DEFAULT_IMG_PATH):
    try:
        happy_path = EMOTION_IMAGES.get("happy")
        if happy_path and os.path.exists(happy_path):
            import shutil
            shutil.copy(happy_path, DEFAULT_IMG_PATH)
            logging.info("Default image not found, copied from happy.png")
        else:
            img = Image.new('RGB', (100, 100), color = 'grey')
            img.save(DEFAULT_IMG_PATH)
            logging.info("Default image not found, created a placeholder.")
    except Exception as e:
        logging.error(f"Error handling missing default image: {e}")

# --- 情緒參數 ---
# (Unchanged)
# ... (EMOTIONS, POSITIVE_EMOTIONS, NEGATIVE_EMOTIONS) ...
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
# Define keys for settings to avoid typos
SETTING_MOOD_STABILITY = 'mood_stability'
SETTING_OPTIMISM_TRAIT = 'optimism_trait'
SETTING_ANXIETY_TRAIT = 'anxiety_trait'
SETTING_EMO_SENSITIVITY = 'emo_sensitivity' # New: General sensitivity multiplier
SETTING_DECAY_RATE = 'decay_rate'
SETTING_TIME_SHIFT_STRENGTH = 'time_shift_strength'
SETTING_PROACTIVE_FREQ = 'proactive_freq' # Store index: 0=High, 1=Mid, 2=Low, 3=Off
SETTING_RESPONSE_DELAY_ENABLED = 'response_delay_enabled' # 0 or 1
SETTING_RESPONSE_DELAY_MAX = 'response_delay_max_ms'
SETTING_FORGET_CHANCE = 'forget_chance'
SETTING_RECALL_CHANCE = 'recall_chance'
SETTING_LLM_TEMP = 'llm_temperature'
SETTING_LLM_MAX_TOKENS = 'llm_max_tokens'
SETTING_STM_RETENTION_DAYS = 'stm_retention_days'
# Add more setting keys here...

DEFAULT_SETTINGS = {
    SETTING_MOOD_STABILITY: 0.3, # 0=Volatile, 1=Very Stable
    SETTING_OPTIMISM_TRAIT: 0.5, # 0=Pessimistic, 1=Optimistic
    SETTING_ANXIETY_TRAIT: 0.5, # 0=Calm, 1=Anxious Prone
    SETTING_EMO_SENSITIVITY: 1.0, # Multiplier for LLM emotion changes
    SETTING_DECAY_RATE: 0.02,
    SETTING_TIME_SHIFT_STRENGTH: 0.05,
    SETTING_PROACTIVE_FREQ: 1, # Index for '普通'
    SETTING_RESPONSE_DELAY_ENABLED: 1, # Enabled by default
    SETTING_RESPONSE_DELAY_MAX: 1200, # Max delay in ms
    SETTING_FORGET_CHANCE: 0.03,
    SETTING_RECALL_CHANCE: 0.01,
    SETTING_LLM_TEMP: 0.75,
    SETTING_LLM_MAX_TOKENS: 150,
    SETTING_STM_RETENTION_DAYS: 30,
}

# --- 資料庫輔助 & 初始化 ---
# (column_exists unchanged)
def column_exists(cursor, table_name, column_name):
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        return column_name in columns
    except sqlite3.Error as e:
        logging.error(f"Error checking column {column_name} in {table_name}: {e}")
        return False

# (init_db unchanged from previous version - already creates app_state and adds status column)
# ... init_db ...
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            tables = {
                'emotions': '''CREATE TABLE IF NOT EXISTS emotions (user_id TEXT, emotion_name TEXT, value REAL, last_updated REAL, PRIMARY KEY (user_id, emotion_name))''',
                'short_term_memory': '''CREATE TABLE IF NOT EXISTS short_term_memory (id TEXT PRIMARY KEY, user_id TEXT, content TEXT, timestamp REAL, importance INTEGER, status TEXT DEFAULT 'remembered')''',
                'long_term_memory': '''CREATE TABLE IF NOT EXISTS long_term_memory (id TEXT PRIMARY KEY, user_id TEXT, content TEXT, timestamp REAL, importance INTEGER, status TEXT DEFAULT 'remembered')''',
                'api_keys': '''CREATE TABLE IF NOT EXISTS api_keys (id TEXT PRIMARY KEY, key_name TEXT UNIQUE, key_value TEXT)''',
                'app_state': '''CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value REAL)''' # Using REAL for flexibility (can store numbers)
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
# ... CHARACTER_PROFILE ...
CHARACTER_PROFILE = (
    "你是一個名叫小星的桌寵，個性多變（活潑、好奇、溫暖、敏感、低落等），要假裝自己不是AI，絕對不要把情緒分數或個性分數顯示出來。"
    "說話時請融入台灣年輕人常用的口頭禪，例如「好喔」、「欸」、「煩欸」、「真的假的」、「對啊」、「屁啦」、「超好笑」、「好扯」、「啦」、「喔」、「啊」等等，"
    "但不強制任何詞語開頭，自然流暢即可。你的回應應該簡短、口語化、像朋友聊天。"
    "如果你的名子叫小星，那就要詢問是否改名，改完後存入長期記憶"
)

# --- API 金鑰管理 ---
# (Unchanged)
# ... get_api_key, set_api_key, clear_api_key ...
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
# Modified save/load to use string keys directly
def save_setting(key, value):
    """Saves a setting value to the app_state table."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # Store as REAL, client code needs to handle type conversion if needed
            c.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, float(value)))
            conn.commit()
            # logging.debug(f"Saved setting: {key} = {value}")
    except (sqlite3.Error, ValueError) as e: # Catch potential float conversion error
        logging.error(f"Failed to save setting '{key}' with value '{value}': {e}")

def load_setting(key, default_value):
    """Loads a setting value from the app_state table."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT value FROM app_state WHERE key=?", (key,))
            row = c.fetchone()
            # Value is stored as REAL, return as float
            return float(row[0]) if row else default_value
    except sqlite3.Error as e:
        logging.error(f"Failed to load setting '{key}': {e}")
        return default_value


# --- 記憶與情緒儲存與載入 ---
# (save_emotion, load_emotions, save_memory, load_memory, clean_short_term_memory unchanged from previous response)
# ... save_emotion ...
def save_emotion(user_id, emotion_name, value):
    value = max(0.0, min(1.0, float(value)))
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO emotions (user_id, emotion_name, value, last_updated) VALUES (?, ?, ?, ?)",(user_id, emotion_name, value, time.time()))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save emotion for user {user_id}: {e}")

# ... load_emotions ...
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

# ... save_memory ...
def save_memory(user_id, content, is_long_term=False, importance=1):
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"INSERT INTO {table} (id, user_id, content, timestamp, importance) VALUES (?, ?, ?, ?, ?)",(str(uuid.uuid4()), user_id, content, time.time(), importance))
            conn.commit()
    except sqlite3.Error as e: logging.error(f"Failed to save memory for user {user_id}: {e}")

# ... load_memory ...
def load_memory(user_id, is_long_term=False, limit=50):
    table = 'long_term_memory' if is_long_term else 'short_term_memory'
    memories = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute(f"SELECT id, content FROM {table} WHERE user_id=? AND status='remembered' ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
            memories = c.fetchall()[::-1]
    except sqlite3.Error as e: logging.error(f"Failed to load memory for user {user_id}: {e}")
    return memories # Returns list of (id, content)

# ... clean_short_term_memory ...
# (Now uses setting for retention days)
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


# --- 設定視窗類別 ---
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
        self.transient(parent.root)
        self.grab_set()
        self.wait_window(self)

    def _create_settings_widgets(self):
        """Creates all the labels and input widgets for settings."""
        frame = self.scrollable_frame # Add widgets to this frame

        # --- Personality Traits ---
        trait_frame = ttk.LabelFrame(frame, text="個性特質")
        trait_frame.pack(fill=tk.X, padx=10, pady=5)

        self.setting_vars[SETTING_OPTIMISM_TRAIT] = tk.DoubleVar()
        ttk.Label(trait_frame, text="樂觀傾向 (0悲觀-1樂觀):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(trait_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_OPTIMISM_TRAIT]).grid(row=0, column=1, sticky="ew", padx=5)

        self.setting_vars[SETTING_ANXIETY_TRAIT] = tk.DoubleVar()
        ttk.Label(trait_frame, text="焦慮傾向 (0冷靜-1易焦慮):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        ttk.Scale(trait_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=200, variable=self.setting_vars[SETTING_ANXIETY_TRAIT]).grid(row=1, column=1, sticky="ew", padx=5)
        # Add more trait sliders if implemented...

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
        ttk.Combobox(behav_frame, textvariable=self.setting_vars[SETTING_PROACTIVE_FREQ], values=freq_options, state="readonly", width=15).grid(row=0, column=1, sticky="w", padx=5) # Use index later

        self.setting_vars[SETTING_RESPONSE_DELAY_ENABLED] = tk.IntVar() # 0 or 1
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
        """Loads current app settings into the UI widgets."""
        logging.debug("Loading settings into Settings UI.")
        for key, var in self.setting_vars.items():
            value = self.app_settings.get(key) # Get value from parent app's settings
            if value is not None:
                 # Handle Combobox case specifically (needs index)
                 if key == SETTING_PROACTIVE_FREQ:
                      # Find the index corresponding to the stored value (which is the index itself)
                      # Combobox uses 0-based index internally when setting via variable
                      try:
                          var.set(int(value)) # Set the index
                      except (ValueError, TypeError):
                          var.set(1) # Default to index 1 ('普通') on error
                 else:
                     try:
                        # Set other variables directly
                        var.set(value)
                     except Exception as e:
                         logging.error(f"Error setting UI for {key} with value {value}: {e}")
            else:
                 logging.warning(f"Setting key {key} not found in app settings during UI load.")


    def _save_settings(self):
        """Saves settings from UI widgets back to app and database."""
        logging.info("Saving settings from Settings UI.")
        try:
            temp_settings = {}
            for key, var in self.setting_vars.items():
                value = var.get()
                # Handle Combobox for frequency (store index)
                if key == SETTING_PROACTIVE_FREQ:
                    freq_options = ["頻繁 (5-15分)", "普通 (10-25分)", "偶爾 (20-40分)", "從不"]
                    try:
                        # Get the selected string and find its index
                        selected_string = value # In Tkinter 8.6+, Combobox var might hold the value directly if editable
                        # If bound to IntVar, value is already the index or string index? Let's assume index for readonly
                        temp_settings[key] = int(value) # Store the index (0, 1, 2, 3)
                    except ValueError:
                         # Fallback if value isn't an integer index directly
                         try:
                             temp_settings[key] = freq_options.index(str(value))
                         except ValueError:
                             logging.warning(f"Could not find index for proactive frequency value: {value}. Defaulting.")
                             temp_settings[key] = 1 # Default to index 1
                elif key == SETTING_RESPONSE_DELAY_ENABLED:
                     temp_settings[key] = int(value) # Ensure 0 or 1
                elif key in [SETTING_RESPONSE_DELAY_MAX, SETTING_LLM_MAX_TOKENS, SETTING_STM_RETENTION_DAYS]:
                    temp_settings[key] = int(value) # Ensure integer
                else:
                    temp_settings[key] = float(value) # Assume float for others (Scales)

            # Update parent app's settings immediately
            self.parent.settings.update(temp_settings)

            # Persist settings to DB
            for key, value in temp_settings.items():
                save_setting(key, value)

            # Notify parent app that settings might have changed
            self.parent.apply_settings_changes()

            messagebox.showinfo("成功", "設定已儲存！", parent=self) # Show message on top of settings window
            self.destroy() # Close window after saving

        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤：\n{e}", parent=self)


# --- 主程式類別 ---
class PetApp:
    def __init__(self, root):
        # ... (initial setup unchanged) ...
        self.root = root
        self.root.title("小星桌寵")
        self.user_id = simpledialog.askstring("用戶ID", "請輸入您的用戶ID：", initialvalue="default_user")
        if not self.user_id: self.user_id = "default_user"

        self.boredom = 0.5
        self.energy = 0.8
        self.last_hourly_shift_time = 0

        # --- Load Settings ---
        self.settings = self._load_all_settings() # Load settings initially

        init_db()
        self.model_var = tk.StringVar(value="gemini-1.5-flash")
        self._ensure_api_key()

        if hasattr(self, 'api_key') and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Configure model using loaded settings if available
                self.model = genai.GenerativeModel(model_name=self.model_var.get()) # Initial config
                self.apply_llm_settings() # Apply temp/tokens immediately
                logging.info(f"Gemini model '{self.model_var.get()}' configured.")
            except Exception as e:
                logging.error(f"Failed to configure Gemini: {e}")
                messagebox.showerror("API 錯誤", f"無法設定 Gemini 模型：{e}\n請檢查您的 API Key 或網路連線。")
                self.root.quit()
                return

            self.last_hourly_shift_time = load_setting('last_hourly_shift_time', 0) # Load specific state
            logging.info(f"Loaded last hourly shift time: {self.last_hourly_shift_time}")

            self.emotions = load_emotions(self.user_id)
            self.reload_memory_lists() # Load initial memories

            self._build_ui()
            self._update_pet_image()
            self._initial_greeting()
            self._schedule_tasks()

            self._hourly_time_check(run_immediately=True) # Apply initial hourly check/catchup

        else:
            logging.warning("API Key not available. Exiting.")
            self.root.quit()

    def _load_all_settings(self):
        """Loads all settings from DB or uses defaults."""
        settings = {}
        for key, default_value in DEFAULT_SETTINGS.items():
            settings[key] = load_setting(key, default_value)
        logging.info("Loaded application settings.")
        # Ensure correct types after loading (DB stores REAL)
        settings[SETTING_PROACTIVE_FREQ] = int(settings.get(SETTING_PROACTIVE_FREQ, DEFAULT_SETTINGS[SETTING_PROACTIVE_FREQ]))
        settings[SETTING_RESPONSE_DELAY_ENABLED] = int(settings.get(SETTING_RESPONSE_DELAY_ENABLED, DEFAULT_SETTINGS[SETTING_RESPONSE_DELAY_ENABLED]))
        settings[SETTING_RESPONSE_DELAY_MAX] = int(settings.get(SETTING_RESPONSE_DELAY_MAX, DEFAULT_SETTINGS[SETTING_RESPONSE_DELAY_MAX]))
        settings[SETTING_LLM_MAX_TOKENS] = int(settings.get(SETTING_LLM_MAX_TOKENS, DEFAULT_SETTINGS[SETTING_LLM_MAX_TOKENS]))
        settings[SETTING_STM_RETENTION_DAYS] = int(settings.get(SETTING_STM_RETENTION_DAYS, DEFAULT_SETTINGS[SETTING_STM_RETENTION_DAYS]))
        return settings

    def apply_llm_settings(self):
         """Applies LLM temperature and max tokens to the generation config."""
         # Note: google-generativeai might not allow changing config after model creation easily.
         # Re-creating the model might be needed, or check if config can be passed per-call.
         # For now, we'll update the config used in call_llm.
         logging.info(f"Applying LLM settings: Temp={self.settings[SETTING_LLM_TEMP]}, MaxTokens={self.settings[SETTING_LLM_MAX_TOKENS]}")
         # This doesn't reconfigure the core model object, but updates the config used in generate_content

    def apply_settings_changes(self):
        """Called after settings are saved to apply immediate changes."""
        logging.info("Applying settings changes...")
        self.apply_llm_settings() # Update LLM parameters used in calls

        # --- Reschedule tasks with potentially new frequencies/parameters ---
        # Cancel existing timers before rescheduling
        self._cancel_timers()
        self._reschedule_tasks_from_settings() # Reschedule with new intervals/logic

        # Apply changes that affect ongoing calculations immediately if needed
        # e.g., if decay rate changed, the next _decay_emotions will use the new rate.

        logging.info("Settings changes applied and tasks rescheduled.")

    def _cancel_timers(self):
        """Cancel all scheduled 'after' tasks."""
        logging.debug("Cancelling scheduled timers...")
        timers = ['proactive_timer_id', 'decay_timer_id', 'needs_timer_id',
                  'cleanup_timer_id', 'forgetting_timer_id', 'hourly_timer_id',
                  'response_delay_timer_id'] # Add any other timers
        for timer_attr in timers:
             if hasattr(self, timer_attr):
                 timer_id = getattr(self, timer_attr, None)
                 if timer_id:
                     try:
                         self.root.after_cancel(timer_id)
                         setattr(self, timer_attr, None) # Clear the ID
                         # logging.debug(f"Cancelled timer: {timer_attr}")
                     except tk.TclError:
                          pass # May already be cancelled or invalid

    def _reschedule_tasks_from_settings(self):
         """Reschedules tasks based on current settings."""
         logging.debug("Rescheduling tasks based on settings...")

         # --- Proactive Chat ---
         freq_index = self.settings[SETTING_PROACTIVE_FREQ]
         if freq_index == 0: # High
              min_delay, max_delay = 5*60, 15*60
         elif freq_index == 1: # Mid
              min_delay, max_delay = 10*60, 25*60
         elif freq_index == 2: # Low
              min_delay, max_delay = 20*60, 40*60
         else: # Off
              min_delay, max_delay = -1, -1

         if min_delay > 0:
              next_proactive_ms = random.randint(min_delay * 1000, max_delay * 1000)
              self.proactive_timer_id = self.root.after(next_proactive_ms, self._proactive)
              logging.info(f"Rescheduled proactive task in {next_proactive_ms/1000:.0f}s")
         else:
              logging.info("Proactive task disabled by settings.")

         # --- Other tasks (use fixed intervals for now, could be made configurable) ---
         decay_interval_ms = 15 * 60 * 1000
         needs_interval_ms = 5 * 60 * 1000
         cleanup_interval_ms = 24 * 60 * 60 * 1000
         forgetting_interval_ms = 6 * 60 * 60 * 1000
         hourly_interval_ms = 60 * 60 * 1000

         self.decay_timer_id = self.root.after(decay_interval_ms, self._decay_emotions)
         self.needs_timer_id = self.root.after(needs_interval_ms, self._update_needs)
         # Pass retention days setting to cleanup function
         self.cleanup_timer_id = self.root.after(cleanup_interval_ms, lambda: clean_short_term_memory(self.settings[SETTING_STM_RETENTION_DAYS]))
         self.forgetting_timer_id = self.root.after(forgetting_interval_ms, self._process_memory_forgetting)
         self.hourly_timer_id = self.root.after(hourly_interval_ms, self._hourly_time_check)


    # ... _ensure_api_key (unchanged) ...
    def _ensure_api_key(self):
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

    # Modified _build_ui to add Settings menu
    def _build_ui(self):
        # ... (image, model select, text, entry, status labels - unchanged) ...
        # --- Image Display ---
        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(pady=10)
        self.pet_label = tk.Label(self.image_frame)
        self.pet_label.pack()
        try:
            img = Image.open(DEFAULT_IMG_PATH).resize((150,150), Image.Resampling.LANCZOS)
            self.pet_photo = ImageTk.PhotoImage(img)
            self.pet_label.config(image=self.pet_photo)
            self.current_image_path = DEFAULT_IMG_PATH # Initialize path tracking
        except Exception as e:
            # ... error handling ...
            logging.error(f"Error loading default image: {e}")
            self.pet_label.config(text="[圖片錯誤]", width=20, height=10)


        # --- Model Selection ---
        model_frame = tk.Frame(self.root)
        model_frame.pack(pady=5, fill=tk.X, padx=10)
        tk.Label(model_frame, text="選擇模型：").pack(side=tk.LEFT)
        opts = ["gemini-1.5-flash", "gemini-1.5-pro-latest", "gemini-1.0-pro"]
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
        # File menu
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="匯入圖片...", command=self.import_image)
        file_menu.add_command(label="開啟設定...", command=self.open_settings_window) # New Settings item
        file_menu.add_command(label="清除 API Key...", command=self._clear_api_key_action)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_close) # Use on_close for proper exit
        # Status menu
        status_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="狀態", menu=status_menu)
        status_menu.add_command(label="查看狀態", command=self._show_emotions)
        status_menu.add_command(label="查看記憶", command=self._show_memories)

    def open_settings_window(self):
         """Opens the settings window."""
         SettingsWindow(self.root, self.settings) # Pass self and current settings

    # ... (_get_dominant_emotion, _update_pet_image, _initial_greeting, _on_model_change, _clear_api_key_action, _show_emotions, _show_memories, import_image - mostly unchanged) ...
    # (Definition functions remain largely the same, but their *behavior* is now influenced by self.settings)
    def _get_dominant_emotion(self):
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
        _, _, visual_mood = self._get_dominant_emotion()
        img_path = EMOTION_IMAGES.get(visual_mood, DEFAULT_IMG_PATH)
        if not os.path.exists(img_path): img_path = DEFAULT_IMG_PATH
        try:
            # Prevent unnecessary reloading if image path hasn't changed
            current_path = getattr(self, 'current_image_path', None)
            if current_path == img_path: return

            img = Image.open(img_path).resize((150, 150), Image.Resampling.LANCZOS)
            self.pet_photo = ImageTk.PhotoImage(img)
            self.pet_label.config(image=self.pet_photo)
            self.current_image_path = img_path # Update tracked path
        except Exception as e: logging.error(f"Error updating pet image to {img_path}: {e}") # Handle errors gracefully

    def _initial_greeting(self):
        dom, strength, _ = self._get_dominant_emotion()
        greeting = f"哈囉！我是小星。"
        if strength >= 0.7: greeting += f" 我現在特別 {dom} 欸！"
        elif strength <= 0.3 and dom in NEGATIVE_EMOTIONS : greeting += f" 嗯...有點{dom}..."
        elif self.energy < 0.4: greeting += f" 有點想睡了..."
        elif self.boredom > 0.7: greeting += f" 好無聊喔，陪我玩啦！"
        else: greeting += f" 今天還不錯，你在幹嘛？"
        self._append(f"小星: {greeting}")

    def _on_model_change(self, selected_model):
        # ... (unchanged) ...
        if not hasattr(self, 'api_key') or not self.api_key:
            messagebox.showerror("錯誤", "API Key 未設定，無法切換模型。")
            if hasattr(self, 'model') and self.model: self.model_var.set(self.model.model_name)
            return
        try:
            self.model = genai.GenerativeModel(model_name=selected_model)
            self.apply_llm_settings() # Re-apply temp/tokens if model changes
            self._append(f"[系統] 已切換模型：{selected_model}")
            logging.info(f"Switched model to: {selected_model}")
        except Exception as e:
            logging.error(f"Model switch failed: {e}")
            messagebox.showerror("錯誤", f"模型切換失敗：{e}\n可能是 API Key 無效或模型名稱錯誤。")
            if hasattr(self, 'model') and self.model: self.model_var.set(self.model.model_name)
            else: self._append("[系統] 模型切換失敗，無法設定生成模型！")


    def _clear_api_key_action(self):
        # ... (unchanged) ...
        if messagebox.askyesno("確認", "確定要清除已儲存的 API Key 嗎？清除後需要重新輸入才能使用。"):
            if clear_api_key('gemini'):
                messagebox.showinfo("成功", "API Key 已清除。請重新啟動應用程式或重新輸入 Key。")
                self.api_key = None
                self.entry.config(state='disabled')
                if hasattr(self, 'model_option_menu'): self.model_option_menu.config(state='disabled')
                self._append("[系統] API Key 已清除，請重新輸入才能對話。")
            else: messagebox.showerror("錯誤", "清除 API Key 時發生錯誤。")

    # Uses Toplevel window now
    def _show_emotions(self):
        status_window = tk.Toplevel(self.root)
        status_window.title("小星的狀態")
        status_window.geometry("350x450")
        txt_area = scrolledtext.ScrolledText(status_window, wrap=tk.WORD, width=40, height=25)
        txt_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        status_text = "--- 個性參數 ---\n"
        status_text += f"無聊度 (Boredom): {self.boredom:.2f}\n"
        status_text += f"精力 (Energy): {self.energy:.2f}\n"
        # Add trait display from settings
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
        # ... (unchanged - shows remembered) ...
        st = self.short_term[-5:] or ["無短期記憶"]
        lt = self.long_term[-3:] or ["無長期記憶"]
        msg = "短期記憶 (最新):\n" + "\n".join(reversed(st)) + "\n\n長期記憶 (最新):\n" + "\n".join(reversed(lt))
        messagebox.showinfo("小星的記憶", msg)

    def import_image(self):
        # ... (unchanged) ...
        fp = filedialog.askopenfilename(title="選擇一張圖片作為小星的樣子", filetypes=[("圖片檔", "*.png;*.jpg;*.jpeg;*.gif"), ("所有檔案", "*.*")], initialdir=BASE_DIR)
        if fp:
            try:
                img = Image.open(fp).resize((150, 150), Image.Resampling.LANCZOS)
                p = ImageTk.PhotoImage(img)
                self.pet_label.config(image=p)
                # self.pet_label.image = p # Keep reference
                self.current_image_path = fp
                logging.info(f"User imported image: {fp}")
            except Exception as e:
                logging.error(f"Failed to import image {fp}: {e}")
                messagebox.showerror("圖片錯誤", f"無法載入所選圖片：\n{e}")

    # Modified call_llm to use settings
    def call_llm(self, prompt, include_context=True):
        # ... (context building unchanged - uses self.short_term_tuples) ...
        if not hasattr(self, 'model') or not self.model: return "嗯...我現在好像沒辦法思考..."
        full_prompt = prompt
        if include_context:
            dom, strength, _ = self._get_dominant_emotion()
            mood_str = f"我現在的主要感覺是 {dom} (強度 {strength:.2f})。" if strength > 0.3 else "我現在心情還算平穩。"
            recent_chats_content = [content for _, content in self.short_term_tuples[-3:]]
            memory_str = "最近聊到：" + "; ".join(recent_chats_content) if recent_chats_content else ""
            context_header = f"{CHARACTER_PROFILE}\n{mood_str}\n{memory_str}\n\n"
            full_prompt = context_header + prompt

        try:
            # Use settings for temperature and max_tokens
            config = genai.types.GenerationConfig(
                temperature=float(self.settings[SETTING_LLM_TEMP]),
                top_p=0.9, # Keep top_p fixed for now, could be setting
                max_output_tokens=int(self.settings[SETTING_LLM_MAX_TOKENS])
            )
            response = self.model.generate_content(full_prompt, generation_config=config)
            # ... (response handling unchanged) ...
            if hasattr(response, 'text'): return response.text.strip()
            elif response.prompt_feedback:
                 logging.warning(f"LLM generation blocked: {response.prompt_feedback}")
                 return f"欸...這個話題我好像不太能說耶。（原因：{response.prompt_feedback.block_reason}）"
            else:
                 logging.error(f"LLM generation failed: {response}")
                 return "糟糕，我好像斷線了..."
        except Exception as e:
            # ... (error handling unchanged) ...
            logging.error(f"LLM call failed: {e}")
            # ... (return specific error messages) ...
            if "API key not valid" in str(e): return "我的能量來源（API Key）好像出問題了..."
            elif "Resource has been exhausted" in str(e): return "今天好像說太多話了，讓我休息一下下喔！"
            else: return "哎呀，我的腦袋好像打結了，等一下再試試？"

    # Modified update_emotions_from_interaction for sensitivity/stability
    def update_emotions_from_interaction(self, user_input, bot_response):
        # ... (prompt unchanged) ...
        emotion_list_str = ", ".join(EMOTIONS.keys())
        prompt = f"""... (prompt content as before) ...
        你的 JSON 輸出："""

        response_text = self.call_llm(prompt, include_context=False)
        if not response_text or response_text.startswith("欸...") or response_text.startswith("糟糕") or response_text.startswith("哎呀"): return

        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
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

                                # Calculate raw change needed
                                raw_change = target_value - current_value

                                # Apply sensitivity
                                sensitive_change = raw_change * sensitivity

                                # Apply stability (inertia) - reduce the change based on stability
                                stable_change = sensitive_change * (1.0 - stability)

                                # Calculate new value
                                new_value = current_value + stable_change
                                new_value = max(0.0, min(1.0, new_value)) # Clamp again

                                # Only save if change is significant enough
                                if abs(new_value - current_value) > 0.005:
                                     self.emotions[name] = new_value
                                     save_emotion(self.user_id, name, new_value)
                                     updated_count += 1

                            except ValueError: logging.warning(f"Invalid value format for emotion '{name}': {target_value_str}")
                        else: logging.warning(f"LLM returned unknown emotion '{name}' in update.")
                    if updated_count > 0: self._update_pet_image()
                else: logging.warning(f"Emotion update response was not a JSON object: {updates}")
            else: logging.warning(f"Could not find valid JSON object in emotion update response: {response_text}")
        except json.JSONDecodeError as e: logging.error(f"Failed to decode JSON from emotion update: {e}\nResponse: {response_text}")
        except Exception as e: logging.error(f"Error processing emotion updates: {e}")

    # Modified process_input for response delay
    def process_input(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input: return

        # Append user input immediately
        self._append(f"你: {user_input}")
        self.entry.delete(0, tk.END)

        # Update boredom/status
        self.boredom = max(0, self.boredom - 0.1)
        self._update_status_labels()

        # Save user memory (unchanged logic)
        is_long_term_worthy = random.random() < 0.05
        importance = 1
        if "重要" in user_input or "記得" in user_input or "記住" in user_input:
             is_long_term_worthy = True
             importance = 5
        save_memory(self.user_id, f"User: {user_input}", is_long_term=is_long_term_worthy, importance=importance)

        # --- Generate Response (without appending yet) ---
        prompt_for_response = f"用戶說：\"{user_input}\"\n請根據你的個性、當前心情和最近的對話，用口語化的方式回應他。"
        bot_response = self.call_llm(prompt_for_response, include_context=True)

        # --- Handle Response Delay ---
        if self.settings[SETTING_RESPONSE_DELAY_ENABLED]:
            delay_ms = random.randint(100, int(self.settings[SETTING_RESPONSE_DELAY_MAX]))
            # Optional: Show typing indicator
            typing_msg = "小星正在輸入..."
            self._append(typing_msg)
            # Schedule the final response handling
            self.response_delay_timer_id = self.root.after(delay_ms, lambda u=user_input, b=bot_response, t_msg=typing_msg: self._finalize_response(u, b, t_msg))
        else:
             # If delay disabled, finalize immediately
             self._finalize_response(user_input, bot_response)

    def _finalize_response(self, user_input, bot_response, typing_msg=None):
         """Appends bot response, saves memory, updates emotions."""
         # Optional: Remove typing indicator if shown
         if typing_msg:
              try:
                   # This is tricky, requires deleting the specific line from the Text widget
                   # A simpler way is often not to show it, or just let it be overwritten.
                   # For simplicity, we'll just append the actual response.
                   pass
              except Exception as e:
                   logging.warning(f"Could not remove typing indicator: {e}")

         # Append final response
         self._append(f"小星: {bot_response}")

         # Save bot response memory
         save_memory(self.user_id, f"小星: {bot_response}", is_long_term=False)

         # Reload memory lists to include the new user/bot messages
         self.reload_memory_lists()

         # Update emotions based on the interaction
         self.update_emotions_from_interaction(user_input, bot_response)


    # ... reload_memory_lists (unchanged) ...
    def reload_memory_lists(self):
        logging.debug("Reloading memory lists from database.")
        self.short_term_tuples = load_memory(self.user_id, False)
        self.long_term_tuples = load_memory(self.user_id, True)
        self.short_term = [content for _, content in self.short_term_tuples]
        self.long_term = [content for _, content in self.long_term_tuples]

    # Modified _decay_emotions for trait-based baseline
    def _decay_emotions(self):
        decay_rate = self.settings[SETTING_DECAY_RATE]
        optimism = self.settings[SETTING_OPTIMISM_TRAIT]
        anxiety_p = self.settings[SETTING_ANXIETY_TRAIT]
        updated = False

        for name, value in list(self.emotions.items()):
            # Calculate target baseline based on traits (example)
            baseline = 0.5
            if name in ['joy', 'hope', 'optimism', 'satisfaction', 'excitement']:
                baseline = 0.5 + (optimism - 0.5) * 0.3 # Optimism influences positive emotions
            elif name in ['sadness', 'pessimism', 'disappointment']:
                 baseline = 0.5 - (optimism - 0.5) * 0.3 # Optimism inversely influences negative
            elif name in ['anxiety', 'fear', 'worry']: # Assuming 'worry' is not an emotion key, using anxiety/fear
                 baseline = 0.5 + (anxiety_p - 0.5) * 0.4 # Anxiety trait influences anxiety/fear

            # Decay towards calculated baseline
            if abs(value - baseline) > 0.01:
                new_value = value + (baseline - value) * decay_rate
                new_value = max(0.0, min(1.0, new_value))
                if abs(new_value - value) > 0.001:
                    self.emotions[name] = new_value
                    save_emotion(self.user_id, name, new_value)
                    updated = True

        if updated: self._update_pet_image()
        self.decay_timer_id = self.root.after(15 * 60 * 1000, self._decay_emotions) # Reschedule


    # ... _update_needs, _update_status_labels (unchanged) ...
    def _update_needs(self):
        self.boredom = min(1.0, self.boredom + 0.01)
        self.energy = max(0.0, self.energy - 0.005)
        self._update_status_labels()
        self.needs_timer_id = self.root.after(5 * 60 * 1000, self._update_needs)

    def _update_status_labels(self):
        self.boredom_label.config(text=f"無聊度: {self.boredom:.1f}")
        self.energy_label.config(text=f"精力: {self.energy:.1f}")

    # Modified _apply_hourly_emotion_shift for stability & strength setting
    def _apply_hourly_emotion_shift(self, hour):
        logging.info(f"Applying hourly emotion shift for hour: {hour}")
        change_magnitude = self.settings[SETTING_TIME_SHIFT_STRENGTH]
        stability = self.settings[SETTING_MOOD_STABILITY]
        emotions_to_update = {}

        # Apply base changes based on time of day
        # ... (time-based logic remains similar, e.g., morning optimism) ...
        if 6 <= hour < 10:
            emotions_to_update['optimism'] = self.emotions.get('optimism', 0.5) + random.uniform(0, change_magnitude * 2)
            emotions_to_update['interest'] = self.emotions.get('interest', 0.5) + random.uniform(0, change_magnitude)
            self.energy = min(1.0, self.energy + 0.05)
        elif 19 <= hour < 23:
            emotions_to_update['calmness'] = self.emotions.get('calmness', 0.5) + random.uniform(0, change_magnitude)
            emotions_to_update['nostalgia'] = self.emotions.get('nostalgia', 0.5) + random.uniform(0, change_magnitude * 0.5)
        elif 23 <= hour or hour < 5:
            emotions_to_update['boredom'] = self.emotions.get('boredom', 0.5) + random.uniform(0, change_magnitude)
            self.boredom = min(1.0, self.boredom + 0.03)
            self.energy = max(0.0, self.energy - 0.05)

        # General random shifts
        for _ in range(random.randint(1, 2)):
             emo_name = random.choice(list(EMOTIONS.keys()))
             change = random.uniform(-change_magnitude, change_magnitude)
             emotions_to_update[emo_name] = self.emotions.get(emo_name, 0.5) + change

        # Apply updates with stability
        updated_count = 0
        if emotions_to_update:
            for name, target_value in emotions_to_update.items():
                 if name in self.emotions:
                     current_value = self.emotions[name]
                     # Calculate change needed to reach target
                     raw_change = target_value - current_value
                     # Apply stability
                     stable_change = raw_change * (1.0 - stability)
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

    # ... _hourly_time_check (unchanged) ...
    def _hourly_time_check(self, run_immediately=False):
        now = time.time()
        current_hour = datetime.now().hour
        hour_in_seconds = 60 * 60
        time_since_last_shift = now - self.last_hourly_shift_time

        # Use >= 1 hour OR (run_immediately AND never run before)
        if time_since_last_shift >= hour_in_seconds or (run_immediately and self.last_hourly_shift_time == 0):
            logging.info("Hourly check triggered.")
            self._apply_hourly_emotion_shift(current_hour)
            self.last_hourly_shift_time = now
            save_setting('last_hourly_shift_time', now) # Use save_setting
        # else: logging.debug("Hourly check: Less than an hour passed.")

        # Cancel previous timer if exists before setting a new one
        if hasattr(self, 'hourly_timer_id') and self.hourly_timer_id:
             try: self.root.after_cancel(self.hourly_timer_id)
             except tk.TclError: pass
        self.hourly_timer_id = self.root.after(hour_in_seconds * 1000, self._hourly_time_check)


    # Modified _proactive to use settings for rescheduling interval
    def _proactive(self):
        # ... (action choosing logic unchanged) ...
        dom, strength, _ = self._get_dominant_emotion()
        threshold = 0.65
        possible_actions = []
        # ... (build possible_actions based on emotions, needs, memory) ...
        if strength > threshold:
             if dom in POSITIVE_EMOTIONS: possible_actions.append(f"我現在超 {dom} 的！({strength:.1f}) 你最近有什麼開心的事嗎？")
             elif dom in NEGATIVE_EMOTIONS: possible_actions.append(f"嗯...現在心情有點 {dom} ({strength:.1f})，不太好受...")
             else: possible_actions.append(f"我現在對某件事超級 {dom} ({strength:.1f})！好好奇喔！")
        if self.boredom > 0.85: possible_actions.append("真的好無聊喔～～～(眼神死) 我們來聊點八卦好不好？")
        if self.energy < 0.25: possible_actions.append("我不行了... (趴) 好想睡覺...晚點再聊？")
        if self.long_term and random.random() < 0.25:
            memory_item = random.choice(self.long_term)
            if memory_item.startswith("User:") and len(memory_item) > 15:
                 topic = memory_item[6:35]
                 possible_actions.append(f"欸～我突然想到，你之前是不是說過「{topic}...」？後來呢？")
        possible_actions.extend(["嗨！突然想找你聊聊～","在嗎在嗎？最近怎麼樣？","（探頭）你在做什麼呀？"])
        if not possible_actions: possible_actions.append("嗯？怎麼了嗎？")

        chosen_action_prompt = random.choice(possible_actions)
        final_utterance = self.call_llm(f"你想要主動跟使用者說話，你想表達的大意是：「{chosen_action_prompt}」。請用自然的口氣說出來。", include_context=True)
        self._append(f"小星 (主動): {final_utterance}")

        self.boredom = max(0, self.boredom - 0.2)
        self._update_status_labels()

        # --- Reschedule using frequency from settings ---
        freq_index = self.settings[SETTING_PROACTIVE_FREQ]
        min_delay, max_delay = -1, -1
        if freq_index == 0: min_delay, max_delay = 5*60, 15*60
        elif freq_index == 1: min_delay, max_delay = 10*60, 25*60
        elif freq_index == 2: min_delay, max_delay = 20*60, 40*60

        if min_delay > 0:
             next_proactive_ms = random.randint(min_delay * 1000, max_delay * 1000)
             # Cancel previous timer if exists before setting a new one
             if hasattr(self, 'proactive_timer_id') and self.proactive_timer_id:
                  try: self.root.after_cancel(self.proactive_timer_id)
                  except tk.TclError: pass
             self.proactive_timer_id = self.root.after(next_proactive_ms, self._proactive)
        # else: Proactive chat is off, don't reschedule


    # Modified _cleanup to use setting
    def _cleanup(self):
        retention_days = self.settings[SETTING_STM_RETENTION_DAYS]
        clean_short_term_memory(retention_days)
        # Cancel previous timer before setting new one
        if hasattr(self, 'cleanup_timer_id') and self.cleanup_timer_id:
             try: self.root.after_cancel(self.cleanup_timer_id)
             except tk.TclError: pass
        self.cleanup_timer_id = self.root.after(24 * 60 * 60 * 1000, self._cleanup)


    # Modified _process_memory_forgetting to use settings
    def _process_memory_forgetting(self):
        logging.debug("Processing memory forgetting/recalling.")
        forget_chance = self.settings[SETTING_FORGET_CHANCE]
        recall_chance = self.settings[SETTING_RECALL_CHANCE]

        try:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                # ... (Forgetting logic using forget_chance) ...
                c.execute("SELECT id FROM short_term_memory WHERE status='remembered' ORDER BY RANDOM() LIMIT 10")
                st_ids_to_consider = [row[0] for row in c.fetchall()]
                c.execute("SELECT id FROM long_term_memory WHERE status='remembered' ORDER BY RANDOM() LIMIT 5")
                lt_ids_to_consider = [row[0] for row in c.fetchall()]
                forgotten_count = 0
                for mem_id in st_ids_to_consider + lt_ids_to_consider:
                    if random.random() < forget_chance:
                        table = 'short_term_memory' if mem_id in st_ids_to_consider else 'long_term_memory'
                        c.execute(f"UPDATE {table} SET status='forgotten' WHERE id=?", (mem_id,))
                        forgotten_count += 1
                if forgotten_count > 0: logging.info(f"Forgot {forgotten_count} memories.")

                # ... (Recalling logic using recall_chance) ...
                c.execute("SELECT id FROM short_term_memory WHERE status='forgotten' ORDER BY RANDOM() LIMIT 5")
                st_ids_to_recall = [row[0] for row in c.fetchall()]
                c.execute("SELECT id FROM long_term_memory WHERE status='forgotten' ORDER BY RANDOM() LIMIT 3")
                lt_ids_to_recall = [row[0] for row in c.fetchall()]
                recalled_count = 0
                for mem_id in st_ids_to_recall + lt_ids_to_recall:
                     if random.random() < recall_chance:
                        table = 'short_term_memory' if mem_id in st_ids_to_recall else 'long_term_memory'
                        c.execute(f"UPDATE {table} SET status='remembered' WHERE id=?", (mem_id,))
                        recalled_count += 1
                if recalled_count > 0: logging.info(f"Recalled {recalled_count} memories.")

                conn.commit()
                if forgotten_count > 0 or recalled_count > 0: self.reload_memory_lists()
        except sqlite3.Error as e: logging.error(f"Error during memory forgetting process: {e}")

        # Reschedule
        if hasattr(self, 'forgetting_timer_id') and self.forgetting_timer_id:
             try: self.root.after_cancel(self.forgetting_timer_id)
             except tk.TclError: pass
        self.forgetting_timer_id = self.root.after(6 * 60 * 60 * 1000, self._process_memory_forgetting)


    # Modified _schedule_tasks to use _reschedule method
    def _schedule_tasks(self):
        """Schedules all recurring tasks based on current settings."""
        # Just call the rescheduling method initially
        self._reschedule_tasks_from_settings()
        logging.info("Initial task scheduling complete based on settings.")

    # ... _append (unchanged) ...
    def _append(self, text_to_append):
        try:
            self.text.config(state='normal')
            self.text.insert(tk.END, text_to_append + "\n")
            self.text.see(tk.END)
            self.text.config(state='disabled')
        except tk.TclError as e: logging.warning(f"Failed to append text, window might be closing: {e}")
        except Exception as e: logging.error(f"Error appending text: {e}")

    # Modified on_close to use _cancel_timers
    def on_close(self):
        """Cancel scheduled tasks before closing."""
        logging.info("Closing application...")
        self._cancel_timers() # Use the dedicated cancel method
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # Use ttk theme for better looking widgets if available
    style = ttk.Style(root)
    try:
        # Try using a modern theme like 'clam', 'alt', 'default', 'classic'
        # Availability depends on OS and Tk/Ttk version
        available_themes = style.theme_names()
        logging.info(f"Available ttk themes: {available_themes}")
        if 'clam' in available_themes: style.theme_use('clam')
        elif 'vista' in available_themes: style.theme_use('vista') # Good on Windows
        elif 'aqua' in available_themes: style.theme_use('aqua') # Good on macOS
        else: style.theme_use('default')
    except tk.TclError:
         logging.warning("Could not set ttk theme.")

    root.minsize(350, 450)
    app = PetApp(root)
    if hasattr(app, 'api_key') and app.api_key:
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        root.mainloop()
    else:
        logging.info("Application did not start due to missing API key or initialization error.")