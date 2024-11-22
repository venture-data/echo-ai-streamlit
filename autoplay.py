import streamlit as st
import base64
import time

def autoplay_audio(file_path: str):
    """
    Automatically plays an audio file in Streamlit using HTML/JavaScript
    
    Parameters:
        file_path (str): Path to the audio file to play
    """
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        
    md = f"""
        <audio id="myAudio" autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            // Function to handle audio error
            document.getElementById('myAudio').addEventListener('error', function() {{
                console.error('Error playing audio');
            }});
            
            // Function to handle audio ended event
            document.getElementById('myAudio').addEventListener('ended', function() {{
                console.log('Audio playback completed');
            }});
        </script>
    """
    st.markdown(md, unsafe_allow_html=True)

def play_audio_sequence(audio_files: list):
    """
    Plays multiple audio files sequentially using Streamlit's native audio component
    
    Parameters:
        audio_files (list): List of paths to audio files to play in sequence
    """
    # Create a unique key for this sequence
    if 'current_audio_index' not in st.session_state:
        st.session_state.current_audio_index = 0
    
    if 'last_audio_time' not in st.session_state:
        st.session_state.last_audio_time = time.time()
    
    # Play current audio file
    if st.session_state.current_audio_index < len(audio_files):
        current_file = audio_files[st.session_state.current_audio_index]
        st.audio(current_file, key=f"audio_{st.session_state.current_audio_index}")
        
        # Add a small delay to ensure sequential playback
        time.sleep(0.5)
        
        # Update index for next audio file
        st.session_state.current_audio_index += 1
        if st.session_state.current_audio_index < len(audio_files):
            st.rerun()
        else:
            # Reset when sequence is complete
            st.session_state.current_audio_index = 0