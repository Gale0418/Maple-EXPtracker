# 🍁 Artale Efficiency Tracker (A.E.T.)
### 專為 Artale 伺服器打造的效率分析儀

> "如果你不知道你在坐牢，那就不算坐牢... 直到你看到這每分鐘只有 0.01% 的經驗值。" \_(:3 」∠ )\_

## 📖 專案簡介 (Introduction)
這是一個基於 Python 圖像識別的自動化分析工具，旨在量化你在楓之谷 (Artale) 中的狩獵效率。
程式會自動監控遊戲畫面，即時計算你的 **經驗值獲取率** 與 **楓幣淨收益**，讓你知道這張地圖到底值不值得你投入青春。

## ⚡ 核心功能 (Features)

*   **📊 即時經驗監控 (Real-time EXP Tracking)**
    *   每分鐘自動掃描經驗條，計算 `EXP/min` 與 `預計升級時間`。
*   **💰 財務報表系統 (Economy Analysis)**
    *   自動打開背包/錢包，識別當前楓幣數量。
    *   與掛機開始時的數值比對，計算 `Mesos/min`。
*   **🧪 淨收益計算 (Net Profit)**
    *   自動扣除藥水消耗成本（水錢），計算出真正的淨利潤。
    *   拒絕虛假繁榮，讓你知道是否越練越窮。
*   **🛠️ 自動化運作**
    *   非侵入式掃描，基於視覺辨識，不讀取記憶體。

## ⚠️ 系統需求與限制 (Requirements) - **重要！**

由於本程式採用 **「絕對座標圖像識別」** 技術，對運行環境有嚴格要求：

1.  **🖥️ 螢幕解析度限定：2560 x 1440 (2K)**
    *   **注意**：本程式專為 2K 螢幕開發。如果您的螢幕不是這個解析度，**座標會跑掉，程式會失效**。
    *   *解決方案*：您需要自行修改程式碼中的座標參數 (如果你會的話)，或是換個螢幕 (推薦)。
2.  **🐍 執行環境：Python 3.x**
    *   本工具為原始碼發布，您需要電腦裡有 Python 環境。
    *   [Python 官方下載](https://www.python.org/downloads/) (安裝教學請自行 Google，這是基本門檻)。

## 🚀 如何開始 (Getting Started)

1.  **Clone 專案**
    ```bash
    git clone https://github.com/Gale0418/Maple-EXPtracker.git
    cd Maple-EXPtracker
    ```

2.  **安裝依賴庫**
    ```bash
    pip install -r requirements.txt
    ```
    *(主要依賴：opencv-python, pyautogui, pytesseract 等)*

3.  **執行程式**
    *   確保遊戲視窗置頂。
    *   執行主程式：
    ```bash
    python main.py
    ```

## 📝 常見問題 (Q&A)

**Q: 為什麼程式跑起來報錯 / 抓不到數據？**
A: 請檢查您的螢幕解析度是否為 **2560x1440**。如果不是，請具備 Python 基礎並自行修復座標定義。

**Q: 我不會安裝 Python / pip 報錯怎麼辦？**
A: 這是開發者工具，建議先學習 Python 基礎環境建置。Google 是您最好的朋友。

**Q: 會有封號風險嗎？**
A: 本程式僅進行螢幕截圖與識別 (OCR)，不修改遊戲封包或記憶體。但所有輔助工具皆有風險，請低調使用。

---
(｀・ω・´)b  Happy Mapling! 祝您打寶運昌隆！
