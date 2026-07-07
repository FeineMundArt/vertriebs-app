import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- DATENBANK-SETUP ---
DB_FILE = "solar_leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen', termin TEXT, notiz TEXT, zuletzt_bearbeitet TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, lead_id INTEGER, timestamp TEXT, notiz TEXT)")
    conn.commit()
    conn.close()

init_db()

# --- HELPER: GEODATEN SUCHEN ---
def get_coords(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location},+Germany&format=json&limit=1"
    headers = {'User-Agent': 'SolarCRM_App'}
    response = requests.get(url, headers=headers).json()
    if response:
        return response[0]['lat'], response[0]['lon']
    return None, None

# --- UI & CRM ---
st.set_page_config(page_title="Solar-Industrie CRM", layout="wide")
st.title("☀️ Solar-Industrie CRM")

tab1, tab2 = st.tabs(["📋 Lead-Pool & CRM", "🚀 Deutschlandweite Suche"])

with tab1:
    # CRM Logik (wie bisher)
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()
    if not df.empty:
        selected_name = st.selectbox("Firma wählen:", df['firmenname'].unique().tolist())
        lead = df[df['firmenname'] == selected_name].iloc[0]
        # ... (hier bleibt deine CRM-Logik gleich wie im letzten Code) ...
    else:
        st.info("Keine Leads vorhanden. Nutze den Tab 'Suche'!")

with tab2:
    st.write("### Deutschlandweite Industriesuche")
    search_loc = st.text_input("Ort oder PLZ für die Suche:", "Garbsen")
    radius = st.slider("Suchradius in Metern:", 1000, 20000, 5000)
    
    if st.button("🔍 Suche starten"):
        lat, lon = get_coords(search_loc)
        if lat and lon:
            with st.spinner("Suche läuft..."):
                query = f"""
                [out:json][timeout:25];
                (
                  nwr["building"="warehouse"](around:{radius},{lat},{lon});
                  nwr["industrial"="logistics"](around:{radius},{lat},{lon});
                  nwr["amenity"="townhall"](around:{radius},{lat},{lon});
                );
                out center;
                """
                response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
                data = response.json().get('elements', [])
                
                if data:
                    conn = sqlite3.connect(DB_FILE)
                    for el in data:
                        name = el.get('tags', {}).get('name', 'Industrie-Objekt')
                        conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, search_loc))
                    conn.commit()
                    conn.close()
                    st.success(f"{len(data)} neue Objekte geladen!")
                else:
                    st.warning("Nichts gefunden.")
        else:
            st.error("Ort konnte nicht gefunden werden.")
