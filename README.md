# DeskWifu 小星桌寵 (版本 1.3.0 - 搜尋進化版)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Collaboration Effort / 合作成果 ✨

**English:**
This project is a collaborative creation by xdrxdrxd, with significant contributions, brainstorming, and code generation assistance from multiple AI models, including **Google Gemini**, **OpenAI ChatGPT**, and **xAI Grok**. It represents a fusion of human creativity and AI capabilities.

**中文:**
本專案由 xdrxdrxd 主導，並在 **Google Gemini**、**OpenAI ChatGPT** 及 **xAI Grok** 等多個大型語言模型的深度參與、腦力激盪與程式碼生成協助下共同建構而成，是人類創意與 AI 智慧的結晶。

---

## 📝 English Abstract

DeskWifu (小星桌寵) is an advanced Python-based interactive desktop pet application. Powered by Google Gemini API for natural language conversations and Google Custom Search API for web searching capabilities, 小星 simulates emotions, maintains short-term and long-term memory in SQLite, and learns individual characteristics. The application features a Tkinter GUI, extensive customization options for personality, emotional responses, appearance, sleep schedules, and now includes the ability to search the web for current events or to answer user queries, with safeguards for API usage.

---

## 📋 Table of Contents / 目錄

- [Features / 主要功能](#-features--主要功能)
- [Important Security & Privacy Notes / 重要安全與隱私說明](#️-important-security--privacy-notes--重要安全與隱私說明)
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

### 🌐 **NEW: Web Search Integration / 網路搜尋整合**
- **LLM-Driven Search:** 小星 can decide to search the web for information it doesn't know or to get context for current events, using Google Custom Search API.
- **First-Time Personality Seeding:** Optionally uses web search on first run to gather random data for initial personality traits.
- **Daily News Fetching:** Optionally fetches daily news summaries to stay updated (user-configurable).
- **API Usage Control:** Includes basic daily call count tracking and error handling for search API quota.

### 😄 Natural Emotional Simulation / 動態情緒系統
- Mimics a wide range of emotions based on interaction, time, learned traits, and personality, with time-based decay.
- Emotion changes trigger different images (e.g., `happy.png`, `sad.png`, etc.).

### 🧠 Organic Memory & Learning System / 記憶與學習系統
- Stores short/long-term memory in SQLite.
- **Advanced Characteristic Learning:** Learns individual characteristics (preferences, habits, user info, pet's self-concept, quirks, favorite topics) from user interactions and its own responses via LLM analysis and regex patterns.
- Characteristics have relevance scores, decay over time, and can be managed/viewed in settings.
- Memory and learned traits influence chat topics, response style, and proactive interactions.

### 🧬 Personality Traits (OCEAN) & Demographics / OCEAN五大性格與背景
- Adjust OCEAN traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
- Set demographic background (culture, age group, gender) influencing language and perspectives.
- Traits and demographics affect response style, proactive chat frequency, emotional reactions, and web search decisions.

### 📋 Task Management / 任務管理
- Add, view, mark complete, and delete tasks.
- Pet may remind you of incomplete tasks based on its Conscientiousness and conversation context.

### 🕒 Sleep Schedule / 作息時間
- Set pet's sleep and wake times.
- During sleep time, pet shows sleeping state and won't initiate chats or perform most background tasks.

### 🔄 Ongoing Proactivity / 主動互動
- Regularly initiates conversations or emotional expressions based on interval settings, personality, learned traits, and current emotional state.
- If inactive for a long time, pet may feel bored or sad and talk to itself.

### 🎨 Appearance Customization / 可自訂外觀
- Replace emotion-specific images to customize appearance for different moods. (Default images included)

### ⚙️ Rich Settings Options / 豐富的設定選項
- **General:** Proactive chat frequency, user location (for weather/context).
- **Emotion:** Mood stability, emotional sensitivity, decay rate.
- **Response:** Simulated response delay.
- **API & Model:**
    - Select Gemini LLM model (Flash/Pro).
    - Configure Gemini API Key.
    - **NEW:** Configure Custom Search API Key and Search Engine ID (CX).
    - **NEW:** Enable/disable web search and daily news search.
    - Adjust LLM temperature and max output tokens.
- **Personality & Background:** Adjust OCEAN traits and demographic info.
- **Learned Characteristics:** View, filter, sort, and delete learned individual traits.
- **Current Emotions:** Real-time display of pet's emotional state.
- Sleep schedule, STM retention days, etc.

### 💾 Data Persistence / 資料庫儲存
- All emotions, memories, settings, API keys, tasks, learned characteristics, and personality traits are stored persistently in a local SQLite database (`pet_data.db`).

---

## ⚠️ Important Security & Privacy Notes / 重要安全與隱私說明

**Please read these points carefully before using DeskWifu, especially if you plan to use the API-dependent features.**

1.  **API Key Storage and Risk:**
    * To use AI chat (Google Gemini) and web search (Google Custom Search), you need to provide your own API keys.
    * **These API keys will be stored locally in the `pet_data.db` SQLite database file in the application's directory.**
    * While the application itself doesn't transmit your keys elsewhere, anyone with direct access to this `pet_data.db` file on your computer could potentially extract these keys.
    * **Protect this file as you would any sensitive information.**
    * Misuse of your API keys by unauthorized parties could lead to unexpected charges on your Google Cloud Platform (GCP) account or API quota exhaustion.
    * **It is highly recommended to set up budget alerts and API usage quotas in your GCP console for the Gemini API and Custom Search API.**

2.  **Data Collection and Privacy:**
    * DeskWifu records and stores various data locally in `pet_data.db` to personalize your experience, including:
        * Chat history (short-term and long-term memory).
        * Your expressed preferences, habits, and other information inferred by the LLM.
        * The pet's emotional history and learned personality traits.
        * Task lists and application settings.
    * **Be mindful of the information you share during chats, as it may be stored.**
    * If privacy is a major concern, you might want to periodically review or clear the `pet_data.db` file (this will reset the pet). Future versions may include in-app data clearing options.

3.  **Web Search Content:**
    * The web search feature uses Google Custom Search. While you can configure safe search in your Custom Search Engine settings, the internet is vast.
    * The application attempts to use search results responsibly, but it's not responsible for the content of external websites or search snippets.
    * You can disable the web search feature entirely in the settings if desired.

4.  **Third-Party Services:**
    * Use of this application involves making calls to third-party services (Google Gemini API, Google Custom Search API). Your use of these services is subject to their respective terms of service and privacy policies.

**By using this application, you acknowledge and accept these risks and responsibilities.**

---

## 💻 Requirements / 環境需求

-   Python 3.8 or above
-   SQLite3 (usually included with Python)
-   Python packages:
    -   `tkinter` (usually included with Python)
    -   `google-generativeai` (for Gemini API)
    -   `google-api-python-client` (for Custom Search API)
    -   `Pillow` (for image processing)

> You can install the necessary Python packages using the `requirements.txt` file (if provided) or individually:
> ```bash
> pip install google-generativeai google-api-python-client Pillow
> ```
> (If you provide a `requirements.txt`, update it to include `google-api-python-client`)

---

## 🧰 Installation / 安裝步驟

1.  Clone the repository:
    ```bash
    git clone [https://github.com/xdrxdrxd/DeskWifu.git](https://github.com/xdrxdrxd/DeskWifu.git)
    ```
2.  Navigate to the project directory:
    ```bash
    cd DeskWifu
    ```
3.  (Optional, if `requirements.txt` is provided) Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Ensure you have the necessary image files (e.g., `default.png`, `happy.png`, etc.) in the same directory as the script, or update paths in the `EMOTION_IMAGES` dictionary in the script.
5.  Run the application:
    ```bash
    python DeskWifu_1.3.0.py 
    ```
    (Replace `DeskWifu_1.3.0.py` with the actual script name if different)

---

## 🛠️ Configuration / 設定

1.  **Database:**
    * The `pet_data.db` SQLite database file will be automatically created in the application directory upon first launch if it doesn't exist.

2.  **API Keys (Crucial for Full Functionality):**
    * **Google Gemini API Key:**
        * Open the application, go to "File" -> "Settings".
        * Navigate to the "API & Model" tab.
        * Click "Set/Change Gemini API Key" and enter your key.
        * Select your preferred Gemini model (e.g., `gemini-1.5-flash`).
    * **Google Custom Search API Key & Search Engine ID (CX):**
        * You need to create a Programmable Search Engine in your Google Cloud Console or Programmable Search Engine control panel.
        * **Configure this search engine to "Search the entire web" if you want broad search capabilities.**
        * Obtain your **API Key** for the Custom Search JSON API.
        * Obtain your **Search Engine ID (CX)** from your Programmable Search Engine settings.
        * In DeskWifu's settings ("API & Model" tab), enter these into the "Custom Search API Key" and "Search Engine ID (CX)" fields.

3.  **Web Search Features:**
    * In the "API & Model" tab in settings, you can:
        * Enable or disable the overall "Web Search Feature".
        * Enable or disable "Daily Automated News Search".

4.  **Other Settings:**
    * All other parameters (personality, emotions, behavior, etc.) can be adjusted through the "Settings" window in their respective tabs. Click "Apply All Changes" to save.

---

## ▶️ Usage / 如何使用

1.  Launch the application (`python DeskWifu_1.3.0.py`).
2.  The 小星 desktop pet window will appear.
3.  **Crucially, configure your API keys via "File" -> "Settings" -> "API & Model" tab for AI chat and web search features to work.**
4.  Customize other parameters as desired in the settings.
5.  Interact with 小星 by typing in the chat input field and pressing Enter or clicking "Send".
6.  Observe its emotional responses, memory recall, learned traits, and potential web search actions!

---

## 🧑‍🎨 Customization / 自訂

-   **Images:**
    * Default emotion images (e.g., `happy.png`, `sad.png`, `neutral.png`, `thinking.png`, etc.) should be placed in the same directory as the script or their paths updated in the `EMOTION_IMAGES` dictionary within the script.
    * You can replace these images with your own, keeping the filenames consistent for automatic loading based on emotion.
-   **Database:**
    * Advanced users can inspect the `pet_data.db` file using an SQLite browser, but direct modification is not recommended unless you know what you're doing, as it might corrupt the pet's state.

---

## 🤝 Contributing / 貢獻

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
Please ensure any contributions align with the project's goal of creating an engaging and customizable desktop companion, while also considering user privacy and API usage responsibility.

---

## 📜 License / 授權條款

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (if you create one, or link to the standard MIT license text).
---
---
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
  - `google.generativeai` *(for Gemini models)*
  - `Pillow`

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
├── DeskWifu_1.0.0.py
├── pet_data.db
├── default.png
├── happy.png
...
├── README.md
└── requirements.txt
```

---

## 🤝 Contributing / 貢獻

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License / 授權條款

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
