import pyttsx3
import threading
import logging
import tempfile
import os

class VoiceService:
    def __init__(self):
        self.engine = None
        self.initialize_engine()
    
    def initialize_engine(self):
        """Initialize the text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice settings
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to use a female voice for a more calming effect
                for voice in voices:
                    if 'female' in voice.name.lower() or 'woman' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate (slower for relaxation)
            self.engine.setProperty('rate', 150)
            
            # Set volume
            self.engine.setProperty('volume', 0.8)
            
        except Exception as e:
            logging.error(f"Error initializing voice engine: {e}")
            self.engine = None
    
    def text_to_speech(self, text):
        """Convert text to speech"""
        if not self.engine:
            logging.error("Voice engine not initialized")
            return None
        
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                temp_path = tmp_file.name
            
            # Save speech to file
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            return temp_path
            
        except Exception as e:
            logging.error(f"Error in text-to-speech: {e}")
            return None
    
    def speak_async(self, text):
        """Speak text asynchronously"""
        def speak():
            try:
                if self.engine:
                    self.engine.say(text)
                    self.engine.runAndWait()
            except Exception as e:
                logging.error(f"Error speaking text: {e}")
        
        thread = threading.Thread(target=speak)
        thread.daemon = True
        thread.start()

# Global voice service instance
voice_service = VoiceService()
