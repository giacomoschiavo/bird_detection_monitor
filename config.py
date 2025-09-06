from pathlib import Path
class Config:
  RASPBERRY_IP = "10.66.175.183" 
  API_BASE = f"http://{RASPBERRY_IP}:5001/api"
  REFRESH_RATE = 15000
  AUDIO_CACHE_DIR = Path("data/downloaded_audio")
  CUSTOM_THRESHOLDS_PATH = Path("data/species_confidence.csv")
  DEFAULT_THRESHOLD_VALUE = 0.2
  REQUEST_TIMEOUT = 5
  CACHE_TTL_DETECTIONS = 15
  CACHE_TTL_METRICS = 5

  def __post_init__(self):
      """Inizializza le directory necessarie"""
      self.AUDIO_CACHE_DIR.mkdir(exist_ok=True)