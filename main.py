# main.py
# 楓之谷經驗計算器（半透明背景、流光動畫、多行描邊文字、可拖曳）
#
# 核心特色：
# - 一個自訂元件一次畫多行文字，可精確控制行距，避免字被截斷或行距過大
# - 所有文字有黑色描邊與多種漸層流光效果
# - 半透明帶背景圖視窗，無邊框且永遠在最前面
# - 視窗可任意拖曳，按鈕仍可正常點擊
#
# 注意：此檔依賴 exp.py, loging.py, meso.py，請與你的專案搭配使用。

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import (
    QColor, QPainter, QFont, QPixmap, QPainterPath, QPen, QLinearGradient, QBrush, QFontMetrics
)

# 導入你原本的邏輯模組
from exp import ExpTracker, capture_exp_bar, read_exp_and_percent, format_time, cute_evaluation
from loging import LoginChannelController
from meso import MesoTracker

ASSETS_DIR = Path("assets")  # 資源資料夾


# ---------------------------------------
# 自訂多行描邊文字元件
# ---------------------------------------
class MultiLineOutlined(QWidget):
    """
    一次繪製多行文字（預設4行），可精確控制行距 line_gap。
    支援三種模式：
     - solid: 固定顏色填充
     - gradient_shimmer: 沿X軸流光金色漸層（可動畫）
     - two_color_shimmer: 兩色藍白流光動畫
    每行可獨立設定文字、顏色及模式。
    """

    def __init__(self, lines=4, parent=None, line_gap=-4):
        super().__init__(parent)
        self.lines_count = lines
        self.texts = [""] * lines

        # 使用的字型
        self._font = QFont("Arial", 12, QFont.Bold)

        # 每行模式與顏色設定
        self.modes = ["solid"] * lines
        self.solid_colors = [QColor(255, 255, 255)] * lines
        self.gradient_colors = [[QColor(255, 215, 0), QColor(255, 235, 160)] for _ in range(lines)]

        # 描邊設定
        self.outline_color = QColor(0, 0, 0)
        self.outline_width = 1.0

        # 行間距（負值讓行更靠近）
        self.line_gap = line_gap

        # 動畫階段（0..1循環）
        self.phase = 0.0

        # 動畫 timer，觸發重繪
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(70)
        self.anim_timer.timeout.connect(self._on_anim)
        self.anim_timer.start()

        # 改變大小策略，寬度彈性，高度根據字型與行數自適應
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def setFont(self, f: QFont):
        """設定字型"""
        self._font = f
        super().setFont(f)
        self.update()

    def set_lines(self, texts: list):
        """一次設定多行文字"""
        for i, t in enumerate(texts[:self.lines_count]):
            self.texts[i] = t
        self.update()

    def set_line(self, idx: int, text: str):
        """設定特定行的文字"""
        if 0 <= idx < self.lines_count:
            self.texts[idx] = text
            self.update()

    def set_line_style(self, idx: int, mode="solid", solid_color=QColor(255, 255, 255), gradient_colors=None):
        """設定特定行的繪製模式與顏色"""
        if 0 <= idx < self.lines_count:
            self.modes[idx] = mode
            self.solid_colors[idx] = solid_color
            if gradient_colors:
                self.gradient_colors[idx] = gradient_colors
            self.update()

    def set_outline(self, color: QColor, width: float = 1.0):
        """設定描邊顏色與寬度"""
        self.outline_color = color
        self.outline_width = width
        self.update()

    def _on_anim(self):
        """動畫更新，更新 phase 並重繪"""
        self.phase += 0.02
        if self.phase > 1.0:
            self.phase -= 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self._font)
        fm = painter.fontMetrics()

        ascent = fm.ascent()
        descent = fm.descent()
        line_height = ascent + descent

        # 開始畫第一行文字 baseline，保留少許頂部 margin
        top_margin = 2
        y = top_margin + ascent

        rect = self.contentsRect()

        for i in range(self.lines_count):
            text = self.texts[i]
            if not text:
                y += line_height + self.line_gap
                continue

            # 建立文字路徑，文字靠左，x偏移8像素
            path = QPainterPath()
            text_x = 8
            path.addText(text_x, y, self._font, text)

            # 描邊（黑色）
            pen = QPen(self.outline_color)
            pen.setWidthF(self.outline_width + 0.6)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            # 依模式繪製內部文字
            mode = self.modes[i]
            if mode == "solid":
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(self.solid_colors[i]))
                painter.drawPath(path)
            elif mode == "gradient_shimmer":
                grad = QLinearGradient(rect.left(), 0, rect.right(), 0)
                p = (self.phase + i * 0.08) % 1.0  # 每行動畫相位偏移
                c0, c1 = self.gradient_colors[i][0], self.gradient_colors[i][1]
                grad.setColorAt((p - 0.15) % 1.0, c0)
                grad.setColorAt(p, c1)
                grad.setColorAt((p + 0.15) % 1.0, c0)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(grad))
                painter.drawPath(path)
            elif mode == "two_color_shimmer":
                grad = QLinearGradient(rect.left(), 0, rect.right(), 0)
                p = (self.phase + i * 0.06) % 1.0
                c1, c2 = self.gradient_colors[i][0], self.gradient_colors[i][1]
                grad.setColorAt((p - 0.12) % 1.0, c1)
                grad.setColorAt(p, c2)
                grad.setColorAt((p + 0.12) % 1.0, c1)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(grad))
                painter.drawPath(path)

            # 下一行 baseline（加上行距）
            y += line_height + self.line_gap

    def sizeHint(self):
        """告訴佈局管理器理想高度"""
        fm = QFontMetrics(self._font)
        h = self.lines_count * (fm.ascent() + fm.descent()) + (self.lines_count - 1) * self.line_gap + 6
        return QSize(self.width(), max(h, 10))


# ---------------------------------------
# 主視窗
# ---------------------------------------
class ExpApp(QWidget):
    def __init__(self):
        super().__init__()

        # 視窗基礎設定
        self.setWindowTitle("楓之谷經驗計算器")
        self.resize(400, 220)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # 永遠在最前
        self.setWindowFlag(Qt.FramelessWindowHint)   # 無邊框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明，方便畫圓角


        # 載入背景圖（存在才載入）
        self.bg_pix = QPixmap(str(ASSETS_DIR / "maple_background.png")) if (ASSETS_DIR / "maple_background.png").exists() else None
        self.bg_opacity = 0.45  # 背景透明度

        # 拖曳用變數
        self._drag_pos = None

        # 按鈕區塊
        self.btn_start = QPushButton("開始計算")
        self.btn_login = QPushButton("登入頻道")
        self.btn_quit = QPushButton("結束程式")
        for b in [self.btn_start, self.btn_login, self.btn_quit]:
            b.setFixedHeight(30)

        self.btn_start.clicked.connect(self.toggle_tracking)
        self.btn_login.clicked.connect(self.toggle_login)
        self.btn_quit.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_quit)

        # 建立多行描邊文字元件，取代原本 4 個獨立 Label
        self.multi_label = MultiLineOutlined(lines=4, parent=self, line_gap=12)
        font = QFont("Arial", 12, QFont.Bold)
        self.multi_label.setFont(font)
        self.multi_label.set_outline(QColor(0, 0, 0), 1.0)

        # 主版面配置
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addLayout(btn_layout)
        layout.addWidget(self.multi_label)
        self.setLayout(layout)


        # 建立邏輯物件
        self.tracker = ExpTracker()
        self.meso_tracker = MesoTracker()
        self.login_ctrl = LoginChannelController()
        self.login_running = False
        self.running = False

        # timer：每10秒更新經驗
        self.exp_timer = QTimer(self)
        self.exp_timer.setInterval(10000)
        self.exp_timer.timeout.connect(self.update_exp)

        # timer：每10分鐘更新估算
        self.estimate_timer = QTimer(self)
        self.estimate_timer.setInterval(600000)
        self.estimate_timer.timeout.connect(self.update_estimate)

        # timer：每1分鐘更新金幣
        self.meso_timer = QTimer(self)
        self.meso_timer.setInterval(60000)
        self.meso_timer.timeout.connect(self.meso_tracker.update)

        # 啟動時更新一次畫面
        self.update_exp()
        self.update_estimate()
        self.refresh_display()

    # 繪製半透明背景與圓角，並疊上背景圖
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        radius = 12

        # 半透明白底圓角
        base_color = QColor(255, 255, 255, int(220 * 0.25))
        painter.setBrush(base_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        # 若有背景圖，縮放並以半透明方式疊上
        if self.bg_pix and not self.bg_pix.isNull():
            scaled = self.bg_pix.scaled(self.width(), self.height(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            painter.setOpacity(self.bg_opacity)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            painter.setOpacity(1.0)

    # 視窗拖曳邏輯，點擊非按鈕區域拖動視窗
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())  # 改成 position().toPoint()
            if isinstance(child, QPushButton):
                self._drag_pos = None
                super().mousePressEvent(event)
                return
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            new_pos = event.globalPosition().toPoint() - self._drag_pos
            self.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # 切換追蹤計算狀態（開始/重新計算）
    def toggle_tracking(self):
        if not self.running:
            self.tracker.reset()
            self.meso_tracker.start()
            self.exp_timer.start()
            self.estimate_timer.start()
            self.meso_timer.start()
            self.running = True
            self.btn_start.setText("重新計算")

            if self.login_running:
                self.login_ctrl.stop()
                self.login_running = False
        else:
            self.exp_timer.stop()
            self.estimate_timer.stop()
            self.meso_timer.stop()
            self.meso_tracker.stop()
            self.running = False
            # 重新開始（清空資料）
            self.toggle_tracking()
        self.refresh_display()

    # 切換登入頻道流程（開始/停止）
    def toggle_login(self):
        if not self.login_running:
            self.login_ctrl.start()
            self.login_running = True
            self.btn_login.setText("停止登入")
        else:
            self.login_ctrl.stop()
            self.login_running = False
            self.btn_login.setText("登入頻道")
        self.refresh_display()

    # 每10秒更新經驗數據（透過截圖與OCR）
    def update_exp(self):
        if self.login_running:
            self.refresh_display()
            return
        try:
            img = capture_exp_bar()
            exp, percent = read_exp_and_percent(img)
            if exp is not None and percent is not None:
                self.tracker.update(exp, percent)
        except Exception as e:
            print("EXP 擷取錯誤:", e)

        # 超過停滯時間自動暫停
        if self.tracker.is_stopped() and self.running:
            print("🔁 超過停滯時間，自動暫停")
            self.exp_timer.stop()
            self.estimate_timer.stop()
            self.meso_timer.stop()
            self.meso_tracker.stop()
            self.running = False
            self.btn_start.setText("開始計算")

        self.refresh_display()

    # 每10分鐘更新升級估算
    def update_estimate(self):
        try:
            self.tracker.update_estimate()
        except Exception as e:
            print("估算更新錯誤:", e)
        self.refresh_display()

    # 更新顯示文字與樣式（傳入多行文字及多行樣式）
    def refresh_display(self):
        t = self.tracker
        m = self.meso_tracker

        start_exp = t.start_exp if t.start_exp is not None else 0
        start_percent = t.start_percent if t.start_percent is not None else 0.0
        gained_exp = t.gained_exp if t.gained_exp is not None else 0
        gained_percent = t.gained_percent if t.gained_percent is not None else 0.0
        meso_now, meso_gained = m.get_meso_info() if hasattr(m, "get_meso_info") else (0, 0)
        best_gain = t.best_exp_gain if t.best_exp_gain else 0
        percent_rate_now = t.percent_per_10min if t.percent_per_10min else 0.0

        # 計算 cute 評價文字
        diff = 0.0
        try:
            diff = abs(percent_rate_now - (t.best_exp_gain / t.gained_exp * t.gained_percent if t.gained_exp else 0))
        except Exception:
            diff = 0.0
        eval_text = cute_evaluation(diff)

        # 四行文字
        txt0 = f"起始: {start_exp:,}   {start_percent:.2f}%    💰: {meso_now:,}"
        txt1 = f"累積: {gained_exp:,}   {gained_percent:.2f}%    💰:+{meso_gained:,}"
        txt2 = f"🎉 最快紀錄: {best_gain:,} EXP/10分鐘   ⚙️ 運作: {format_time(t.runtime())}"
        txt3 = f"⏱️ 剩多久升級: {format_time(t.estimated_time)}    {eval_text}"

        # 設定多行文字內容
        self.multi_label.set_lines([txt0, txt1, txt2, txt3])

        # 設定多行文字樣式
        self.multi_label.set_line_style(0, mode="solid", solid_color=QColor(150, 230, 170))  # 淡綠
        self.multi_label.set_line_style(1, mode="solid", solid_color=QColor(130, 220, 140))  # 淡綠
        self.multi_label.set_line_style(2, mode="gradient_shimmer", gradient_colors=[QColor(200, 150, 0), QColor(255, 230, 120)])  # 金色流光
        self.multi_label.set_line_style(3, mode="two_color_shimmer", gradient_colors=[QColor(60, 140, 255), QColor(240, 250, 255)])  # 藍白流光



    # 視窗關閉前釋放資源
    def closeEvent(self, event):
        self.exp_timer.stop()
        self.estimate_timer.stop()
        self.meso_timer.stop()
        self.meso_tracker.stop()
        self.login_ctrl.stop()
        event.accept()


# ---------------------------------------
# 主程式入口
# ---------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ExpApp()
    w.show()
    sys.exit(app.exec())
