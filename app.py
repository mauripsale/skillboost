from flask import Flask, render_template, request, jsonify, session
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
    ###
    return render_template('index.html')

@app.route('/gemini', methods=['GET', 'POST'])
def gemini_chat():
    user_input = ""
    if request.method == 'GET':
        user_input = request.args.get('user_input')
    else:
        user_input = request.form['user_input']
    logger.log(f"Starting chat session...")

        # Check if a chat session exists in the Flask session
    if 'chat' not in session:
        logger.log(f"Starting new chat session...")
        session['chat'] = create_session()  # Store the chat object in the session
        logger.log(f"New Chat Session created")
    else:
        logger.log(f"Reusing existing chat session...")

    chat = session['chat'] # Retrieve the chat object from the session

    content = response(chat_model,user_input)
    return jsonify(content=content)

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')