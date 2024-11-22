import streamlit as st
import base64
import uuid
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
    Plays multiple audio files sequentially, waiting for each to finish before starting the next
    
    Parameters:
        audio_files (list): List of paths to audio files to play in sequence
    """
    if not audio_files:
        return

    # Generate unique IDs for each audio element
    audio_ids = [f"audio_{uuid.uuid4().hex[:8]}" for _ in audio_files]
    
    # Create base64 encodings for all audio files
    audio_b64s = []
    for file_path in audio_files:
        with open(file_path, "rb") as f:
            data = f.read()
            audio_b64s.append(base64.b64encode(data).decode())
    
    # Create HTML/JavaScript for sequential playback
    audio_elements = []
    for i, (b64, audio_id) in enumerate(zip(audio_b64s, audio_ids)):
        audio_elements.append(f"""
            <audio id="{audio_id}" style="display: none">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
        """)
    
    js_code = """
        <script>
            function playSequentially(audioIds, currentIndex) {
                if (currentIndex >= audioIds.length) return;
                
                const currentAudio = document.getElementById(audioIds[currentIndex]);
                if (currentAudio) {
                    currentAudio.play();
                    currentAudio.addEventListener('ended', function() {
                        playSequentially(audioIds, currentIndex + 1);
                    });
                }
            }
            
            // Start playing the sequence
            const audioIds = {audio_ids_str};
            playSequentially(audioIds, 0);
        </script>
    """
    
    # Combine all elements and inject into page
    md = f"""
        {''.join(audio_elements)}
        {js_code.replace('{audio_ids_str}', str(audio_ids))}
    """
    st.markdown(md, unsafe_allow_html=True)

def play_greeting_audio(file_path: str):
    """
    Plays greeting audio with auto-refresh support
    
    Parameters:
        file_path (str): Path to the audio file to play
    """
    # Generate a timestamp to force browser to reload audio on each refresh
    timestamp = str(int(time.time() * 1000))
    
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        
    md = f"""
        <div id="greetingAudioContainer">
            <audio id="greetingAudio" autoplay="true">
                <source src="data:audio/mp3;base64,{b64}?t={timestamp}" type="audio/mp3">
            </audio>
            <script>
                const audio = document.getElementById('greetingAudio');
                
                // Force reload and play
                audio.load();
                
                // Play the audio as soon as possible
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {{
                    playPromise.catch(error => {{
                        console.log("Auto-play prevented by browser");
                    }});
                }}
                
                // Clean up when done
                audio.addEventListener('ended', function() {{
                    const container = document.getElementById('greetingAudioContainer');
                    if (container) {{
                        container.style.display = 'none';
                    }}
                }});
            </script>
        </div>
    """
    st.markdown(md, unsafe_allow_html=True)