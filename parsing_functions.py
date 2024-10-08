import csv
import re
import json
from datetime import datetime

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

def extract_character_name(entrytag):
    """
    Extracts the character's name from the entry tag.
    Args: entrytag. The entry tag string.
    Returns: The extracted character name.
    """
    parts = entrytag.split('_')
    if len(parts) >= 3:
        # Character name is everything between the first and last part
        character_name_parts = parts[1:-1]
        character_name = '_'.join(character_name_parts)
        return character_name
    elif len(parts) == 2:
        # Entry tag format: <number>_<character_name>
        return parts[1]
    else:
        print(f"Warning: Unexpected entry tag format: '{entrytag}'")
        return 'Unknown'

def clean_dialogue_text(dialogueText):
    """
    Cleans the dialogue text by removing unwanted items and replacing specified items.
    Arg: dialogueText (str)
    Returns: The cleaned dialogue text.
    """
    if not dialogueText:
        return ''

    # Remove unwanted items
    for item in remove_items:
        dialogueText = dialogueText.replace(item, '')

    # Replace specified items
    for old, new in replace_items.items():
        dialogueText = dialogueText.replace(old, new)

    # Use regex to remove any remaining placeholders or tags, and any text within double braces {{}}, double brackets [[]], or angle brackets <>
    dialogueText = re.sub(r'\{\{.*?\}\}', '', dialogueText)   # {{...}}
    dialogueText = re.sub(r'\[\[.*?\]\]', '', dialogueText)   # [[...]]
    dialogueText = re.sub(r'<.*?>', '', dialogueText)         # <...>
    dialogueText = re.sub(r'\\[rn]', '', dialogueText)        # \r and \n
    dialogueText = re.sub(r'\.\.\.', '', dialogueText)        # ...
    dialogueText = re.sub(r'“', '"', dialogueText)            # Replaces fancy quotes with standard quotes
    dialogueText = re.sub(r'”', '"', dialogueText)

    # Normalize whitespace
    dialogueText = ' '.join(dialogueText.split())

    # Strip leading and trailing whitespace
    dialogueText = dialogueText.strip()

    return dialogueText

def parse_dialogue_csv(csv_file, voices_file):
    """
    Takes in a csv file containing a DialogueEntries table, and the VoiceAssignments.json file, and returns a list of entries.
    Args: csv_file (dialogue.csv), and voices_file (VoiceAssignments.json)
    Returns a list of entries, each one having an entrytag, dialogue_text, character ID, character name, voice ID, and voice name
    """
    # Read voice assignments
    voice_data = read_voices(voices_file)
    
    entries_original = []
    entries_cleaned = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        # Skip to the 'DialogueEntries' section
        for row in reader:
            if row and row[0] == 'DialogueEntries':
                break
        
        # Skip the next two header rows, as those are the column names
        next(reader, None)
        next(reader, None)
        
        # Iterate over the dialogue entries
        for row in reader:
            if not row or row[0] == 'OutgoingLinks':
                break
            entrytag = row[0]
            if len(row) > 7:
                dialogue_text = row[7]  # Adjust column index if needed
            else:
                print(f"Warning: Row has insufficient columns: {row}")
                continue

            cleaned_text = clean_dialogue_text(dialogue_text)

            # Skips entries with empty dialogue text
            if not cleaned_text.strip():
                continue

            # Extract character name from entrytag
            character_name = extract_character_name(entrytag)

            # Get character data from voice_data
            character_info = voice_data.get(character_name)

            if character_info:
                if character_name == 'Player':
                    #For 'Player', character_info is a list of voices
                    for char in character_info:
                        # Build the entry with all data
                        entry = {
                            'entrytag': entrytag,
                            'dialogue_text': dialogue_text,  # Original text
                            'character_id': char.get('ID'),
                            'character_name': char.get('Name'),
                            'voice_id': char.get('Voice ID'),
                            'voice_name': char.get('Voice Name'),
                        }
                        entries_original.append(entry)
                        entry_cleaned = entry.copy()
                        entry_cleaned['dialogue_text'] = cleaned_text  # Cleaned text
                        entries_cleaned.append(entry_cleaned)
                else:
                    # Build the entry with all data
                    entry = {
                        'entrytag': entrytag,
                        'dialogue_text': dialogue_text,  # Original text
                        'character_id': character_info.get('ID'),
                        'character_name': character_info.get('Name'),
                        'voice_id': character_info.get('Voice ID'),
                        'voice_name': character_info.get('Voice Name'),
                    }
                    entries_original.append(entry)
                    entry_cleaned = entry.copy()
                    entry_cleaned['dialogue_text'] = cleaned_text  # Cleaned text
                    entries_cleaned.append(entry_cleaned)
            else:
                # If character not found, print a warning
                print(f"Warning: Character '{character_name}' not found in voice assignments.")

    # Save the original entries to JSON with date in the filename
    with open(f'dialogue_original_{current_date}.json', 'w', encoding='utf-8') as f:
        json.dump(entries_original, f, indent=4)

    # Save the cleaned entries to JSON with date in the filename
    with open(f'dialogue_cleaned_{current_date}.json', 'w', encoding='utf-8') as f:
        json.dump(entries_cleaned, f, indent=4)

    print(f"Files created: dialogue_original_{current_date}.json, dialogue_cleaned_{current_date}.json")
    
    return entries_cleaned  # Ensure this function returns a non-None value

# TESTING
csv_file = 'dialogue.csv'
voices_file = 'VoiceAssignments.json'
entries = parse_dialogue_csv(csv_file, voices_file)

# Check if entries were successfully created
if entries:
    for entry in entries:
        print(f"EntryTag: {entry['entrytag']}")
        print(f"Character ID: {entry['character_id']}")
        print(f"Character Name: {entry['character_name']}")
        print(f"Voice ID: {entry['voice_id']}")
        print(f"Voice Name: {entry['voice_name']}")
        print(f"DialogueText: {entry['dialogue_text']}")
        print('-' * 50)
else:
    print("No entries were created. Check input files and parsing logic.")
