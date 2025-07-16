# DeskWifu 小星桌寵 (版本 1.5.0 - 認知進化版)

**Collaboration Effort / 合作成果**

**English:** This project is a collaborative creation by xdrxdrxd, with significant contributions, brainstorming, and code generation assistance from multiple AI models, including Google Gemini, OpenAI ChatGPT, and xAI Grok. It represents a fusion of human creativity and AI capabilities.

**中文:** 本專案由 xdrxdrxd 主導，並在 Google Gemini、OpenAI ChatGPT 及 xAI Grok 等多個大型語言模型的深度參與、腦力激盪與程式碼生成協助下共同建構而成，是人類創意與 AI 智慧的結晶。

---

**English Abstract**

DeskWifu (小星桌寵) v1.5.0 is a significant evolution, transforming the interactive desktop pet into a sophisticated digital agent with a simulated cognitive architecture. Powered by the Google Gemini API for conversations and Google Custom Search for real-world knowledge, 小星 now features an **advanced emotional core** driven by valence-arousal models, a **simulated neurochemical state** (influencing motivation, stress, and mood), and implements psychological concepts like **attachment theory** and **self-efficacy**. It learns not only from user interaction but through **LLM-powered self-reflection** on its own thoughts and responses. This version represents a deeper attempt at simulating a believable, dynamic, and adaptive digital consciousness.

---

**Table of Contents / 目錄**

1.  [Features / 主要功能](#-features--主要功能)
2.  [Important Security & Privacy Notes / 重要安全與隱私說明](#️-important-security--privacy-notes--重要安全與隱私說明)
3.  [Requirements / 環境需求](#-requirements--環境需求)
4.  [Installation / 安裝步驟](#-installation--安裝步驟)
5.  [Configuration / 設定](#️-configuration--設定)
6.  [Usage / 如何使用](#️-usage--如何使用)
7.  [Customization / 自訂](#-customization--自訂)
8.  [Contributing / 貢獻](#-contributing--貢獻)
9.  [License / 授權條款](#-license--授權條款)

---

## Features / 主要功能

### NEW: Advanced Cognitive & Emotional Core / 先進的認知與情感核心

-   **Simulated Neurochemistry (`sim_neuro_state`):** 模擬一個內在的神經化學狀態（如動機、壓力、情緒平衡、社交溫暖），動態地影響寵物的行為、情緒穩定性和主動性。
-   **Core Affect Model (Valence/Arousal):** 情感系統由更底層的「效價」（愉悅/不悅）和「喚醒度」（激動/平靜）模型驅動，產生更自然、更細膩的離散情緒表現。
-   **Attachment Theory Implementation:** 小星對使用者的「依戀分數」會根據互動品質（如陪伴、讚美、忽視）而變化，深刻影響其語氣、關心程度和分享意願。
-   **Self-Efficacy Model:** 模擬在不同領域（社交、任務管理、資訊檢索）的「自我效能感」（自信心），影響其行為的主動性和成功/失敗後的反應。
-   **Emotion Regulation:** 當偵測到強烈的負面情緒時，小星會嘗試「自我調節」，透過 LLM 生成應對想法來平復心情。

### AI-Powered Conversations & Hybrid Thinking / 智慧聊天與混合思維

-   由 Google Gemini (Flash/Pro) 提供支援，進行自然、有上下文的對話。
-   **Hybrid Thinking (System 1/2):** 採用混合思維架構，對簡單的互動（如問候）進行快速、基於規則的「系統一」回應；對複雜對話則啟用完整的「系統二」LLM 思考，兼顧效率與深度。

### Web Search Integration / 網路搜尋整合

-   **LLM-Driven Search:** 小星可以自行決定搜尋牠不知道的資訊，或獲取時事背景，使用 Google Custom Search API。
-   **Daily News Fetching:** 可選擇每日自動獲取新聞摘要，讓小星「了解」時事。
-   **First-Time Personality Seeding:** 可選擇在首次運行時透過搜尋隨機資料來豐富其初始個性。

### Organic Memory & Learning System / 記憶與學習系統

-   **LLM-Powered Memory Summarization:** 重要的短期記憶會由 LLM 進行「總結」，轉化為更抽象的長期記憶儲存在 SQLite 中。
-   **Self-Reflection Learning:** 小星會定期「反思」自己記錄下來的「內心思考」和「口頭回應」，從中提取新的自我認知、興趣點或行為模式，實現真正的自我成長。
-   **Advanced Characteristic Learning:** 透過 LLM 分析和正則表達式，深入學習使用者的偏好、習慣、個人資訊，以及寵物自身的口頭禪、語言風格和自我概念。

### Personality Traits (OCEAN) & Demographics / OCEAN五大性格與背景

-   可自由調整 OCEAN 五大性格特質：經驗開放性 (O)、盡責性 (C)、外向性 (E)、親和性 (A)、神經質性 (N)。
-   可設定文化、年齡、性別等背景，影響其語言風格和觀點。

### Task Management & Other Features / 任務管理與其他功能

-   完整的任務管理功能：新增、檢視、完成和刪除任務。
-   **作息時間：** 可設定睡眠和起床時間，影響其行為和狀態。
-   **主動互動：** 會根據其內在狀態（個性、情緒、動機）主動發起對話或自言自語。
-   **豐富的設定選項：** 提供極其詳細的設定視窗，可調整幾乎所有認知、情感和行為參數。
-   **資料庫儲存：** 所有狀態（情感、記憶、個性、設定、API金鑰等）都儲存在本地的 `pet_data.db` 檔案中。

---

## Important Security & Privacy Notes / 重要安全與隱私說明

在使用 DeskWifu 前，請仔細閱讀以下說明，特別是當您計劃使用 API 功能時。

-   **API 金鑰儲存與風險:**
    -   AI 聊天（Google Gemini）和網路搜尋（Google Custom Search）功能需要您提供自己的 API 金鑰。
    -   這些金鑰將以**明文形式**儲存在您電腦上的 `pet_data.db` 檔案中。**請像保護敏感檔案一樣保護此資料庫檔案**。
    -   任何能存取此檔案的人都可能獲取您的金鑰，這可能導致您的 Google Cloud Platform (GCP) 帳戶產生非預期費用。
    -   強烈建議您在 GCP 控制台中為相關 API 設定**預算提醒**和**用量配額**。

-   **資料收集與隱私:**
    -   本應用會在本地 `pet_data.db` 中記錄大量資料以個人化體驗，包括：聊天紀錄、由 LLM 推斷的您的偏好與習慣、寵物的情緒歷史、任務清單等。
    -   請注意您在聊天中分享的資訊。如果您極度重視隱私，可以考慮定期清理資料庫檔案（這會重置寵物）。

-   **網路搜尋內容:**
    -   網路搜尋功能使用 Google Custom Search。應用程式不對外部網站的內容負責。您可以在設定中完全停用此功能。

-   **第三方服務:**
    -   本應用會呼叫 Google 的第三方服務。您對這些服務的使用受其各自的服務條款和隱私政策約束。

**使用本應用即表示您理解並接受上述風險與責任。**

---

## Requirements / 環境需求

-   Python 3.8 或更高版本
-   SQLite3 (通常隨 Python 一起安裝)
-   Python 套件:
    -   `tkinter` (通常隨 Python 一起安裝)
    -   `google-generativeai`
    -   `google-api-python-client`
    -   `Pillow`

您可以使用 `pip` 單獨安裝所需套件：
```bash
pip install google-generativeai google-api-python-client Pillow
## Installation / 安裝步驟

1.  **複製儲存庫:**
    ```bash
    git clone [https://github.com/xdrxdrxd/DeskWifu.git](https://github.com/xdrxdrxd/DeskWifu.git)
    ```
2.  **進入專案目錄:**
    ```bash
    cd DeskWifu
    ```
3.  **安裝依賴套件:**
    ```bash
    pip install google-generativeai google-api-python-client Pillow
    ```
4.  **確保圖片檔案存在:**
    請確保 `default.png`, `happy.png` 等情緒圖片檔案與腳本位於同一目錄中。
5.  **執行應用程式:**
    ```bash
    python DeskWifu_1.5.0.py
    ```
    (如果腳本名稱不同，請替換)

---

## Configuration / 設定

-   **資料庫:**
    `pet_data.db` 資料庫檔案將在首次啟動時自動建立。

-   **API 金鑰 (核心功能必需):**
    1.  啟動應用程式，點擊選單「檔案」->「設定」。
    2.  切換到「API與模型」分頁。
    3.  **Gemini API:** 點擊「設定/更改 Gemini API 金鑰」並輸入您的金鑰。
    4.  **Custom Search API:**
        -   在您的 [Google Programmable Search Engine 控制台](https://programmablesearchengine.google.com/) 建立一個搜尋引擎，並設定為「搜尋整個網路」。
        -   取得您的 **API 金鑰** 和 **Search Engine ID (CX)**。
        -   將這兩者填入 DeskWifu 設定中對應的欄位。

-   **其他設定:**
    所有其他參數（個性、情緒、行為等）都可透過「設定」視窗在對應的分頁中進行調整。點擊「套用全部變更」以儲存。

---
## Usage / 如何使用

1.  啟動應用程式。
2.  **首次使用請務必前往「設定」->「API与模型」分頁設定您的 API 金鑰。**
3.  在聊天輸入框中輸入文字，按下 `Enter` 或「傳送」按鈕與小星互動。
4.  觀察其豐富的情緒反應、記憶引用、學習到的特徵以及各種認知行為！

---

## Customization / 自訂

-   **圖片:** 您可以替換目錄中的 `.png` 圖片來自訂小星的外觀，只需保持檔名與 `EMOTION_IMAGES` 字典中的鍵名一致即可。
-   **資料庫:** 進階使用者可以使用 SQLite 瀏覽器查看 `pet_data.db`，但不建議直接修改，以免損壞寵物狀態。

---

## Contributing / 貢獻

歡迎提交 Pull Request。對於重大變更，請先建立一個 Issue 進行討論。請確保您的貢獻符合專案目標，即創造一個引人入勝且可自訂的桌面伴侶，同時考慮使用者隱私和 API 使用責任。

---

## License / 授權條款

This project is licensed under the MIT License - see the `LICENSE` file for details.






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
