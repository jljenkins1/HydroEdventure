# Entry.py

class Entry:
    def __init__(self, entrytag, voiceID=None, voiceName=None, rawText=''):
        self.entrytag = entrytag
        self.voiceID = voiceID
        self.voiceName = voiceName
        self.rawText = rawText
        self.cleanText = None  # to be set after cleaning
        self.characterName = self.getName()
    
    def getTag(self):
        return self.entrytag
    
    def getVoiceID(self):
        return self.voiceID
    
    def getVoiceName(self):
        return self.voiceName
    
    def getRawText(self):
        return self.rawText
    
    def getCleanText(self):
        return self.cleanText
    
    def setCleanText(self, cleanText):
        self.cleanText = cleanText
    
    def getName(self):
        """
        Extracts the character's name from the entrytag.
        """
        splitTag = self.entrytag.split('_')
        if len(splitTag) > 3:
            name_parts = splitTag[1:-1]
            name = '_'.join(name_parts)
            return name
        elif len(splitTag) > 1:
            return splitTag[1]
        else:
            return 'Unknown'
    
    def to_dict(self):
        """
        Converts the Entry object to a dictionary for JSON serialization.
        """
        return {
            'entrytag': self.entrytag,
            'voiceID': self.voiceID,
            'voiceName': self.voiceName,
            'rawText': self.rawText,
            'cleanText': self.cleanText,
            'characterName': self.characterName,
        }
