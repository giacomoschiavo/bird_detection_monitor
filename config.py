from pathlib import Path

class Config:
  RASPBERRY_IP = "10.91.179.101" 
  API_BASE = f"http://{RASPBERRY_IP}:5001/api"
  REFRESH_RATE = 15000
  AUDIO_CACHE_DIR = Path("data/downloaded_audio")
  CUSTOM_THRESHOLDS_PATH = Path("data/species_confidence.csv")
  DEFAULT_THRESHOLD_VALUE = 0.2
  REQUEST_TIMEOUT = 5
  CACHE_TTL_DETECTIONS = 15
  CACHE_TTL_METRICS = 5
  NON_SPECIES_PREFIXES = ("None_", "Wind_", "Rain_", "Insect_", "Vegetation_")


Config.AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
