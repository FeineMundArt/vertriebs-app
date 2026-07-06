import streamlit as st
import sqlite3
import requests
from datetime import datetime
import pandas as pd
import os
from config import DB_PATH

# --- ECHTE SUCHE (API-Modul direkt integriert) ---
def search_live_leads(suchbegriff, projekt):
    geo_url = f"https://nominatim.openstreetmap.org/search?q={suchbegriff},+Germany&format=json&limit=1"
    headers = {'User-Agent': 'EcoLeadCRM_Pro_Search/1.0'}
    try:
        geo_res = requests.get(geo_url, headers=headers, timeout=10).json()
        if not geo_res: return 0
        lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
        
        # Tags für die Suche je nach Projekt
        tag = '["industrial"="logistics"]' if "Solar" in projekt else '["craft"="metal_construction"]'
        osm_query = f'nwr{tag}(around:20000,{lat},{lon});'
        
        resp = requests.get("https://overpass-api.de/api/interpreter", params={'data': f"[out:json];({osm_query});out tags center;"}, timeout=45)
        elements = resp.json().get('elements', [])
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        count = 0
        heute = datetime.now().strftime("%d.%m.%Y")
        for el in elements:
            tags = el.get('tags', {})
            name = tags.get('name')
            if name:
                try:
                    cursor.execute("INSERT INTO leads (projekt, firmenname, adresse, eingetragen_am) VALUES (?, ?, ?, ?)", 
                                   (projekt, name, "Gefunden via OSM", heute))
                    count += 1
                except: continue
        conn.commit(); conn.close()
        return count
    except: return 0

# --- AUTOMATISCHE POOL-LOGIK ---
def ensure_lead_supply(projekt, suchbegriff):
    conn = sqlite3.connect(DB_PATH)
    offen = pd.read_sql_query("SELECT COUNT(*) FROM leads WHERE projekt=? AND status='Offen (Unbearbeitet)'", conn, params=(projekt,)).iloc[0,0]
    conn.close()
    if offen < 30:
        with st.spinner("Pool wird mit frischen Leads aufgefüllt..."):
            added = search_live_leads(suchbegriff, projekt)
            if added > 0: st.rerun()

# --- DESIGN & UI ---
st.set_page_config(page_title="Vertriebs-Zentrale", layout="wide")
st.markdown("<h1 style='color: #4caf50;'>🌱 Vertriebs-Zentrale</h1>", unsafe_allow_html=True)

with st.sidebar:
    aktueller_nutzer = st.selectbox("Wer arbeitet?", ["Patrick", "Elke", "Admin"])
    projekt = st.selectbox("Projekt:", ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"])
    suchbegriff = st.text_input("Region (Such-Start):", "Garbsen")

if suchbegriff:
    ensure_lead_supply(projekt, suchbegriff)

# --- CRM BEARBEITUNG ---
conn = sqlite3.connect(DB_PATH)
df_leads = pd.read_sql_query("SELECT * FROM leads WHERE projekt = ?", conn, params=(projekt,))
conn.close()

if not df_leads.empty:
    df_offen = df_leads[df_leads['status'] == 'Offen (Unbearbeitet)']
    if not df_offen.empty:
        firmen_liste = df_offen['firmenname'].tolist()
        wahl_firma = st.selectbox("Aktueller Lead:", firmen_liste)
        lead_row = df_offen[df_offen['firmenname'] == wahl_firma].iloc[0]
        
        st.write(f"### {lead_row['firmenname']}")
        st.write(f"📍 Adresse: {lead_row['adresse']} | 📞 Telefon: {lead_row['telefon']}")
        
        status = st.selectbox("Status:", ["In Bearbeitung", "Termin vereinbart", "Kein Interesse"])
        notiz = st.text_area("Telefon-Notiz:")
        
        if st.button("💾 Speichern"):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE leads SET status=?, bearbeiter=? WHERE id=?", (status, aktueller_nutzer, int(lead_row['id'])))
            if notiz:
                cursor.execute("INSERT INTO history (lead_id, timestamp, bearbeiter, notiz) VALUES (?, ?, ?, ?)", 
                               (int(lead_row['id']), datetime.now().strftime("%d.%m.%Y %H:%M"), aktueller_nutzer, notiz))
            conn.commit(); conn.close()
            st.success("Gespeichert!")
            st.rerun()
    else:
        st.info("Pool ist leer. Suche läuft...")
else:
    st.info("Bitte Projekt wählen und Such-Region eingeben.")
