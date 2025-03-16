# Gemini Chat Assistant

![LinuxAi]()![](linuxai.png))


A modern desktop chat application powered by Google's Gemini AI, built with PyQt5. This application provides an intuitive interface for interacting with Gemini AI and executing commands.

Linux AI Assistant

## Features
- 🔑 **Secure API Key Management**: Safely store and manage your Gemini API key
- 💻 **Command Execution**: Execute commands directly from chat responses
- 🎨 **Modern Dark Theme**: Easy on the eyes with a beautiful dark interface
- ⚡ **Responsive Design**: Asynchronous processing prevents UI freezing
- 📋 **Command History**: View and re-run previous commands

## Installation

1. Clone the repository:
```bash
git clone https://github.com/@ZeroXJacks/LinuxAi.git
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Get your Gemini API key:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Keep it safe for use in the application

## Usage

1. Start the application:
```bash
python LinuxAi.py
```

2. First-time setup:
   - Click the "🔑 Manage API Key" button
   - Enter your Gemini API key
   - Click "Save API Key"

3. Start chatting:
   - Type your message in the input field
   - Press Enter or click "Send"
   - View AI responses in the chat area

4. Execute commands:
   - When the AI provides a command (in ```backticks```), it will appear in the command area
   - Click "📋 Copy" to copy the command
   - Click "▶ Execute" to run the command
   - View command output in the chat area

## Security Notes

- Your API key is stored locally in `api_key.json`
- Never share your API key or commit it to version control
- The application validates API key format before saving

## Troubleshooting

Common issues and solutions:

1. **API Key Issues**:
   - Ensure you've entered the correct API key
   - Check your internet connection
   - Verify your API key is active in Google AI Studio

2. **Command Execution**:
   - Make sure you have appropriate permissions
   - Check command syntax before execution
   - View error messages in the chat area


## Acknowledgments

- Google Gemini AI for the powerful language model
- PyQt5 for the GUI framework
- All contributors and users of this application

## Contact

Your Name - [@ZeroXJacks](https://twitter.com/@ZeroXJacks)

