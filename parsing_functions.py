import csv
import re
import json
import os
from Entry import Entry
from datetime import datetime
from config import CONFIG

"""
The script performs the following main tasks:

-Parse the CSV file containing dialogue entries and create Entry objects for each line. (either "dialogue.csv" or "2024-10-09 - vSchool Dialogue Export.csv")
-Clean the dialogue text in each Entry, ensuring we keep the raw text and cleaned text.
-Load in voice assignments from a JSON file (VoiceAssignments.json).
-Assign voice IDs to each Entry based on character names.
-Save the assigned entries to a JSON file (assigned_entries.json).
-Save any unknown entries (entries without a matching voice ID) to another JSON file (unknown_entries.json).

The script uses a configuration file (config.py) to store settings such as column names, text cleaning rules, and other parameters.
"""

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime('%Y%m%d')

def parse_csv_dialogue(csv_file, config):
    """
    Parses the CSV file containing dialogue entries.
    Returns a list of Entry objects.
    """
    entries = []
    csv_config = config['csv']
    entrytag_column = csv_config['entrytag_column']
    dialogue_text_column = csv_config['dialogue_text_column']
    delimiter = csv_config.get('delimiter', ',')
    skip_rows = csv_config.get('skip_rows', 0)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=delimiter)
        
        # Skip to the 'DialogueEntries' section
        for row in reader:
            if row and row[0] == 'DialogueEntries':
                break

        # Read the header row after 'DialogueEntries'
        headers = next(reader, None)
        if headers is None:
            print("Error: Could not find header row after 'DialogueEntries' section.")
            return []
        
        # Skip additional header rows if necessary (you can change the amount of skip_rows in config.py)
        for _ in range(skip_rows):
            next(reader, None)
        
        headers = [header.strip() for header in headers]

        # Create a mapping from header names to indices
        header_indices = {header: index for index, header in enumerate(headers)}

        # Get indices for required columns
        try:
            entrytag_index = header_indices[entrytag_column]
            dialogue_text_index = header_indices[dialogue_text_column]
        except KeyError as e:
            print(f"Error: Required column not found in headers: {e}")
            print(f"Available headers: {headers}")
            return []

        # Read data rows
        for row in reader:
            if not row or row[0] == 'OutgoingLinks':
                break
            if len(row) <= max(entrytag_index, dialogue_text_index):
                continue

            entrytag = row[entrytag_index].strip()
            raw_text = row[dialogue_text_index].strip()

            # Skip empty or invalid rows
            if not entrytag or not raw_text:
                continue

            # Create an Entry object
            entry = Entry(entrytag=entrytag, rawText=raw_text)
            entries.append(entry)
    return entries

def clean_text(text, config):
    """
    Cleans the dialogue text based on the configuration.
    """
    if not text:
        return ''
    text_cleaning_config = config['text_cleaning']
    # Remove unwanted items
    for item in text_cleaning_config['remove_items']:
        text = text.replace(item, '')
    # Replace specified items
    for old, new in text_cleaning_config['replace_items'].items():
        text = text.replace(old, new)
    # Apply regex patterns
    for pattern in text_cleaning_config['regex_patterns']:
        text = re.sub(pattern, '', text)
    # Normalize whitespace
    text = ' '.join(text.split()).strip()
    return text

def load_voice_assignments(json_file):
    """
    Loads voice assignments from a JSON file.
    Returns a dictionary mapping character names to a list of voice IDs.
    """
    if not os.path.isfile(json_file):
        print(f"Error: Voice assignments file '{json_file}' not found.")
        return {}
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Build a mapping from character names to a list of voice IDs
    voice_assignments = {}
    for character_info in data.get('Character', []):
        name = character_info['Name']
        voice_id = character_info['Voice ID']
        if name not in voice_assignments:
            voice_assignments[name] = []
        voice_assignments[name].append(voice_id)
    return voice_assignments

def assign_voice_ids(entries, voice_assignments):
    """
    Assigns voice IDs to entries based on character names.
    Returns two lists: assigned_entries and unknown_entries.
    Handles multiple voice IDs for a character.
    """
    assigned_entries = []
    unknown_entries = []
    for entry in entries:
        character_name = entry.getName()
        voice_ids = voice_assignments.get(character_name)
        if voice_ids:
            # For multiple voice IDs, create copies of the entry
            for voice_id in voice_ids:
                new_entry = Entry(
                    entrytag=entry.entrytag,
                    rawText=entry.rawText,
                    voiceID=voice_id
                )
                new_entry.cleanText = entry.cleanText
                assigned_entries.append(new_entry)
        else:
            unknown_entries.append(entry)
    return assigned_entries, unknown_entries


def save_entries_to_json(entries, filename):
    """
    Saves a list of Entry objects to a JSON file.
    """
    entries_data = [entry.to_dict() for entry in entries]
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(entries_data, f, ensure_ascii=False, indent=4)
    print(f"Entries saved to '{filename}'.")

def main():

    csv_file = '2024-10-09 - vSchool Dialogue Export.csv'  # Replace with your actual CSV file name
    voice_assignments_file = 'VoiceAssignments.json'

    # Step 1: Parse dialogue entries into Entry objects
    entries = parse_csv_dialogue(csv_file, CONFIG)

    # Step 2: Clean dialogue text and set cleanText in Entry objects
    for entry in entries:
        clean_text_value = clean_text(entry.getRawText(), CONFIG)
        entry.setCleanText(clean_text_value)

    # Step 3: Load voice assignments
    voice_assignments = load_voice_assignments(voice_assignments_file)

    # Step 4: Assign voice IDs to entries, including handling for multiple voice IDs per character
    assigned_entries, unknown_entries = assign_voice_ids(entries, voice_assignments)

    # Step 5: Save assigned entries to JSON
    save_entries_to_json(assigned_entries, 'assigned_entries.json')

    # Step 6: Save unknown entries to JSON
    if unknown_entries:
        save_entries_to_json(unknown_entries, 'unknown_entries.json')
        print("Please review 'unknown_entries.json' and update your VoiceAssignments.json accordingly.")
    else:
        print("All entries have assigned voice IDs.")

if __name__ == "__main__":
    main()
