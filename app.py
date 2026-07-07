import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- DATENBANK & KONFIG ---
DB_FILE = "solar_leads.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen', 
            notiz TEXT, bearbeiter TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- APP UI ---
st.set_page_config(layout="wide", page_title="Solar CRM Pipeline")
st.title("☀️ CRM Pipeline (Industrie-Solar)")

# Sidebar
with st.sidebar:
    bearbeiter = st.text_input("Dein Name:", "Elke")

tab1, tab2 = st.tabs(["📊 Pipeline-Ansicht", "🔍 Suche (OSM)"])

with tab1:
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    spalten = ["Offen", "In Prüfung", "Termin vereinbart", "Vertrag"]
    cols = st.columns(len(spalten))
    
    for i, spalte in enumerate(spalten):
        with cols[i]:
            st.subheader(spalte)
            leads = df[df['status'] == spalte]
            for _, lead in leads.iterrows():
                with st.container(border=True):
                    st.write(f"**{lead['firmenname']}**")
                    st.caption(f"📍 {lead['adresse']}")
                    # Status-Update innerhalb der Karte
                    new_status = st.selectbox("Status ändern:", spalten, index=i, key=f"sel_{lead['id']}")
                    if new_status != spalte:
                        if st.button("Speichern", key=f"btn_{lead['id']}"):
                            conn = get_db_connection()
                            conn.execute("UPDATE leads SET status=?, bearbeiter=? WHERE id=?", (new_status, bearbeiter, lead['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()

with tab2:
    st.write("### Industrie-Solar Suche")
    loc = st.text_input("Ort eingeben:", "Schwabach")
    if st.button("Jetzt scannen"):
        url = f"https://nominatim.openstreetmap.org/search?q={loc},+Germany&format=json&limit=1"
        try:
            res = requests.get(url, headers={'User-Agent': 'SolarCRM'}).json()
            if res:
                lat, lon = res[0]['lat'], res[0]['lon']
                query = f'[out:json];nwr["building"="warehouse"](around:5000,{lat},{lon});out center;'
                data = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}).json()
                
                conn = get_db_connection()
                for el in data.get('elements', []):
                    name = el.get('tags', {}).get('name')
                    if name:
                        conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, loc))
                conn.commit()
                conn.close()
                st.success("Suche beendet.")
                st.rerun()
            else:
                st.error("Ort nicht gefunden.")
        except Exception as e:
            st.error(f"API Fehler (evtl. überlastet): {e}")
