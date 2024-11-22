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
import threading

# Set up the Flask application and define the upload directory.
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)  # Random secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Ensure the uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define a consistent secret key for JWT encoding/decoding
JWT_SECRET_KEY = os.urandom(24)  # Random JWT secret key

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

# Define a function to create a directory if it does not exist
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path) 
        print(f"Directory created: {path}") 
    else: 
        print(f"Directory already exists: {path}")

# Define a function to generate the audio files for each dialogue line
def generate_audio_file(entry, api_key, folder_path, date_stamp, output_format):
    text = entry.getCleanText()
    if not text:
        return # Skip entries with no text
        
    voice_id = entry.getVoiceID()
    if not voice_id:
        return # Skip entries with no voice ID
        
    # Set the Accept header based on the selected output format
    accept_header = 'audio/ogg'  # Default to 'ogg'
    if output_format == 'mp3':
        accept_header = 'audio/mpeg'
        
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = { 
        "xi-api-key": api_key,
        "Accept": accept_header,
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
        create_directory(folder_path) # Ensure directory exists
        with open(audio_file_path, 'wb') as f:
            f.write(response.content)
    else:
        # Log the error
        print(f"Error generating audio for entry {entry.getTag()}: {response.status_code} - {response.text}")


# Route for handling the file uploads and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Confirm that both files have been submitted
        dialogue_file = request.files.get('dialogue')
        voice_file = request.files.get('voices')
        output_format = request.form.get('output_format', 'ogg')  # Default to 'ogg' if not provided

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

        if not entries:
            flash('No valid entries found in the uploaded files.', 'error')
            return redirect(request.url)

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
        os.makedirs(output_base_dir, exist_ok=True)

        # Get unique player voice IDs
        player_voice_ids = sorted(set(entry.voiceID for entry in entries if entry.characterName == "Player"))

        # Map voice IDs to Player1, Player2, etc.
        player_folders = {}
        for index, voice_id in enumerate(player_voice_ids, start=1):
            folder_name = f"Player{index}"
            folder_path = os.path.join(output_base_dir, folder_name)
            player_folders[voice_id] = folder_path
            os.makedirs(folder_path, exist_ok=True)

        # Generate audio files using ElevenLabs API
        threads = []
        for entry in entries[:31]:
            if entry.characterName == "Player":
                folder_path = player_folders.get(entry.getVoiceID())
                if not folder_path:
                    flash(f"Voice ID {voice_id} not assigned to any player folder.", 'error')
            else: 
                folder_path = output_base_dir # Save NPC lines to main folder
                
            thread = threading.Thread(target=generate_audio_file, args=(entry, api_key, folder_path, date_stamp)) 
            threads.append(thread) 
            thread.start()

        # Wait for threads to complete!
        for thread in threads:
            thread.join()
            # Determine folder based on character type
            if entry.characterName == "Player":
                folder_path = player_folders.get(voice_id)
                if not folder_path:
                    flash(f"Voice ID {voice_id} not assigned to any player folder.", 'error')
                    continue  # Skip if voice_id not found
            else:
                folder_path = output_base_dir  # Save NPC lines directly in main folder


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
