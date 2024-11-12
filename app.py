# app.py

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_session import Session
from zipfile import ZipFile
from werkzeug.utils import secure_filename
from parsing_functions import parse_dialogue_csv
from Entry import Entry
from datetime import datetime
import jwt
import secrets

# Set up the Flask application and define the upload directory.
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'your_secret_key_here'  # Replace with your actual secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Ensure the uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define a consistent secret key for JWT encoding/decoding
JWT_SECRET_KEY = 'jwt_secret_key_here'  # Replace with a secure key

# Define the route for the API key input
@app.route('/')
def index():
    return render_template('index.html')  # Using index.html for API key entry

# Route for API key verification and redirecting to the file upload page
@app.route('/verify_key', methods=['POST'])
def verify_key():
    api_key = request.form.get('api_key')

    # Create a JWT token with the API key
    payload = {'api_key': api_key}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

    # Test the API key by making a request to ElevenLabs API
    headers = {
        "xi-api-key": api_key
    }
    response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)

    if response.status_code == 200:
        # Store JWT Token and logged_in status in the session
        session['token'] = token
        session['logged_in'] = True
        return redirect(url_for('upload_page'))  # Redirect to file upload page
    else:
        flash('Invalid API key. Please try again.', 'error')
        return redirect(url_for('index'))

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()  # Clear session to log out the user
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # Redirect back to the API key entry page

# Define the route to show the file upload form after verifying the API key
@app.route('/upload_page')
def upload_page():
    # Ensure that only logged-in users can access the upload page
    if not session.get('logged_in'):
        flash('Please log in first.', 'error')
        return redirect(url_for('index'))  # Redirect to the API key page if not logged in
    return render_template('upload_files.html')  # Render the file upload page

# Route for handling the file uploads and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Confirm that both files have been submitted
        dialogue_file = request.files.get('dialogue')
        voice_file = request.files.get('voices')

        if not dialogue_file or not voice_file:
            flash('Both dialogue and voice files are required.', 'error')
            return redirect(request.url)

        if dialogue_file.filename == '' or voice_file.filename == '':
            flash('No file(s) selected.', 'error')
            return redirect(request.url)

        # Save the files securely
        dialogue_filename = secure_filename(dialogue_file.filename)
        voices_filename = secure_filename(voice_file.filename)

        dialogue_file_path = os.path.join(app.config['UPLOAD_FOLDER'], dialogue_filename)
        voices_file_path = os.path.join(app.config['UPLOAD_FOLDER'], voices_filename)

        dialogue_file.save(dialogue_file_path)
        voice_file.save(voices_file_path)

        # Process the files
        entries = parse_dialogue_csv(dialogue_file_path, voices_file_path)

        # Retrieve the JWT token from the session instead of API key
        token = session.get('token')
        if not token:
            flash('API key not found in session. Please re-enter your API key.', 'error')
            return redirect(url_for('index'))

        # Decode the JWT token to get the API key
        try:
            decoded_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            flash('Error in decoding JWT token. Please re-enter your API key.', 'error')
            return redirect(url_for('index'))

        # Get API key from decoded JWT token
        api_key = decoded_payload.get('api_key')

        # Date-time stamp for filenames
        date_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Base output directory
        output_base_dir = os.path.join(app.config['UPLOAD_FOLDER'], f"voice_files_{date_stamp}")

        # Character-specific folders for players
        player_folders = {f"Player{i}": os.path.join(output_base_dir, f"Player{i}") for i in range(1, 6)}
        for folder_path in player_folders.values():
            os.makedirs(folder_path, exist_ok=True)

        # Generate audio files using ElevenLabs API
        for entry in entries[:10]:  # Limit to 10 entries for testing
            text = entry.getCleanText()
            if not text:
                continue  # Skip entries with no text

            voice_id = entry.getVoiceID()
            if not voice_id:
                continue  # Skip entries with no voice ID

            # Determine folder based on character type
            folder_path = player_folders.get(entry.getTag(), output_base_dir)  # Player folders or base for NPCs

            # Generate audio request
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json"
            }
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.5
                }
            }

            response = requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                audio_filename = f"{entry.getTag()}_{date_stamp}.mp3"
                audio_file_path = os.path.join(folder_path, audio_filename)
                with open(audio_file_path, 'wb') as f:
                    f.write(response.content)
            else:
                # Log the error and continue
                flash(f"Error generating audio for entry {entry.getTag()}: {response.status_code}", 'error')

        # Create a zip file of the audio files for download
        zip_filename = f'voice_files_{date_stamp}.zip'
        zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        with ZipFile(zip_file_path, 'w') as zipf:
            for root, dirs, files in os.walk(output_base_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_base_dir)
                    zipf.write(file_path, arcname)

        # Provide the zip file for download
        return send_file(zip_file_path, as_attachment=True)

    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=True)
