CONFIG = {
    'csv': {
        'entrytag_column': 'entrytag',
        'dialogue_text_column': 'DialogueText',
        'skip_header_rows': 1,
        'delimiter': ',',
    },
    'character_name_extraction': {
        'pattern': r'^\d+_(.+?)_\d+$',
        'group': 1,
    },
    'text_cleaning': {
        'remove_items': [
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
    "{{PLACEHOLDER- DANI MENU ACTIVATION ANIMATION}}", "{{PLACEHOLDER - PLAYER CLOSES MENU}}",
    "[In ear]",
    "[links to toppo lesson]",
], 
        'replace_items': {
    "’": "'",
    "–": " ",
    "-": " ",
    "—": " ",
    "TK": "Tea Kay",
    "C c c": "Kah, kah, kah",
    "WAT247": "Watt 2 4 7",
    "Mission HydroSci": "Mission Hydro Sci",
    "Mission Hydrosci": "Mission Hydro Sci",
}, 
        'regex_patterns': [
            r'\{\{.*?\}\}',   # {{...}}
            r'\[\[.*?\]\]',   # [[...]]
            r'<.*?>',         # <...>
            r'\\[rn]',        # \r and \n
            r'\.\.\.',        # ...
            r'[“”]',          # Fancy quotes
        ],
    },
}
