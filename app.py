import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- DATENBANK SETUP ---
DB_FILE = "solar_leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
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

# --- APP LAYOUT ---
st.set_page_config(layout="wide", page_title="EcoLead Manager")
st.title("☀️ EcoLead Manager — Akquise-Dashboard")

# Sidebar
with st.sidebar:
    bearbeiter = st.text_input("Dein Name:", "Elke")

tab1, tab2 = st.tabs(["📊 Pipeline", "📍 Manuelle Akquise-Karte"])

# TAB 1: PIPELINE (Kanban)
with tab1:
    conn = sqlite3.connect(DB_FILE)
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
                    # Status ändern
                    new_status = st.selectbox("Status:", spalten, index=i, key=f"sel_{lead['id']}")
                    if new_status != spalte:
                        if st.button("Speichern", key=f"btn_{lead['id']}"):
                            conn = sqlite3.connect(DB_FILE)
                            conn.execute("UPDATE leads SET status=?, bearbeiter=? WHERE id=?", 
                                         (new_status, bearbeiter, lead['id']))
                            conn.commit()
                            conn.close()
                            st.rerun()

# TAB 2: MANUELLE AKQUISE-KARTE
with tab2:
    col_map, col_input = st.columns([2, 1])
    
    with col_map:
        # Karte mit Satelliten-Ansicht (via Tiles)
        m = folium.Map(location=[51.1657, 10.4515], zoom_start=6, tiles="OpenStreetMap")
        st_folium(m, width=800, height=500)
    
    with col_input:
        st.subheader("Neuen Lead manuell erfassen")
        name = st.text_input("Firmenname:")
        adresse = st.text_area("Standort/Adresse:")
        if st.button("Lead in Pipeline ziehen"):
            if name:
                conn = sqlite3.connect(DB_FILE)
                conn.execute("INSERT INTO leads (firmenname, adresse, bearbeiter) VALUES (?, ?, ?)", 
                             (name, adresse, bearbeiter))
                conn.commit()
                conn.close()
                st.success("Erfolgreich hinzugefügt!")
                st.rerun()
            else:
                st.error("Bitte Firmennamen eingeben.")
