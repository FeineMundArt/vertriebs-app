import streamlit as st
import sqlite3
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIG ---
DB_FILE = "solar_leads.db"

# --- DATENBANK ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen', notiz TEXT)")
    conn.commit()
    conn.close()

init_db()

# --- APP ---
st.set_page_config(page_title="Industrie-Solar CRM", layout="wide")
st.title("☀️ Industrie-Solar CRM")

tab1, tab2 = st.tabs(["📋 Lead-Pool", "🚀 Suche starten"])

with tab1:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Datenbank ist leer. Gehe zu 'Suche starten'.")

with tab2:
    st.write("### Suche neue Industrieprojekte")
    loc = st.text_input("Ort eingeben:", "Garbsen")
    
    if st.button("Jetzt Scannen"):
        with st.spinner("Verbinde mit Server..."):
            try:
                # 1. Koordinaten holen
                geo_url = f"https://nominatim.openstreetmap.org/search?q={loc},+Germany&format=json&limit=1"
                geo_res = requests.get(geo_url, headers={'User-Agent': 'SolarCRM'}).json()
                
                if geo_res:
                    lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
                    
                    # 2. Overpass API mit Timeout und Delay
                    query = f'[out:json];(nwr["building"="warehouse"](around:5000,{lat},{lon}););out center;'
                    time.sleep(1) # Kurze Pause zum Schutz vor API-Blockaden
                    
                    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        elements = data.get('elements', [])
                        
                        conn = sqlite3.connect(DB_FILE)
                        count = 0
                        for el in elements:
                            name = el.get('tags', {}).get('name')
                            if name:
                                conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, loc))
                                count += 1
                        conn.commit()
                        conn.close()
                        st.success(f"Erfolg! {count} neue Firmen gefunden.")
                    else:
                        st.warning("Server antwortet nicht. Warte kurz und versuche es erneut.")
                else:
                    st.error("Ort nicht gefunden.")
            except Exception as e:
                st.error(f"Verbindungsfehler: {e}. Die API ist vermutlich gerade überlastet.")
