import os

# Pfade für die Datenhaltung
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ecolead.db")

# Sicherstellen, dass der Datenordner existiert
os.makedirs(DATA_DIR, exist_ok=True)
