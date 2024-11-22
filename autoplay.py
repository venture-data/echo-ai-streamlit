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