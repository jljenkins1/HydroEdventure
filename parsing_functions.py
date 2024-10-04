import csv
import re

#List of items to remove from entries.
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
    "\\r", "\\n",
    "[links to toppo lesson]",
]

#Dictionary of items to replace 
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

def parse_dialogue_csv(csv_file):
    """
    Takes in a csv file containing a DialogueEntries table
    Returns a list of entries, each one having an entrytag and dialogue_text
    """
    entries = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        #Skip to the 'DialogueEntries' section
        for row in reader:
            if row and row[0] == 'DialogueEntries':
                break
        
        #Skip the next two header rows, as those are the column names
        next(reader, None)
        next(reader, None)
        
        #Iterate over the dialogue entries
        for row in reader:
            if not row or row[0] == 'OutgoingLinks':
                break
            entrytag = row[0]   
            dialogue_text = row[7]  #Adjust column index if needed

            cleaned_text = clean_dialogue_text(dialogue_text)

            entries.append({'entrytag': entrytag, 'dialogue_text': cleaned_text})
    return entries

def clean_dialogue_text(dialogueText):
    """
    Cleans the dialogue text by removing unwanted items and replacing specified items.
    Returns the cleaned dialogue text.
    """
    if not dialogueText:
        return ''

    #Remove unwanted items
    for item in remove_items:
        dialogueText = dialogueText.replace(item, '')

    #Replace specified items
    for old, new in replace_items.items():
        dialogueText = dialogueText.replace(old, new)

    #Use regex to remove any remaining placeholders or tags, and any text within double braces {{}}, double brackets [[]], or angle brackets <>
    dialogueText = re.sub(r'\{\{.*?\}\}', '', dialogueText)   # {{...}}
    dialogueText = re.sub(r'\[\[.*?\]\]', '', dialogueText)   # [[...]]
    dialogueText = re.sub(r'<.*?>', '', dialogueText)         # <...>
    dialogueText = re.sub(r'\(.*?\)', '', dialogueText)       # (...), e.g., (brightly)
    dialogueText = re.sub(r'\\[rn]', '', dialogueText)        # \r and \n
    dialogueText = re.sub(r'\.\.\.', '', dialogueText)        # ...
    dialogueText = re.sub(r'“', '"', dialogueText)            # Replace fancy quotes with standard quotes
    dialogueText = re.sub(r'”', '"', dialogueText)

    #Normalize whitespace
    dialogueText = ' '.join(dialogueText.split())

    #Strip leading and trailing whitespace
    dialogueText = dialogueText.strip()

    return dialogueText

#Testing
csv_file = 'dialogue.csv'
dialogue_Entries = parse_dialogue_csv(csv_file)

#Print every entry
for entry in dialogue_Entries:
    print(f"EntryTag: {entry['entrytag']}")
    print(f"DialogueText: {entry['dialogue_text']}")
    print('-' * 50)
