# app.py

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_session import Session
from zipfile import ZipFile
from werkzeug.utils import secure_filename
from parsing_functions import parse_dialogue_csv
from Entry import Entry

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

# Define the route for the API key input
@app.route('/')
def index():
    return render_template('index.html')  # Using index.html for API key entry

# Route for API key verification and redirecting to the file upload page
@app.route('/verify_key', methods=['POST'])
def verify_key():
    api_key = request.form.get('api_key')

    # Test the API key by making a request to ElevenLabs API
    headers = {
        "xi-api-key": api_key
    }
    response = requests.get('https://api.elevenlabs.io/v1/voices', headers=headers)

    if response.status_code == 200:
        # Store the API key in the session
        session['api_key'] = api_key
        return redirect(url_for('upload_page'))  # Redirect to file upload page
    else:
        flash('Invalid API key. Please try again.', 'error')
        return redirect(url_for('index'))

# Define the route to show the file upload form after verifying the API key
@app.route('/upload_page')
def upload_page():
    return render_template('upload_files.html')  # Second page for file upload

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

        # Get the API key from the session
        api_key = session.get('api_key')
        if not api_key:
            flash('API key not found in session. Please re-enter your API key.', 'error')
            return redirect(url_for('index'))

        # Create a temporary directory to save the audio files
        audio_output_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'audio_files')
        if not os.path.exists(audio_output_folder):
            os.makedirs(audio_output_folder)

        # Generate audio files using ElevenLabs API
        for entry in entries[:10]:
            text = entry.getCleanText()
            if not text:
                continue  # Skip entries with no text

            voice_id = entry.getVoiceID()
            if not voice_id:
                continue  # Skip entries with no voice ID

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
                audio_filename = f"{entry.getTag()}.mp3"
                audio_file_path = os.path.join(audio_output_folder, audio_filename)
                with open(audio_file_path, 'wb') as f:
                    f.write(response.content)
            else:
                print(f"Error generating audio for entry {entry.getTag()}: {response.status_code}, {response.text}")

        # Create a zip file of the audio files
        zip_filename = 'audio_files.zip'
        zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        with ZipFile(zip_file_path, 'w') as zipf:
            for root, dirs, files in os.walk(audio_output_folder):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        # Provide the zip file for download
        return send_file(zip_file_path, as_attachment=True)

    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=True)
