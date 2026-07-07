import streamlit as st
import sqlite3
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIG & DB ---
DB_FILE = "solar_leads.db"

def get_db_connection():
    # timeout=20 sorgt dafür, dass SQLite wartet, wenn jemand anderes schreibt
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen', 
            termin TEXT, notiz TEXT, bearbeiter TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER, timestamp TEXT, notiz TEXT, bearbeiter TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- APP UI ---
st.set_page_config(page_title="Solar-Industrie CRM", layout="wide")
st.title("☀️ Solar-Industrie CRM")

# Globales Feld für den Mitarbeiter (in der Sidebar)
with st.sidebar:
    st.header("Einstellungen")
    bearbeiter_name = st.text_input("Dein Name (für Protokolle):", "Unbekannt")

tab1, tab2 = st.tabs(["📋 Lead-Pool & CRM", "🚀 Suche starten"])

with tab1:
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    if not df.empty:
        col_left, col_right = st.columns([1, 2])
        with col_left:
            selected_name = st.selectbox("Firma wählen:", df['firmenname'].unique().tolist())
            lead = df[df['firmenname'] == selected_name].iloc[0]
            st.write(f"**Aktueller Bearbeiter:** {lead['bearbeiter']}")
        
        with col_right:
            st.subheader(f"Bearbeitung: {selected_name}")
            new_status = st.selectbox("Status:", ["Offen", "Kontakt", "Termin", "Kein Interesse"], 
                                     index=["Offen", "Kontakt", "Termin", "Kein Interesse"].index(lead['status']))
            new_note = st.text_area("Neue Notiz:")
            if st.button("💾 Speichern"):
                conn = get_db_connection()
                conn.execute("UPDATE leads SET status=?, notiz=?, bearbeiter=? WHERE id=?", 
                             (new_status, new_note, bearbeiter_name, lead['id']))
                conn.execute("INSERT INTO history (lead_id, timestamp, notiz, bearbeiter) VALUES (?, ?, ?, ?)", 
                             (lead['id'], datetime.now().strftime("%d.%m.%Y %H:%M"), new_note, bearbeiter_name))
                conn.commit()
                conn.close()
                st.success("Gespeichert!")
                st.rerun()

        st.subheader("📜 Historie")
        conn = get_db_connection()
        hist = pd.read_sql_query(f"SELECT * FROM history WHERE lead_id={lead['id']} ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(hist, use_container_width=True)
    else:
        st.info("Datenbank ist leer. Nutze 'Suche starten'.")

with tab2:
    st.write("### Industrie-Solar Suche")
    loc = st.text_input("Ort oder PLZ:", "Garbsen")
    
    if st.button("🔍 Suche starten"):
        with st.spinner("Scanne Industrie-Datenbank..."):
            try:
                geo_res = requests.get(f"https://nominatim.openstreetmap.org/search?q={loc},+Germany&format=json&limit=1", headers={'User-Agent': 'SolarCRM'}).json()
                if geo_res:
                    lat, lon = geo_res[0]['lat'], geo_res[0]['lon']
                    time.sleep(1)
                    query = f'[out:json];(nwr["building"="warehouse"](around:5000,{lat},{lon}););out center;'
                    data = requests.get("https://overpass-api.de/api/interpreter", params={'data': query}, timeout=30).json()
                    
                    conn = get_db_connection()
                    count = 0
                    for el in data.get('elements', []):
                        name = el.get('tags', {}).get('name')
                        if name:
                            conn.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", (name, loc))
                            count += 1
                    conn.commit()
                    conn.close()
                    st.success(f"Erfolg: {count} neue Firmen geladen!")
                    st.rerun()
                else:
                    st.error("Ort nicht gefunden.")
            except Exception as e:
                st.error(f"API Fehler: {e}")
