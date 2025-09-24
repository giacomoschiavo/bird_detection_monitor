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
def fetch_new_detections(start_date: datetime.date, end_date: datetime.date):
    return APIClient.fetch_detections(start_date, end_date)

@st.cache_data(ttl=Config.CACHE_TTL_METRICS)
def fetch_system_metrics():
    return APIClient.fetch_system_metrics()

    
# Sidebar
with st.sidebar:        
    
    # Metriche di sistema
    st.header("📊 System status")
    with st.spinner('Loading system status...'):
        UIComponents.display_system_metrics()

    st.header("Table view")
    # selected_date = st.date_input("Select date", value=datetime.now().date())
    # show_all = st.toggle('Show all', value=False, help='Render all detections for the selected date')
    max_rows = st.slider('Rows to show', min_value=100, max_value=500, value=250, step=50,
                         help="Number of most recent detections to render when 'Show all' is off")

    hide_non_species = st.toggle("Hide non-species classes", value=True,
                                 help="Filter out classes like None_, Wind_, Rain_, etc.")

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


# Metriche di sistema
# st.header("📊 System status")
# with st.spinner('Loading system status...'):
#     UIComponents.display_system_metrics()
# st.divider()

# Detection
st.header("🐦 Detections")

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
        default=["medium", "high", "very_high"],
        help="Filter detections by confidence level quality"
    )

# if "last_selected_date" not in st.session_state:
#     st.session_state.last_selected_date = selected_date
if "last_selected_dates" not in st.session_state:
    st.session_state.last_selected_dates = selected_dates

# if date changed while one row is selected -> remove selection
# date_changed = selected_date != st.session_state.last_selected_date
dates_changed = selected_dates != st.session_state.last_selected_dates
if dates_changed:
    if 'detections_table' in st.session_state:
        try:
            st.session_state.detections_table.selection.rows = []
        except Exception:
            st.session_state.pop('detections_table', None)
    st.session_state.last_selected_dates = selected_dates

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if isinstance(selected_dates, datetime.date) else datetime.now().date()

with st.spinner("Loading..."):
    detections = fetch_new_detections(start_date, end_date)
    confidence_thresholds = DataProcessor.get_confidence_thresholds(Config.CUSTOM_THRESHOLDS_PATH)
    with st.expander("Modify confidence thresholds per species"):
        col1, col2 = st.columns(2)
        # Dizionario per soglie modificate
        modified_thresholds = {}
        for i, (species, threshold) in enumerate(confidence_thresholds.items()):
            formatted_name = species.replace("_", ", " if species.split("_")[1] else "")
            if i < len(confidence_thresholds) / 2:
                with col1:
                    modified_value = st.slider(
                        label=f"Threshold for **{formatted_name}**",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(threshold),
                        step=0.01,
                        key=f"slider_{species}",
                    )
                    modified_thresholds[species] = modified_value

            else:
                with col2:
                    modified_value = st.slider(
                        label=f"Threshold for **{formatted_name}**",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(threshold),
                        step=0.01,
                        key=f"slider_{species}"
                    )
                    modified_thresholds[species] = modified_value

    df = DataProcessor.process_detections(detections, modified_thresholds)
    df = Utils.add_confidence_level_column(df, modified_thresholds)
    if selected_confidence_levels:
        df = df[df["confidence_level"].isin(selected_confidence_levels)]
    else:
        st.warning("No confidence levels selected. Please select at least one level.")
        df = pd.DataFrame()

df_view = df   # by default
if hide_non_species:
    df_view = DataProcessor.filter_non_species(df_view, Config.NON_SPECIES_PREFIXES)

if not df.empty:
    df_view = df_view.head(max_rows)

if not df.empty:
    # Statistiche rapide
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total detections", len(df))
    with col2:
        unique_species = df['species'].nunique()
        st.metric("Unique species", unique_species)

# Species confidence setup



# Tabella detection
selection = UIComponents.display_detections_table(df_view)

if not selection:
    st.info("Select a row to listen to the audio")
else:
    st.header("🎵 Audio Analysis")
    UIComponents.display_audio_and_spectrogram(selection['filename'], selection["start_time"] - int(selection['filename']), selection["duration"])

    # show species and confidence scores in the same segment
    # segment_detections = df[(df['timestamp'] == selection['timestamp']) & (df['offset'] == selection['offset'])]
    # segment_detections.sort_values('confidence', ascending=False)
    # species_confidence = segment_detections[['species', 'confidence']].values.tolist()
    # for species, conf in species_confidence:
    #     st.markdown(f"{species.replace('_', ' - ')}: {conf:.3f}")
