import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- KONFIGURATION ---
DB_FILE = "solar_leads.db"

# --- DATENBANK-SETUP ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen',
            termin TEXT, notiz TEXT, zuletzt_bearbeitet TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER, timestamp TEXT, notiz TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNKTIONEN ---
def get_coords(location):
    url = f"https://nominatim.openstreetmap.org/search?q={location},+Germany&format=json&limit=1"
    headers = {'User-Agent': 'SolarCRM_App_V1'}
    try:
        response = requests.get(url, headers=headers).json()
        if response:
            return response[0]['lat'], response[0]['lon']
    except: pass
    return None, None

# --- UI START ---
st.set_page_config(page_title="Solar-Industrie CRM", layout="wide")
st.title("☀️ Solar-Industrie CRM")

# TABS DEFINIEREN
tab1, tab2 = st.tabs(["📋 Lead-Pool & CRM", "🚀 Deutschlandweite Suche"])

with tab1:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    if not df.empty:
        selected_name = st.selectbox("Firma wählen:", df['firmenname'].unique().tolist())
        lead = df[df['firmenname'] == selected_name].iloc[0]
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"### 🏢 {lead['firmenname']}")
            st.write(f"📍 **Adresse:** {lead['adresse']}")
            status = st.selectbox("Status:", ["Offen", "Kontakt aufgenommen", "Termin vereinbart", "Kein Interesse"], 
                                 index=["Offen", "Kontakt aufgenommen", "Termin vereinbart", "Kein Interesse"].index(lead['status']))
            termin = st.date_input("Nächster Termin:", value=datetime.today())
        
        with col2:
            neue_notiz = st.text_area("Neues Protokoll:")
            if st.button("💾 Speichern"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("UPDATE leads SET status=?, termin=?, zuletzt_bearbeitet=? WHERE id=?", 
                             (status, str(termin), datetime.now().strftime("%d.%m.%Y"), lead['id']))
                if neue_notiz:
                    conn.execute("INSERT INTO history (lead_id, timestamp, notiz) VALUES (?, ?, ?)", 
                                 (lead['id'], datetime.now().strftime("%d.%m.%Y %H:%M"), neue_notiz))
                conn.commit()
                conn.close()
                st.rerun()
        
        st.subheader("📜 Historie")
        conn = sqlite3.connect(DB_FILE)
        hist = pd.read_sql_query(f"SELECT * FROM history WHERE lead_id={lead['id']} ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(hist, use_container_width=True)
    else:
        st.info("Noch keine Leads. Nutze den Tab 'Suche'.")

with tab2:
    st.write("### Industrie-Solar Suche")
    search_loc = st.text_input("Ort oder PLZ:", "Garbsen")
    radius = st.slider("Radius (Meter):", 1000, 20000, 5000)
    
    if st.button("🔍 Suche starten"):
        lat, lon = get_coords(search_loc)
        if lat and lon:
            with st.spinner("Suche läuft..."):
                query = f"""
                [out:json][timeout:30];
                (
                  nwr["building"="warehouse"](around:{radius},{lat},{lon});
                  nwr["industrial"="logistics"](around:{radius},{lat},{lon});
                  nwr["amenity"="townhall"](around:{radius},{lat},{lon});
                );
                out center;
                """
                try:
                    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=30)
                    if response.status_code == 200:
                        elements = response.json().get('elements', [])
                        conn = sqlite3.connect(DB_FILE)
                        for el in elements:
                            name = el.get('tags', {}).get('name', 'Industrie-Objekt')
                            if name != 'Industrie-Objekt':
                                conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, search_loc))
                        conn.commit()
                        conn.close()
                        st.success("Erfolgreich geladen!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")
        else:
            st.error("Ort nicht gefunden.")
