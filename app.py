import streamlit as st
import subprocess
import os
import sqlite3
from datetime import datetime, date
import pandas as pd

from config import DB_PATH
from modules.lead_search import search_live_leads
from modules.lead_pool import generate_mock_leads

# --- AUTOMATISCHE DATENBANK-INITIALISIERUNG ---
if not os.path.exists(DB_PATH):
    try:
        subprocess.run(["python", "database/init_db.py"], check=True)
    except Exception as e:
        st.error(f"Datenbankfehler beim Start: {e}")

# --- MODERNES DESIGN SETUP ---
st.set_page_config(
    page_title="FeineMundArt / Eco Lead Manager Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Global CSS für das dunkle Umwelt-Design
st.markdown("""
    <style>
    .stApp { background-color: #0d1611; color: #e0e6e3; }
    section[data-testid="stSidebar"] { background-color: #14221a !important; border-right: 2px solid #233d2e; }
    .dashboard-card { background-color: #182a20; border: 1px solid #2a4737; padding: 20px; border-radius: 12px; text-align: center; }
    .lead-card { background-color: #182a20; border: 1px solid #2a4737; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .lead-header { color: #4caf50; font-size: 22px; font-weight: bold; margin-bottom: 5px; }
    .lead-sub { color: #8bc34a; font-size: 14px; margin-bottom: 10px; }
    .badge-solar { background-color: #2e7d32; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-3nine { background-color: #0277bd; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #4caf50;'>🌱 EcoLead Manager — Cockpit</h1>", unsafe_allow_html=True)

# --- SEITENLEISTE (Nutzer & Suche) ---
with st.sidebar:
    st.markdown("<h3 style='color: #4caf50;'>👤 Aktiver Nutzer</h3>", unsafe_allow_html=True)
    aktueller_nutzer = st.selectbox("Wer arbeitet gerade?", ["Patrick", "Elke", "Admin"])
    
    st.write("---")
    st.markdown("<h3 style='color: #4caf50;'>🔍 Regionale Suche</h3>", unsafe_allow_html=True)
    
    # Projekt-Auswahl
    projekt = st.selectbox(
        "Wähle das Projekt:",
        ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"]
    )
    
    suchbegriff = st.text_input("Ort oder PLZ:", placeholder="z.B. Garbsen")
    radius = st.slider("Such-Radius (km)", 5, 50, 20)
    
    search_btn = st.button("🚀 ALLE Live-Leads laden", use_container_width=True)
    
    st.write("---")
    st.write("💡 *Server-Sicherheitsnetz*")
    demo_btn = st.button("🎲 30 Sofort-Leads würfeln", use_container_width=True)

# --- STATISTIKEN AUS DER DATENBANK HOLEN ---
def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Offen (Unbearbeitet)' AND projekt = ?", (projekt,))
        offen = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'In Bearbeitung' AND projekt = ?", (projekt,))
        bereit = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Termin vereinbart' AND projekt = ?", (projekt,))
        termine = cursor.fetchone()[0]
        conn.close()
        return offen, bereit, termine
    except Exception:
        return 0, 0, 0

offen, bereit, termine = get_stats()

# Anzeige der KPI-Karten für das gewählte Projekt
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"<div class='dashboard-card'><h3 style='color:#4caf50;'>📥 Freie Leads</h3><h2>{offen}</h2><p style='color:#a1b5ab;'>Verfügbar im Pool</p></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='dashboard-card'><h3 style='color:#0277bd;'>🔄 In Bearbeitung</h3><h2>{bereit}</h2><p style='color:#a1b5ab;'>Aktuell reserviert</p></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='dashboard-card'><h3 style='color:#ffb300;'>📅 Termine</h3><h2>{termine}</h2><p style='color:#a1b5ab;'>Erfolge für {projekt.split()[0]}</p></div>", unsafe_allow_html=True)

# --- LOGIK FÜR DIE KNÖPFE ---
if search_btn and suchbegriff:
    with st.spinner("Durchsuche Industrie-Datenbanken..."):
        ergebnis = search_live_leads(suchbegriff, radius, projekt)
        if isinstance(ergebnis, int):
            st.success(f"🎉 {ergebnis} echte Live-Potenziale erfolgreich in die Datenbank geladen!")
            st.rerun()
        else:
            st.error(ergebnis)

if demo_btn and suchbegriff:
    ergebnis = generate_mock_leads(suchbegriff, projekt)
    st.success(f"🎲 {ergebnis} exakt gefilterte Test-Leads für {projekt.split()[0]} eingespielt!")
    st.rerun()

# --- DATEN-ANSICHT & CRM-BEARBEITUNG ---
st.write("---")
st.subheader("📋 Lead-Pool & CRM-Zentrale")

# Live-Daten für dieses Projekt laden
def load_project_leads():
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM leads WHERE projekt = ?", conn, params=(projekt,))
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

df_leads = load_project_leads()

if not df_leads.empty:
    status_filter = st.radio(
        "Listen-Ansicht filtern:", 
        ["📥 Freie Leads", "🔄 In Bearbeitung", "📅 Termine & Wiedervorlagen", "Alle"],
        horizontal=True
    )
    
    # Filterung anwenden
    if status_filter == "📥 Freie Leads":
        df_filtered = df_leads[df_leads['status'] == 'Offen (Unbearbeitet)']
    elif status_filter == "🔄 In Bearbeitung":
        df_filtered = df_leads[df_leads['status'] == 'In Bearbeitung']
    elif status_filter == "📅 Termine & Wiedervorlagen":
        df_filtered = df_leads[df_leads['status'].isin(['In Bearbeitung', 'Termin vereinbart']) & (df_leads['wiedervorlage'] != 'Keine')]
    else:
        df_filtered = df_leads

    if df_filtered.empty:
        st.info("In dieser Kategorie liegen aktuell keine Adressen vor.")
    else:
        # Dropdown für die Firmenauswahl
        firmen_liste = df_filtered['firmenname'].tolist()
        wahl_firma = st.selectbox(f"Wähle eine Firma aus ({len(firmen_liste)} Treffer):", firmen_liste)
        
        # Details der gewählten Firma holen
        lead_row = df_filtered[df_filtered['firmenname'] == wahl_firma].iloc[0]
        lead_id = int(lead_row['id'])
        
        badge_style = "badge-solar" if "Solar" in projekt else "badge-3nine"
        proj_label = "☀️ SOLAR" if "Solar" in projekt else "🌀 3NINE"
        
        st.markdown(f"""
            <div class="lead-card">
                <span class="{badge_style}">{proj_label}</span>
                <div class="lead-header">{lead_row['firmenname']}</div>
                <div class="lead-sub">📍 {lead_row['adresse']} &nbsp;|&nbsp; 📞 Telefon: {lead_row['telefon']}</div>
                <div class="lead-meta" style="color: #a1b5ab;">👤 <b>Bearbeiter:</b> {lead_row['bearbeiter']} &nbsp;|&nbsp; ⏳ <b>WV am:</b> {
