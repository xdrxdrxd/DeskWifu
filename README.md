
# DeskWifu 小星桌寵 (版本 1.0.0)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Collaboration Effort / 合作成果 ✨

**English:**  
This project is a collaborative creation by xdrxdrxd, with significant contributions, brainstorming, and code generation assistance from multiple AI models, including **Google Gemini**, **OpenAI ChatGPT**, and **xAI Grok**. It represents a fusion of human creativity and AI capabilities.

**中文:**  
本專案由 xdrxdrxd 主導，並在 **Google Gemini**、**OpenAI ChatGPT** 及 **xAI Grok** 等多個大型語言模型的深度參與、腦力激盪與程式碼生成協助下共同建構而成，是人類創意與 AI 智慧的結晶。

---

## 📝 English Abstract

DeskWifu (小星桌寵) is a Python-based interactive desktop pet application powered by Google Gemini API. It simulates emotions, maintains short-term and long-term memory stored in SQLite, and interacts with the user through natural language chat. The application leverages Tkinter for its graphical interface and offers high customization through user settings, allowing adjustments to personality traits, emotional responses, appearance, and more.

---

## 📋 Table of Contents / 目錄

- [Features / 主要功能](#-features--主要功能)
- [Requirements / 環境需求](#-requirements--環境需求)
- [Installation / 安裝步驟](#-installation--安裝步驟)
- [Configuration / 設定](#️-configuration--設定)
- [Usage / 如何使用](#️-usage--如何使用)
- [Customization / 自訂](#️-customization--自訂)
- [Project Structure / 專案結構](#-project-structure--專案結構)
- [Contributing / 貢獻](#-contributing--貢獻)
- [License / 授權條款](#-license--授權條款)

---

## ✨ Features / 主要功能

### 💬 AI-Powered Conversations / 智慧聊天
- Powered by Google Gemini (Flash/Pro models) for natural, contextual dialogues.
- Simulates modern, casual slang used by young people in Taiwan for relatable chats.

### 😄 Natural Emotional Simulation / 動態情緒系統
- Mimics emotions (happy, sad, bored, anxious) based on interaction, time, and traits, with time-based decay.
- Emotion changes trigger different images (e.g., `happy.png`, `sad.png`, etc.).

### 🧠 Organic Memory System / 記憶系統
- Stores short/long-term memory in SQLite, simulates forgetting/recall with customizable probabilities.
- Memory content influences chat topics and references to past events.

### 🧬 Personality Traits (OCEAN) / OCEAN 五大性格特質
- Adjust traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
- Traits affect response style, proactive chat frequency, and content.

### 📋 Task Management / 任務管理
- Add, view, mark complete, and delete tasks via settings window.
- Pet may remind you of incomplete tasks based on Conscientiousness trait.

### 🕒 Sleep Schedule / 作息時間
- Set pet's sleep and wake times.
- During sleep time, pet shows sleeping state and won't initiate chats.

### 🔄 Ongoing Proactivity / 主動互動
- Regularly initiates conversations or emotional expressions based on interval settings and personality traits.
- If inactive for a long time, pet may feel bored or sad and talk to itself.

### 🎨 Appearance Customization / 可自訂外觀
- Change pet's base appearance via "File" -> "Import Image...".
- Replace emotion-specific images to customize appearance for different moods.

### ⚙️ Rich Settings Options / 豐富的設定選項
- Adjust emotional response parameters (sensitivity, stability, decay speed, etc.).
- Behavior pattern parameters (proactive chat frequency, response delay simulation, memory forget/recall probabilities, etc.).
- LLM settings (response temperature, max tokens, model selection).
- Sleep schedule, location (for potential future weather features), etc.

### 💾 Data Persistence / 資料庫儲存
- All emotions, memories, settings, API keys, and tasks are stored persistently in SQLite database (`pet_data.db`).

---

## 💻 Requirements / 環境需求

- Python 3.8 or above  
- SQLite3  
- Python packages:
  - `tkinter`
  - `requests`
  - `openai` *(if you use OpenAI models)*
  - `google.generativeai` *(for Gemini models)*
  - `Pillow`
  - `pyttsx3` *(optional, for voice playback)*

> Install dependencies via:
```bash
pip install -r requirements.txt
```

---

## 🧰 Installation / 安裝步驟

```bash
git clone https://github.com/xdrxdrxd/DeskWifu.git
cd DeskWifu
python main.py
```

---

## 🛠️ Configuration / 設定

- 在首次啟動時會自動建立資料庫 `pet_data.db`  
- 開啟「設定」視窗以輸入你的 Gemini API 金鑰與模型名稱  
- 所有參數皆可透過設定視窗進行調整，包括記憶機率、性格傾向與情緒靈敏度等

---

## ▶️ Usage / 如何使用

1. 啟動程式後，桌面上會出現一個小星桌寵視窗  
2. 點選「設定」可自訂所有參數  
3. 點選「檔案」可匯入新的圖片或資料庫  
4. 開始與桌寵互動並觀察牠的情緒與回應變化！

---

## 🧑‍🎨 Customization / 自訂

- 預設圖像位置：`images/`  
- 更換對應情緒圖檔（檔名需保持一致如 `happy.png`）  
- 更換資料庫檔案：點選「檔案」>「切換資料庫...」  

---

## 📁 Project Structure / 專案結構

```
DeskWifu/
├── main.py
├── gui.py
├── ai_logic.py
├── memory.py
├── emotion.py
├── settings.py
├── tasks.py
├── database/
│   └── pet_data.db
├── images/
│   ├── default.png
│   ├── happy.png
│   ├── sad.png
│   └── ...
├── README.md
└── requirements.txt
```

---

## 🤝 Contributing / 貢獻

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License / 授權條款

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
