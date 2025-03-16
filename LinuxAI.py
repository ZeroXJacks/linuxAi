import sys
import os
import json
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                           QLabel, QFrame, QScrollArea, QSplitter, 
                           QDialog, QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont, QTextCursor
import google.generativeai as genai
import platform
import datetime
import getpass
import subprocess
COLORS = {
    'bg_dark': '#0D1117',      
    'bg_medium': '#161B22',   
    'text': '#E6EDF3',    
    'primary': '#1F6FEB', 
    'primary_hover': '#2F81F7',
    'accent': '#F7B64B',
    'error': '#F85149',
    'success': '#3FB950',
    'border': '#30363D' 
}

class TerminalTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: none;
                font-family: 'Ubuntu Mono', 'Courier New';
                font-size: 14px;
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.WidgetWidth)

class APIKeyDialog(QDialog):
    def __init__(self, parent=None, current_api_key=''):
        super().__init__(parent)
        self.setWindowTitle("Manage Gemini API Key")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border-radius: 10px;
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 13px;
            }}
            QLineEdit {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px;
                font-family: 'Ubuntu Mono', 'Courier New';
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
            QPushButton#cancelButton {{
                background-color: {COLORS['bg_medium']};
            }}
            QPushButton#cancelButton:hover {{
                background-color: {COLORS['error']};
                color: {COLORS['text']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        info_label = QLabel("Enter your Gemini API key below.")
        info_label.setStyleSheet(f"color: {COLORS['accent']};")
        layout.addWidget(info_label)
        
        input_layout = QFormLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(current_api_key)
        self.api_key_input.setPlaceholderText("Enter your API key here...")
        self.api_key_input.textChanged.connect(self.validate_api_key)
        input_layout.addRow("API Key:", self.api_key_input)
        layout.addLayout(input_layout)
        
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet(f"color: {COLORS['error']};")
        layout.addWidget(self.validation_label)
        
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save API Key")
        self.save_button.clicked.connect(self.accept)
        self.save_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

    def validate_api_key(self):
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            self.validation_label.setText("❌ API Key cannot be empty")
            self.validation_label.setStyleSheet(f"color: {COLORS['error']};")
            self.save_button.setEnabled(False)
            return False
        
        if not re.match(r'^[A-Za-z0-9_-]{39}$', api_key):
            self.validation_label.setText("❌ Invalid API Key format")
            self.validation_label.setStyleSheet(f"color: {COLORS['error']};")
            self.save_button.setEnabled(False)
            return False
        
        self.validation_label.setText("✓ Valid API Key format")
        self.validation_label.setStyleSheet(f"color: {COLORS['success']};")
        self.save_button.setEnabled(True)
        return True

class AIResponseThread(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, message):
        super().__init__()
        self.message = message
    
    def run(self):
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(self.message)
            self.response_ready.emit(response.text)
        except Exception as e:
            self.error_occurred.emit(str(e))

class CommandExecutionThread(QThread):
    output_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, command):
        super().__init__()
        self.command = command
    
    def run(self):
        try:
            process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = process.communicate()
            
            if output:
                self.output_ready.emit(output.rstrip())
            if error:
                self.error_occurred.emit(error)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

class CommandWidget(QFrame):
    def __init__(self, command, main_window):
        super().__init__()
        self.main_window = main_window
        self.command_thread = None
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                margin: 5px;
                padding: 10px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        header_layout = QHBoxLayout()
        command_label = QLabel("💻 Command:")
        command_label.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(command_label)
        layout.addLayout(header_layout)
        
        command_layout = QHBoxLayout()
        self.command_input = QLineEdit(command)
        self.command_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px;
                font-family: 'Ubuntu Mono', 'Courier New';
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        command_layout.addWidget(self.command_input)
        
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        copy_btn.clicked.connect(self.copy_command)
        command_layout.addWidget(copy_btn)
        layout.addLayout(command_layout)
        
        button_layout = QHBoxLayout()
        self.execute_btn = QPushButton("▶ Execute")
        self.execute_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['bg_dark']};
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
            }}
        """)
        self.execute_btn.clicked.connect(self.execute_command)
        button_layout.addWidget(self.execute_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def copy_command(self):
        QApplication.clipboard().setText(self.command_input.text())
        self.main_window.show_status_message("Command copied to clipboard!")

    def execute_command(self):
        command = self.command_input.text()
        self.execute_btn.setEnabled(False)
        self.execute_btn.setText("⏳ Running...")
        
        self.command_thread = CommandExecutionThread(command)
        self.command_thread.output_ready.connect(
            lambda output: self.main_window.chat_area.append(f"\nOutput:\n{output}")
        )
        self.command_thread.error_occurred.connect(
            lambda error: self.main_window.chat_area.append(f"\nError:\n{error}")
        )
        self.command_thread.finished.connect(self.on_command_finished)
        
        self.main_window.chat_area.append(f"\n> Executing: {command}")
        self.command_thread.start()
    
    def on_command_finished(self):
        self.execute_btn.setEnabled(True)
        self.execute_btn.setText("▶ Execute")
        self.command_thread = None

class GeminiChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux AI")
        self.setGeometry(100, 100, 1000, 800)
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['bg_dark']};
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_medium']};
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['primary']};
                min-height: 20px;
                border-radius: 6px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.api_key_file = os.path.join(os.path.dirname(__file__), 'api_key.json')
        self.load_api_key()
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        header_layout = QHBoxLayout()
        self.api_status_label = QLabel("API Key: Not Set")
        self.api_status_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['error']};
                padding: 5px 10px;
                background-color: {COLORS['bg_dark']};
                border-radius: 5px;
            }}
        """)
        header_layout.addWidget(self.api_status_label)
        
        self.api_key_button = QPushButton("🔑 Manage API Key")
        self.api_key_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self.api_key_button.clicked.connect(self.manage_api_key)
        header_layout.addWidget(self.api_key_button)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        splitter = QSplitter(Qt.Vertical)
        
        self.chat_area = TerminalTextEdit()
        splitter.addWidget(self.chat_area)
        
        commands_scroll = QScrollArea()
        commands_scroll.setWidgetResizable(True)
        commands_scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['bg_dark']};
                border: none;
                border-radius: 5px;
            }}
        """)
        
        self.commands_area = QWidget()
        self.commands_area.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self.commands_layout = QVBoxLayout(self.commands_area)
        self.commands_layout.setContentsMargins(10, 10, 10, 10)
        self.commands_layout.setSpacing(5)
        commands_scroll.setWidget(self.commands_area)
        splitter.addWidget(commands_scroll)
        
        main_layout.addWidget(splitter)
        
        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_medium']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(15, 10, 15, 10)
        
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
                border: 2px solid {COLORS['border']};
                border-radius: 5px;
                padding: 8px;
                font-family: 'Ubuntu Mono', 'Courier New';
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['primary']};
            }}
        """)
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['bg_dark']};
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
            }}
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        main_layout.addWidget(input_frame)
        
        self.show_welcome_message()
        self.input_field.setFocus()
        self.update_api_status()

    def load_api_key(self):
        try:
            if os.path.exists(self.api_key_file):
                with open(self.api_key_file, 'r') as f:
                    data = json.load(f)
                    api_key = data.get('api_key', '')
                    if api_key:
                        genai.configure(api_key=api_key)
                        return True
            return False
        except Exception as e:
            self.show_status_message(f"Error loading API key: {str(e)}")
            return False

    def save_api_key(self, api_key):
        try:
            with open(self.api_key_file, 'w') as f:
                json.dump({'api_key': api_key}, f)
            genai.configure(api_key=api_key)
            self.update_api_status()
            self.show_status_message("✓ API Key updated successfully!")
            return True
        except Exception as e:
            self.show_status_message(f"Error saving API key: {str(e)}")
            return False

    def update_api_status(self):
        has_api_key = os.path.exists(self.api_key_file)
        if has_api_key:
            self.api_status_label.setText("API Key: ✓ Set")
            self.api_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['success']};
                    padding: 5px 10px;
                    background-color: {COLORS['bg_dark']};
                    border-radius: 5px;
                }}
            """)
        else:
            self.api_status_label.setText("API Key: ❌ Not Set")
            self.api_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['error']};
                    padding: 5px 10px;
                    background-color: {COLORS['bg_dark']};
                    border-radius: 5px;
                }}
            """)

    def manage_api_key(self):
        current_api_key = ''
        try:
            if os.path.exists(self.api_key_file):
                with open(self.api_key_file, 'r') as f:
                    data = json.load(f)
                    current_api_key = data.get('api_key', '')
        except Exception:
            pass

        dialog = APIKeyDialog(self, current_api_key)
        if dialog.exec_() == QDialog.Accepted:
            new_api_key = dialog.api_key_input.text().strip()
            if new_api_key:
                self.save_api_key(new_api_key)

    def show_welcome_message(self):
        welcome_message = """Welcome to LinuxAI > 🚀
        
Type your message below to start chatting with the AI assistant.
To get started, make sure you have set up your API key using the 🔑 button above.
--------------------------
Have a great conversation! 😊
Dev @ZeroXJacks
"""
        self.chat_area.setPlainText(welcome_message)

    def show_status_message(self, message):
        msg = QMessageBox(self)
        msg.setWindowTitle("Status")
        msg.setText(message)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QPushButton {{
                background-color: {COLORS['primary']};
                color: {COLORS['text']};
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        msg.exec_()

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return
            
        if not os.path.exists(self.api_key_file):
            self.show_status_message("Please set up your API key first!")
            return
        
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)
        self.send_button.setText("⏳ Processing...")
        
        self.chat_area.append(f"\nYou: {message}")
        self.input_field.clear()
        
        self.response_thread = AIResponseThread(message)
        self.response_thread.response_ready.connect(self.handle_ai_response)
        self.response_thread.error_occurred.connect(self.handle_ai_error)
        self.response_thread.finished.connect(self.on_response_finished)
        self.response_thread.start()
    
    def handle_ai_response(self, response):
        self.chat_area.append(f"\nAI: {response}")
        self.detect_and_add_execute_buttons(response)
    
    def handle_ai_error(self, error):
        self.chat_area.append(f"\nError: {error}")
    
    def on_response_finished(self):
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self.input_field.setFocus()

    def detect_and_add_execute_buttons(self, response):
        for i in reversed(range(self.commands_layout.count())): 
            self.commands_layout.itemAt(i).widget().setParent(None)
        
        command_blocks = re.findall(r'```(.*?)```', response, re.DOTALL)
        for command in command_blocks:
            command = command.strip()
            if command.startswith('bash') or command.startswith('shell'):
                command = command[4:].strip()
            if command:
                command_widget = CommandWidget(command, self)
                self.commands_layout.addWidget(command_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeminiChatApp()
    window.show()
    sys.exit(app.exec_())