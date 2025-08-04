# main.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import os
import config
from database import DatabaseManager
from services.llm_service import GeminiService
from services.search_service import GoogleSearchService
from core.pet_logic import PetLogic
from ui.main_window import MainWindow

def setup_logging():
    """設定日誌記錄器"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(module)s.%(funcName)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler("deskwifu_log.txt", encoding='utf-8', mode='w'),
            logging.StreamHandler()
        ]
    )

def ensure_assets_exist():
    """檢查必要的 assets 檔案是否存在，如果不存在則嘗試創建"""
    if not os.path.exists(config.ASSETS_DIR):
        os.makedirs(config.ASSETS_DIR)
        logging.info(f"Created assets directory at: {config.ASSETS_DIR}")

    if not os.path.exists(config.DEFAULT_IMG_PATH):
        try:
            from PIL import Image
            import shutil
            source_img_path = None
            if os.path.exists(config.EMOTION_IMAGES.get("neutral")):
                source_img_path = config.EMOTION_IMAGES.get("neutral")
            elif os.path.exists(config.EMOTION_IMAGES.get("happy")):
                source_img_path = config.EMOTION_IMAGES.get("happy")

            if source_img_path:
                shutil.copy(source_img_path, config.DEFAULT_IMG_PATH)
                logging.info(f"Default image not found, copied from {os.path.basename(source_img_path)}")
            else:
                img = Image.new('RGBA', (150, 150), (200, 200, 200, 255))
                img.save(config.DEFAULT_IMG_PATH)
                logging.warning("No base emotion images found. Created a placeholder default.png.")
        except Exception as e:
            logging.error(f"Error handling missing default image: {e}")

def main():
    """應用程式的主入口點，負責組裝所有元件。"""
    setup_logging()
    ensure_assets_exist()

    root = tk.Tk()
    root.withdraw()

    try:
        db_manager = DatabaseManager(config.DB_PATH)
    except Exception as e:
        logging.critical(f"FATAL: Failed to initialize DatabaseManager: {e}", exc_info=True)
        messagebox.showerror("嚴重錯誤", f"無法初始化資料庫，應用程式無法啟動。\n錯誤: {e}")
        root.destroy()
        return

    gemini_api_key = db_manager.get_api_key('gemini_api_key')
    search_api_key = db_manager.get_api_key('custom_search_api_key')
    search_cx_id = db_manager.get_api_key('custom_search_cx_id')

    llm_service = None
    if gemini_api_key:
        try:
            model_name = db_manager.load_app_setting(
                config.SETTING_SELECTED_LLM,
                config.DEFAULT_APP_SETTINGS[config.SETTING_SELECTED_LLM]
            )
            llm_service = GeminiService(api_key=gemini_api_key, model_name=model_name)
        except Exception as e:
            logging.error(f"Failed to initialize GeminiService on startup: {e}", exc_info=True)
            messagebox.showwarning("LLM 警告", f"啟動時初始化 Gemini 模型失敗：{e}\n將以有限模式啟動，請檢查設定。")
            llm_service = None

    search_service = GoogleSearchService(api_key=search_api_key, cx_id=search_cx_id)

    pet_logic = PetLogic(
        db_manager=db_manager,
        llm_service=llm_service,
        search_service=search_service
    )

    # --- *** 新增的觸發點 *** ---
    # 在 PetLogic 初始化後，立即觸發一次性的個性化搜尋
    pet_logic.initial_personality_setup_async()
    # --- *** 觸發點結束 *** ---

    style = ttk.Style(root)
    available_themes = style.theme_names()
    if 'clam' in available_themes: style.theme_use('clam')
    elif 'vista' in available_themes: style.theme_use('vista')
    else:
        if available_themes: style.theme_use(available_themes[0])

    app_ui = MainWindow(root, pet_logic)
    
    root.deiconify()

    logging.info("Application startup successful. Entering main loop.")
    root.mainloop()

if __name__ == "__main__":
    main()