# app.py

import os
import requests
import threading
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_session import Session
from zipfile import ZipFile
from werkzeug.utils import secure_filename
from parsing_functions import parse_dialogue_csv
from Entry import Entry
from datetime import datetime
import jwt

# Set up the Flask application and define the upload directory.
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)  # Random secret key

# Configure server-side session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Dictionary to store job information
jobs = {}

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

def process_audio_files(dialogue_file_path, voices_file_path, token, output_format, job_id):
    """
    This function processes the audio files in a separate thread.
    """
    entries = parse_dialogue_csv(dialogue_file_path, voices_file_path)

    # Decode the JWT token to get the API key
    try:
        decoded_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        # If the token is invalid or expired, we can't process further.
        # Mark the job as failed
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = 'Invalid token'
        return

    # Get API key from decoded JWT token
    api_key = decoded_payload.get('api_key')

    # Date-time stamp for filenames
    date_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Base output directory
    output_base_dir = os.path.join(app.config['UPLOAD_FOLDER'], job_id, f"voice_files_{date_stamp}")
    os.makedirs(output_base_dir, exist_ok=True)

    # Character-specific folders
    player_folders = {}
    npc_folder = output_base_dir

    # Get unique player voices from entries
    player_voices = {entry.voiceID for entry in entries if entry.characterName == "Player" and entry.voiceID is not None}
    for index, voice_id in enumerate(sorted(player_voices), start=1):
        folder_name = f"Player{index}"
        folder_path = os.path.join(output_base_dir, folder_name)
        player_folders[voice_id] = folder_path
        os.makedirs(folder_path, exist_ok=True)

    # Generate audio files using ElevenLabs API
    for entry in entries[:31]:
        text = entry.getCleanText()
        if not text:
            continue  # Skip entries with no text

        voice_id = entry.getVoiceID()
        if not voice_id:
            continue  # Skip entries with no voice ID

        # Determine folder based on character type
        if entry.characterName == "Player" and voice_id in player_folders:
            folder_path = player_folders[voice_id]
        else:
            folder_path = npc_folder  # Save NPC lines or player lines without a voice folder directly in main folder

        # Set the Accept header based on the selected output format
        accept_header = 'audio/mpeg'  # Default to 'mp3'
        if output_format == 'ogg':
            accept_header = 'audio/ogg'

        # Generate audio request
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
            audio_filename = f"{entry.getTag()}_{date_stamp}.{output_format}"
            audio_file_path = os.path.join(folder_path, audio_filename)
            with open(audio_file_path, 'wb') as f:
                f.write(response.content)
        else:
            # Log the error and continue
            print(f"Error generating audio for entry {entry.getTag()}: {response.status_code}, {response.text}")

    # Create a zip file of the audio files for download
    zip_filename = f'voice_files_{date_stamp}.zip'
    zip_file_path = os.path.join(app.config['UPLOAD_FOLDER'], job_id, zip_filename)
    with ZipFile(zip_file_path, 'w') as zipf:
        for root, dirs, files in os.walk(output_base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_base_dir)
                zipf.write(file_path, arcname)

    # Processing completed, mark job as completed and store the zip file path
    jobs[job_id]['status'] = 'completed'
    jobs[job_id]['filename'] = zip_file_path
    print(f"Processing complete for job_id {job_id}. Output available at: {zip_file_path}")

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

        # Generate a unique job_id
        job_id = str(uuid.uuid4())

        # Create a job-specific folder
        job_folder = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
        os.makedirs(job_folder, exist_ok=True)

        dialogue_filename = secure_filename(dialogue_file.filename)
        voices_filename = secure_filename(voice_file.filename)

        dialogue_file_path = os.path.join(job_folder, dialogue_filename)
        voices_file_path = os.path.join(job_folder, voices_filename)

        dialogue_file.save(dialogue_file_path)
        voice_file.save(voices_file_path)

        # Retrieve the JWT token from the session instead of API key
        token = session.get('token')
        if not token:
            flash('API key not found in session. Please re-enter your API key.', 'error')
            return redirect(url_for('index'))

        # Store job information
        jobs[job_id] = {
            'status': 'processing',
            'filename': None
        }

        # Start a new thread for processing audio files
        thread = threading.Thread(
            target=process_audio_files,
            args=(dialogue_file_path, voices_file_path, token, output_format, job_id)
        )
        thread.start()

        flash(f"Your files are being processed in the background. Your job ID is {job_id}. Use this ID to check the status.", 'info')
        return redirect(url_for('job_status_page', job_id=job_id))

    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(request.url)

@app.route('/job_status_check', methods=['POST'])
def job_status_check():
    """
    This route handles the form submission for checking job status.
    It retrieves the job_id from the form and redirects the user to the job_status route.
    """
    job_id = request.form.get('job_id')
    return redirect(url_for('job_status_page', job_id=job_id))

@app.route('/job_status/<job_id>')
def job_status_page(job_id):
    """
    This route displays the status of a job based on the provided job_id.
    """
    job_info = jobs.get(job_id)

    if job_info is None:
        flash('Invalid Job ID.', 'error')
        return redirect(url_for('upload_page'))

    if job_info['status'] == 'completed':
        # Job is completed, user can download the file
        download_url = url_for('download_file', job_id=job_id)
        return render_template('job_status.html', zip_available=True, job_id=job_id, download_url=download_url)
    elif job_info['status'] == 'processing':
        # Job is still processing
        return render_template('job_status.html', zip_available=False, job_id=job_id)
    else:
        # Job failed or unknown status
        error_message = job_info.get('error', 'Unknown error')
        flash(f"Job {job_id} failed or has an unknown status: {error_message}", 'error')
        return redirect(url_for('upload_page'))

@app.route('/download/<job_id>')
def download_file(job_id):
    """
    This route handles downloading the processed zip file if available.
    """
    job_info = jobs.get(job_id)
    if not job_info or not job_info.get('filename'):
        flash('File not found or job not complete.', 'error')
        return redirect(url_for('job_status_page', job_id=job_id))

    zip_file_path = job_info['filename']
    if zip_file_path and os.path.exists(zip_file_path):
        return send_file(zip_file_path, as_attachment=True)
    else:
        flash('File not found or job not complete.', 'error')
        return redirect(url_for('job_status_page', job_id=job_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
