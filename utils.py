from config import Config
import streamlit as st
import pandas as pd

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

    @staticmethod
    def calculate_confidence_level(confidence_score, threshold_confidence):
        deviation_percentage = ((confidence_score - threshold_confidence) / threshold_confidence) * 100
        
        if deviation_percentage <= -15:
            return 'very_low'
        elif -15 < deviation_percentage <= -5:
            return 'low'
        elif -5 < deviation_percentage <= 5:
            return 'medium'
        elif 5 < deviation_percentage <= 15:
            return 'high'
        else:
            return 'very_high'

    @staticmethod
    def add_confidence_level_column(df, confidence_thresholds):
        df_copy = df.copy()
        df_copy["confidence_level"] = df_copy.apply(
            lambda row: Utils.calculate_confidence_level(
                row["confidence"],
                confidence_thresholds.get(row["species"], Config.DEFAULT_THRESHOLD_VALUE)
            ),
            axis=1
        )
        df_copy["threshold"] = df_copy.apply(
            lambda row: confidence_thresholds.get(row["species"], Config.DEFAULT_THRESHOLD_VALUE),
            axis=1
        )
        return df_copy

