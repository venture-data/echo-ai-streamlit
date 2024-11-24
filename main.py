import streamlit as st
import os
import time
from voice_interface import VoiceInterface
import requests
from dotenv import load_dotenv
from st_audiorec import st_audiorec
from utils import DataMapping, Responses
from autoplay import autoplay_audio, delayed_autoplay_audio

# Load environment variables
load_dotenv(override=True)

class StreamlitApp:
    def __init__(self):
        """Initialize the Streamlit application."""
        self.setup_streamlit()
        self.initialize_session_state()
        
        # Initialize voice interface
        self.voice_interface = VoiceInterface()
        self.data_mapping = DataMapping()
        self.response = Responses()
        
        # Initialize API endpoint
        self.api_endpoint = st.secrets['API_ENDPOINT']
        
    def initialize_session_state(self):
        """Initialize session state variables."""
        session_vars = {
            'cart': [],
            'order_complete': False,
            'conversation': [],
            'last_recommendation': None,
            'selected_product': None,
            'pending_audio': None,  # New session state variable for audio
            'pending_delayed_audio': None,  # New session state variable for delayed audio
            'audio_delay': None  # New session state variable for audio delay
        }
        
        for var, default_value in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default_value
                
    def display_voice_controls(self):
        """Display voice control buttons and recording status."""
        with st.container():
            st.write("Click to start/stop recording:")
            greetings_text = self.response.greeting_based_on_time()
            audio_path_greetings = self.voice_interface.text_to_speech(greetings_text)
            if audio_path_greetings:
                st.audio(audio_path_greetings)
            
            # Add the audio recorder
            wav_audio_data = st_audiorec()
            
            if wav_audio_data is not None:
                try:
                    with st.spinner("Processing your voice input..."):
                        # Create recordings directory if it doesn't exist
                        os.makedirs("recordings", exist_ok=True)
                        
                        # Generate filename with timestamp
                        timestamp = time.strftime("%Y%m%d-%H%M%S")
                        recording_path = os.path.join("recordings", f"recording_{timestamp}.wav")
                        
                        # Save the audio data
                        with open(recording_path, 'wb') as f:
                            f.write(wav_audio_data)
                        
                        print(f"Recording saved to: {recording_path}")
                        
                        # Transcribe using AssemblyAI
                        print("Transcribing...")
                        transcript = self.voice_interface.transcribe_audio(recording_path)
                        
                        if hasattr(transcript, 'error'):
                            st.error(f"Transcription error: {transcript.error}")
                            return
                        
                        print(f"Transcribed text: {transcript}")
                        
                        if not transcript:
                            st.error("Could not understand the audio. Please try again.")
                            return
                        
                        item_name = self.voice_interface.extract_item_name(transcript)

                        if not item_name:
                            order_intent = self.voice_interface.check_order_intent(transcript)
                            audio_path = self.voice_interface.text_to_speech(order_intent)
                            if audio_path:
                                st.session_state.pending_audio = audio_path
                                st.rerun()

                        if item_name:
                            item_captilized = self.voice_interface.capitalize_word(item_name)
                        
                            try:
                                response = requests.post(
                                    f"{self.api_endpoint}/all-recommendations",
                                    json={"product_name": item_captilized},
                                    timeout=10
                                )
                                response.raise_for_status()
                                
                                recommendations = response.json()["recommendations"]
                                print(recommendations)
                                
                                # Update session state
                                st.session_state.last_recommendation = recommendations

                                matching_items, not_matching_items = self.data_mapping.split_list_on_product_name(
                                    recommendations, item_captilized)
                                matching_script = self.response.matching_list(matching_items)
                                not_matching_script = self.response.not_matching_list(not_matching_items)

                                audio_path_1 = self.voice_interface.text_to_speech(matching_script)
                                audio_path_2 = self.voice_interface.text_to_speech(not_matching_script)
                                
                                if audio_path_1:
                                    st.session_state.pending_audio = audio_path_1
                                if audio_path_2:
                                    st.session_state.pending_delayed_audio = audio_path_2
                                    st.session_state.audio_delay = 20
                                
                                st.rerun()
                            
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error getting recommendations: {str(e)}")
                                return
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    print(f"Error details: {str(e)}")
    
    def run(self):
        """Run the Streamlit application."""
        self.display_header()
        
        # Handle pending audio playback
        if st.session_state.pending_audio:
            autoplay_audio(st.session_state.pending_audio)
            st.session_state.pending_audio = None  # Clear the pending audio
            
        # Handle delayed audio playback
        if st.session_state.pending_delayed_audio and st.session_state.audio_delay:
            delayed_autoplay_audio(st.session_state.pending_delayed_audio, st.session_state.audio_delay)
            st.session_state.pending_delayed_audio = None
            st.session_state.audio_delay = None
        
        # Display recommendations first
        if st.session_state.last_recommendation:
            with st.container():
                st.subheader("Latest Recommendations")
                for rec in st.session_state.last_recommendation:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                            <div class="recommendation-card">
                                <div>{rec}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("Add", key=f"add_{rec}"):
                            if rec not in st.session_state.cart:
                                st.session_state.cart.append(rec)
                                st.rerun()
        
        # Sidebar/Cart
        self.display_cart()
        
        # Main content
        main_content_col1, main_content_col2 = st.columns([2, 1])
        
        with main_content_col1:
            # Conversation history
            st.subheader("Conversation")
            for message in st.session_state.conversation:
                css_class = "user-message" if message["role"] == "user" else "assistant-message"
                st.markdown(f"""
                    <div class="chat-message {css_class}">
                        {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
        
        with main_content_col2:
            st.subheader("Voice Controls")
            self.display_voice_controls()
            
            # Reset button
            if st.button("🔄 Reset Conversation", key="reset"):
                st.session_state.conversation = []
                st.session_state.cart = []
                st.session_state.order_complete = False
                st.session_state.last_recommendation = None
                st.session_state.pending_audio = None
                st.session_state.pending_delayed_audio = None
                st.session_state.audio_delay = None
                st.rerun()

if __name__ == "__main__":
    app = StreamlitApp()
    app.run()