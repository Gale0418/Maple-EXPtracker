# exp.py

import time
import re
import cv2
import pytesseract
import numpy as np
import pyautogui

# 設定 Tesseract 路徑（請依照你的安裝位置調整）
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------- 經驗追蹤核心 ----------
class ExpTracker:
    def __init__(self):
        self.reset()
        self.best_time = None
        self.best_exp_gain = 0          # 最佳經驗值增量（每10分鐘）
        self.last_10min_exp_gain = 0    # 最新10分鐘經驗值增量

    def reset(self):
        self.start_exp = None
        self.start_percent = None
        self.last_exp = None
        self.last_percent = None
        self.last_update = None
        self.gained_exp = 0
        self.gained_percent = 0.0
        self.start_time = None
        self.percent_per_10min = 0.0
        self.estimated_time = 0
        self.stop_threshold = 60  # 停止閾值（秒）
        self.best_exp_gain = 0
        self.last_10min_exp_gain = 0

    def update(self, exp, percent):
        now = time.time()
        if self.start_exp is None:
            self.start_exp = exp
            self.start_percent = percent
            self.start_time = now
        self.gained_exp = exp - self.start_exp
        self.gained_percent = percent - self.start_percent
        self.last_exp = exp
        self.last_percent = percent
        self.last_update = now

    def is_stopped(self):
        if self.last_update is None:
            return False
        return time.time() - self.last_update > self.stop_threshold

    def runtime(self):
        if self.start_time is None:
            return 0
        return time.time() - self.start_time

    def update_estimate(self):
        elapsed_min = self.runtime() / 60
        if elapsed_min < 0.1:
            self.percent_per_10min = 0
            self.estimated_time = 0
            self.last_10min_exp_gain = 0
            return

        # 計算百分比增速與經驗值增速
        rate_percent = self.gained_percent / elapsed_min
        self.percent_per_10min = rate_percent * 10

        rate_exp = self.gained_exp / elapsed_min
        self.last_10min_exp_gain = int(rate_exp * 10)

        # 更新最大記錄
        if self.last_10min_exp_gain > self.best_exp_gain:
            self.best_exp_gain = self.last_10min_exp_gain

        if rate_percent > 0:
            self.estimated_time = int((100 - self.last_percent) / rate_percent * 60)
        else:
            self.estimated_time = 0

        if self.estimated_time > 0 and (self.best_time is None or self.estimated_time < self.best_time):
            self.best_time = self.estimated_time


# ---------- 金幣追蹤 ----------
class MesoTracker:
    def __init__(self):
        self.start_meso = None
        self.last_meso = None

    def update(self, meso):
        if self.start_meso is None:
            self.start_meso = meso
        self.last_meso = meso

    def get_meso_info(self):
        if self.start_meso is None or self.last_meso is None:
            return None, None
        gained = self.last_meso - self.start_meso
        return self.last_meso, gained


# ---------- OCR 辨識 ----------
def read_exp_and_percent(img) -> tuple[int | None, float | None]:
    """
    從圖片中讀取經驗值與百分比，例如格式：440740[13.21%]
    """
    if img is None:
        return None, None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY_INV)

    config = "--psm 7 -c tessedit_char_whitelist=0123456789[].% "
    text = pytesseract.image_to_string(thresh, config=config).strip()

    match = re.search(r"(\d+)\s*\[\s*(\d+\.\d+)%\s*\]", text)
    if not match:
        return None, None
    exp = int(match.group(1))
    percent = float(match.group(2))
    return exp, percent


def read_meso_amount(img) -> int | None:
    """
    從金幣圖像中讀取金幣總額，例如 1,234,567
    """
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    config = "--psm 7 -c tessedit_char_whitelist=0123456789,"
    text = pytesseract.image_to_string(thresh, config=config).strip()

    match = re.search(r"[\d,]+", text)
    if not match:
        return None

    return int(match.group().replace(",", ""))


# ---------- 圖片擷取 ----------
def find_template_on_screen(template_path, confidence=0.8):
    screen = pyautogui.screenshot()
    screen = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        return max_loc
    return None


def capture_exp_bar() -> np.ndarray | None:
    """
    找到 EXP.png 後，擷取其右方 400x20 的區塊（顯示數字用）
    """
    pos = find_template_on_screen("assets/EXP.png", confidence=0.8)
    if not pos:
        return None
    x, y = pos
    x += 50  # 避開 EXP 字樣本體
    region = (x+15, y, 400, 100)
    img = pyautogui.screenshot(region=region)
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return img


# ---------- 工具函數 ----------
def format_time(seconds: int | float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def cute_evaluation(diff_percent: float) -> str:
    """
    根據與歷史最佳百分比增速差異來評價可愛程度
    """
    if diff_percent < 1:
        return "(*≧ω≦)✨摸頭害鴨哭！"
    elif diff_percent < 2:
        return "(๑•̀ㅂ•́)و有進步空間！"
    elif diff_percent < 3:
        return "(・_・;)稍微慢下來了呢"
    else:
        return "(；´Д｀)呆膠布？需要休息嗎？"
