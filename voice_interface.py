import os
import time
import tempfile
import sounddevice as sd
import soundfile as sf
import requests
from dotenv import load_dotenv
import assemblyai as aai
from openai import OpenAI
import os
from typing import Optional
import streamlit as st

# Load environment variables
load_dotenv(override=True)

class VoiceInterface:
    def __init__(self):
        """Initialize the voice interface with API keys and audio settings."""
        # Load API keys from environment
        self.assemblyai_api_key = st.secrets['ASSEMBLYAI_API_KEY']
        self.elevenlabs_api_key = st.secrets['ELEVENLABS_API_KEY']
        
        if not self.assemblyai_api_key or not self.elevenlabs_api_key:
            raise ValueError("Missing required API keys in environment variables")
            
        # Initialize AssemblyAI
        aai.settings.api_key = self.assemblyai_api_key
        self.transcriber = aai.Transcriber()
        
        # Create recordings directory if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # ElevenLabs API settings
        self.tts_url = "https://api.elevenlabs.io/v1/text-to-speech"
        self.voice_options = {
        "rachel": "Xb7hH8MSUJpSbSDYk0k2",    # Rachel
        "domi": "pqHfZKP75CvOlQylNhV4	",      # Domi
        "bella": "9BWtsMINqrJLrRacOk9x",     # Bella
        "antoni": "nPczCjzI2devNBz1zQrb",     # Antoni
        "elli": "pFZP5JQG7iQjIQuC4Bku",      # Elli
       # Sam
        }
        self.voice_id = self.voice_options["rachel"]
        # self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Josh voice

    def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file using AssemblyAI.
        
        Args:
            audio_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text or None if failed
        """
        try:
            print(f"Transcribing audio file: {audio_path}")
            transcript = self.transcriber.transcribe(audio_path)
            
            if transcript.status == aai.TranscriptStatus.error:
                print(f"Transcription error: {transcript.error}")
                return None
            
            print(f"Transcription successful: {transcript.text}")
            return transcript.text
            
        except Exception as e:
            print(f"Error in transcription: {str(e)}")
            return None
    
    def extract_item_name(self, sentence: str) -> Optional[str]:
        """
        Extract item name from a sentence using OpenAI's API.
        
        Args:
            sentence (str): Input sentence containing item mention
            
        Returns:
            Optional[str]: Extracted item name or None if extraction fails

        """
        # print(f"API Key being used: {os.getenv('OPENAI_API_KEY')}")
        try:
            # Initialize OpenAI client
            client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
            
            # Construct the prompt
            prompt = f"""
            Extract only the item or product name from the following sentence. Return only the item name, nothing else.
            If multiple items are mentioned, return the main item being referred to.
            If no item is found, return "None".

            Sentence: "{sentence}"
            """
            
            # Make the API call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that extracts item names from sentences. Return only the item name, no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Use 0 for consistent responses
                max_tokens=50   # Limit response length
            )
            
            # Get the extracted item
            extracted_item = response.choices[0].message.content.strip()
            
            # Return None if no item was found
            if extracted_item.lower() == 'none':
                return None
                
            return extracted_item
            
        except Exception as e:
            print(f"Error extracting item name: {str(e)}")
            return None
        
    def capitalize_word(self, word: str) -> str:
        """
        Capitalizes first letter of word and handles special cases.
        
        Args:
            word (str): Input word to capitalize
            
        Returns:
            str: Capitalized word
        """
        try:
            # Handle empty strings
            if not word:
                return word
                
            # Basic capitalization
            capitalized = word[0].upper() + word[1:].lower()
            
            # Handle special cases with common product categories
            special_words = {
                "iphone": "iPhone",
                "ipad": "iPad",
                "macbook": "MacBook",
                "airpods": "AirPods"
            }
            
            return special_words.get(word.lower(), capitalized)
            
        except Exception as e:
            print(f"Error capitalizing word: {str(e)}")
            return word
        
    def format_recommendation_message(self, item_list: list) -> str:
        """
        Formats recommendation message based on item list.
        
        Args:
            item_list (list): List of recommended items
            
        Returns:
            str: Formatted recommendation message
        """
        if not item_list:
            return "I couldn't find any recommendations for you right now. Let me know if you'd like to order something else?"
        
        items_str = ", ".join(item_list)
        return f"Here are some items I recommend: [{items_str}]. Let me know if you'd like to add any of these to your cart!"
    
    def check_order_intent(self, response: str) -> str:
        """
        Analyzes user's response to determine if they want to place an order.
        
        Args:
            response (str): User's response text
            
        Returns:
            str: Appropriate response message
        """
        try:
            client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])
            
            prompt = f"""
            Analyze if this response indicates a positive intent to order/buy (yes) or negative (no).
            Return only 'yes' or 'no'.
            Response: "{response}"
            """
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a classifier that determines if a customer wants to place an order. Respond with only 'yes' or 'no'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            intent = completion.choices[0].message.content.strip().lower()
            
            if intent == 'yes':
                return "Thank you for shopping with us, your order has been placed. See you next time"
            else:
                return "Let me know if you would like some recommendations on other items you are considering to buy"
                
        except Exception as e:
            print(f"Error checking order intent: {str(e)}")
            return "I apologize, but I couldn't understand your response. Could you please try again?"
    
    def text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs.
        
        Args:
            text (str): Text to convert to speech
            
        Returns:
            Optional[str]: Path to generated audio file or None if failed
        """
        try:
            url = f"{self.tts_url}/{self.voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            print("Generating speech...")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                print("Speech generated successfully")
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                tts_path = os.path.join("recordings", f"tts_response_{timestamp}.mp3")
                
                # Save the audio response
                with open(tts_path, 'wb') as audio_file:
                    audio_file.write(response.content)
                
                return tts_path
                
            else:
                print(f"Error: Received status code {response.status_code} from ElevenLabs API")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error in text to speech: {str(e)}")
            return None

# Test function
def main():
    """Test the VoiceInterface functionality."""
    try:
        print("Initializing Voice Interface...")
        voice_interface = VoiceInterface()

        # print(voice_interface.extract_item_name("Hello. Can you recommend me items similar to milk?"))

        voice_interface.text_to_speech('')
        
        # Test transcription
    #     test_file = "new.wav"  # Replace with your test file
    #     if os.path.exists(test_file):
    #         print("\nTesting transcription...")
    #         transcribed_text = voice_interface.transcribe_audio(test_file)
            
    #         if transcribed_text:
    #             print(f"\nTranscribed text: {transcribed_text}")
                
    #             # Test text-to-speech
    #             # print("\nTesting text-to-speech...")
    #             # voice_interface.text_to_speech(f"You said: {transcribed_text}")
    #         else:
    #             print("\nTranscription failed.")
    #     else:
    #         print(f"\nTest file not found: {test_file}")
    #         print("Please provide a valid audio file for testing.")
            
    except Exception as e:
        print(f"\nError during test: {str(e)}")



if __name__ == "__main__":
    main()