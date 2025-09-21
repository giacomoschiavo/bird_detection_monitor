import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import logging 
from config import Config
import os

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
    def get_confidence_thresholds(thresholds_path: str = "/data/species_confidence.csv"):
        try:
            if os.path.exists(thresholds_path):
                df = pd.read_csv(thresholds_path)
                return dict(zip(df["species"], df["threshold"]))
            else:
                logger.warning(f"Threshold folder not loaded. Using a default threshold of 0.2")
                return {}
        except Exception as e:
            logger.error("Error while fetching species threshold")
        
    @staticmethod
    def process_detections(detections: List[Dict[str, Any]], 
                           selected_date: int, 
                           confidence_thresholds: Dict[str, float] = None,
                           show_all: bool = False) -> pd.DataFrame:
        """
        Elabora le detection applicando la logica delle threshold per gruppo datetime
        
        Logica:
        1. Per ogni datetime, se è presente 'None' e supera la sua threshold -> elimina tutto il gruppo
        2. Se 'None' è presente ma non supera threshold -> controlla altre specie nel gruppo
        3. Se in un datetime c'è solo 'None' -> elimina il datetime
        4. Mantieni solo le specie che superano le loro threshold individuali
        """

        if not detections:
            return pd.DataFrame()
        
        if confidence_thresholds is None:
            confidence_thresholds = {}

        df = pd.DataFrame(detections)

        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True) + pd.to_timedelta(df['offset'], unit='s')
        df['datetime'] = df['datetime'].dt.tz_convert('Europe/Rome')

        df['date'] = df['datetime'].dt.date
        df['time'] = df['datetime'].dt.time

        df.sort_values(by="datetime", ascending=False, inplace=True)
        
        if df.empty or show_all:
            return df
        
        final_rows = []
        for datetime_group, group_df in df.groupby("datetime"):
            # cerca none nel gruppo
            none_rows = group_df[group_df["species"] == "None_"]
            other_species_rows = group_df[group_df["species"] != "None_"]

            # caso solo None 
            if len(none_rows) > 0 and len(other_species_rows) == 0:
                continue    # skip this datetime

            # caso none con altre specie
            if len(none_rows) > 0:
                none_confidence = none_rows.iloc[0]["confidence"]
                none_threshold = confidence_thresholds.get("None_", 0.2)

                if none_confidence >= none_threshold:
                    continue    # skip this datetime

            # controlla le altre specie
            for _, row in other_species_rows.iterrows():
                species = row["species"]
                confidence = row["confidence"]
                threshold = confidence_thresholds.get(species, 0.2)

                if confidence >= threshold:
                    final_rows.append(row)

        if final_rows:
            result_df = pd.DataFrame(final_rows)
            result_df.sort_values(by="datetime", ascending=False, inplace=True)
            return result_df

        return pd.DataFrame(columns=df.columns)
    
    @staticmethod
    def filter_non_species(df, non_species_list):
        if df.empty or "species" not in df.columns:
            return df
        mask = ~df["species"].astype(str).str.startswith(non_species_list)
        return df[mask]
