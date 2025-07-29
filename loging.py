# loging.py
import threading
import time
import random
import mss
import cv2
import numpy as np
import pyautogui

class LoginChannelController:
    def __init__(self):
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None

    def _run(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while self.running:
                screen = np.array(sct.grab(monitor))
                screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

                login_loc = self._find_image(screen, "assets/login.png")
                select_loc = self._find_image(screen, "assets/select.png")

                if login_loc:
                    self._click_random_pos(login_loc)
                    time.sleep(1)  # 等一秒再點第二次
                    self._click_random_pos(login_loc)

                if select_loc:
                    self._click_random_pos(select_loc)
                    self.running = False  # 停止登入流程
                    break

                time.sleep(5)  # 改成 5 秒掃描一次

    def _find_image(self, haystack, needle_path, threshold=0.8):
        needle = cv2.imread(needle_path)
        if needle is None:
            return None
        res = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= threshold)
        points = list(zip(*loc[::-1]))
        if points:
            return points[0], needle.shape[1], needle.shape[0]
        return None

    def _click_random_pos(self, loc):
        (x, y), w, h = loc
        rand_x = x + random.randint(5, max(5, w - 10))
        rand_y = y + random.randint(5, max(5, h - 10))
        # 模擬不規則弧線移動
        pyautogui.moveTo(rand_x, rand_y, duration=random.uniform(0.3, 0.7), tween=pyautogui.easeInOutQuad)
        pyautogui.click()
