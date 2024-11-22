import streamlit as st
import os
import time
from voice_interface import VoiceInterface
import requests
from dotenv import load_dotenv
from st_audiorec import st_audiorec
from utils import DataMapping, Responses
from autoplay import autoplay_audio

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
        
    def setup_streamlit(self):
        """Configure Streamlit page settings and styling."""
        st.set_page_config(
            page_title="ECHO AI Recommender",
            page_icon="🎙️",
            layout="wide"
        )
        
        # Add custom CSS for styling
        st.markdown("""
            <style>
                .stButton button {
                    width: 100%;
                    min-height: 45px;
                    font-size: 16px;
                    margin: 5px 0;
                    padding: 0 15px;
                    border-radius: 8px;
                }
                
                .order-summary {
                    background-color: #f0f2f6;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 10px 0;
                }
                
                .chat-message {
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    word-wrap: break-word;
                }
                
                .user-message {
                    background-color: #e1f5fe;
                    margin-left: 10px;
                }
                
                .assistant-message {
                    background-color: #f5f5f5;
                    margin-right: 10px;
                }
                
                .recommendation-card {
                    background-color: white;
                    padding: 12px;
                    border-radius: 8px;
                    margin: 8px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .recommendation-card button {
                    min-height: 35px;
                }
                
                .voice-controls {
                    position: sticky;
                    top: 0;
                    z-index: 100;
                    background-color: white;
                    padding: 10px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                
                .stAudio {
                    margin-bottom: 20px;
                }
            </style>
        """, unsafe_allow_html=True)
        
    def initialize_session_state(self):
        """Initialize session state variables."""
        session_vars = {
            'cart': [],
            'order_complete': False,
            'conversation': [],
            'last_recommendation': None,
            'selected_product': None
        }
        
        for var, default_value in session_vars.items():
            if var not in st.session_state:
                st.session_state[var] = default_value
                
    def display_header(self):
        """Display the application header."""
        st.markdown("""
            <h1 class="main-header" style="text-align: center;">🎙️ ECHO AI Recommender</h1>
            <h3 class="sub-header" style="text-align: center;">Voice-Enabled Shopping Assistant</h3>
            <hr>
        """, unsafe_allow_html=True)
                
    def display_cart(self):
        """Display the shopping cart and its controls."""
        if st.session_state.cart:
            st.sidebar.subheader("🛒 Shopping Cart")
            
            for item in st.session_state.cart:
                with st.sidebar.container():
                    col1, col2 = st.sidebar.columns([4, 1])
                    col1.text(f"• {item}")
                    if col2.button("❌", key=f"remove_{item}"):
                        st.session_state.cart.remove(item)
                        st.rerun()
            
            st.sidebar.markdown("---")
            total_items = len(st.session_state.cart)
            st.sidebar.text(f"Total Items: {total_items}")
            
            if st.sidebar.button("🛍️ Complete Order", key="complete_order"):
                self.complete_order()
                
    def display_voice_controls(self):
        """Display voice control buttons and recording status."""
        with st.container():
            st.write("Click to start/stop recording:")
            greetings_text = self.response.greeting_based_on_time()
            audio_path_greetings = self.voice_interface.text_to_speech(greetings_text)
            if audio_path_greetings:
                autoplay_audio(audio_path_greetings)
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
                                st.audio(audio_path)

                        if item_name:
                            item_captilized = self.voice_interface.capitalize_word(item_name)
                        
                        # st.session_state.conversation.append({
                        #     "role": "user",
                        #     "content": transcript
                        # })
                        
                            try:
                                response = requests.post(
                                    f"{self.api_endpoint}/all-recommendations",
                                    json={"product_name": item_captilized},
                                    timeout=10
                                )
                                response.raise_for_status()
                                
                                recommendations = response.json()["recommendations"]
                                print(recommendations)
                                st.session_state.last_recommendation = recommendations

                                matching_items, not_matching_items = self.data_mapping.split_list_on_product_name(recommendations, item_captilized)
                                matching_script = self.response.matching_list(matching_items)
                                not_matching_script = self.response.not_matching_list(not_matching_items)
                                print(f"Matching Script: {matching_script}")
                                print(f"Not Matching Script: {not_matching_script}")

                                # script = self.voice_interface.format_recommendation_message(recommendations)
                                # # print(script)
                                # audio_paths = []

                                audio_path_1 = self.voice_interface.text_to_speech(matching_script)
                                if audio_path_1:
                                    autoplay_audio(audio_path_1)

                                audio_path_2 = self.voice_interface.text_to_speech(not_matching_script)
                                if audio_path_2:
                                    autoplay_audio(audio_path_2)

                            
                        #     recommendation_text = "I recommend:\n" + "\n".join(
                        #         [f"• {rec}" for rec in recommendations[:3]]
                        #     )
                            
                            except requests.exceptions.RequestException as e:
                                st.error(f"Error getting recommendations: {str(e)}")
                                recommendation_text = "I'm having trouble getting recommendations right now."
                                return recommendation_text
                        
                        # st.session_state.conversation.append({
                        #     "role": "assistant",
                        #     "content": recommendation_text
                        # })
                        
                        # self.voice_interface.text_to_speech(recommendation_text)
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    print(f"Error details: {str(e)}")  # More detailed error in console
    
    def complete_order(self):
        """Complete the order and reset the cart."""
        if st.session_state.cart:
            order_summary = "Order completed! Items purchased:\n" + "\n".join(
                [f"• {item}" for item in st.session_state.cart]
            )
            
            st.session_state.conversation.append({
                "role": "assistant",
                "content": order_summary
            })
            
            self.voice_interface.text_to_speech(order_summary)
            
            st.session_state.cart = []
            st.session_state.order_complete = True
            st.rerun()
            
    def display_recommendations(self):
        """Display current recommendations if available."""
        if st.session_state.last_recommendation:
            st.subheader("Latest Recommendations")
            for rec in st.session_state.last_recommendation[:3]:
                with st.container():
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
    
    def run(self):
        """Run the Streamlit application."""
        self.display_header()
        
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
            
            # Recommendations
            self.display_recommendations()
        
        with main_content_col2:
            st.subheader("Voice Controls")
            self.display_voice_controls()
            
            # Reset button
            if st.button("🔄 Reset Conversation", key="reset"):
                st.session_state.conversation = []
                st.session_state.cart = []
                st.session_state.order_complete = False
                st.session_state.last_recommendation = None
                st.rerun()

if __name__ == "__main__":
    app = StreamlitApp()
    app.run()