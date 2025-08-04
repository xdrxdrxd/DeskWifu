# database.py (Part 1/5)
import sqlite3
import logging
import time
import uuid
import json
import os
from typing import List, Dict, Any, Optional

# 從 config 模組匯入常數
import config

class DatabaseManager:
    """負責所有與 SQLite 資料庫的互動"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        # 確保資料庫目錄存在
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """建立並返回一個資料庫連線"""
        return sqlite3.connect(self.db_path)

    def _column_exists(self, cursor: sqlite3.Cursor, table_name: str, column_name: str) -> bool:
        """檢查表格中是否存在某個欄位"""
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in cursor.fetchall()]
            return column_name in columns
        except sqlite3.Error as e:
            logging.error(f"Error checking column {column_name} in {table_name}: {e}")
            return False

    def init_db(self):
        """初始化資料庫，建立所有必要的表格和欄位。"""
        logging.info(f"Initializing database at: {self.db_path}")
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                # --- 表格建立 ---
                c.execute('''CREATE TABLE IF NOT EXISTS emotions (
                                user_id TEXT, emotion_name TEXT, value REAL, last_updated REAL,
                                PRIMARY KEY (user_id, emotion_name)
                             )''')
                c.execute('''CREATE TABLE IF NOT EXISTS short_term_memory (
                                id TEXT PRIMARY KEY, user_id TEXT, content TEXT, timestamp REAL,
                                importance INTEGER, status TEXT DEFAULT 'remembered',
                                pet_emotions_snapshot TEXT, user_emotions_snapshot TEXT,
                                keywords TEXT DEFAULT NULL, emotional_intensity REAL DEFAULT 0.0
                             )''')
                c.execute('''CREATE TABLE IF NOT EXISTS long_term_memory (
                                id TEXT PRIMARY KEY, user_id TEXT, content TEXT,
                                timestamp REAL, importance INTEGER, status TEXT DEFAULT 'remembered',
                                pet_emotions_snapshot TEXT, user_emotions_snapshot TEXT,
                                keywords TEXT DEFAULT NULL, emotional_intensity REAL DEFAULT 0.0
                             )''')
                c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
                                id TEXT PRIMARY KEY, key_name TEXT UNIQUE, key_value TEXT
                             )''')
                c.execute('''CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value TEXT)''')
                c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                                id TEXT PRIMARY KEY, user_id TEXT, description TEXT NOT NULL,
                                created_at REAL, due_at REAL DEFAULT NULL, completed INTEGER DEFAULT 0
                             )''')

                c.execute(f'''CREATE TABLE IF NOT EXISTS characters (
                                user_id TEXT PRIMARY KEY,
                                {config.SETTING_OCEAN_OPENNESS} REAL DEFAULT {config.DEFAULT_CHARACTER_TRAITS[config.SETTING_OCEAN_OPENNESS]},
                                {config.SETTING_OCEAN_CONSCIENTIOUSNESS} REAL DEFAULT {config.DEFAULT_CHARACTER_TRAITS[config.SETTING_OCEAN_CONSCIENTIOUSNESS]},
                                {config.SETTING_OCEAN_EXTRAVERSION} REAL DEFAULT {config.DEFAULT_CHARACTER_TRAITS[config.SETTING_OCEAN_EXTRAVERSION]},
                                {config.SETTING_OCEAN_AGREEABLENESS} REAL DEFAULT {config.DEFAULT_CHARACTER_TRAITS[config.SETTING_OCEAN_AGREEABLENESS]},
                                {config.SETTING_OCEAN_NEUROTICISM} REAL DEFAULT {config.DEFAULT_CHARACTER_TRAITS[config.SETTING_OCEAN_NEUROTICISM]},
                                last_personality_event_time REAL DEFAULT 0,
                                attachment_score REAL DEFAULT 0.4,
                                self_efficacy_general REAL DEFAULT 0.5,
                                self_efficacy_social REAL DEFAULT 0.5,
                                self_efficacy_task_management REAL DEFAULT 0.5,
                                self_efficacy_info_retrieval REAL DEFAULT 0.5,
                                last_updated REAL
                            )''')

                c.execute(f'''CREATE TABLE IF NOT EXISTS demographic_settings (
                                user_id TEXT PRIMARY KEY,
                                {config.SETTING_DEMO_CULTURE} TEXT DEFAULT '{config.DEFAULT_DEMOGRAPHICS[config.SETTING_DEMO_CULTURE]}',
                                {config.SETTING_DEMO_AGE_GROUP} TEXT DEFAULT '{config.DEFAULT_DEMOGRAPHICS[config.SETTING_DEMO_AGE_GROUP]}',
                                {config.SETTING_DEMO_GENDER} TEXT DEFAULT '{config.DEFAULT_DEMOGRAPHICS[config.SETTING_DEMO_GENDER]}',
                                last_updated REAL, FOREIGN KEY (user_id) REFERENCES characters(user_id)
                             )''')
                c.execute('''CREATE TABLE IF NOT EXISTS individual_characteristics (
                                trait_id TEXT PRIMARY KEY, user_id TEXT, trait_type TEXT NOT NULL,
                                trait_key TEXT, trait_value TEXT NOT NULL, creation_timestamp REAL,
                                last_accessed_timestamp REAL, last_reinforced_timestamp REAL,
                                relevance_score REAL DEFAULT 0.5, source TEXT, version INTEGER DEFAULT 1,
                                FOREIGN KEY (user_id) REFERENCES characters(user_id)
                             )''')
                c.execute('''CREATE INDEX IF NOT EXISTS idx_individual_characteristics_user_type
                             ON individual_characteristics(user_id, trait_type)''')
                c.execute('''CREATE INDEX IF NOT EXISTS idx_individual_characteristics_relevance
                             ON individual_characteristics(user_id, relevance_score DESC)''')
                c.execute('''CREATE TABLE IF NOT EXISTS emotion_history (
                                event_id TEXT PRIMARY KEY, user_id TEXT, timestamp REAL, emotion_name TEXT,
                                previous_value REAL, new_value REAL, trigger_event TEXT,
                                FOREIGN KEY (user_id) REFERENCES characters(user_id)
                            )''')
                c.execute('''CREATE INDEX IF NOT EXISTS idx_emotion_history_user_time
                             ON emotion_history(user_id, timestamp DESC)''')

                # --- 欄位遷移 (Schema migrations) ---
                # 將原始檔案中的所有 ALTER TABLE 邏輯遷移至此
                if not self._column_exists(c, 'characters', 'last_personality_event_time'):
                     c.execute(f"ALTER TABLE characters ADD COLUMN last_personality_event_time REAL DEFAULT 0")
                if not self._column_exists(c, 'characters', 'attachment_score'):
                     c.execute("ALTER TABLE characters ADD COLUMN attachment_score REAL DEFAULT 0.4")
                
                efficacy_columns_to_add = {
                    "self_efficacy_general": 0.5, "self_efficacy_social": 0.5,
                    "self_efficacy_task_management": 0.5, "self_efficacy_info_retrieval": 0.5
                }
                for col_name, default_val in efficacy_columns_to_add.items():
                    if not self._column_exists(c, 'characters', col_name):
                        c.execute(f"ALTER TABLE characters ADD COLUMN {col_name} REAL DEFAULT {default_val}")

                memory_tables = ['short_term_memory', 'long_term_memory']
                for table in memory_tables:
                    if not self._column_exists(c, table, 'status'):
                        c.execute(f"ALTER TABLE {table} ADD COLUMN status TEXT DEFAULT 'remembered'")
                    if not self._column_exists(c, table, 'pet_emotions_snapshot'):
                        c.execute(f"ALTER TABLE {table} ADD COLUMN pet_emotions_snapshot TEXT")
                    if not self._column_exists(c, table, 'user_emotions_snapshot'):
                        c.execute(f"ALTER TABLE {table} ADD COLUMN user_emotions_snapshot TEXT")
                    if not self._column_exists(c, table, 'keywords'):
                        c.execute(f"ALTER TABLE {table} ADD COLUMN keywords TEXT DEFAULT NULL")
                    if not self._column_exists(c, table, 'emotional_intensity'):
                        c.execute(f"ALTER TABLE {table} ADD COLUMN emotional_intensity REAL DEFAULT 0.0")

                if not self._column_exists(c, 'individual_characteristics', 'source'):
                    c.execute("ALTER TABLE individual_characteristics ADD COLUMN source TEXT")
                if not self._column_exists(c, 'individual_characteristics', 'version'):
                    c.execute("ALTER TABLE individual_characteristics ADD COLUMN version INTEGER DEFAULT 1")
                if not self._column_exists(c, 'individual_characteristics', 'last_reinforced_timestamp'):
                    c.execute("ALTER TABLE individual_characteristics ADD COLUMN last_reinforced_timestamp REAL")

                conn.commit()
                logging.info("Database schema initialized or verified successfully.")
        except sqlite3.Error as e:
            logging.critical(f"FATAL: Database initialization failed: {e}", exc_info=True)
            raise
    # --- API 金鑰管理 ---
    def get_api_key(self, key_name: str) -> Optional[str]:
        """從資料庫獲取指定的 API 金鑰"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT key_value FROM api_keys WHERE key_name=?", (key_name,))
                row = c.fetchone()
                return row[0] if row else None
        except sqlite3.Error as e:
            logging.error(f"Failed to get API key '{key_name}': {e}")
            return None

    def set_api_key(self, key_name: str, key_value: str) -> bool:
        """設定或更新 API 金鑰"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                # 使用 INSERT OR REPLACE，需要確保 key_name 是唯一的
                c.execute("INSERT OR REPLACE INTO api_keys (id, key_name, key_value) VALUES ((SELECT id FROM api_keys WHERE key_name=?), ?, ?)",
                          (key_name, key_name, key_value))
                # 如果上面這行在某些 SQLite 版本有問題，使用更安全的方式
                c.execute("DELETE FROM api_keys WHERE key_name=?", (key_name,))
                c.execute("INSERT INTO api_keys (id, key_name, key_value) VALUES (?, ?, ?)",
                          (str(uuid.uuid4()), key_name, key_value))
                conn.commit()
                logging.info(f"API key '{key_name}' set successfully.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Failed to set API key '{key_name}': {e}")
            return False

    def clear_api_key(self, key_name: str) -> bool:
        """清除指定的 API 金鑰"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM api_keys WHERE key_name=?", (key_name,))
                conn.commit()
                logging.info(f"API key '{key_name}' cleared.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Failed to clear API key '{key_name}': {e}")
            return False

    # --- App 設定管理 ---
    def load_app_setting(self, key: str, default_value: Any) -> Any:
        """載入應用程式設定，若不存在則使用預設值並儲存"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT value FROM app_state WHERE key=?", (key,))
                row = c.fetchone()
                if row:
                    val_str = row[0]
                    # 根據預設值的類型進行轉換
                    if isinstance(default_value, bool): return val_str.lower() in ['true', '1', 'yes']
                    if isinstance(default_value, int): return int(float(val_str))
                    if isinstance(default_value, float): return float(val_str)
                    return val_str
                else:
                    self.save_app_setting(key, default_value)
                    return default_value
        except (sqlite3.Error, ValueError) as e:
            logging.error(f"Failed to load or cast app setting '{key}': {e}. Returning default.")
            self.save_app_setting(key, default_value) # 如果讀取或轉換失敗，用預設值覆蓋
            return default_value

    def save_app_setting(self, key: str, value: Any):
        """儲存應用程式設定"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (key, str(value)))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to save app setting '{key}': {e}")

    # --- 情緒管理 ---
    def save_emotion(self, user_id: str, emotion_name: str, value: float, previous_value: Optional[float] = None, trigger_event: str = "unknown"):
        """儲存單個情緒值並記錄歷史"""
        value = max(0.0, min(1.0, float(value)))
        now = time.time()
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                if previous_value is None:
                    c.execute("SELECT value FROM emotions WHERE user_id=? AND emotion_name=?", (user_id, emotion_name))
                    row = c.fetchone()
                    previous_value = row[0] if row else 0.5

                c.execute("INSERT OR REPLACE INTO emotions (user_id, emotion_name, value, last_updated) VALUES (?, ?, ?, ?)",
                          (user_id, emotion_name, value, now))
                          
                if abs(value - previous_value) > 0.01: # 只有在變化顯著時才記錄歷史
                    event_id = str(uuid.uuid4())
                    c.execute('''INSERT INTO emotion_history
                                 (event_id, user_id, timestamp, emotion_name, previous_value, new_value, trigger_event)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                              (event_id, user_id, now, emotion_name, previous_value, value, trigger_event))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to save emotion or history for {emotion_name} of user {user_id}: {e}")

    def load_emotions(self, user_id: str) -> Dict[str, float]:
        """載入指定使用者的所有情緒值"""
        emo = config.EMOTIONS.copy()
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT emotion_name, value FROM emotions WHERE user_id=?", (user_id,))
                rows = c.fetchall()
                for name, val in rows:
                    if name in emo:
                        emo[name] = float(val)
        except sqlite3.Error as e:
            logging.error(f"Failed to load emotions for user {user_id}: {e}")
        return emo

    # --- 記憶管理 ---
    def save_memory(self, user_id: str, content: str, is_long_term: bool, importance: int, status: str,
                    pet_emotions_json: Optional[str], user_emotions_json: Optional[str],
                    keywords: Optional[str], emotional_intensity: float):
        """將一條記憶儲存到資料庫"""
        table = 'long_term_memory' if is_long_term else 'short_term_memory'
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                mem_id = str(uuid.uuid4())
                c.execute(f"""INSERT INTO {table}
                              (id, user_id, content, timestamp, importance, status,
                               pet_emotions_snapshot, user_emotions_snapshot,
                               keywords, emotional_intensity)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (mem_id, user_id, content, time.time(),
                           importance, status, pet_emotions_json, user_emotions_json,
                           keywords, emotional_intensity))
                conn.commit()
                logging.debug(f"Saved memory to {table} (ID: {mem_id[:8]}) for user {user_id}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to save memory to {table} for user {user_id}: {e}")

    def load_memory(self, user_id: str, is_long_term: bool = False, limit: int = 50, status_filter: Optional[str] = 'remembered') -> List[Dict]:
        """從資料庫載入記憶"""
        table = 'long_term_memory' if is_long_term else 'short_term_memory'
        memories = []
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = f"SELECT * FROM {table} WHERE user_id=? "
                params: List[Any] = [user_id]
                if status_filter:
                    query += "AND status=? "
                    params.append(status_filter)
                query += "ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                c.execute(query, tuple(params))
                # 將 sqlite3.Row 物件轉換為標準字典
                memories = [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Failed to load memory from {table} for user {user_id}: {e}")
        return memories

    def update_stms_status(self, stm_ids: List[str], new_status: str) -> bool:
        """批次更新短期記憶的狀態"""
        if not stm_ids:
            return False
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                placeholders = ','.join('?' for _ in stm_ids)
                c.execute(f"UPDATE short_term_memory SET status=? WHERE id IN ({placeholders})",
                          (new_status, *stm_ids))
                conn.commit()
                logging.info(f"Updated status to '{new_status}' for {c.rowcount} STM entries.")
                return True
        except sqlite3.Error as e:
            logging.error(f"Failed to update STM statuses: {e}")
            return False

    def clean_short_term_memory(self, user_id: str, retention_days: int,
                                importance_threshold_for_archive: int,
                                emotional_intensity_threshold_for_archive: float):
        """清理舊的短期記憶，標記為'forgotten'或'to_be_archived'"""
        if retention_days <= 0:
            retention_days = 1

        threshold_timestamp = time.time() - retention_days * 24 * 3600
        archived_count = 0
        forgotten_count = 0

        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT id, importance, emotional_intensity FROM short_term_memory
                             WHERE user_id=? AND timestamp < ? AND status='remembered'""",
                          (user_id, threshold_timestamp))
                old_stms = c.fetchall()

                stm_to_archive_ids: List[str] = []
                stm_to_forget_ids: List[str] = []

                for stm_id, importance, emotional_intensity in old_stms:
                    intensity_val = float(emotional_intensity) if emotional_intensity is not None else 0.0
                    if importance >= importance_threshold_for_archive or \
                       intensity_val >= emotional_intensity_threshold_for_archive:
                        stm_to_archive_ids.append(stm_id)
                    else:
                        stm_to_forget_ids.append(stm_id)

                if stm_to_archive_ids:
                    self.update_stms_status(stm_to_archive_ids, 'to_be_archived')
                    archived_count = len(stm_to_archive_ids)

                if stm_to_forget_ids:
                    self.update_stms_status(stm_to_forget_ids, 'forgotten')
                    forgotten_count = len(stm_to_forget_ids)

                if archived_count > 0 or forgotten_count > 0:
                    logging.info(f"STM cleanup for user {user_id}: {archived_count} marked for archive, {forgotten_count} marked as forgotten.")

        except sqlite3.Error as e:
            logging.error(f"Failed to clean short-term memory for user {user_id}: {e}")

    # --- 角色、人口統計、個體特徵 ---

    def load_character_data(self, user_id: str) -> Dict[str, Any]:
        """從資料庫載入角色的所有綜合數據（OCEAN, 依戀, 自我效能等），並以字典形式返回。"""
        traits = config.DEFAULT_CHARACTER_TRAITS.copy()
        attachment_score = 0.4
        self_efficacy = {
            "general": 0.5, "social": 0.5,
            "task_management": 0.5, "info_retrieval": 0.5
        }
        
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                # 確保 user_id 存在，若不存在則使用 characters 表中定義的 DEFAULT 值創建
                c.execute(f'''INSERT OR IGNORE INTO characters (user_id) VALUES (?)''', (user_id,))
                conn.commit()

                all_trait_cols = config.OCEAN_TRAIT_KEYS + ["attachment_score"] + [f"self_efficacy_{domain}" for domain in self_efficacy.keys()]
                select_cols_str = ", ".join(all_trait_cols)
                
                c.execute(f"SELECT {select_cols_str} FROM characters WHERE user_id=?", (user_id,))
                row = c.fetchone()

                if row:
                    col_idx = 0
                    for key in config.OCEAN_TRAIT_KEYS:
                        traits[key] = float(row[col_idx]) if row[col_idx] is not None else config.DEFAULT_CHARACTER_TRAITS[key]
                        col_idx += 1
                    
                    attachment_score = float(row[col_idx]) if row[col_idx] is not None else 0.4
                    col_idx += 1

                    for domain_key in self_efficacy.keys():
                        self_efficacy[domain_key] = float(row[col_idx]) if row[col_idx] is not None else 0.5
                        col_idx += 1
        except sqlite3.Error as e:
            logging.error(f"DB error loading character data for user '{user_id}': {e}", exc_info=True)
        except (IndexError, ValueError) as e:
            logging.warning(f"Error parsing character data for '{user_id}', DB structure might be outdated. Using defaults. Error: {e}")

        return {'traits': traits, 'attachment_score': attachment_score, 'self_efficacy': self_efficacy}

    def save_character_data(self, user_id: str, traits: Dict, attachment: float, efficacy: Dict):
        """將角色的所有綜合數據儲存到資料庫"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                
                set_clauses = [f"{key}=?" for key in config.OCEAN_TRAIT_KEYS]
                params = [traits.get(key, config.DEFAULT_CHARACTER_TRAITS[key]) for key in config.OCEAN_TRAIT_KEYS]

                set_clauses.append("attachment_score=?")
                params.append(attachment)

                for domain in efficacy.keys():
                    set_clauses.append(f"self_efficacy_{domain}=?")
                    params.append(efficacy.get(domain, 0.5))

                set_clauses.append("last_updated=?")
                params.append(time.time())

                params.append(user_id)

                update_sql = f"UPDATE characters SET {', '.join(set_clauses)} WHERE user_id=?"
                c.execute(update_sql, tuple(params))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database error saving character data for '{user_id}': {e}", exc_info=True)

    def load_last_personality_event_time(self, user_id: str) -> float:
        """讀取最後一次人格事件的時間戳"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT last_personality_event_time FROM characters WHERE user_id=?", (user_id,))
                row = c.fetchone()
                return float(row[0]) if row and row[0] is not None else 0.0
        except sqlite3.Error as e:
            logging.error(f"Failed to load last personality event time for '{user_id}': {e}")
            return 0.0

    def save_last_personality_event_time(self, user_id: str, event_time: float):
        """更新最後一次人格事件的時間戳"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE characters SET last_personality_event_time = ? WHERE user_id=?", (event_time, user_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to save last personality event time for '{user_id}': {e}")

    def load_demographics(self, user_id: str) -> Dict[str, str]:
        """載入人口統計學設定"""
        demographics = config.DEFAULT_DEMOGRAPHICS.copy()
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO demographic_settings (user_id) VALUES (?)", (user_id,))
                columns_str = ", ".join(config.DEMOGRAPHIC_KEYS)
                c.execute(f"SELECT {columns_str} FROM demographic_settings WHERE user_id=?", (user_id,))
                row = c.fetchone()
                if row:
                    for i, key in enumerate(config.DEMOGRAPHIC_KEYS):
                        demographics[key] = str(row[i]) if row[i] is not None else config.DEFAULT_DEMOGRAPHICS[key]
        except sqlite3.Error as e:
            logging.error(f"Failed to load demographics for '{user_id}': {e}")
        return demographics

    def save_demographics(self, user_id: str, demographics_dict: Dict[str, str]):
        """儲存人口統計學設定"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                values = [str(demographics_dict.get(key, config.DEFAULT_DEMOGRAPHICS[key])) for key in config.DEMOGRAPHIC_KEYS]
                columns_str = ", ".join(config.DEMOGRAPHIC_KEYS)
                placeholders_str = ", ".join(["?"] * len(config.DEMOGRAPHIC_KEYS))
                
                c.execute(f'''INSERT OR REPLACE INTO demographic_settings (user_id, {columns_str}, last_updated)
                              VALUES (?, {placeholders_str}, ?)''',
                          (user_id, *values, time.time()))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to save demographics for '{user_id}': {e}")
    # --- 個體特徵管理 ---

    def get_individual_characteristics(self, user_id: str, trait_type: Optional[str] = None, min_relevance: float = 0.2, limit: int = 100) -> List[Dict]:
        """從資料庫獲取個體特徵列表"""
        characteristics = []
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = "SELECT * FROM individual_characteristics WHERE user_id=? AND relevance_score >= ? "
                params: List[Any] = [user_id, min_relevance]
                if trait_type:
                    query += "AND trait_type=? "
                    params.append(trait_type)
                query += "ORDER BY relevance_score DESC, last_accessed_timestamp DESC LIMIT ?"
                params.append(limit)
                c.execute(query, tuple(params))
                characteristics = [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Failed to get characteristics for user '{user_id}': {e}", exc_info=True)
        return characteristics

    def find_characteristic(self, user_id: str, trait_type: str, trait_key: Optional[str], trait_value: str) -> Optional[Dict]:
        """尋找一個完全匹配的現有特徵"""
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = "SELECT * FROM individual_characteristics WHERE user_id=? AND trait_type=?"
                params: List[Any] = [user_id, trait_type]
                if trait_key is not None:
                    query += " AND trait_key=?"
                    params.append(trait_key)
                else: # 對於沒有key的類型，用value來比對
                    query += " AND trait_value=?"
                    params.append(trait_value)

                c.execute(query, tuple(params))
                row = c.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Error finding characteristic for user '{user_id}': {e}", exc_info=True)
            return None

    def raw_insert_characteristic(self, data: Dict) -> Optional[str]:
        """底層的新增特徵方法"""
        trait_id = str(uuid.uuid4())
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO individual_characteristics
                             (trait_id, user_id, trait_type, trait_key, trait_value,
                              creation_timestamp, last_accessed_timestamp, last_reinforced_timestamp,
                              relevance_score, source, version)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (trait_id, data['user_id'], data['trait_type'], data['trait_key'], data['trait_value'],
                           data['timestamp'], data['timestamp'], data['timestamp'],
                           data['relevance_score'], data['source'], 1))
                conn.commit()
                return trait_id
        except sqlite3.Error as e:
            logging.error(f"Failed to raw insert characteristic: {e}", exc_info=True)
            return None

    def raw_update_characteristic(self, data: Dict):
        """底層的更新特徵方法"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute('''UPDATE individual_characteristics
                             SET trait_value=?, relevance_score=?, last_accessed_timestamp=?,
                                 last_reinforced_timestamp=?, version=version+1, source=?
                             WHERE trait_id=?''',
                          (data['trait_value'], data['relevance_score'], data['timestamp'],
                           data['timestamp'], data['source'], data['trait_id']))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to raw update characteristic: {e}", exc_info=True)

    def reinforce_characteristic(self, trait_id: str, new_relevance: float, new_source: str, timestamp: float):
        """強化一個現有的特徵"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""UPDATE individual_characteristics
                             SET last_accessed_timestamp=?, last_reinforced_timestamp=?, relevance_score=?, version=version+1, source=?
                             WHERE trait_id=?""",
                          (timestamp, timestamp, new_relevance, new_source, trait_id))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to reinforce characteristic '{trait_id}': {e}", exc_info=True)

    def delete_individual_characteristic(self, trait_id: str) -> bool:
        """刪除一個指定的個體特徵"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM individual_characteristics WHERE trait_id = ?", (trait_id,))
                conn.commit()
                if c.rowcount > 0:
                    logging.info(f"Successfully deleted characteristic with trait_id: {trait_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logging.error(f"Database error when trying to delete characteristic {trait_id}: {e}")
            return False

    def decay_characteristics_relevance(self, user_id: str, decay_amount: float, decay_interval_days: int):
        """對長時間未使用的特徵進行相關性衰減"""
        now = time.time()
        decay_threshold_time = now - (decay_interval_days * 24 * 3600)
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""UPDATE individual_characteristics
                             SET relevance_score = MAX(0.0, relevance_score - ?)
                             WHERE user_id = ?
                               AND COALESCE(last_reinforced_timestamp, creation_timestamp) < ?
                               AND COALESCE(last_accessed_timestamp, creation_timestamp) < ?
                               AND relevance_score > 0.01""",
                          (decay_amount, user_id, decay_threshold_time, decay_threshold_time))
                if c.rowcount > 0:
                    logging.info(f"Decayed relevance for {c.rowcount} characteristics for user '{user_id}'.")
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to decay characteristic relevance for '{user_id}': {e}")

    def remove_low_relevance_characteristics(self, user_id: str, relevance_threshold: float, unused_days_threshold: int):
        """移除相關性過低且長時間未使用的特徵"""
        now = time.time()
        unused_timestamp_threshold = now - (unused_days_threshold * 24 * 3600)
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""DELETE FROM individual_characteristics
                             WHERE user_id = ?
                               AND relevance_score < ?
                               AND (last_accessed_timestamp IS NULL OR last_accessed_timestamp < ?)
                               AND (last_reinforced_timestamp IS NULL OR last_reinforced_timestamp < ?)""",
                          (user_id, relevance_threshold, unused_timestamp_threshold, unused_timestamp_threshold))
                if c.rowcount > 0:
                    logging.info(f"Removed {c.rowcount} low-relevance, old characteristics for user '{user_id}'.")
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to remove low-relevance characteristics for '{user_id}': {e}")


    # --- 任務管理 ---
    def add_task(self, user_id: str, description: str, due_at: Optional[float] = None) -> Dict[str, Any]:
        """新增任務到資料庫"""
        task_id = str(uuid.uuid4())
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("INSERT INTO tasks (id, user_id, description, created_at, due_at, completed) VALUES (?, ?, ?, ?, ?, ?)",
                          (task_id, user_id, description, time.time(), due_at, 0))
                conn.commit()
                logging.info(f"DB: Added task '{description}' for user {user_id}")
                return {"status": "success", "task_id": task_id, "description": description}
        except sqlite3.Error as e:
            logging.error(f"DB: Failed to add task for user {user_id}: {e}")
            return {"status": "error", "message": f"資料庫錯誤: {e}"}

    def get_tasks(self, user_id: str, include_completed: bool = False) -> List[Dict]:
        """從資料庫獲取任務列表"""
        tasks = []
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                query = "SELECT * FROM tasks WHERE user_id=?"
                params: List[Any] = [user_id]
                if not include_completed:
                    query += " AND completed=0"
                query += " ORDER BY due_at ASC NULLS LAST, created_at ASC"
                c.execute(query, tuple(params))
                tasks = [dict(row) for row in c.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"DB: Failed to get tasks for user {user_id}: {e}")
        return tasks

    def complete_task(self, task_id: str) -> bool:
        """在資料庫中標記任務為完成"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE tasks SET completed=1 WHERE id=?", (task_id,))
                conn.commit()
                return c.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"DB: Failed to complete task {task_id}: {e}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """從資料庫刪除任務"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
                conn.commit()
                return c.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"DB: Failed to delete task {task_id}: {e}")
            return False