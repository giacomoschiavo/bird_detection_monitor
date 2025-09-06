import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging 
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
  
    @staticmethod
    def load_confidence_thresholds() -> Dict[str, float]:
        if not Config.CUSTOM_THRESHOLDS_PATH.exists():
            logger.warning("Custom thresholds file not found, using defaults")
            return {}

        try:
            df = pd.read_csv(Config.CUSTOM_THRESHOLDS_PATH)
            return dict(zip(df.iloc[:, 0], df.iloc[:, 1]))
        except Exception as e:
            logger.error("Error while retrieving confidence score: {e}")
            return {}
        
    @staticmethod
    def process_detections(detections: List[Dict[str, Any]], selected_date: int) -> pd.DataFrame:
        if not detections:
            return pd.DataFrame()
        df = pd.DataFrame(detections)

        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True) + pd.to_timedelta(df['offset'], unit='s')
        df['datetime'] = df['datetime'].dt.tz_convert('Europe/Rome')

        df['date'] = df['datetime'].dt.date
        df['time'] = df['datetime'].dt.time

        last_detection = df['datetime'].max()
        st.metric("Ultimo rilevamento", last_detection.strftime("%H:%M:%S"))

        df_filtered = df[df['date'] == selected_date]
        df_filtered.sort_values(by="datetime", ascending=False, inplace=True)

        return df_filtered
    
