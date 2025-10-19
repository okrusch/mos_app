import streamlit as st
import streamlit.components.v1 as components
import json
import random
import pandas as pd
import os
import datetime
import uuid
import glob
from supabase import create_client, Client

# --- Supabase connection ---
url: str =  st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
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
st.title("🎧 Progressive MOS Study")
st.markdown("""
You will be presented with **one audio clip at a time**.  
Rate it from 1–5
Click next to rate the next audio sample. Your progress ill automatically be saved.
Before exiting click 'safe progress'.
Thank you for your participation!
""")

def pick_random_audio():
    dataset_name, urls = random.choice(st.session_state.audio_data)
    audio_url = random.choice(urls)
    return dataset_name, audio_url

def save_rating(dataset_name, audio_url, rating):
    new_row = {
        "user_id": st.session_state.user_id,
        "dataset": dataset_name,
        "audio_url": audio_url,
        "rating": int(rating)
    }

    response = supabase.table("MOS").insert(new_row).execute()
    if response != None:
        st.success("✅ Data saved to Supabase!")
    else:
        st.error("❌ Something went wrong!")

    
    st.success("Rating saved!")
    return True
    
def set_audio():
    # ---- DISPLAY AUDIO AND RATING ----
    if st.session_state.current_audio is None:
        dataset_name, audio_url = pick_random_audio()
        st.session_state.current_audio = (dataset_name, audio_url)
    else:
        dataset_name, audio_url = st.session_state.current_audio

    st.subheader(f"Dataset: {dataset_name}")
    st.audio(audio_url)

    rating = st.radio(
        "Rate this audio (1-5):",
        [1, 2, 3, 4, 5],
        index=0,
        key="rating",
        horizontal=True
    )
        
    return dataset_name, audio_url, rating

dataset_name, audio_url, rating = set_audio()
col1, col2 = st.columns(2)

with col2:
    if st.button("Next"):
        # Save rating
        saved = save_rating(dataset_name, audio_url, rating)
        if saved:
            
            # Pick next audio
            dataset_name, audio_url = pick_random_audio()
            st.session_state.current_audio = (dataset_name, audio_url)
            
            # Rerun
            st.rerun()


with col1:
    if st.button("Safe progress"):
        saved = save_rating(dataset_name, audio_url, rating)
        if saved:
            st.success(f"Rating saved. Thank you! You can close the tab or continue rating!")
