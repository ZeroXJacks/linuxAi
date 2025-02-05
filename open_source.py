import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
                           QLabel, QFrame)
from PyQt5.QtCore import Qt
import google.generativeai as genai
import re
import subprocess

class CommandWidget(QFrame):
    def __init__(self, command, main_window):
        super().__init__()
        self.main_window = main_window
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        
        layout = QVBoxLayout(self)
        
        self.command_input = QLineEdit(command)
        layout.addWidget(self.command_input)
        
        button_layout = QHBoxLayout()
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(self.execute_command)
        button_layout.addWidget(self.execute_btn)
        
        layout.addLayout(button_layout)

    def execute_command(self):
        command = self.command_input.text()
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, error = process.communicate()
            if output:
                self.main_window.append_message("Command Output:\n" + output)
            if error:
                self.main_window.append_message("Error:\n" + error)
                
        except Exception as e:
            self.main_window.append_message(f"Error executing command: {str(e)}")

class GeminiChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux Chat")
        self.setGeometry(100, 100, 500, 300)
        genai.configure(api_key='AIzaSyB-RFTECTnoRKV5xRtLPoeDTTGSYnrowu4')
        self.model = genai.GenerativeModel('gemini-pro')
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)
        self.commands_area = QWidget()
        self.commands_layout = QVBoxLayout(self.commands_area)
        layout.addWidget(self.commands_area)
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
    def send_message(self):
        user_message = self.input_field.text().strip()
        if not user_message:
            return
            
        self.input_field.clear()
        self.append_message("You: " + user_message)
        response = self.get_ai_response(user_message)
        self.append_message("AI: " + response)
        self.detect_and_add_execute_buttons(response)
    def get_ai_response(self, message):
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    def append_message(self, message):
        self.chat_area.append(message + "\n\n")
    def detect_and_add_execute_buttons(self, response):
        for i in reversed(range(self.commands_layout.count())): 
            self.commands_layout.itemAt(i).widget().setParent(None)
        command_blocks = re.findall(r'```(.*?)```', response, re.DOTALL)
        for command in command_blocks:
            command = command.strip()
            if command:
                command_widget = CommandWidget(command, self)
                self.commands_layout.addWidget(command_widget)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GeminiChatApp()
    window.show()
    sys.exit(app.exec_())
