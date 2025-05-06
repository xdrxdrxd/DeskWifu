# DeskWifu-Gemini - AI Emotional Desktop Pet (AI 情感桌面寵物)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

* AI-Powered Conversations: Powered by Google Gemini (Flash/Pro models) for natural, contextual dialogues.
* Natural Emotional Simulation: Mimics emotions (happy, sad, bored, anxious) based on interaction, time, and traits, with time-based decay.
* Organic Memory System: Stores short/long-term memory in SQLite, simulates forgetting/recall with customizable probabilities.
* Name & Image Customization: Rename your pet and import custom emotion images; default name is "小星".(In development)
* Trait Configuration: Graphical settings interface to adjust traits (optimism, anxiety), emotional reactivity, and behavior patterns.
* Output Modulation: Fine-tune Gemini’s output using parameters like temperature and max tokens for personality shaping.
* Key Retention: Gemini API Key is securely stored and reused unless manually cleared.
* Youthful Colloquialism: Simulates modern, casual slang used by young people in Taiwan for relatable chats.
* Ongoing Proactivity: Regularly initiates conversations or emotional expressions based on interval settings.

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
* **Name / 名稱:** Use "File" -> "Rename..." to give your pet a new name.(In development)
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
