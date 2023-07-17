from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton


class SelectPath:
    def __init__(self, hint="", on_choice=None):
        self.layout = QHBoxLayout()
        self.path_textbox = QLineEdit()
        self.path_textbox.setPlaceholderText(hint)
        self.path_textbox.setReadOnly(True)
        self.choose_button = QPushButton("Choose...")
        self.choose_button.clicked.connect(on_choice)
        self.layout.addWidget(self.path_textbox)
        self.layout.addWidget(self.choose_button)

    def setEnabled(self, enabled):
        self.path_textbox.setEnabled(enabled)
        self.choose_button.setEnabled(enabled)
