import streamlit as st
import sqlite3
import pandas as pd
import os
import subprocess
from config import DB_PATH

# 1. Automatischer Datenbank-Check beim Start
if not os.path.exists(DB_PATH):
    st.info("Datenbank wird initialisiert...")
    try:
        # Führt das Skript aus, das du gerade gezeigt hast
        subprocess.run(["python", "database/init_db.py"], check=True)
    except Exception as e:
        st.error(f"Fehler bei der Initialisierung: {e}")

# 2. UI-Layout
st.set_page_config(page_title="Vertriebs-Zentrale", layout="wide")
st.title("🌱 Vertriebs-Zentrale")

# 3. Datenbank-Verbindung
def get_leads(projekt):
    conn = sqlite3.connect(DB_PATH)
    # Prüfe ob Tabelle existiert, bevor wir abfragen
    try:
        df = pd.read_sql_query("SELECT * FROM leads WHERE projekt = ?", conn, params=(projekt,))
    except:
        df = pd.DataFrame()
    conn.close()
    return df

# 4. Sidebar für Auswahl
with st.sidebar:
    st.header("Einstellungen")
    aktueller_nutzer = st.selectbox("Wer arbeitet?", ["Patrick", "Elke", "Admin"])
    projekt = st.selectbox("Projekt:", ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"])

# 5. Hauptinhalt
st.write(f"Arbeitsbereich für: **{projekt}**")

df = get_leads(projekt)

if df.empty:
    st.warning("Keine Leads gefunden. Bitte stelle sicher, dass die Datenbank initialisiert wurde.")
else:
    st.dataframe(df)
