import os
import streamlit as st
import pygame
from mutagen import File

# --- Page Configuration ---
st.set_page_config(
    page_title="Professional Audio Player",
    page_icon="🎵",
    layout="centered"
)

# --- Initialize Pygame Mixer ---
if not pygame.mixer.get_init():
    pygame.mixer.init()

# --- Initialize Session State ---
if "playlist" not in st.session_state:
    st.session_state.playlist = []  # List of dicts: {"name", "path", "duration"}

if "current_index" not in st.session_state:
    st.session_state.current_index = 0  

if "is_playing" not in st.session_state:
    st.session_state.is_playing = False

if "volume" not in st.session_state:
    st.session_state.volume = 0.5  # Default volume 50%

if "muted" not in st.session_state:
    st.session_state.muted = False
    st.session_state.prev_volume = 0.5

# Set initial volume in pygame
current_vol = 0.0 if st.session_state.muted else st.session_state.volume
pygame.mixer.music.set_volume(current_vol)

# --- Helper Function: Get Audio Duration ---
def get_audio_duration(file_path):
    try:
        audio = File(file_path)
        if audio is not None and audio.info is not None:
            return int(audio.info.length)
    except Exception:
        pass
    return 0  # Default if duration can't be fetched

def format_time(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

# --- App Header ---
st.title("🎵 Professional Audio Player")
st.markdown("A robust audio player built with **Streamlit**, **Pygame**, and **Mutagen**.")

# ==========================================
# 1. FILE MANAGEMENT HEADER
# ==========================================
st.subheader("📁 File Management")

col_file, col_folder = st.columns(2)

with col_file:
    uploaded_files = st.file_uploader(
        "1. Open Files (MP3, WAV, OGG)", 
        type=["mp3", "wav", "ogg"], 
        accept_multiple_files=True,
        key="file_uploader"
    )
    if uploaded_files:
        for file in uploaded_files:
            file_name = file.name
            if file_name not in [item["name"] for item in st.session_state.playlist]:
                temp_path = os.path.join("temp_" + file_name)
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                
                duration = get_audio_duration(temp_path)
                st.session_state.playlist.append({
                    "name": file_name,
                    "path": temp_path,
                    "duration": duration
                })

with col_folder:
    st.write("2. Open Folder Path")
    folder_path = st.text_input("Enter local folder directory path:", placeholder="e.g., C:/Music or ./my_songs")
    if st.button("Scan Folder"):
        if folder_path and os.path.isdir(folder_path):
            valid_extensions = (".mp3", ".wav", ".ogg")
            scanned_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
            
            added_count = 0
            for file_name in scanned_files:
                full_path = os.path.join(folder_path, file_name)
                if file_name not in [item["name"] for item in st.session_state.playlist]:
                    duration = get_audio_duration(full_path)
                    st.session_state.playlist.append({
                        "name": file_name,
                        "path": full_path,
                        "duration": duration
                    })
                    added_count += 1
            st.success(f"Successfully imported {added_count} tracks from folder!")
        else:
            st.error("Invalid directory path. Please check and try again.")

# --- Now Playing Display ---
st.markdown("---")
if st.session_state.playlist:
    current_track = st.session_state.playlist[st.session_state.current_index]
    st.markdown(f"### 🎧 Now Playing: **{current_track['name']}**")
else:
    st.markdown("### 🎧 Now Playing: *No tracks loaded*")

# ==========================================
# 2. INTERACTIVE PLAYLIST BOX
# ==========================================
st.subheader("📜 Interactive Playlist")

if st.session_state.playlist:
    for idx, track in enumerate(st.session_state.playlist):
        is_current = (idx == st.session_state.current_index)
        prefix = "▶️ **[Active]** " if is_current else "🎵 "
        duration_str = format_time(track['duration'])
        
        col_item, col_dur, col_select = st.columns([4, 1, 1])
        with col_item:
            st.write(f"{prefix} {track['name']}")
        with col_dur:
            st.text(duration_str)
        with col_select:
            if st.button("Select", key=f"select_{idx}"):
                st.session_state.current_index = idx
                pygame.mixer.music.load(track['path'])
                pygame.mixer.music.play()
                st.session_state.is_playing = True
                st.rerun()
else:
    st.warning("Playlist is empty. Please upload files or scan a folder.")

# ==========================================
# 3. SEEK BAR & TIME STAMPS
# ==========================================
st.markdown("---")
st.subheader("⏱️ Playback Progress")

current_duration = 0
if st.session_state.playlist:
    current_duration = st.session_state.playlist[st.session_state.current_index]['duration']

col_time_left, col_progress, col_time_right = st.columns([1, 6, 1])
with col_time_left:
    st.text("0:00")  # Elapsed time placeholder
with col_progress:
    # Interactive progress scrubber
    progress_val = st.slider(
        "Seek Bar", 
        min_value=0, 
        max_value=max(current_duration, 1), 
        value=0, 
        label_visibility="collapsed",
        disabled=not bool(st.session_state.playlist)
    )
with col_time_right:
    st.text(format_time(current_duration))

# ==========================================
# 4. PLAYBACK CONTROL PANEL
# ==========================================
st.markdown("---")
st.subheader("🎛️ Control Panel")

c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("⏮️ Previous"):
        if st.session_state.playlist:
            st.session_state.current_index = (st.session_state.current_index - 1) % len(st.session_state.playlist)
            track = st.session_state.playlist[st.session_state.current_index]
            pygame.mixer.music.load(track['path'])
            pygame.mixer.music.play()
            st.session_state.is_playing = True
            st.rerun()

with c2:
    if not st.session_state.is_playing:
        if st.button("▶️ Play"):
            if st.session_state.playlist:
                track = st.session_state.playlist[st.session_state.current_index]
                if not pygame.mixer.music.get_busy() and pygame.mixer.music.get_pos() > 0:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.load(track['path'])
                    pygame.mixer.music.play()
                st.session_state.is_playing = True
                st.rerun()
    else:
        if st.button("⏸️ Pause"):
            pygame.mixer.music.pause()
            st.session_state.is_playing = False
            st.rerun()

with c3:
    if st.button("⏹️ Stop"):
        pygame.mixer.music.stop()
        st.session_state.is_playing = False
        st.rerun()

with c4:
    if st.button("⏭️ Next"):
        if st.session_state.playlist:
            st.session_state.current_index = (st.session_state.current_index + 1) % len(st.session_state.playlist)
            track = st.session_state.playlist[st.session_state.current_index]
            pygame.mixer.music.load(track['path'])
            pygame.mixer.music.play()
            st.session_state.is_playing = True
            st.rerun()

# ==========================================
# 5. VOLUME CONTROL WITH MUTE TOGGLE
# ==========================================
st.markdown("---")
vol_col_icon, vol_col_slider = st.columns([1, 5])

with vol_col_icon:
    mute_label = "🔇 Unmute" if st.session_state.muted else "🔊 Mute"
    if st.button(mute_label):
        st.session_state.muted = not st.session_state.muted
        if st.session_state.muted:
            st.session_state.prev_volume = st.session_state.volume
            pygame.mixer.music.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(st.session_state.prev_volume)
        st.rerun()

with vol_col_slider:
    current_slider_val = 0.0 if st.session_state.muted else st.session_state.volume
    new_volume = st.slider(
        "Volume Slider", 
        0.0, 1.0, 
        current_slider_val, 
        0.05, 
        label_visibility="collapsed"
    )
    if not st.session_state.muted and new_volume != st.session_state.volume:
        st.session_state.volume = new_volume
        pygame.mixer.music.set_volume(st.session_state.volume)