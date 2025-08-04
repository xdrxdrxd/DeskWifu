# ui/main_window.py (Part 1/3)
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import logging
import threading
import os
from datetime import datetime
from typing import Optional, Dict, Any 
import config
from core.pet_logic import PetLogic
from ui.settings_window import SettingsWindow # 稍後會建立這個檔案
import random
class MainWindow:
    """應用程式的主視窗，負責所有UI操作。"""

    def __init__(self, root: tk.Tk, logic: PetLogic):
        self.root = root
        self.logic = logic
        self.root.title("小星 Pet (Refactored)")
        self.root.geometry("400x550")

        # --- UI 相關屬性 ---
        self.pet_img_label: Optional[tk.Label] = None
        self.chat_history_text: Optional[scrolledtext.ScrolledText] = None
        self.user_input_entry: Optional[ttk.Entry] = None
        self.current_pet_image: Optional[ImageTk.PhotoImage] = None
        self.settings_window_instance: Optional[tk.Toplevel] = None
        
        # --- 計時器 ID ---
        self._periodic_update_id: Optional[str] = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 根據 LLM 是否準備就緒來決定顯示哪個 UI
        initial_state = self.logic.get_initial_state()
        if initial_state.get("llm_ready"):
            self._setup_full_ui()
            self._add_chat_message("小星", initial_state["initial_message"], "pet")
        else:
            self._setup_minimal_ui_for_error("LLM 模型尚未就緒。\n請點擊「設定API金鑰」按鈕或透過選單設定。")
            # 應用程式啟動時，如果沒有金鑰，自動彈出輸入視窗
            self.root.after(100, self.prompt_for_api_key)
        
        self.update_pet_appearance(initial_state["dominant_emotion"])
        
        # 啟動背景更新循環
        self._periodic_update_id = self.root.after(10000, self._periodic_update)
    def prompt_for_api_key(self):
        """彈出視窗讓使用者輸入 API 金鑰，成功後嘗試重新初始化。"""
        if not self.root or not self.root.winfo_exists(): return

        key = simpledialog.askstring("API 金鑰", "請輸入您的 Google Gemini API 金鑰:", parent=self.root)
        if key:
            self.logic.db.set_api_key('gemini_api_key', key)
            if self.logic.reinitialize_llm_service():
                messagebox.showinfo("成功", "API 金鑰已設定，LLM 服務已成功啟動！", parent=self.root)
                self.rebuild_full_ui() # 核心：重建 UI
            else:
                messagebox.showerror("失敗", "API 金鑰無效或模型初始化失敗，請重試或檢查金鑰。", parent=self.root)
        else:
            messagebox.showwarning("未設定", "未提供 API 金鑰。LLM 功能將無法使用。", parent=self.root)
    def rebuild_full_ui(self):
        """銷毀當前 UI (無論是最小化還是完整的)，並重建完整的 UI。"""
        if self._periodic_update_id:
            self.root.after_cancel(self._periodic_update_id)
            self._periodic_update_id = None
        
        self._clear_all_ui_elements()
        self._setup_full_ui()
        
        initial_state = self.logic.get_initial_state()
        self.update_pet_appearance(initial_state["dominant_emotion"])
        
        self._periodic_update_id = self.root.after(10000, self._periodic_update)

    
    def _setup_full_ui(self):
        """建立完整的UI介面"""
        self._clear_all_ui_elements()

        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        image_frame = ttk.Frame(main_frame)
        image_frame.pack(pady=10)
        self.pet_img_label = ttk.Label(image_frame)
        self.pet_img_label.pack()

        chat_frame = ttk.LabelFrame(main_frame, text="聊天室", padding="5")
        chat_frame.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.chat_history_text = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, 
            relief=tk.FLAT, bd=0, font=('TkDefaultFont', 10)
        )
        self.chat_history_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        # 設定不同角色的文字樣式
        self.chat_history_text.tag_configure("user", foreground="blue", font=('TkDefaultFont', 10, 'bold'))
        self.chat_history_text.tag_configure("pet", foreground="#006400")
        self.chat_history_text.tag_configure("system", foreground="grey", font=('TkDefaultFont', 9, 'italic'))
        self.chat_history_text.tag_configure("error", foreground="red", font=('TkDefaultFont', 9, 'italic'))
        self.chat_history_text.tag_configure("task_reminder", foreground="#DAA520", font=('TkDefaultFont', 9, 'italic'))
        self.chat_history_text.tag_configure("self_talk", foreground="#483D8B", font=('TkDefaultFont', 9, 'italic'))
        self.chat_history_text.tag_configure("thought", foreground="#8A2BE2", font=('TkDefaultFont', 9, 'italic')) # 藍紫色
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        self.user_input_entry = ttk.Entry(input_frame, width=40)
        self.user_input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.user_input_entry.bind("<Return>", self.on_user_submit)
        send_button = ttk.Button(input_frame, text="傳送", command=self.on_user_submit)
        send_button.pack(side=tk.LEFT)
        
        self.user_input_entry.focus_set()
        
        self._setup_menubar()

    def _setup_minimal_ui_for_error(self, error_message: str):
        """建立一個最小化的 UI，只包含提示和設定選項。"""
        self._clear_all_ui_elements()
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        ttk.Label(main_frame, text=error_message, justify=tk.CENTER, wraplength=350).pack(pady=20)
        
        ttk.Button(main_frame, text="設定 API 金鑰", command=self.prompt_for_api_key).pack(pady=10)
        
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(pady=10)
        self.pet_img_label = ttk.Label(image_frame)
        self.pet_img_label.pack()
        
        self._setup_menubar()

    def _setup_menubar(self):
        """建立頂部選單欄，並加入更強大的偵錯選項。"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="設定", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="離開", command=self.on_close)

        debug_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="除錯", menu=debug_menu)
        debug_menu.add_command(label="印出目前完整狀態", command=lambda: logging.info(self.logic.get_full_debug_status_report()))
        debug_menu.add_command(label="印出個體特徵快取", command=lambda: logging.info(f"--- 個體特徵快取 ---\n{json.dumps(self.logic.personality_system.characteristics_cache, ensure_ascii=False, indent=2)}\n--- 快取結束 ---"))
        debug_menu.add_command(label="印出最新 LLM 提示 (下次)", command=self.logic.log_next_llm_prompt)
        debug_menu.add_separator()
        debug_menu.add_command(label="測試搜尋功能", command=lambda: self.logic.test_search())
        debug_menu.add_command(label="手動觸發一次反思", command=lambda: self.logic.personality_system.reflect_on_thoughts_async())

    def _clear_all_ui_elements(self):
        """清除 root 視窗中除了選單之外的所有元件"""
        for widget in self.root.winfo_children():
            if not isinstance(widget, tk.Menu):
                widget.destroy()

    def on_user_submit(self, event=None):
        """處理使用者從輸入框提交文字的事件"""
        if not self.user_input_entry:
            return

        user_text = self.user_input_entry.get().strip()
        if not user_text:
            return

        # 清空輸入框並顯示使用者的訊息
        self.user_input_entry.delete(0, tk.END)
        self._add_chat_message("你", user_text, "user")
        
        # 檢查是否為特殊的回饋指令
        feedback_triggers = {
            "/好棒": "positive", "/喜歡": "positive",
            "/不好": "negative", "/不喜歡": "negative",
            "/糾正": "correction", "其實應該是": "correction"
        }
        triggered_feedback_type = None
        feedback_content = ""

        for cmd, f_type in feedback_triggers.items():
            if user_text.lower().startswith(cmd):
                triggered_feedback_type = f_type
                feedback_content = user_text[len(cmd):].strip()
                break
        
        # 根據指令類型決定要執行的邏輯
        if triggered_feedback_type:
            target_method = self.logic.process_direct_user_feedback
            args = (triggered_feedback_type, feedback_content)
        else:
            target_method = self.logic.handle_user_input
            args = (user_text,)

        # 禁用輸入框，顯示思考中
        self.user_input_entry.config(state=tk.DISABLED)
        self.update_pet_appearance("thinking")

        # 使用執行緒處理耗時的邏輯，避免UI卡死
        thread = threading.Thread(target=self._process_response_worker, args=(target_method, args))
        thread.daemon = True
        thread.start()

    def _process_response_worker(self, target_method, args):
        """
        在背景執行緒中執行核心邏輯。
        target_method: 要執行的 PetLogic 中的方法。
        args: 該方法的參數元組。
        """
        try:
            # 呼叫核心邏輯
            result = target_method(*args)
            
            # 處理完畢後，將UI更新操作交回主執行緒
            if result and self.root and self.root.winfo_exists():
                self.root.after(0, self._finalize_response, result)
        except Exception as e:
            logging.error(f"Error in worker thread for {target_method.__name__}: {e}", exc_info=True)
            # 即使發生錯誤，也要確保UI可以恢復
            error_result = {
                "display_text": "處理時發生了內部錯誤...",
                "new_emotion_for_ui": "sad",
                "tag": "error"
            }
            if self.root and self.root.winfo_exists():
                self.root.after(0, self._finalize_response, error_result)
        finally:
            # 確保輸入框在任何情況下都會被重新啟用
            if self.root and self.root.winfo_exists():
                 self.root.after(1, lambda: self.user_input_entry.config(state=tk.NORMAL) if self.user_input_entry else None)

    def _finalize_response(self, result: Dict[str, Any]):
        """在主執行緒中安全地更新UI，現在會顯示內心思考。"""
        if not self.root or not self.root.winfo_exists():
            return

        # 顯示內心思考
        internal_thought = result.get("internal_thought")
        if internal_thought:
            # 使用新的 "thought" 標籤
            self._add_chat_message("小星 (思考)", internal_thought, "thought")

        # 顯示口頭回應
        if "display_text" in result and result["display_text"]:
            self._add_chat_message(
                "小星",
                result["display_text"],
                result.get("tag", "pet")
            )
        
        if "new_emotion_for_ui" in result:
            self.update_pet_appearance(result["new_emotion_for_ui"])
            
        if self.user_input_entry:
            self.user_input_entry.config(state=tk.NORMAL)
            self.user_input_entry.focus_set()

    def _add_chat_message(self, sender: str, message: str, tag: str):
        """安全地將訊息新增到聊天視窗"""
        if not self.chat_history_text or not self.chat_history_text.winfo_exists():
            logging.warning(f"Chat history UI not available for message: [{sender}]")
            return
        try:
            message_str = str(message)
            self.chat_history_text.config(state=tk.NORMAL)
            
            # 確保訊息之間有換行
            if self.chat_history_text.index('end-1c') != "1.0":
                self.chat_history_text.insert(tk.END, "\n")
            
            timestamp = datetime.now().strftime("%H:%M")
            display_message = message_str[:1000] + ("..." if len(message_str) > 1000 else "")
            
            formatted_message = f"[{timestamp}] {sender}: {display_message}"
            self.chat_history_text.insert(tk.END, formatted_message, tag)
            self.chat_history_text.see(tk.END) # 自動捲動到底部
            self.chat_history_text.config(state=tk.DISABLED)
        except tk.TclError as e:
            logging.error(f"TclError adding chat message (widget might be destroyed): {e}")

    def update_pet_appearance(self, emotion_key: str):
        """根據情緒鍵名更新寵物圖片"""
        if not self.pet_img_label or not self.pet_img_label.winfo_exists():
            return

        img_path = config.EMOTION_IMAGES.get(emotion_key, config.DEFAULT_IMG_PATH)
        if not os.path.exists(img_path):
            img_path = config.DEFAULT_IMG_PATH # 如果找不到對應圖片，使用預設圖片
        
        try:
            img = Image.open(img_path).convert("RGBA")
            img.thumbnail((150, 150))
            self.current_pet_image = ImageTk.PhotoImage(img)
            self.pet_img_label.config(image=self.current_pet_image)
        except Exception as e:
            logging.error(f"Error loading image {img_path}: {e}", exc_info=True)
            self.pet_img_label.config(image=None, text=f"圖片錯誤:\n{emotion_key}")

    def _periodic_update(self):
        """
        定期執行的背景任務，用於觸發寵物的主動行為和狀態更新。
        """
        if self.logic.is_processing_llm: # 如果正在處理使用者輸入，則跳過此次主動行為
            self.root.after(10000, self._periodic_update)
            return

        # 執行緒化以避免阻塞UI
        thread = threading.Thread(target=self._periodic_worker)
        thread.daemon = True
        thread.start()

        # 重新排程下一次更新
        self._periodic_update_id = self.root.after(random.randint(15000, 25000), self._periodic_update)

    def _periodic_worker(self):
        """在背景執行緒中執行定期的核心邏輯檢查"""
        try:
            # 1. 執行核心邏輯的定期維護
            maintenance_result = self.logic.periodic_maintenance()
            if maintenance_result and self.root and self.root.winfo_exists():
                self.root.after(0, self.update_pet_appearance, maintenance_result["new_emotion_for_ui"])

            # 2. 檢查是否有主動行為
            proactive_result = self.logic.check_for_proactive_action()
            if proactive_result and self.root and self.root.winfo_exists():
                self.root.after(0, self._finalize_response, proactive_result)

            # 3. 檢查是否有任務提醒
            reminder_result = self.logic.check_task_reminders()
            if reminder_result and self.root and self.root.winfo_exists():
                self.root.after(0, self._finalize_response, reminder_result)
        except Exception as e:
            logging.error(f"Error in periodic_worker thread: {e}", exc_info=True)

    def _open_settings(self):
        """打開設定視窗"""
        if self.settings_window_instance and self.settings_window_instance.winfo_exists():
            self.settings_window_instance.lift()
            self.settings_window_instance.focus_set()
        else:
            # 將 self (即 MainWindow 的實例) 傳遞給 SettingsWindow
            self.settings_window_instance = SettingsWindow(self.root, self.logic, self)

    def on_close(self):
        """處理應用程式關閉事件"""
        logging.info("Close button clicked. Shutting down.")
        if self._periodic_update_id:
            self.root.after_cancel(self._periodic_update_id)
            self._periodic_update_id = None
        
        # (可選) 可以在此處加入儲存最終狀態的邏輯
        
        self.root.destroy()