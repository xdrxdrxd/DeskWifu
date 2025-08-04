import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import TYPE_CHECKING
from datetime import datetime
import config

# 使用 TYPE_CHECKING 來避免循環匯入，這是一種標準做法
if TYPE_CHECKING:
    from core.pet_logic import PetLogic
    from ui.main_window import MainWindow 

class SettingsWindow(tk.Toplevel):
    """應用程式的設定視窗"""

    def __init__(self, parent: tk.Tk, logic: "PetLogic", main_window_ref: "MainWindow"):
        super().__init__(parent)
        self.main_window = main_window_ref
        self.logic = logic
        self.transient(parent)
        self.grab_set()
        self.title("小星設定")
        self.geometry("750x800")

        self.protocol("WM_DELETE_WINDOW", self._on_close_settings)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # 建立所有分頁
        self.tab_general = ttk.Frame(self.notebook)
        self.tab_personality = ttk.Frame(self.notebook)
        self.tab_emotions = ttk.Frame(self.notebook)
        self.tab_characteristics = ttk.Frame(self.notebook)
        self.tab_api = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_general, text='常規與情緒')
        self.notebook.add(self.tab_personality, text='個性與背景')
        self.notebook.add(self.tab_emotions, text='目前情緒')
        self.notebook.add(self.tab_characteristics, text='個體特徵 (學習)')
        self.notebook.add(self.tab_api, text='API與模型')

        # 填充每個分頁的內容
        self._populate_general_tab()
        self._populate_personality_tab()
        self._populate_emotions_tab()
        self._populate_characteristics_tab()
        self._populate_api_tab()

        # 底部按鈕
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        close_button = ttk.Button(button_frame, text="關閉", command=self._on_close_settings)
        close_button.pack(side=tk.RIGHT, padx=5)
        apply_button = ttk.Button(button_frame, text="套用全部變更", command=self._apply_all_tab_settings)
        apply_button.pack(side=tk.RIGHT, padx=5)

        self.wait_window(self)

    def _populate_general_tab(self):
        """填充「常規與情緒」分頁的內容"""
        # --- 互動設定 ---
        frame_proactive = ttk.LabelFrame(self.tab_general, text="互動設定", padding=10)
        frame_proactive.pack(fill=tk.X, padx=5, pady=5, expand=True)

        ttk.Label(frame_proactive, text="主動聊天頻率:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.proactive_freq_var = tk.StringVar(value=str(self.logic.settings.get(config.SETTING_PROACTIVE_FREQ, "1")))
        freq_options = {"高": "0", "中 (預設)": "1", "低": "2", "從不": "3"}
        for i, (text, val) in enumerate(freq_options.items()):
            ttk.Radiobutton(frame_proactive, text=text, variable=self.proactive_freq_var, value=val).grid(row=0, column=i + 1, sticky=tk.W)

        ttk.Label(frame_proactive, text="使用者地點:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.location_var = tk.StringVar(value=self.logic.settings.get(config.SETTING_LOCATION, ""))
        ttk.Entry(frame_proactive, textvariable=self.location_var).grid(row=1, column=1, columnspan=4, sticky=tk.EW)

        # --- 情緒參數設定 ---
        frame_emotion = ttk.LabelFrame(self.tab_general, text="情緒參數設定", padding=10)
        frame_emotion.pack(fill=tk.X, padx=5, pady=5, expand=True)
        self.emotion_param_vars = {}
        param_configs = {
            config.SETTING_MOOD_STABILITY: ("情緒穩定度 (0.0-1.0):", (0.0, 1.0)),
            config.SETTING_EMO_SENSITIVITY: ("情緒敏感度 (0.0-2.0):", (0.0, 2.0)),
            config.SETTING_DECAY_RATE: ("情緒衰減率 (0.0-0.1):", (0.0, 0.1))
        }
        for i, (key, (label, (from_, to_))) in enumerate(param_configs.items()):
            var = tk.DoubleVar(value=round(float(self.logic.settings.get(key, config.DEFAULT_APP_SETTINGS[key])), 4))
            self.emotion_param_vars[key] = var
            ttk.Label(frame_emotion, text=label).grid(row=i, column=0, sticky=tk.W, pady=3)
            ttk.Scale(frame_emotion, from_=from_, to=to_, variable=var, orient=tk.HORIZONTAL).grid(row=i, column=1, sticky=tk.EW, padx=5)
            ttk.Entry(frame_emotion, textvariable=var, width=7).grid(row=i, column=2, padx=5)
        frame_emotion.columnconfigure(1, weight=1)

    def _populate_api_tab(self):
        """填充「API與模型」分頁的內容"""
        # --- Gemini API 設定 ---
        gemini_frame = ttk.LabelFrame(self.tab_api, text="Gemini LLM API 設定", padding=10)
        gemini_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)

        ttk.Label(gemini_frame, text="目前LLM模型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.llm_model_var = tk.StringVar(value=self.logic.settings.get(config.SETTING_SELECTED_LLM))
        model_cb = ttk.Combobox(gemini_frame, textvariable=self.llm_model_var, values=config.AVAILABLE_LLM_MODELS, state="readonly", width=25)
        model_cb.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(gemini_frame, text="設定/更改 Gemini API 金鑰", command=self.main_window.prompt_for_api_key).grid(row=1, column=0, columnspan=2, pady=10)
        # (為了簡化，直接在主邏輯中觸發API Key提示，這裡只提供說明)
        #ttk.Label(gemini_frame, text="API 金鑰請在主程式的彈出視窗中設定。").grid(row=1, column=0, columnspan=2, pady=10)
        
        # --- Custom Search API 設定 ---
        search_frame = ttk.LabelFrame(self.tab_api, text="Google Custom Search API 設定", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5, expand=True)
        
        self.search_api_enabled_var = tk.BooleanVar(value=bool(self.logic.settings.get(config.SETTING_SEARCH_API_ENABLED, 0)))
        ttk.Checkbutton(search_frame, text="啟用網路搜尋功能", variable=self.search_api_enabled_var).grid(row=0, column=0, columnspan=2, sticky=tk.W)

        self.search_daily_news_enabled_var = tk.BooleanVar(value=bool(self.logic.settings.get(config.SETTING_SEARCH_DAILY_NEWS_ENABLED, 0)))
        ttk.Checkbutton(search_frame, text="啟用每日自動搜尋新聞", variable=self.search_daily_news_enabled_var).grid(row=1, column=0, columnspan=2, sticky=tk.W)

        ttk.Label(search_frame, text="Search API 金鑰:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_api_key_var = tk.StringVar(value=self.logic.db.get_api_key('custom_search_api_key') or "")
        ttk.Entry(search_frame, textvariable=self.search_api_key_var, show="*").grid(row=2, column=1, sticky=tk.EW)

        ttk.Label(search_frame, text="Search Engine ID (CX):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_cx_id_var = tk.StringVar(value=self.logic.db.get_api_key('custom_search_cx_id') or "")
        ttk.Entry(search_frame, textvariable=self.search_cx_id_var).grid(row=3, column=1, sticky=tk.EW)
        search_frame.columnconfigure(1, weight=1)


    def _populate_personality_tab(self):
        """填充「個性與背景」分頁的內容"""
        # --- OCEAN 五大性格特質 ---
        frame_ocean = ttk.LabelFrame(self.tab_personality, text="OCEAN 五大性格特質 (0.0 - 1.0)", padding=10)
        frame_ocean.pack(fill=tk.X, padx=5, pady=5, expand=True)
        self.ocean_vars = {}
        ocean_labels_cn = {
            config.SETTING_OCEAN_OPENNESS: "經驗開放性 (O):",
            config.SETTING_OCEAN_CONSCIENTIOUSNESS: "盡責性 (C):",
            config.SETTING_OCEAN_EXTRAVERSION: "外向性 (E):",
            config.SETTING_OCEAN_AGREEABLENESS: "親和性 (A):",
            config.SETTING_OCEAN_NEUROTICISM: "神經質性 (N):"
        }

        for i, key in enumerate(config.OCEAN_TRAIT_KEYS):
            val = self.logic.personality_system.character_traits.get(key, config.DEFAULT_CHARACTER_TRAITS[key])
            var = tk.DoubleVar(value=round(val, 3))
            self.ocean_vars[key] = var
            
            ttk.Label(frame_ocean, text=ocean_labels_cn.get(key, key)).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Scale(frame_ocean, from_=0.0, to=1.0, variable=var, orient=tk.HORIZONTAL).grid(row=i, column=1, sticky=tk.EW, padx=5)
            ttk.Entry(frame_ocean, textvariable=var, width=6).grid(row=i, column=2, padx=5)
        frame_ocean.columnconfigure(1, weight=1)

        # --- 人口統計學背景 ---
        frame_demo = ttk.LabelFrame(self.tab_personality, text="人口統計學背景", padding=10)
        frame_demo.pack(fill=tk.X, padx=5, pady=5, expand=True)
        self.demographic_vars = {}
        demo_labels_cn = {
            config.SETTING_DEMO_CULTURE: "文化背景:",
            config.SETTING_DEMO_AGE_GROUP: "年齡層:",
            config.SETTING_DEMO_GENDER: "性別認同:"
        }
        for i, key in enumerate(config.DEMOGRAPHIC_KEYS):
            val = self.logic.personality_system.demographics.get(key, config.DEFAULT_DEMOGRAPHICS[key])
            var = tk.StringVar(value=val)
            self.demographic_vars[key] = var
            ttk.Label(frame_demo, text=demo_labels_cn.get(key, key)).grid(row=i, column=0, sticky=tk.W, padx=5, pady=3)
            ttk.Entry(frame_demo, textvariable=var, width=30).grid(row=i, column=1, sticky=tk.EW, padx=5)
        frame_demo.columnconfigure(1, weight=1)


    def _populate_emotions_tab(self):
        """填充「目前情緒」分頁的內容"""
        header_frame = ttk.Frame(self.tab_emotions)
        header_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Label(header_frame, text="小星目前的情緒狀態 (即時更新):", font=('TkDefaultFont', 11, 'bold')).pack(side=tk.LEFT, anchor=tk.W)

        # --- 除錯/測試按鈕 ---
        debug_frame = ttk.Frame(self.tab_emotions, padding=5)
        debug_frame.pack(fill=tk.X)
        ttk.Button(debug_frame, text="觸發一次情緒衰減", command=self._debug_trigger_decay).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(debug_frame, text="觸發一次隨機波動", command=self._debug_trigger_fluctuation).pack(side=tk.LEFT, padx=5)

        # --- 情緒狀態展示框架 ---
        status_frame = ttk.Frame(self.tab_emotions)
        status_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        # 建立一個 Canvas 和 Scrollbar 來容納進度條
        canvas = tk.Canvas(status_frame)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.emotion_bars = {}
        sorted_emotions = sorted(self.logic.emotion_system.get_current_emotions().items())
        
        for i, (name, value) in enumerate(sorted_emotions):
            # 建立標籤和進度條
            label = ttk.Label(scrollable_frame, text=f"{name:<25s}")
            label.grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            
            progress_var = tk.DoubleVar(value=value * 100)
            p_bar = ttk.Progressbar(scrollable_frame, orient='horizontal', length=300, mode='determinate', variable=progress_var)
            p_bar.grid(row=i, column=1, sticky=tk.EW, padx=5)

            value_label = ttk.Label(scrollable_frame, text=f"{value:.3f}")
            value_label.grid(row=i, column=2, sticky=tk.W, padx=5)
            
            self.emotion_bars[name] = (progress_var, value_label)
        
        scrollable_frame.columnconfigure(1, weight=1)

    def _refresh_emotion_status_display(self):
        """由外部呼叫，用以更新情緒分頁的顯示"""
        if not hasattr(self, 'emotion_bars') or not self.winfo_exists():
            return
            
        current_emotions = self.logic.emotion_system.get_current_emotions()
        for name, (progress_var, value_label) in self.emotion_bars.items():
            value = current_emotions.get(name, 0.0)
            progress_var.set(value * 100)
            value_label.config(text=f"{value:.3f}")
        logging.debug("Emotion display in settings window refreshed.")

    def _debug_trigger_decay(self):
        """處理 '觸發一次情緒衰減' 按鈕的點擊事件"""
        logging.info("SETTINGS_DEBUG: Manually triggering emotion decay.")
        effective_stability = self.logic.personality_system.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        self.logic.emotion_system.decay_emotions(effective_stability)
        self._refresh_emotion_status_display() # 手動觸發後立即更新

    def _debug_trigger_fluctuation(self):
        """處理 '觸發一次隨機波動' 按鈕的點擊事件"""
        logging.info("SETTINGS_DEBUG: Manually triggering random mood fluctuations.")
        effective_stability = self.logic.personality_system.character_traits.get(config.SETTING_OCEAN_NEUROTICISM, 0.5)
        self.logic.emotion_system.apply_random_fluctuations(effective_stability)
        self._refresh_emotion_status_display() # 手動觸發後立即更新



    def _populate_characteristics_tab(self):
        """填充「個體特徵 (學習)」分頁的內容"""
        # --- 篩選控制框架 ---
        filter_frame = ttk.LabelFrame(self.tab_characteristics, text="篩選條件", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="特徵類型:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.char_filter_type_var = tk.StringVar(value=config.ALL_TRAIT_TYPES_DISPLAY[0])
        type_combo = ttk.Combobox(filter_frame, textvariable=self.char_filter_type_var, values=config.ALL_TRAIT_TYPES_DISPLAY, state="readonly", width=25)
        type_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        type_combo.bind("<<ComboboxSelected>>", self._apply_char_filters_event)

        ttk.Label(filter_frame, text="來源:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.char_filter_source_var = tk.StringVar(value=config.ALL_SOURCE_TYPES_DISPLAY[0])
        source_combo = ttk.Combobox(filter_frame, textvariable=self.char_filter_source_var, values=config.ALL_SOURCE_TYPES_DISPLAY, state="readonly", width=25)
        source_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        source_combo.bind("<<ComboboxSelected>>", self._apply_char_filters_event)

        ttk.Label(filter_frame, text="關鍵字:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.char_filter_keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(filter_frame, textvariable=self.char_filter_keyword_var, width=30)
        keyword_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        keyword_entry.bind("<Return>", self._apply_char_filters_event)

        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)

        # --- 管理控制按鈕框架 ---
        controls_frame = ttk.Frame(self.tab_characteristics, padding=(5, 5, 5, 0))
        controls_frame.pack(fill=tk.X)
        ttk.Button(controls_frame, text="刷新列表", command=self._load_and_display_characteristics).pack(side=tk.LEFT)
        ttk.Button(controls_frame, text="忘記選定特徵", command=self._forget_selected_characteristic).pack(side=tk.LEFT, padx=5)
        ttk.Label(controls_frame, text="(雙擊欄位標題可排序)").pack(side=tk.LEFT, padx=10)

        # --- Treeview 表格 ---
        tree_frame = ttk.Frame(self.tab_characteristics)
        tree_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.char_tree = ttk.Treeview(tree_frame, show='headings')
        
        self.char_tree['columns'] = ('type', 'key', 'value', 'relevance', 'source', 'accessed', 'version')
        col_configs = {
            'type': {'text': '類型', 'width': 120}, 'key': {'text': '鍵名', 'width': 150},
            'value': {'text': '值', 'width': 250}, 'relevance': {'text': '相關性', 'width': 70, 'anchor': tk.E},
            'source': {'text': '來源', 'width': 150}, 'accessed': {'text': '最後存取', 'width': 140},
            'version': {'text': '版本', 'width': 50, 'anchor': tk.CENTER}
        }
        for col_id, config_dict in col_configs.items():
            self.char_tree.heading(col_id, text=config_dict['text'], anchor=tk.W, command=lambda c=col_id: self._treeview_sort_column(self.char_tree, c, False))
            self.char_tree.column(col_id, width=config_dict['width'], minwidth=60, stretch=True, anchor=config_dict.get('anchor', tk.W))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.char_tree.yview)
        vsb.pack(side='right', fill='y')
        self.char_tree.configure(yscrollcommand=vsb.set)
        self.char_tree.pack(side="left", fill="both", expand=True)

        self._load_and_display_characteristics() # 初始載入

    def _apply_char_filters_event(self, event=None):
        """事件處理函式，用於觸發篩選並重新載入數據"""
        self._load_and_display_characteristics()

    def _treeview_sort_column(self, tv: ttk.Treeview, col: str, reverse: bool):
        """Treeview 排序功能"""
        try:
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            # 嘗試數值排序，失敗則字串排序
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            
            tv.heading(col, command=lambda _col=col: self._treeview_sort_column(tv, _col, not reverse))
        except Exception as e:
            logging.error(f"Error sorting treeview column {col}: {e}")

    def _load_and_display_characteristics(self):
        """載入並篩選資料，然後顯示在 Treeview 中"""
        if not hasattr(self, 'char_tree') or not self.char_tree.winfo_exists(): return
        for item in self.char_tree.get_children(): self.char_tree.delete(item)

        type_filter = self.char_filter_type_var.get()
        source_filter = self.char_filter_source_var.get()
        keyword_filter = self.char_filter_keyword_var.get().strip().lower()

        # 從 DB 獲取所有數據，在 UI 層進行篩選
        all_characteristics = self.logic.db.get_individual_characteristics(
            self.logic.user_id, min_relevance=0.0, limit=1000
        )

        filtered = []
        for char in all_characteristics:
            if type_filter != "(所有類型)" and char.get('trait_type') != type_filter: continue
            if source_filter != "(所有來源)" and char.get('source') != source_filter: continue
            if keyword_filter and not (keyword_filter in str(char.get('trait_key','')).lower() or keyword_filter in str(char.get('trait_value','')).lower()): continue
            filtered.append(char)

        if not filtered:
            self.char_tree.insert('', 'end', values=("(無)", "沒有符合篩選條件的特徵。", "", "", "", "", ""))
            return

        for char_dict in filtered:
            def format_ts(ts): return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M') if ts else "N/A"
            values = (
                char_dict.get('trait_type', 'N/A'),
                char_dict.get('trait_key', 'N/A'),
                str(char_dict.get('trait_value', ''))[:100], # 限制長度
                f"{char_dict.get('relevance_score', 0.0):.3f}",
                char_dict.get('source', 'N/A'),
                format_ts(char_dict.get('last_accessed_timestamp')),
                str(char_dict.get('version', '1'))
            )
            self.char_tree.insert('', 'end', iid=char_dict['trait_id'], values=values)


    def _populate_characteristics_tab(self):
        """填充「個體特徵 (學習)」分頁的內容"""
        # --- 篩選控制框架 ---
        filter_frame = ttk.LabelFrame(self.tab_characteristics, text="篩選條件", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="特徵類型:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.char_filter_type_var = tk.StringVar(value=config.ALL_TRAIT_TYPES_DISPLAY[0])
        type_combo = ttk.Combobox(filter_frame, textvariable=self.char_filter_type_var, values=config.ALL_TRAIT_TYPES_DISPLAY, state="readonly", width=25)
        type_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        type_combo.bind("<<ComboboxSelected>>", self._apply_char_filters_event)

        ttk.Label(filter_frame, text="來源:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.char_filter_source_var = tk.StringVar(value=config.ALL_SOURCE_TYPES_DISPLAY[0])
        source_combo = ttk.Combobox(filter_frame, textvariable=self.char_filter_source_var, values=config.ALL_SOURCE_TYPES_DISPLAY, state="readonly", width=25)
        source_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)
        source_combo.bind("<<ComboboxSelected>>", self._apply_char_filters_event)

        ttk.Label(filter_frame, text="關鍵字:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.char_filter_keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(filter_frame, textvariable=self.char_filter_keyword_var, width=30)
        keyword_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        keyword_entry.bind("<Return>", self._apply_char_filters_event)

        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)

        # --- 管理控制按鈕框架 ---
        controls_frame = ttk.Frame(self.tab_characteristics, padding=(5, 5, 5, 0))
        controls_frame.pack(fill=tk.X)
        ttk.Button(controls_frame, text="刷新列表", command=self._load_and_display_characteristics).pack(side=tk.LEFT)
        ttk.Button(controls_frame, text="忘記選定特徵", command=self._forget_selected_characteristic).pack(side=tk.LEFT, padx=5)
        ttk.Label(controls_frame, text="(雙擊欄位標題可排序)").pack(side=tk.LEFT, padx=10)

        # --- Treeview 表格 ---
        tree_frame = ttk.Frame(self.tab_characteristics)
        tree_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.char_tree = ttk.Treeview(tree_frame, show='headings')
        
        self.char_tree['columns'] = ('type', 'key', 'value', 'relevance', 'source', 'accessed', 'version')
        col_configs = {
            'type': {'text': '類型', 'width': 120}, 'key': {'text': '鍵名', 'width': 150},
            'value': {'text': '值', 'width': 250}, 'relevance': {'text': '相關性', 'width': 70, 'anchor': tk.E},
            'source': {'text': '來源', 'width': 150}, 'accessed': {'text': '最後存取', 'width': 140},
            'version': {'text': '版本', 'width': 50, 'anchor': tk.CENTER}
        }
        for col_id, config_dict in col_configs.items():
            self.char_tree.heading(col_id, text=config_dict['text'], anchor=tk.W, command=lambda c=col_id: self._treeview_sort_column(self.char_tree, c, False))
            self.char_tree.column(col_id, width=config_dict['width'], minwidth=60, stretch=True, anchor=config_dict.get('anchor', tk.W))

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.char_tree.yview)
        vsb.pack(side='right', fill='y')
        self.char_tree.configure(yscrollcommand=vsb.set)
        self.char_tree.pack(side="left", fill="both", expand=True)

        self._load_and_display_characteristics() # 初始載入

    def _apply_char_filters_event(self, event=None):
        """事件處理函式，用於觸發篩選並重新載入數據"""
        self._load_and_display_characteristics()

    def _treeview_sort_column(self, tv: ttk.Treeview, col: str, reverse: bool):
        """Treeview 排序功能"""
        try:
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            # 嘗試數值排序，失敗則字串排序
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            
            tv.heading(col, command=lambda _col=col: self._treeview_sort_column(tv, _col, not reverse))
        except Exception as e:
            logging.error(f"Error sorting treeview column {col}: {e}")

    def _load_and_display_characteristics(self):
        """載入並篩選資料，然後顯示在 Treeview 中"""
        if not hasattr(self, 'char_tree') or not self.char_tree.winfo_exists(): return
        for item in self.char_tree.get_children(): self.char_tree.delete(item)

        type_filter = self.char_filter_type_var.get()
        source_filter = self.char_filter_source_var.get()
        keyword_filter = self.char_filter_keyword_var.get().strip().lower()

        # 從 DB 獲取所有數據，在 UI 層進行篩選
        all_characteristics = self.logic.db.get_individual_characteristics(
            self.logic.user_id, min_relevance=0.0, limit=1000
        )

        filtered = []
        for char in all_characteristics:
            if type_filter != "(所有類型)" and char.get('trait_type') != type_filter: continue
            if source_filter != "(所有來源)" and char.get('source') != source_filter: continue
            if keyword_filter and not (keyword_filter in str(char.get('trait_key','')).lower() or keyword_filter in str(char.get('trait_value','')).lower()): continue
            filtered.append(char)

        if not filtered:
            self.char_tree.insert('', 'end', values=("(無)", "沒有符合篩選條件的特徵。", "", "", "", "", ""))
            return

        for char_dict in filtered:
            def format_ts(ts): return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M') if ts else "N/A"
            values = (
                char_dict.get('trait_type', 'N/A'),
                char_dict.get('trait_key', 'N/A'),
                str(char_dict.get('trait_value', ''))[:100], # 限制長度
                f"{char_dict.get('relevance_score', 0.0):.3f}",
                char_dict.get('source', 'N/A'),
                format_ts(char_dict.get('last_accessed_timestamp')),
                str(char_dict.get('version', '1'))
            )
            self.char_tree.insert('', 'end', iid=char_dict['trait_id'], values=values)

    def _forget_selected_characteristic(self):
        """處理'忘記選定特徵'按鈕的點擊事件"""
        if not hasattr(self, 'char_tree') or not self.char_tree.winfo_exists():
            return

        selected_items = self.char_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "請先在列表中選擇一個要忘記的特徵。", parent=self)
            return

        trait_id_to_delete = selected_items[0]
        item_values = self.char_tree.item(trait_id_to_delete, 'values')
        confirm_msg = f"確定要讓小星忘記這個特徵嗎？\n\n類型: {item_values[0]}\n值: {str(item_values[2])[:50]}..."

        if messagebox.askyesno("確認忘記", confirm_msg, parent=self):
            # 呼叫資料庫管理員直接刪除
            if self.logic.db.delete_individual_characteristic(trait_id_to_delete):
                # 操作成功後，刷新核心邏輯的快取和UI列表
                self.logic.personality_system.load_characteristics_cache(min_relevance=0.01)
                self._load_and_display_characteristics()
                messagebox.showinfo("操作成功", "小星已經忘記了該特徵。", parent=self)
            else:
                messagebox.showerror("操作失敗", f"無法忘記特徵 (ID: {trait_id_to_delete})。")

    def _apply_all_tab_settings(self):
        """套用所有分頁中的設定變更"""
        logging.info("Applying all settings from SettingsWindow...")
        try:
            # --- 套用 General Tab 設定 ---
            self.logic.settings[config.SETTING_PROACTIVE_FREQ] = int(self.proactive_freq_var.get())
            self.logic.settings[config.SETTING_LOCATION] = self.location_var.get()
            for key, var in self.emotion_param_vars.items():
                self.logic.settings[key] = var.get()
            
            # --- 套用 Personality Tab 設定 ---
            for key, var in self.ocean_vars.items():
                self.logic.personality_system.character_traits[key] = round(var.get(), 3)
            # 儲存更新後的角色資料
            self.logic.personality_system._save_character_data()

            for key, var in self.demographic_vars.items():
                self.logic.personality_system.demographics[key] = var.get()
            # 儲存更新後的人口統計資料
            self.logic.db.save_demographics(self.logic.user_id, self.logic.personality_system.demographics)

            # --- 套用 API & Model Tab 設定 ---
            previous_model = self.logic.settings.get(config.SETTING_SELECTED_LLM)
            selected_model = self.llm_model_var.get()
            model_changed = (selected_model != previous_model)
            self.logic.settings[config.SETTING_SELECTED_LLM] = selected_model

            self.logic.settings[config.SETTING_SEARCH_API_ENABLED] = 1 if self.search_api_enabled_var.get() else 0
            self.logic.settings[config.SETTING_SEARCH_DAILY_NEWS_ENABLED] = 1 if self.search_daily_news_enabled_var.get() else 0
            
            # 儲存所有 AppState 設定
            for key, value in self.logic.settings.items():
                self.logic.db.save_app_setting(key, value)
            
            # 儲存 API Keys
            self.logic.db.set_api_key('custom_search_api_key', self.search_api_key_var.get())
            self.logic.db.set_api_key('custom_search_cx_id', self.search_cx_id_var.get())
            
            messagebox.showinfo("設定已儲存", "所有設定已成功套用。\n部分設定可能需要重新啟動應用程式才能完全生效。", parent=self)
            
            # 如果模型已更改，需要特別處理
            if model_changed:
                messagebox.showinfo("模型已更改", "偵測到LLM模型已更改，建議重新啟動應用程式以確保變更生效。")

        except Exception as e:
            logging.error(f"Error applying settings: {e}", exc_info=True)
            messagebox.showerror("錯誤", f"儲存設定時發生錯誤：\n{e}", parent=self)

    def _on_close_settings(self):
        """處理設定視窗的關閉事件"""
        logging.info("Settings window closed.")
        # 通知主視窗實例已銷毀
        parent_main_window = self.master
        if hasattr(parent_main_window, "settings_window_instance"):
            parent_main_window.settings_window_instance = None
        self.destroy()