import streamlit as st
import logging
from datetime import datetime
from config import Config
from api_client import APIClient
from data_processor import DataProcessor
from utils import Utils
from ui_components import UIComponents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if 'audio_cache' not in st.session_state:
    st.session_state.audio_cache = {}


st.set_page_config(
    page_title="Bird Detection Monitor",
    page_icon="🐦",
    layout='wide',
    initial_sidebar_state="expanded"
)
# st_autorefresh(interval=REFRESH_RATE, limit=None, key="api_request")

@st.cache_data(ttl=Config.CACHE_TTL_DETECTIONS)
def fetch_new_detections(date: datetime.date):
    return APIClient.fetch_detections(date)

@st.cache_data(ttl=Config.CACHE_TTL_METRICS)
def fetch_system_metrics():
    return APIClient.fetch_system_metrics()

    
# Sidebar
with st.sidebar:
    st.header("Settings")
    selected_date = st.date_input("Date selection", value=datetime.now().date())

    if "last_selected_date" not in st.session_state:
        st.session_state.last_selected_date = selected_date

    # if date changed while one row is selected
    # remove selection
    date_changed = selected_date != st.session_state.last_selected_date
    if date_changed:
        if 'detections_table' in st.session_state:
            try:
                st.session_state.detections_table.selection.rows = []
            except Exception:
                st.session_state.pop('detections_table', None)
        st.session_state.last_selected_date = selected_date

    if st.button("🔄 Refresh", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🗑️ Clean Cache", width="stretch"):
        Utils.clear_audio_cache()
    
    # show cache info
    cache_files = list(Config.AUDIO_CACHE_DIR.glob("*.wav"))
    st.info(f"Audio file in cache: {len(cache_files)}")

# Metriche di sistema
st.header("📊 System status")
UIComponents.display_system_metrics()

st.divider()

# Detection
st.header("🐦 Detections")

with st.spinner("Loading..."):
    detections = fetch_new_detections(selected_date)
    confidence_thresholds = DataProcessor.get_confidence_thresholds(Config.CUSTOM_THRESHOLDS_PATH)
    df_filtered = DataProcessor.process_detections(detections, selected_date, confidence_thresholds, remove_None=False)

if not df_filtered.empty:
    # Statistiche rapide
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total detections", len(df_filtered))
    with col2:
        unique_species = df_filtered['species'].nunique()
        st.metric("Unique species", unique_species)
    with col3:
        if not df_filtered.empty:
            last_detection = df_filtered['datetime'].iloc[0]
            st.metric("Last detection", last_detection.strftime("%H:%M:%S"))

# Tabella detection
selection = UIComponents.display_detections_table(df_filtered)

if not selection:
    st.info("Select a row to listen to the audio")
else:
    st.divider()
    st.header("🎵 Audio Analysis")
    UIComponents.display_audio_and_spectrogram(selection['timestamp'], selection['offset'])
