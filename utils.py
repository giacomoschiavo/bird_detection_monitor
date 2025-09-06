from config import Config
import streamlit as st

class Utils:
    @staticmethod
    def clear_audio_cache():
        """Pulisce la cache audio"""
        try:
            for file_path in Config.AUDIO_CACHE_DIR.glob("*.wav"):
                file_path.unlink()
            st.session_state.audio_cache = {}
            st.success("Cache audio pulita!")
        except Exception as e:
            st.error(f"Error when trying to clean cache: {e}")
