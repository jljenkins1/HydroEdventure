import csv
import re
import json
from datetime import datetime
from config import CONFIG

# List of items to remove from entries.
remove_items = [
    "[em1]", "[/em1]", "[em2]", "[/em2]", "[em3]", "[/em3]", "[em4]", "[/em4]",
    "[em5]", "[/em5]", "[em6]", "[/em6]", "\\r", "[/r]", "[/n]", "\\n",
    "<joke>", "[var=classifierFeedback]", "...", "{{PLACEHOLDER - CLOSE MAP}}",
    "{{PLACEHOLDER - OPEN MAP MENU}}", "{{PLACEHOLDER - MAP OPENS, MAP TUTORIAL 2 PLAYS}}",
    "{{PLACEHOLDER - ARGUMENTATION INTERFACE OPENS}}", "{{PLACEHOLDER - DRONE CONTROL TUTORIAL}}",
    "{{PLACEHOLDER - DATA TABLE POP-UP}}", "{{PLACEHOLDER - TOPOGRAPHY VIDEO}}",
    "{{PLACEHOLDER - U1 TOPOGRAPHY LESSON PLAYS}}", "{{PLACEHOLDER - WATERSHED TOPPO LESSON}}",
    "{{PLACEHOLDER - WATERSHED TOPPO LESSON PLAYS}}", "{{PLACEHOLDER - FORGE MINI GAME}}",
    "{{PLACEHOLDER - MAP OPENS AUTOMATICALLY}}", "{{PLACEHOLDER - MAP OPENS}}",
    "{{PLACEHOLDER - ARGUMENTATION}}", "{{PLACEHOLDER - TRANSITION TO BASE CAMP}}",
    "{{PLACEHOLDER - CLASSIFICATION EXERCISE AND FEEDBACK}}", "{{PLACEHOLDER - LAUNCH DRONE}}",
    "{{PLACEHOLDER - DANI MENU ACTIVATION ANIMATION}}", "{{PLACEHOLDER - MENU OPENS AUTOMATICALLY}}",
    "{{PLACEHOLDER - PLAYER CLOSES MENU}}", "{{PLACEHOLDER - TOPOGRAPHY LESSON PLAYS}}",
    "{{PLACEHOLDER - ARGUMENTATION TOPPO LESSON PLAYS}}",
    "{{PLACEHOLDER - SHIP SHAKES VIOLENTLY, DISTANT EXPLOSION}}",
    "{{PLACEHOLDER - OPEN ARGUMENTATION INTERFACE}}", "[[PLACEHOLDER - Argument]]",
    "[[PLACEHOLDER - Skipping the facility because it isn't in the scene yet]]", "[nosubtitle]",
    "<color=#35F>", "<color=#F53>", "*", '"', '"', "(brightly)", "(getting excited)", "…", "“",
    "”", "(muttering to herself)", "</color>", "[[Placeholder - Character Customization]]",
    "{{PLACEHOLDER- DANI MENU ACTIVATION ANIMATION}}", "{{PLACEHOLDER - PLAYER CLOSES MENU}",
    "[In ear]",
    "[links to toppo lesson]",
]

# Dictionary of items to replace 
replace_items = {
    "’": "'",
    "–": " ",
    "-": " ",
    "—": " ",
    "TK": "Tea Kay",
    "C c c": "Kah, kah, kah",
    "WAT247": "Watt 2 4 7",
    "Mission HydroSci": "Mission Hydro Sci",
    "Mission Hydrosci": "Mission Hydro Sci",
}

# Get the current date in YYYYMMDD format
current_date = datetime.now().strftime('%Y%m%d')

def read_voices(json_file):
    """
    Reads the voice assignments from the provided JSON file.
    Args:
        json_file (str): Path to the VoiceAssignments.json file.
    Returns:
        dict: A dictionary mapping character names to their data.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    characters = data.get('Character', [])
    voice_data = {}
    
    for char in characters:
        name = char.get('Name')
        if name == 'Player':
            # For 'Player', accumulate all voices
            if 'Player' not in voice_data:
                voice_data['Player'] = []
            voice_data['Player'].append(char)
        else:
            voice_data[name] = char
    
    return voice_data

def parse_csv_dialogue(csv_file, config):
    """
    Parses the CSV file containing dialogue entries.
    """
    entries = []
    csv_config = config['csv']
    entrytag_column = csv_config['entrytag_column']
    dialogue_text_column = csv_config['dialogue_text_column']
    delimiter = csv_config.get('delimiter', ',')

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
        
        # Skip the amount of header rows specified in the config file
        for _ in range(csv_config.get('skip_header_rows', 0)):
            next(reader, None)
        
        headers = [header.strip() for header in headers]  # Clean up header names
        print(f"CSV Headers: {headers}")  # Debugging print

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
                print(f"Warning: Row has insufficient columns: {row}")
                continue

            entrytag = row[entrytag_index]
            dialogue_text = row[dialogue_text_index]

            # Skip empty or invalid rows
            if not entrytag.strip() or not dialogue_text.strip():
                continue

            entry = {
                entrytag_column: entrytag,
                dialogue_text_column: dialogue_text,
            }
            entries.append(entry)
    return entries

def extract_character_name(entrytag, config):
    """
    Extracts the character's name from the entry tag using a regex pattern.
    """
    pattern = config['character_name_extraction']['pattern']
    group = config['character_name_extraction']['group']
    match = re.match(pattern, entrytag)
    if match:
        return match.group(group)
    else:
        print(f"Warning: Unable to extract character name from entrytag '{entrytag}'")
        return 'Unknown'

def clean_text(text, config):
    """
    Cleans the dialogue text based on the configuration.
    """
    if not text:
        return ''
    # Remove unwanted items
    for item in config['text_cleaning']['remove_items']:
        text = text.replace(item, '')
    # Replace specified items
    for old, new in config['text_cleaning']['replace_items'].items():
        text = text.replace(old, new)
    # Apply regex patterns
    for pattern in config['text_cleaning']['regex_patterns']:
        text = re.sub(pattern, '', text)
    # Normalize whitespace
    text = ' '.join(text.split()).strip()
    return text

def assign_voices_to_entries(entries, voice_data):
    """
    Assigns voices to each entry based on the character name.
    """
    assigned_entries = []
    for entry in entries:
        character_name = entry.get('character_name')
        character_info = voice_data.get(character_name)
        if character_info:
            if character_name == 'Player':
                for char in character_info:
                    assigned_entry = entry.copy()
                    assigned_entry.update({
                        'character_id': char.get('ID'),
                        'voice_id': char.get('Voice ID'),
                        'voice_name': char.get('Voice Name'),
                    })
                    assigned_entries.append(assigned_entry)
            else:
                entry.update({
                    'character_id': character_info.get('ID'),
                    'voice_id': character_info.get('Voice ID'),
                    'voice_name': character_info.get('Voice Name'),
                })
                assigned_entries.append(entry)
        else:
            print(f"Warning: Character '{character_name}' not found in voice assignments. ")

    return assigned_entries

def save_entries_to_json(entries, filename):
    """
    Saves the list of entries to a JSON file.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=4)
    print(f"Entries saved to {filename}")


if __name__ == "__main__":
    from config import CONFIG

    csv_file = '2024-10-09 - vSchool Dialogue Export.csv'
    voices_file = 'VoiceAssignments.json'

    # Read voice assignments
    voice_data = read_voices(voices_file)

    # Parse CSV dialogue
    entries = parse_csv_dialogue(csv_file, CONFIG)



    # Process entries
    for entry in entries:
        # Extract character name
        entrytag = entry[CONFIG['csv']['entrytag_column']]
        entry['character_name'] = extract_character_name(entrytag, CONFIG)

        # Clean dialogue text
        dialogue_text = entry[CONFIG['csv']['dialogue_text_column']]
        entry['dialogue_text_cleaned'] = clean_text(dialogue_text, CONFIG)

    # Assign voices
    entries_with_voices = assign_voices_to_entries(entries, voice_data)

    # Save entries to JSON
    current_date = datetime.now().strftime('%Y%m%d')
    output_filename = f'dialogue_entries_{current_date}.json'
    save_entries_to_json(entries_with_voices, output_filename)
