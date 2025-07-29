# main.py
import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QFont, QMouseEvent

from exp import ExpTracker, capture_exp_bar, read_exp_and_percent, format_time, cute_evaluation
from loging import LoginChannelController
from meso import MesoTracker


class ExpApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("楓之谷經驗計算器")
        self.resize(360, 220)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)  # 視窗永遠在最前面
        self.setWindowFlag(Qt.FramelessWindowHint)   # 無邊框視窗
        self.setAttribute(Qt.WA_TranslucentBackground)  # 背景透明

        self.opacity = 0.5
        self.bg_color = QColor(135, 206, 250, int(255 * self.opacity))
        self.font = QFont("Arial", 11, QFont.Bold)

        # 按鈕初始化
        self.btn_start = QPushButton("開始計算")
        self.btn_login = QPushButton("登入頻道")
        self.btn_quit = QPushButton("結束程式")

        for b in [self.btn_start, self.btn_login, self.btn_quit]:
            b.setFixedHeight(30)

        # 按鈕事件綁定
        self.btn_start.clicked.connect(self.toggle_tracking)
        self.btn_login.clicked.connect(self.toggle_login)
        self.btn_quit.clicked.connect(self.close)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_quit)

        # 四個顯示用 Label
        self.labels = [QLabel() for _ in range(4)]
        for lbl in self.labels:
            lbl.setFont(self.font)
            lbl.setTextFormat(Qt.RichText)
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            lbl.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 6px;
                color: black;
            """)

        layout = QVBoxLayout()
        layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        layout.addLayout(btn_layout)
        for lbl in self.labels:
            layout.addWidget(lbl)
        self.setLayout(layout)

        self.old_pos = None  # 紀錄滑鼠拖曳視窗的舊位置

        # 追蹤器初始化
        self.tracker = ExpTracker()
        self.meso_tracker = MesoTracker()

        # 設定三個計時器
        self.exp_timer = QTimer()
        self.exp_timer.setInterval(10000)  # 10秒更新經驗
        self.exp_timer.timeout.connect(self.update_exp)

        self.estimate_timer = QTimer()
        self.estimate_timer.setInterval(600000)  # 10分鐘更新估算
        self.estimate_timer.timeout.connect(self.update_estimate)

        self.meso_timer = QTimer()
        self.meso_timer.setInterval(60000)  # 1分鐘更新金幣
        self.meso_timer.timeout.connect(self.meso_tracker.update)

        self.login_ctrl = LoginChannelController()
        self.login_running = False  # 登入狀態旗標
        self.running = False        # 經驗計算狀態旗標

        # 啟動時先更新一次畫面顯示
        self.update_exp()
        self.update_estimate()
        self.refresh_display()

    # 繪製半透明背景與圓角視窗
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 12, 12)

    # 以下三個函數用來讓視窗可以用滑鼠拖曳移動
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.old_pos = None

    # 切換經驗計算開始/暫停
    def toggle_tracking(self):
        if not self.running:
            # 啟動經驗計算與金幣計算計時器
            self.meso_tracker.start()
            self.exp_timer.start()
            self.estimate_timer.start()
            self.meso_timer.start()
            self.running = True
            self.btn_start.setText("暫停中")
            # 如果登入正在進行，先停止登入功能
            if self.login_running:
                self.login_ctrl.stop()
                self.login_running = False
        else:
            # 停止所有計時器與追蹤器
            self.exp_timer.stop()
            self.estimate_timer.stop()
            self.meso_timer.stop()
            self.meso_tracker.stop()
            self.running = False
            self.btn_start.setText("開始計算")
        self.refresh_display()

    # 切換登入頻道開始/停止
    def toggle_login(self):
        if not self.login_running:
            self.login_ctrl.start()
            self.login_running = True
        else:
            self.login_ctrl.stop()
            self.login_running = False
        self.refresh_display()

    # 讀取並更新經驗數據
    def update_exp(self):
        # 如果登入中，暫時不更新經驗顯示
        if self.login_running:
            self.refresh_display()
            return
        try:
            img = capture_exp_bar()
            exp, percent = read_exp_and_percent(img)
            if exp is not None and percent is not None:
                self.tracker.update(exp, percent)
        except Exception as e:
            print("EXP擷取錯誤:", e)

        # 自動暫停判斷：超過設定秒數沒更新自動停止計算
        if self.tracker.is_stopped() and self.running:
            print("🔁 超過10分鐘無更新，自動暫停")
            self.toggle_tracking()

        self.refresh_display()

    # 更新升級時間等估算數據
    def update_estimate(self):
        try:
            self.tracker.update_estimate()
        except Exception as e:
            print("估算更新錯誤:", e)
        self.refresh_display()

    # 更新UI標籤顯示
    def refresh_display(self):
        t = self.tracker
        m = self.meso_tracker
        meso_now, meso_gained = m.get_meso_info()

        start_exp = t.start_exp if t.start_exp is not None else 0
        start_percent = t.start_percent if t.start_percent is not None else 0.0
        gained_exp = t.gained_exp if t.gained_exp is not None else 0
        gained_percent = t.gained_percent if t.gained_percent is not None else 0.0
        meso_now = meso_now if meso_now is not None else 0
        meso_gained = meso_gained if meso_gained is not None else 0
        best_gain = t.best_exp_gain if t.best_exp_gain else 0
        this_gain = t.last_10min_exp_gain if t.last_10min_exp_gain else 0
        percent_rate_now = t.percent_per_10min if t.percent_per_10min else 0.0

        if self.login_running:
            self.labels[0].setText("<b><span style='color:#0040FF;'>登入中</span></b>")
        else:
            self.labels[0].setText(
                f"<b><span style='color:#0040FF;'>起始:</span></b> "
                f"<b style='color:#003399;'>{start_exp:,}</b> "
                f"<b style='color:#0066CC;'>{start_percent:.2f}%</b>  "
                f"<span style='color:#8B4513;'>金幣: {meso_now:,}</span>"
            )

        self.labels[1].setText(
            f"<b><span style='color:#006400;'>累積:</span></b> "
            f"<b style='color:#004d00;'>{gained_exp:,}</b> "
            f"<b style='color:#228B22;'>{gained_percent:.2f}%</b>  "
            f"<span style='color:#A0522D;'>+{meso_gained:,} 金幣</span>"
        )

        self.labels[2].setText(
            f"<b><span style='color:#800000;'>紀錄:</span></b> "
            f"<b>{best_gain:,} EXP</b> / 10 分鐘  "
            f"<b>運行:</b> {format_time(t.runtime())}"
        )

        diff = abs(percent_rate_now - (t.best_exp_gain / t.gained_exp * t.gained_percent if t.gained_exp else 0))
        self.labels[3].setText(
            f"<b><span style='color:#FF8C00;'>剩餘:</span></b> "
            f"<b>{format_time(t.estimated_time)}</b> "
            f"{cute_evaluation(diff)}"
        )


def main():
    app = QApplication(sys.argv)
    win = ExpApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
