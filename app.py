import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- CONFIG ---
DB_FILE = "solar_leads.db"

# --- DATENBANK ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen', termin TEXT, notiz TEXT, zuletzt_bearbeitet TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER, timestamp TEXT, notiz TEXT)")
    conn.commit()
    conn.close()

init_db()

# --- APP LAYOUT ---
st.set_page_config(page_title="Industrie-Solar CRM", layout="wide")

# CSS für ein schöneres Aussehen
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    div.stButton > button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("☀️ Industrie-Solar CRM")

# TABS
tab1, tab2 = st.tabs(["📋 Lead-Pool", "🚀 Neue Leads suchen"])

with tab1:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    if not df.empty:
        # Layout: Links Auswahl, Rechts Details
        col_left, col_right = st.columns([1, 2])
        with col_left:
            firmen = df['firmenname'].unique().tolist()
            selected = st.selectbox("Wähle Firma:", firmen)
            lead = df[df['firmenname'] == selected].iloc[0]
            
        with col_right:
            st.subheader(f"Bearbeitung: {selected}")
            new_status = st.selectbox("Status", ["Offen", "Kontakt", "Termin", "Kein Interesse"], index=0)
            new_note = st.text_area("Protokoll:")
            if st.button("Speichern"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("UPDATE leads SET status=?, notiz=? WHERE id=?", (new_status, new_note, lead['id']))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.info("Datenbank ist leer. Gehe zu 'Neue Leads suchen'.")

with tab2:
    st.write("### Suche neue Industrieprojekte")
    loc = st.text_input("Ort eingeben (z.B. Hannover):", "Garbsen")
    
    if st.button("Scannen starten"):
        with st.spinner("Suche in OSM..."):
            # Geocoding
            url = f"https://nominatim.openstreetmap.org/search?q={loc},+Germany&format=json&limit=1"
            try:
                res = requests.get(url, headers={'User-Agent': 'SolarCRM'}).json()
                if res:
                    lat, lon = res[0]['lat'], res[0]['lon']
                    # Overpass API
                    query = f'[out:json];(nwr["building"="warehouse"](around:5000,{lat},{lon}););out center;'
                    data = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}).json()
                    
                    found = 0
                    conn = sqlite3.connect(DB_FILE)
                    for el in data.get('elements', []):
                        name = el.get('tags', {}).get('name')
                        if name:
                            conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, loc))
                            found += 1
                    conn.commit()
                    conn.close()
                    st.success(f"Gefunden: {found} neue Objekte.")
                else:
                    st.error("Ort nicht gefunden.")
            except Exception as e:
                st.error(f"Fehler beim Scannen: {e}")
