from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QLabel, QSizePolicy


class QElidedLabel(QLabel):
    def __init__(self, text: str = ""):
        super().__init__(text=text)
        self.full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def setText(self, text: str):
        self.full_text = text
        self.update_text()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.update_text()

    def update_text(self):
        metrics = QFontMetrics(self.font())
        elided = metrics.elidedText(self.full_text, Qt.ElideRight, self.width() - 10)
        super().setText(elided)
