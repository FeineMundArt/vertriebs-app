import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- DATENBANK-SETUP ---
# Wir speichern die Datei im Hauptverzeichnis für maximale Stabilität
DB_FILE = "solar_leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Haupttabelle
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firmenname TEXT, adresse TEXT, status TEXT DEFAULT 'Offen',
            termin TEXT, notiz TEXT, zuletzt_bearbeitet TEXT
        )
    """)
    # Historie-Tabelle für Telefonnotizen
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

# --- UI & CRM FUNKTIONEN ---
st.set_page_config(page_title="Solar-Industrie CRM", layout="wide")
st.title("☀️ Solar-Industrie CRM")

# Tab-System zur besseren Übersicht
tab1, tab2 = st.tabs(["📋 Lead-Pool & CRM", "🚀 Suche nach neuen Leads"])

with tab1:
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    if not df.empty:
        selected_name = st.selectbox("Firma zur Bearbeitung wählen:", df['firmenname'].tolist())
        lead = df[df['firmenname'] == selected_name].iloc[0]
        
        # Grid-Layout für die CRM-Bearbeitung
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"### 🏢 {lead['firmenname']}")
            st.write(f"📍 **Adresse:** {lead['adresse']}")
            status = st.selectbox("Status:", ["Offen", "Kontakt aufgenommen", "Termin vereinbart", "Kein Interesse"], 
                                 index=["Offen", "Kontakt aufgenommen", "Termin vereinbart", "Kein Interesse"].index(lead['status']))
            termin = st.date_input("Nächster Termin/Wiedervorlage:", value=datetime.today())
        
        with col2:
            neue_notiz = st.text_area("Neues Telefon-Protokoll:")
            if st.button("💾 Änderungen speichern"):
                conn = sqlite3.connect(DB_FILE)
                conn.execute("UPDATE leads SET status=?, termin=?, zuletzt_bearbeitet=? WHERE id=?", 
                             (status, str(termin), datetime.now().strftime("%d.%m.%Y"), lead['id']))
                if neue_notiz:
                    conn.execute("INSERT INTO history (lead_id, timestamp, notiz) VALUES (?, ?, ?)", 
                                 (lead['id'], datetime.now().strftime("%d.%m.%Y %H:%M"), neue_notiz))
                conn.commit()
                conn.close()
                st.success("Daten aktualisiert!")
                st.rerun()

        # Historie-Anzeige
        st.subheader("📜 Gesprächs-Historie")
        conn = sqlite3.connect(DB_FILE)
        hist = pd.read_sql_query(f"SELECT * FROM history WHERE lead_id={lead['id']} ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(hist, use_container_width=True)
    else:
        st.info("Der Pool ist aktuell leer. Nutze den Tab 'Suche' um Kontakte zu laden.")

with tab2:
    st.write("### Industrie-Solar Suche")
    st.write("Suche gezielt nach Logistikzentren, Lagerhallen und öffentlichen Einrichtungen.")
    if st.button("🔍 Suche starten (Industrie-Datenbank)"):
        # Hier werden wir später den Overpass-API-Filter einbauen
        st.warning("Die Suche wird aktuell für die Anbindung an die Industrie-Datenbank konfiguriert.")
