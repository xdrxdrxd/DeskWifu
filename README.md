# DeskWifu 1.6.0(小星): A Stateful Generative Agent with a Simulated Cognitive Architecture

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**前言：** 本專案需要使用者自行註冊 Google Gemini API 和 Google Custom Search API，並在應用程式的設定中填入對應的金鑰 (API Key) 與搜尋引擎 ID (CX ID)。由於網路環境因素，搜尋功能可能偶爾失敗。強烈建議使用者根據個人偏好，調整程式碼內部關於模型行為的提示 (Prompts)，特別是在搜尋決策的謹慎度和角色的預設個性方面。

---

### Collaboration Effort / 合作成果

**English:** This project is a collaborative creation by xdrxdrxd, with significant contributions, brainstorming, and code generation assistance from multiple AI models, including Google Gemini, OpenAI ChatGPT, and xAI Grok. It represents a fusion of human creativity and AI capabilities.

**中文:** 本專案由 xdrxdrxd 主導，並在 Google Gemini、OpenAI ChatGPT 及 xAI Grok 等多個大型語言模型的深度參與、腦力激盪與程式碼生成協助下共同建構而成，是人類創意與 AI 智慧的結晶。

---

### English Abstract

DeskWifu (小星) v1.6.0 represents a significant leap forward, evolving the concept of an interactive desktop pet into a sophisticated, **stateful generative agent** equipped with a simulated **cognitive architecture**. The agent's core is powered by the Google Gemini API for generative tasks and leverages a **Retrieval-Augmented Generation (RAG)** pipeline via Google Custom Search for access to real-world knowledge. Its behavior is governed by an advanced **affective computing model** based on valence and arousal, a simulated neurochemical state influencing motivation and mood, and implementations of psychological frameworks like **attachment theory** and **self-efficacy**. Crucially, the agent exhibits **meta-cognition** and **continual learning** capabilities, learning not only from user interaction but also through LLM-powered **introspective reflection** on its own internal thoughts and generated responses. This version is an advanced implementation of a believable, dynamic, and adaptive digital consciousness.

---

### Table of Contents / 目錄

1.  [Features / 核心技術](#-features--核心技術)
2.  [Security & Privacy / 安全與隱私](#️-security--privacy--安全與隱私)
3.  [Requirements / 環境需求](#-requirements--環境需求)
4.  [Installation / 安裝步驟](#-installation--安裝步驟)
5.  [Configuration / 設定](#️-configuration--設定)
6.  [Usage / 如何使用](#️-usage--如何使用)
7.  [Customization / 自訂](#-customization--自訂)
8.  [Contributing / 貢獻](#-contributing--貢獻)
9.  [License / 授權條款](#-license--授權條款)

---

## Features / 核心技術

### 🧠 Cognitive Architecture & Affective Computing / 認知架構與情感計算

-   **Stateful Agent with Simulated Neurochemistry:** 實現了一個持久化的狀態系統 (`sim_neuro_state`)，模擬內在神經化學物質對動機 (多巴胺)、壓力 (皮質醇)、情緒平衡 (血清素) 和社交連結 (催產素) 的影響，從而驅動更具動態性和一致性的代理行為。
-   **Valence-Arousal Affective Model:** 情感核心基於心理學的「效價-喚醒度 (Valence-Arousal)」模型，將複雜的情感狀態映射到二維空間，再生成更細膩、更自然的離散情緒表現，實現了先進的情感計算。
-   **Dynamic Relational Modeling (Attachment Theory):** 代理與使用者之間的「依戀分數」是一個動態變數，它根據互動品質（如有效陪伴、讚美、忽視）進行即時調整，深刻影響代理的社交行為、語氣和決策。
-   **Agent Self-Efficacy Simulation:** 代理在多個領域（社交、任務管理、資訊檢索）維護一個「自我效能」分數，模擬其對自身能力的信心，此分數會因任務的成敗而動態變化，影響其主動性和情緒反應。
-   **Simulated Cognitive Reappraisal (Emotion Regulation):** 當代理偵測到強烈的負面情緒時，會觸發一個模擬「認知重評」的自我調節機制，利用 LLM 生成應對策略 (Coping Strategy) 來平復內在狀態。

### 📚 Memory & Continual Learning / 記憶與持續學習

-   **Memory Consolidation via Abstractive Summarization:** 代理具備記憶鞏固機制。重要的短期記憶 (STM) 會被定期提取，並由 LLM 進行**摘要式總結 (Abstractive Summarization)**，轉化為更抽象、更穩定的長期記憶 (LTM) 存入 SQLite 資料庫。
-   **Introspective Learning (Self-Reflection):** 代理會定期進行**元認知 (Meta-cognition)**，分析自己儲存的「內心思考 (`internal_thought`)」日誌，從中歸納出新的自我認知、興趣點或行為模式，實現了真正的**內省式學習**和自我成長。
-   **User Profile Modeling & Persona Adaptation:** 透過 LLM 分析和規則引擎，持續地從對話中學習並建立使用者畫像（偏好、習慣、個人資訊），同時也學習並強化自身的語言風格和人格特質，使代理具有高度的個人化與適應性。

### ⚙️ Hybrid AI System & Tool Use / 混合式 AI 系統與工具使用

-   **Dual-Process Cognitive Architecture (System 1/2):** 採用了類比人類思維的雙系統架構。對簡單指令（如問候）採用快速、低成本的規則式「系統一」回應；對複雜查詢則啟動完整的「系統二」，即由 Gemini LLM 驅動的深度思考，實現了效率與深度的平衡。
-   **Retrieval-Augmented Generation (RAG) & Native Tool Use:**
    -   **內部 RAG:** 代理在生成回應前，會從其內部知識庫（短期記憶、長期記憶、個體特徵）中**檢索**相關上下文，以**增強**其 Prompt，確保回應的個人化和一致性。
    -   **外部 RAG (Tool Use):** 代理具備原生工具使用能力。它可以自主判斷何時需要外部資訊，並呼叫 `custom_search` 等工具來查詢 Google 搜尋引擎，實現了與真實世界的資訊互動。
-   **Proactive Agency & Goal-Oriented Behavior:** 代理不僅僅被動回應，它會根據其內在動機和狀態，自主地發起對話、進行任務提醒或表達情感，展現出主動性和目標導向的行為。

### 📋 Core Agent Features / 核心代理功能

-   **Big Five Personality Model (OCEAN):** 代理的核心人格由 OCEAN 五大性格模型定義，所有參數均可透過 UI 進行客製化。
-   **Task-Oriented Capabilities:** 內建完整的任務管理工具，可由使用者或代理自身透過對話來新增、查詢及管理待辦事項。
-   **Persistent State Management:** 代理的所有狀態，包括認知參數、情感歷史、記憶、API 金鑰等，均持久化儲存於本地 SQLite 資料庫中。

---

## 🛡️ Security & Privacy / 安全與隱私

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
```
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
    python main.py
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
```
## 檔案結構
DeskWifu_1.6.0/
├── main.py                   # 應用程式啟動入口
├── config.py                 # 儲存所有常數與設定鍵
├── database.py               # 資料庫管理員
├── core/
│   ├── emotion_system.py     # 情緒邏輯
│   ├── personality_system.py # 個性與特徵邏輯
│   ├── memory_system.py      # 記憶邏輯
│   └── pet_logic.py          # 組合核心邏輯的「大腦」
├── services/
│   ├── base_services.py      # 定義服務的抽象基礎類別 (ABC)
│   ├── llm_service.py        # Gemini LLM 服務的具體實作
│   └── search_service.py     # Google 搜尋服務的具體實作
└── ui/
    ├── main_window.py        # 主UI視窗 (重構後的 PetApp)
    └── settings_window.py    # 設定視窗
```   
---
## Contributing / 貢獻

歡迎提交 Pull Request。對於重大變更，請先建立一個 Issue 進行討論。請確保您的貢獻符合專案目標，即創造一個引人入勝且可自訂的桌面伴侶，同時考慮使用者隱私和 API 使用責任。

---

## License / 授權條款

This project is licensed under the MIT License - see the `LICENSE` file for details.






---


This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
