import streamlit as st
import logging
from datetime import datetime
from config import Config
from api_client import APIClient
from data_processor import DataProcessor
from utils import Utils
from ui_components import UIComponents
from datetime import datetime, timedelta
import pandas as pd

# Configure logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Session state initialization
# ─────────────────────────────────────────────────────────────────────────────

# Initialize audio cache dictionary in session state if not present
# Stores {filename: cached_path} to avoid redundant downloads
if 'audio_cache' not in st.session_state:
    st.session_state.audio_cache = {}

# ─────────────────────────────────────────────────────────────────────────────
# Page configuration
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bird Detection Monitor",
    page_icon="🐦",
    layout='wide',      # Use full browser width for data tables
    initial_sidebar_state="expanded"        # Show sidebar controls by default
)

# ─────────────────────────────────────────────────────────────────────────────
# Cached data-fetching functions
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=Config.CACHE_TTL_DETECTIONS)
def fetch_new_detections(start_date: datetime.date, end_date: datetime.date):
    """
    Fetch bird detections within the given date range from the backend API.
    
    Results are cached with TTL defined in Config.CACHE_TTL_DETECTIONS to 
    minimize redundant network calls during repeated queries.
    
    Args:
        start_date: Beginning of detection query window (inclusive).
        end_date: End of detection query window (inclusive).
    
    Returns:
        list[dict]: Detection records with keys: species, confidence, filename, 
                    start_time, duration, and any additional metadata.
    """
    return APIClient.fetch_detections(start_date, end_date)

@st.cache_data(ttl=Config.CACHE_TTL_METRICS)
def fetch_system_metrics():
    """
    Fetch system health metrics from the monitoring backend.
    
    Metrics include CPU usage, memory, disk space, and detection queue length.
    Results are cached with TTL defined in Config.CACHE_TTL_METRICS.
    
    Returns:
        dict: Metric keys and values (e.g., {'cpu': 45.2, 'ram_used': 2048}).
    """

    return APIClient.fetch_system_metrics()

    
# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════

with st.sidebar:        
    
    st.header("📊 System status")
    with st.spinner('Loading system status...'):
        UIComponents.display_system_metrics()

    st.header("Table view")

    # Slider to limit number of rendered rows for performance on large datasets
    max_rows = st.slider('Rows to show', min_value=100, max_value=500, value=250, step=50,
                         help="Number of most recent detections to render when 'Show all' is off")
    # Toggle to exclude non-species classes (e.g., None_, Wind_, Rain_)
    hide_non_species = st.toggle("Hide non-species classes", value=True,
                                 help="Filter out classes like None_, Wind_, Rain_, etc.")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Manual controls section
    # ─────────────────────────────────────────────────────────────────────────
    st.header("Controls")

    if "is_fetching" not in st.session_state:
        st.session_state.is_fetching = False
    if "last_refresh_at" not in st.session_state:
        st.session_state.last_refresh_at = None

    if st.session_state.last_refresh_at:
        st.caption(f"Last refresh: {st.session_state.last_refresh_at.strftime('%H:%M:%S')}")
    refresh_clicked = st.button("🔄 Refresh", width="stretch", disabled=st.session_state.is_fetching)
    if refresh_clicked and not st.session_state.is_fetching:
        st.cache_data.clear()
        st.session_state.is_fetching = True
        st.rerun()
    
    st.button("🗑️ Clean Cache", width="stretch", on_click=Utils.clear_audio_cache, disabled=st.session_state.is_fetching)

    
    # show cache info
    cache_files = list(Config.AUDIO_CACHE_DIR.glob("*.wav"))
    st.info(f"Audio file in cache: {len(cache_files)}")

# ═════════════════════════════════════════════════════════════════════════════
# MAIN AREA: DETECTIONS
# ═════════════════════════════════════════════════════════════════════════════

# Detection
st.header("🐦 Detections")
st.subheader(f"Listening to: {Config.RASPBERRY_IP}")

# ─────────────────────────────────────────────────────────────────────────────
# User input controls: date range and confidence levels
# ─────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    # Dates selection
    selected_dates = st.date_input(
        "Select date range",
        value=(datetime.now().date() -  timedelta(days=7), datetime.now().date()),
        help="Select start and end dates for analysis"
    )
with col2:
    confidence_levels = ['very_low', 'low', 'medium', 'high', 'very_high']
    selected_confidence_levels = st.multiselect(
        "Confidence Levels",
        options=confidence_levels,
        default=["medium", "high", "very_high", 'very_low', 'low'],
        help="Filter detections by confidence level quality"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Handle date change: clear table selection to prevent stale row references
# ─────────────────────────────────────────────────────────────────────────────
if "last_selected_dates" not in st.session_state:
    st.session_state.last_selected_dates = selected_dates

# if date changed while one row is selected -> remove selection
dates_changed = selected_dates != st.session_state.last_selected_dates
if dates_changed:
    if 'detections_table' in st.session_state:
        try:
            st.session_state.detections_table.selection.rows = []
        except Exception:
            st.session_state.pop('detections_table', None)
    st.session_state.last_selected_dates = selected_dates

# ─────────────────────────────────────────────────────────────────────────────
# Parse date range input (handles tuple or single date)
# ─────────────────────────────────────────────────────────────────────────────
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if isinstance(selected_dates, datetime.date) else datetime.now().date()

# ─────────────────────────────────────────────────────────────────────────────
# Data pipeline: fetch → threshold adjustment → processing → filtering
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Loading..."):
    detections = fetch_new_detections(start_date, end_date)
    confidence_thresholds = DataProcessor.get_confidence_thresholds(Config.CUSTOM_THRESHOLDS_PATH)
    modified_thresholds = UIComponents.display_species_confidence_slider(confidence_thresholds)
    df = DataProcessor.process_detections(detections, modified_thresholds)
    df = Utils.add_confidence_level_column(df, modified_thresholds)
    if selected_confidence_levels:
        df = df[df["confidence_level"].isin(selected_confidence_levels)]
    else:
        st.warning("No confidence levels selected. Please select at least one level.")
        df = pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# Apply optional non-species filtering
# ─────────────────────────────────────────────────────────────────────────────
df_view = df   # by default
if hide_non_species:
    df_view = DataProcessor.filter_non_species(df_view, Config.NON_SPECIES_PREFIXES)

# ═════════════════════════════════════════════════════════════════════════════
# DISPLAY: Summary statistics and detection table
# ═════════════════════════════════════════════════════════════════════════════
if not df.empty:
    df_view = df_view.head(max_rows)
    # Statistiche rapide
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total detections", len(df))
    with col2:
        unique_species = df['species'].nunique()
        st.metric("Unique species", unique_species)


# ─────────────────────────────────────────────────────────────────────────
# Detections table with row selection
# ─────────────────────────────────────────────────────────────────────────
selection = UIComponents.display_detections_table(df_view)

if not selection:
    st.info("Select a row to listen to the audio")
else:
    st.header("🎵 Audio Analysis")
    UIComponents.display_audio_and_spectrogram(selection['filename'], selection["start_time"] - int(selection['filename']), selection["duration"])