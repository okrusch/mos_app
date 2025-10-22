import streamlit as st
import streamlit.components.v1 as components
import json
import random
import pandas as pd
import os
import time
import uuid
import glob
from supabase import create_client, Client

# --- Supabase connection ---
#url: str =  st.secrets["supabase"]["url"]
#key: str = st.secrets["supabase"]["key"]

url = "https://vhfwyymsccsbcxqutqjz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZoZnd5eW1zY2NzYmN4cXV0cWp6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA4Mjk1MjksImV4cCI6MjA3NjQwNTUyOX0.lnymYqhS-T5813lWbjWGDL2AiwLC3I8CapYQvpaRlhc"
supabase: Client = create_client(url, key)


# ---- SESSION STATE ----
if "current_audio" not in st.session_state:
    st.session_state.current_audio = None

if "user_id" not in st.session_state:
    st.session_state.user_id = uuid.uuid4().hex[:8]

# ---- LOAD ALL AUDIO LINKS ----
if "audio_data" not in st.session_state:
    st.session_state.audio_data = []
    for file in glob.glob("audio_links/*.json"):
        with open(file, "r") as f:
            data = json.load(f)["dataset"]
            st.session_state.audio_data.append((os.path.basename(file), data))  # (dataset_name, list of URLs)


# Session title
st.title("🎧 TTS Evaluation")
st.markdown("""
You will be presented with **one audio clip at a time**.  
Rate certain aspects on a scale of 1 to 5.

        
- Click next to rate the next audio sample. Your progress will be automatically saved.
- Before leaving the page click 'safe progress' to save your current rating.
            

Thank you for your participation!
""")

def pick_random_audio():
    dataset_name, urls = random.choice(st.session_state.audio_data)
    audio_url = random.choice(urls)
    return dataset_name, audio_url
    
def set_audio():
    # ---- DISPLAY AUDIO AND RATING ----
    if st.session_state.current_audio is None:
        dataset_name, audio_url = pick_random_audio()
        st.session_state.current_audio = (dataset_name, audio_url)
    else:
        dataset_name, audio_url = st.session_state.current_audio

    st.audio(audio_url)
        
    return dataset_name, audio_url

# Set default value
default_rating = "No answer"

# Initialize or reset session state BEFORE creating the radio
if "quality_rating" not in st.session_state:
    st.session_state.quality_rating = default_rating
if "naturalness_rating" not in st.session_state:
    st.session_state.naturalness_rating = default_rating
if "emotion_rating" not in st.session_state:
    st.session_state.emotion_rating = default_rating

# Radio button (uses session_state for its value)
st.subheader('Rate this audio (1-5)')
dataset_name, audio_url = set_audio()
quality_rating = st.radio(
    "Audio Quality (1=bad, 5=good):",
    ["No answer", 1, 2, 3, 4, 5],
    key="quality_rating",
    horizontal=True
)
naturalness_rating = st.radio(
    "Speech Naturalness (1=robotic, 5=real human):",
    ["No answer", 1, 2, 3, 4, 5],
    key="naturalness_rating",
    horizontal=True
)
emotion_rating = st.radio(
    "Emotion expressiveness (1=not emotional, 5=very emotional):",
    ["No answer", 1, 2, 3, 4, 5],
    key="emotion_rating",
    horizontal=True
)



col1, col2 = st.columns(2, gap="small", width="stretch")


def save_rating(dataset_name, audio_url, quality_rating, naturalness_rating, emotion_rating):
    if quality_rating != "No answer" and naturalness_rating != "No answer" and emotion_rating != "No answer":
        new_row = {
            "user_id": st.session_state.user_id,
            "dataset": dataset_name,
            "audio_url": audio_url,
            "quality_rating": int(quality_rating),
            "naturalness_rating": int(naturalness_rating),
            "emotion_rating": int(emotion_rating)
        }

        response = supabase.table("MOS").insert(new_row).execute()
        if response != None:
            st.toast("Your rating was submitted!", icon="✅")
            
            # Pick next audio
            dataset_name, audio_url = pick_random_audio()
            st.session_state.current_audio = (dataset_name, audio_url)

            time.sleep(1.0)
            st.session_state.quality_rating = default_rating
            st.session_state.naturalness_rating = default_rating
            st.session_state.emotion_rating = default_rating

            return True
        else:
            st.toast("Something went wrong!", icon="❌", duration='long')

    else:    
        st.toast("Pick a rating!", icon="❌", duration='long')

    return False

with col2:
    if st.button("Next ➡️", on_click=save_rating, args=(dataset_name, audio_url, quality_rating, naturalness_rating, emotion_rating)):
        st.rerun()


with col1:
    st.button("Safe progress ✅", on_click=save_rating, args=(dataset_name, audio_url, quality_rating, naturalness_rating, emotion_rating))


# Footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #f0f0f0;
        color: #333;
        text-align: center;
        padding: 10px 0;
        font-size: 14px;
    }
    </style>
    <div class="footer">
        Author: Leonhard Okrusch, Contact: leonokrusch@gmail.com
    </div>
    """,
    unsafe_allow_html=True
)