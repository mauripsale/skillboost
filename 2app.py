from flask import Flask, render_template, request, jsonify
import vertexai
from vertexai.generative_models import Content, GenerativeModel, Part
import os
import google.cloud.logging

app = Flask(__name__)
PROJECT_ID = os.environ.get('GCP_PROJECT') #Your Google Cloud Project ID
LOCATION = os.environ.get('GCP_REGION')   #Your Google Cloud Project Region

client = google.cloud.logging.Client(project=PROJECT_ID)
client.setup_logging()

LOG_NAME = "flask-app-internal-logs"
logger = client.logger(LOG_NAME)

vertexai.init(project=PROJECT_ID, location=LOCATION)

def create_session():
    chat_model = GenerativeModel("gemini-2.0-flash")
    chat = chat_model.start_chat()
    return chat

def response(chat, message):
    result = chat.send_message(message)
    return result.text

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gemini Chat App</title>
        <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', sans-serif;
            }
        </style>
    </head>
    <body class="bg-gradient-to-r from-blue-100 to-purple-100 flex justify-center items-center min-h-screen p-4">
        <div class="bg-white rounded-lg shadow-xl p-8 w-full max-w-2xl transition-transform hover:scale-105">
            <h1 class="text-2xl font-semibold text-center text-gray-800 mb-6">Gemini Chat</h1>
            <div id="chat-container" class="space-y-4">
                </div>
            <form id="input-form" class="mt-6">
                <div class="flex space-x-4">
                    <input
                        type="text"
                        id="user-input"
                        placeholder="Type your message..."
                        required
                        class="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 p-4"
                    >
                    <button type="submit" class="bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white rounded-md shadow-md p-4 transition-colors duration-300">
                        <span class="font-semibold">Send</span>
                    </button>
                </div>
            </form>
        </div>

        <script>
            const chatContainer = document.getElementById('chat-container');
            const userInputField = document.getElementById('user-input');
            const inputForm = document.getElementById('input-form');

            function addMessage(sender, message) {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('p-4', 'rounded-lg', 'shadow-sm');
                messageDiv.classList.add(sender === 'user' ? 'bg-indigo-100 text-indigo-800 ml-auto w-fit' : 'bg-gray-100 text-gray-800 mr-auto w-fit');
                messageDiv.textContent = message;
                chatContainer.appendChild(messageDiv);
                // Scroll to the bottom of the chat container to show the latest message
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            inputForm.addEventListener('submit', (event) => {
                event.preventDefault();
                const userMessage = userInputField.value.trim();
                if (!userMessage) return;

                addMessage('user', userMessage);
                userInputField.value = ''; // Clear the input field

                fetch('/gemini', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `user_input=${encodeURIComponent(userMessage)}`,
                })
                .then(response => response.json())
                .then(data => {
                    const geminiResponse = data.content;
                    addMessage('Gemini', geminiResponse);
                })
                .catch(error => {
                    console.error('Error:', error);
                    addMessage('Gemini', 'Sorry, there was an error communicating with the server.');
                });
            });
        </script>
    </body>
    </html>
    """

@app.route('/gemini', methods=['GET', 'POST'])
def gemini_chat():
    user_input = ""
    if request.method == 'GET':
        user_input = request.args.get('user_input')
    else:
        user_input = request.form['user_input']
    logger.log(f"Starting chat session...")
    chat_model = create_session()
    logger.log(f"Chat Session created")
    content = response(chat_model,user_input)
    return jsonify(content=content)

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
