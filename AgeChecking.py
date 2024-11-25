from flask import Flask, request, jsonify
from telethon.sync import TelegramClient
import os
import time

# Flask App setup
app = Flask(__name__)

# Directory where session files are stored
SESSION_DIR = './sessions'

# Telegram API credentials (replace with your actual values)
API_ID = 27477637
API_HASH = '059ef651932df7a0a1998e5db5148127'

# Ensure the session directory exists
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# Route to check session age
@app.route('/api/phonenumber', methods=['GET'])
def check_session_age():
    phone_number = request.args.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400

    # Construct session file name
    session_file = os.path.join(SESSION_DIR, f'{phone_number}.session')

    if not os.path.exists(session_file):
        return jsonify({'error': 'Session file not found'}), 404

    # Get the age of the session file
    file_creation_time = os.path.getctime(session_file)
    current_time = time.time()
    age_in_seconds = current_time - file_creation_time

    return jsonify({
        'phone_number': phone_number,
        'session_age_seconds': age_in_seconds
    })

# Route to create a new session
@app.route('/api/create_session', methods=['POST'])
def create_session():
    data = request.get_json()
    phone_number = data.get('phone_number')
    if not phone_number:
        return jsonify({'error': 'Phone number is required'}), 400

    session_file = os.path.join(SESSION_DIR, f'{phone_number}.session')

    # Create a new Telegram client session
    try:
        client = TelegramClient(session_file, API_ID, API_HASH)
        client.connect()

        if not client.is_user_authorized():
            return jsonify({'error': 'The provided phone number is not authorized'}), 403

        client.disconnect()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Session created successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8000)
