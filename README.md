# DeskWifu-Gemini - AI Emotional Desktop Pet (AI 情感桌面寵物)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**(建議在此處插入一張應用程式截圖或 GIF 動畫 / Recommended: Insert a screenshot or GIF here)**
## ✨ Collaboration Effort / 合作成果 ✨

**English:** This project is a collaborative creation by xdrxdrxd, with significant contributions, brainstorming, and code generation assistance from multiple AI models, including **Google Gemini**, **OpenAI ChatGPT**, and **xAI Grok**. It represents a fusion of human creativity and AI capabilities.

**中文:** 本專案由 xdrxdrxd 主導，並在 **Google Gemini**、**OpenAI ChatGPT** 及 **xAI Grok** 等多個大型語言模型的深度參與、腦力激盪與程式碼生成協助下共同建構而成，是人類創意與 AI 智慧的結晶。

## 📝 English Abstract

DeskWifu-Gemini is a Python-based desktop pet application featuring an AI companion powered by Google Gemini. It simulates emotions, maintains short-term and long-term memory stored in SQLite, and interacts with the user through natural language chat. The application leverages Tkinter for its graphical interface and offers high customization through user settings, allowing adjustments to personality traits, emotional responses, appearance, and more.

## 📋 Table of Contents / 目錄

* [Features / 主要功能](#-features--主要功能)
* [Requirements / 環境需求](#-requirements--環境需求)
* [Installation / 安裝步驟](#-installation--安裝步驟)
* [Configuration / 設定](#️-configuration--設定)
* [Usage / 如何使用](#️-usage--如何使用)
* [Customization / 自訂](#️-customization--自訂)
* [Project Structure / 專案結構](#-project-structure--專案結構)
* [Contributing / 貢獻](#-contributing--貢獻)
* [License / 授權條款](#-license--授權條款)

## ✨ Features / 主要功能

* **🤖 AI Interaction / AI 互動聊天:**
    * **EN:** Powered by Google Gemini (Flash/Pro models) for natural language conversations.
    * **中:** 由 Google Gemini (Flash/Pro 模型) 提供支援，能進行自然流暢的對話。
* **🎭 Emotion Simulation / 情感模擬:**
    * **EN:** Possesses various emotional states (e.g., happy, sad, bored, anxious) influenced by time, interaction (via LLM analysis), and traits. Includes decay over time.
    * **中:** 擁有多種情緒狀態（如開心、難過、無聊、焦慮等），情緒會隨時間自然衰減、受對話內容影響 (透過 LLM 分析)、受一天中的時間影響，並可調整相關參數。
* **🧠 Memory System / 記憶系統:**
    * **EN:** Features short-term and long-term memory persistence using SQLite. Includes simulated forgetting and recall mechanisms based on configurable chances.
    * **中:** 具備短期記憶和長期記憶 (使用 SQLite 資料庫)。會根據對話內容自動儲存記憶，並模擬記憶遺忘和回憶的過程 (機率可設定)。
* **🎨 High Customization / 高度自訂化:**
    * **EN:** Rename the pet (default: "小星"). Import custom images for different emotional states. Access a graphical settings window to adjust personality traits (optimism, anxiety), emotional responses (stability, sensitivity), behavior patterns (proactive chat frequency, response delay), LLM parameters (temperature, max tokens), and memory settings (retention days, forget/recall chance).
    * **中:** 可為寵物**重新命名** (預設為 "小星")。可**匯入自訂圖片**作為寵物不同情緒的形象。提供**圖形化設定介面**，可調整個性特質、情緒反應、行為模式、LLM 參數及記憶相關設定。
* **🗣️ Colloquial Language / 口語化表達:**
    * **EN:** Simulates colloquialisms often used by young people in Taiwan for more lively chat.
    * **中:** 模擬台灣年輕人常用口頭禪，讓對話更生動。
* **🕰️ Proactive Interaction / 定期互動:**
    * **EN:** Initiates conversations or expresses status periodically based on configured frequency.
    * **中:** 會根據設定的頻率主動發起對話或表達狀態。
* **💾 State Persistence / 狀態儲存:**
    * **EN:** Emotions, memories, API Key, and all settings are saved automatically and restored on next launch.
    * **中:** 情緒、記憶、API Key 和所有設定都會自動儲存，下次開啟時恢復。

## 📋 Requirements / 環境需求

* Python 3.8 or higher
* Third-party libraries (see `requirements.txt`):
    * `Pillow` (for image processing)
    * `google-generativeai` (for Google Gemini API)
* Google AI Gemini API Key (obtain it yourself)
* Operating System: Windows, macOS, Linux (may require installing `python3-tk` package)

## 🚀 Installation / 安裝步驟

1.  **Clone Repository:**
    ```bash
    git clone [https://github.com/](https://github.com/)[Your_GitHub_Username]/[Your_Repository_Name].git
    cd [Your_Repository_Name]
    ```
    *(Replace `[Your_GitHub_Username]` and `[Your_Repository_Name]`)*

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Recommended to use a virtual environment)*

3.  **Prepare Image Files:**
    * Ensure the following image files are present in the repository directory or provide your own:
        * `default.png` (fallback image)
        * `happy.png`, `sad.png`, `neutral.png`, `excited.png`, `angry.png`, `anxious.png`
    * If `default.png` is missing, the app attempts to copy it from `happy.png` or creates a placeholder.
    * You can change the pet's base appearance via the "File" -> "Import Image..." menu.

## ⚙️ Configuration / 設定

* **Google AI Gemini API Key:**
    * On the first run (or if the key is missing), the application will prompt you to enter your Google AI Gemini API Key.
    * The key is stored locally in the `pet_data.db` SQLite file.
    * Use the "File" -> "Clear API Key..." menu option to remove the saved key.

## ▶️ Usage / 如何使用

1.  Run the main script:
    ```bash
    python DeskWifu.py
    ```
2.  Enter your User ID when prompted (optional, used to separate data if multiple users share the app).
3.  Enter your API Key if prompted.
4.  Start chatting with your desktop pet in the input box at the bottom! Press Enter to send.
5.  Use the top menu bar for various actions:
    * **File:** Import Image, Rename Pet, Open Settings, Clear API Key, Exit.
    * **Status:** View detailed emotion/personality status, View memories.

## 🛠️ Customization / 自訂

* **Appearance / 外觀:** Use "File" -> "Import Image..." to change the pet's main look. Replace emotion-specific images (like `happy.png`, `sad.png`) to customize its appearance for different moods.
* **Name / 名稱:** Use "File" -> "Rename..." to give your pet a new name.
* **Behavior & Personality / 行為與個性:** Use "File" -> "Open Settings..." to access the detailed settings window and fine-tune parameters to shape a unique personality.

## 📁 Project Structure / 專案結構

```
.
├── DeskWifu.py         # Main application script / 主應用程式腳本
├── pet_data.db         # SQLite database file (stores state, memory, settings) / SQLite 資料庫檔案
├── default.png         # Default image / 預設圖片
├── happy.png           # Emotion images... / 各種情緒圖片...
├── sad.png
├── neutral.png
├── excited.png
├── angry.png
├── anxious.png
├── requirements.txt    # Python dependencies list / Python 依賴套件列表
├── LICENSE             # MIT License file / MIT 授權條款檔案
└── README.md           # This README file / 本說明檔案
```

## 🤝 Contributing / 貢獻

Issues and Pull Requests are welcome! Feel free to report bugs or suggest features.
(Add more detailed contribution guidelines here if needed)

歡迎提出 Issue 或 Pull Request！如果你有任何建議或發現 Bug，請隨時告知。
(如果需要，可以在此處加入更詳細的貢獻指南)

## 📄 License / 授權條款

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

本專案採用 MIT 授權條款。詳情請見 [LICENSE](LICENSE) 檔案。
