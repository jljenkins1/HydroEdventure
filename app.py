# Import Libraries
import os
from flask import Flask, render_template, request, redirect, url_for, flash

# set up the Flask application and define the upload directory.
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'elevenlabssecretkey'  # Placeholder key

# configure the API key required for authentication
TEST_API_KEY = "Capstone-HydroDevs"

# Ensure the uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# define the route for the API key input
@app.route('/')
def index():
    return render_template('index.html')  # Using index.html for API key entry

# route for API key verification and redirecting to the file upload page
@app.route('/verify_key', methods=['POST'])
def verify_key():
    api_key = request.form.get('api_key')
    if api_key == TEST_API_KEY:
        return redirect(url_for('upload_page'))  # Redirect to file upload page
    else:
        flash('Invalid API key. Please try again.', 'error')
        return redirect(url_for('index'))

#define the route to show the file upload form after verifying the API key
@app.route('/upload_page')
def upload_page():
    return render_template('upload_files.html')  # Second page for file upload

# route for handling the file uploads
@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # confirm that both files have been submitted
        dialogue_file = request.files.get('dialogue')
        voice_file = request.files.get('voices')

        if not dialogue_file or not voice_file:
            flash('Both dialogue and voice files are required.', 'error')
            return redirect(request.url)

        if dialogue_file.filename == '' or voice_file.filename == '':
            flash('No file(s) selected.', 'error')
            return redirect(request.url)

        # file Saver
        dialogue_file.save(os.path.join(app.config['UPLOAD_FOLDER'], dialogue_file.filename))
        voice_file.save(os.path.join(app.config['UPLOAD_FOLDER'], voice_file.filename))

        flash('Files uploaded successfully!', 'success')
        return redirect(url_for('upload_page'))

    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=True)