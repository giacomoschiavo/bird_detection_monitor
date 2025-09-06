from config import Config
import logging
import streamlit as st
import requests
from datetime import datetime, time
from typing import List, Dict, Any, Optional

class APIClient:
  
    # request info from a specific date (timestamp from midnight of that day)
    @staticmethod
    def fetch_detections(date: datetime.date) -> List[Dict[str, Any]]:
        # combine the date with a time of midnight (00:00:00)
        midnight_ts = int(datetime.combine(date, time.min).timestamp())
        try:
            response = requests.get(
                f"{Config.API_BASE}/birds/classifications",
                params={"since": midnight_ts}, 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching detections: {e}")
            st.error(f"Error while fetching info: {e}")
            return []
    
    @staticmethod
    def fetch_system_metrics() -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{Config.API_BASE}/system_metrics", 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()  
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error while fetching system metrics: {e}")
            st.error(f"Error while fetching system metrics: {e}")
            return None
    
    # request a specific audio using the name (timestamp)
    @staticmethod
    def fetch_audio(timestamp: int) -> Optional[bytes]:
        try:
            response = requests.get(
                f"{Config.API_BASE}/birds/audio/{timestamp}",
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Error while fetching audio {timestamp}: {e}")
            st.error(f"Error while fetching audio {timestamp}: {e}")
            return None
