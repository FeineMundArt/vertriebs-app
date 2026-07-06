import streamlit as st
import sqlite3
import pandas as pd
import os
from config import DB_PATH

# --- FRISCHSTART-GARANTIE ---
# Löscht die Datenbank-Datei beim Start, damit wir immer einen sauberen Zustand haben
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass # Falls sie gerade benutzt wird, ignorieren wir es einfach
# ----------------------------
