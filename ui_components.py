import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from api_client import APIClient
from audio_processor import AudioProcessor, SpectrogramGenerator

class UIComponents:
    @staticmethod
    def display_system_metrics():
        metrics = APIClient.fetch_system_metrics()
        
        if metrics:
            # col1, col2, col3, col4 = st.columns(4)
            
            # with col1:
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
    def display_audio_and_spectrogram(timestamp: int, offset: float):
        if not AudioProcessor.download_and_cache_audio(timestamp):
            warn = st.warning("Audio download failed. Check connection or try again.")
            retry = st.button("Retry download", key=f"retry_{timestamp}", help="Attempt to download audio again")
            if retry:
                if AudioProcessor.download_and_cache_audio(timestamp):
                    st.rerun()
                else:
                    st.error("Retry failed. Please try later.")
            return
        
        file_path = AudioProcessor.get_cached_audio_path(timestamp)
        
        try:
            audio_data = file_path.read_bytes()
            trimmed_audio_buffer = AudioProcessor.extract_audio_segment(audio_data, offset)
            
            st.subheader("Audio")
            st.text(f"Audio name: {timestamp}.wav")
            st.audio(trimmed_audio_buffer, format="audio/wav")
        
            st.subheader("Spectrogram")
            with st.spinner("Spectrogram generation..."):
                fig = SpectrogramGenerator.create_spectrogram_xc(trimmed_audio_buffer)
                st.pyplot(fig)
                plt.close(fig) 
                    
        except Exception as e:
            st.error(f"Audio processing error: {e}")

    @staticmethod
    def display_detections_table(df_filtered: pd.DataFrame):
        """Mostra la tabella delle detection"""
        if df_filtered.empty:
            st.info("Nessun rilevamento per questa data.")
            return None
        
        # Prepara i dati per la visualizzazione
        display_df = df_filtered[['date', 'time', 'species', 'confidence']].copy()
        display_df['confidence'] = display_df['confidence'].round(3)

        st.dataframe(
            display_df,
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
                'timestamp': int(df_filtered.iloc[selected_index]["timestamp"]),
                'offset': float(df_filtered.iloc[selected_index]["offset"])
            }
        return None

