import streamlit as st
import sqlite3
import pandas as pd
import os
from config import DB_PATH

# --- EINSTELLUNGEN ---
st.set_page_config(page_title="EcoLead Manager", layout="wide")

# --- DATENBANK SICHERSTELLEN ---
def init_db():
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt TEXT,
            firmenname TEXT,
            adresse TEXT,
            status TEXT DEFAULT 'Offen (Unbearbeitet)',
            bearbeiter TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- UI ---
st.markdown("<h1 style='color: #4caf50;'>🌱 EcoLead Manager — Cockpit</h1>", unsafe_allow_html=True)

with st.sidebar:
    projekt = st.selectbox("Projekt:", ["Solar & Speicher", "3nine"])
    if st.button("➕ Test-Lead Solar hinzufügen"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO leads (projekt, firmenname, adresse) VALUES (?, ?, ?)", 
                     (projekt, "Test-Firma Solar", "Solarweg 1"))
        conn.commit()
        conn.close()
        st.rerun()

# --- DATEN ANZEIGEN ---
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM leads WHERE projekt = ?", conn, params=(projekt,))
conn.close()

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Noch keine Leads in der Datenbank. Klicke auf den Button in der Sidebar.")
