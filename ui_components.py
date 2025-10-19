import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from api_client import APIClient
from audio_processor import AudioProcessor, SpectrogramGenerator
from typing import Dict

class UIComponents:
    @staticmethod
    def display_system_metrics():
        metrics = APIClient.fetch_system_metrics()
        
        if metrics:
            # col1, col2, col3, col4 = st.columns(4)
            
            # with col1:
            st.markdown(f"Recording status: **{'✅ On' if metrics['is_recording'] else '⛔ Off'}**")
            st.markdown(f"CPU Usage: **{metrics['cpu_usage']:.1f}%**")
            st.markdown(f"RAM Usage: **{metrics['ram_usage']:.1f}%**")
            st.markdown(f"Disk Usage: **{metrics['disk_usage']:.1f}%**")
        # with col2:
        # with col4:
            temp = metrics.get('temperature', 'N/A')
            if temp != 'N/A':
                st.markdown(f"Temperature: **{temp:.1f}°C**")
            else:
                st.markdown("Temperature: **N/A**")
        else:
            st.info("Waiting for new data...")

    @staticmethod
    def display_audio_and_spectrogram(filename: str, prediction_time: float, prediction_duration: float):
        if not AudioProcessor.download_and_cache_audio(filename):
            warn = st.warning("Audio download failed. Check connection or try again.")
            retry = st.button("Retry download", key=f"retry_{filename}", help="Attempt to download audio again")
            if retry:
                if AudioProcessor.download_and_cache_audio(filename):
                    st.rerun()
                else:
                    st.error("Retry failed. Please try later.")
            return
        
        file_path = AudioProcessor.get_cached_audio_path(filename)
        
        try:
            audio_data = file_path.read_bytes()
            trimmed_audio_buffer = AudioProcessor.extract_audio_segment(audio_data)
            
            st.text(f"Audio name: {filename}.wav")
            st.audio(trimmed_audio_buffer, format="audio/wav")
        
            with st.spinner("Spectrogram generation..."):
                fig = SpectrogramGenerator.create_spectrogram_xc(trimmed_audio_buffer, prediction_time, prediction_duration)
                st.pyplot(fig)
                plt.close(fig) 
                    
        except Exception as e:
            st.error(f"Audio processing error: {e}")

    @staticmethod
    def display_detections_table(df: pd.DataFrame):
        if df.empty:
            st.info("Nessun rilevamento per questa data.")
            return None
        
        # Prepara i dati per la visualizzazione
        display_df = df[['date', 'time', 'duration', 'species', 'confidence', 'threshold', 'confidence_level', 'filename']].copy()
        display_df['duration'] = display_df['duration'].astype(int)
        display_df['confidence'] = display_df['confidence'].round(3).map('{:.3f}'.format)
        display_df['threshold'] = display_df['threshold'].round(3).map('{:.3f}'.format)
        display_df['species'] = display_df['species'].str.replace('_', ', ')
        styled_df = display_df.style.map(UIComponents._color_confidence_level, subset=['confidence_level'])

        st.dataframe(
            styled_df,
            key="detections_table",     # st.session_state.detections_table
            on_select="rerun",
            selection_mode="single-row",
            height=500,
            hide_index=True,
            width='stretch'
        )
        
        # handle selection
        selected_rows = []
        table_state = st.session_state.get('detections_table')
        if table_state is not None:
            selected_rows = getattr(getattr(table_state, 'selection', None), 'rows', [])
        
        if selected_rows:
            selected_index = selected_rows[0]
            return {
                'filename': int(df.iloc[selected_index]["filename"]),
                "start_time": int(df.iloc[selected_index]["start_time"]),
                "duration": int(df.iloc[selected_index]["duration"])
            }
        return None

    @staticmethod
    def display_species_confidence_slider(confidence_thresholds: Dict[str, float] = {}):
        with st.expander("Modify confidence thresholds per species"):
            col1, col2 = st.columns(2)      # divide in two columns 
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
        return modified_thresholds
    
    @staticmethod
    def _color_confidence_level(val):
        """Colora le celle in base al livello di confidenza"""
        color_map = {
            'very_low': 'background-color: #d32f2f; color: white;',    # Rosso scuro
            'low': 'background-color: #f57c00; color: white',         # Arancione  
            'medium': 'background-color: #fbc02d; color: black',      # Giallo
            'high': 'background-color: #689f38; color: white',        # Verde chiaro
            'very_high': 'background-color: #388e3c; color: white'    # Verde scuro
        }
        return color_map.get(val, '')
    
