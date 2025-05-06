import sys
from PyQt5.QtWidgets import QApplication

# Import the main UI class
from stopwatch_ui import NekoToki

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Reverted application style
    app.setStyleSheet("""
        QToolTip {
            border: 1px solid rgba(235, 226, 155, 150);
            background-color: rgba(146, 149, 196, 150);
            color: rgba(235, 226, 155, 220);
            border-radius: 5px;
            padding: 4px; /* Added padding */
        }
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: white;
            height: 8px;
            border-radius: 4px;
        }
        QSlider::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #eee, stop:1 #ccc);
            border: 1px solid #777;
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 4px;
        }
        QSlider::add-page:horizontal { background: #fff; }
        QSlider::sub-page:horizontal { background: rgba(176, 179, 226, 180); }
    """)

    # Create and show the stopwatch using the imported UI class
    stopwatch = NekoToki()
    stopwatch.show()

    sys.exit(app.exec_()) 