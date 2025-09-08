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
    st.header("Controlli")
    
    if st.button("🔄 Aggiorna", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🗑️ Pulisci Cache Audio", use_container_width=True):
        Utils.clear_audio_cache()
    
    st.header("Impostazioni")
    selected_date = st.date_input("Seleziona data", value=datetime.now().date())
    
    # Mostra info cache
    cache_files = list(Config.AUDIO_CACHE_DIR.glob("*.wav"))
    st.info(f"File audio in cache: {len(cache_files)}")

# Metriche di sistema
st.header("📊 Stato Sistema")
UIComponents.display_system_metrics()

st.divider()

# Detection
st.header("🐦 Rilevamenti")

with st.spinner("Caricamento rilevamenti..."):
    detections = fetch_new_detections(selected_date)
    confidence_thresholds = DataProcessor.get_confidence_thresholds(Config.CUSTOM_THRESHOLDS_PATH)
    df_filtered = DataProcessor.process_detections(detections, selected_date)

if not df_filtered.empty:
    # Statistiche rapide
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale rilevamenti", len(df_filtered))
    with col2:
        unique_species = df_filtered['species'].nunique()
        st.metric("Specie uniche", unique_species)
    with col3:
        if not df_filtered.empty:
            last_detection = df_filtered['datetime'].iloc[0]
            st.metric("Ultimo rilevamento", last_detection.strftime("%H:%M:%S"))

# Tabella detection
selection = UIComponents.display_detections_table(df_filtered)

# Audio e spettrogramma
if selection:
    st.divider()
    st.header("🎵 Analisi Audio")
    UIComponents.display_audio_and_spectrogram(selection['timestamp'], selection['offset'])
