# meso.py
import cv2
import numpy as np
import pytesseract
import pyautogui
import time
from datetime import datetime
from PIL import ImageGrab
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
class MesoTracker:
    def __init__(self):
        self.start_meso = None
        self.current_meso = None
        self.running = False

    def start(self):
        self.running = True
        self.update()

    def stop(self):
        self.running = False

    def update(self):
        if not self.running:
            return
        meso = open_and_read_wallet()
        if meso is not None:
            if self.start_meso is None:
                self.start_meso = meso
            self.current_meso = meso

    def get_meso_info(self):
        if self.start_meso is None or self.current_meso is None:
            return (0, 0)
        return (self.current_meso, self.current_meso - self.start_meso)


def read_meso_amount(img) -> int | None:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    config = "--psm 7 -c tessedit_char_whitelist=0123456789,"
    text = pytesseract.image_to_string(thresh, config=config).strip()
    match = re.search(r"[\d,]+", text)
    if not match:
        return None
    return int(match.group().replace(",", ""))


def open_and_read_wallet(template_path="assets/GASH.png"):
    pyautogui.press('i')
    time.sleep(0.8)

    screenshot = ImageGrab.grab()
    screen_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    template = cv2.imread(template_path)
    if template is None:
        print("❌ 無法載入 GASH.png")
        return None

    result = cv2.matchTemplate(screen_np, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < 0.75:
        print("⚠️ 未找到錢包圖標")
        pyautogui.press('i')  # 關掉錢包
        return None

    x, y = max_loc
    roi_left = max(x - 400, 0)
    roi_top = y
    roi_right = x - 5
    roi_bottom = y + template.shape[0]
    meso_img = screen_np[roi_top:roi_bottom, roi_left:roi_right]

    meso = read_meso_amount(meso_img)

    pyautogui.press('i')  # 關掉錢包
    return meso
