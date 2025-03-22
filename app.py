from flask import Flask, render_template, request, jsonify, session
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
import os
import google.cloud.logging
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SESSION_SECRET', 'your_secret_key')  # Use a secure secret key
PROJECT_ID = os.environ.get('GCP_PROJECT')
LOCATION = os.environ.get('GCP_REGION')

client = google.cloud.logging.Client(project=PROJECT_ID)
client.setup_logging()
LOG_NAME = "flask-app-internal-logs"
logger = client.logger(LOG_NAME)

vertexai.init(project=PROJECT_ID, location=LOCATION)

def create_session():
    chat_model = GenerativeModel("gemini-1.5-pro")
    chat = chat_model.start_chat()
    return chat

def response(chat, message):
    result = chat.send_message(message)
    return result.text

# Custom encoder to handle ChatSession serialization
class ChatSessionEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ChatSession):
            #  Serialize the chat session.  This is simplified for demonstration.
            #  In a real application, you might need to store more state.
            return {
                "_type": "ChatSession",
                "history": obj.history,
            }
        return super().default(obj)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gemini', methods=['GET', 'POST'])
def gemini_chat():
    user_input = ""
    if request.method == 'GET':
        user_input = request.args.get('user_input')
    else:
        user_input = request.form['user_input']

    logger.log(f"User input: {user_input}")

    # Check if a chat session exists in the Flask session
    if 'chat' not in session:
        logger.log(f"Starting new chat session...")
        chat = create_session()  # Create the chat object
        session['chat'] = ChatSessionEncoder().encode(chat) # Store the encoded chat object in the session
        logger.log(f"New Chat Session created")
    else:
        logger.log(f"Reusing existing chat session...")
        chat_data = session['chat']
        #  Decode the chat data back into a ChatSession object.
        chat_dict = json.loads(chat_data)

        #Reconstruct chat object
        chat = GenerativeModel("gemini-1.5-pro").start_chat(history=chat_dict['history'])

    session['chat'] = ChatSessionEncoder().encode(chat)  # Store the updated chat object back in the session

    content = response(chat, user_input)
    return jsonify(content=content)

if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
