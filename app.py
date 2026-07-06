import streamlit as st
import subprocess
import os
import sqlite3
import requests
import random
from datetime import datetime, date
import pandas as pd

from config import DB_PATH

# --- AUTOMATISCHE DATENBANK-INITIALISIERUNG ---
if not os.path.exists(DB_PATH):
    try:
        subprocess.run(["python", "database/init_db.py"], check=True)
    except Exception as e:
        st.error(f"Datenbankfehler beim Start: {e}")

# --- INTEGRATION: LIVE-SUCH-MODUL ---
def search_live_leads(suchbegriff, radius_km, projekt):
    geo_url = f"https://nominatim.openstreetmap.org/search?q={suchbegriff},+Germany&format=json&limit=1"
    headers = {'User-Agent': 'EcoLeadCRM_SearchSystem/1.0'}
    try:
        geo_res = requests.get(geo_url, headers=headers, timeout=10).json()
        if not geo_res:
            return "Ort oder PLZ konnte nicht gefunden werden."
        
        lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
        radius_meters = radius_km * 1000
        
        if "Solar" in projekt:
            osm_query = f"""
            nwr["industrial"="logistics"](around:{radius_meters},{lat},{lon});
            nwr["building"="warehouse"](around:{radius_meters},{lat},{lon})["name"];
            nwr["shop"="supermarket"](around:{radius_meters},{lat},{lon})["name"];
            nwr["shop"="doityourself"](around:{radius_meters},{lat},{lon})["name"];
            nwr["amenity"="townhall"](around:{radius_meters},{lat},{lon});
            nwr["landuse"="industrial"](around:{radius_meters},{lat},{lon})["name"];
            """
        else:
            osm_query = f"""
            nwr["craft"="metal_construction"](around:{radius_meters},{lat},{lon})["name"];
            nwr["industrial"="factory"](around:{radius_meters},{lat},{lon})["name"];
            nwr["name"~"Zerspanung",i](around:{radius_meters},{lat},{lon});
            nwr["name"~"Dreherei",i](around:{radius_meters},{lat},{lon});
            nwr["name"~"Werkzeugbau",i](around:{radius_meters},{lat},{lon});
            nwr["name"~"Maschinen",i](around:{radius_meters},{lat},{lon});
            """
        
        overpass_url = "https://overpass-api.de/api/interpreter"
        full_query = f"[out:json][timeout:60]; ({osm_query}); out tags center;"
        
        resp = requests.get(overpass_url, params={'data': full_query}, timeout=45)
        if resp.status_code != 200:
            return "Der Live-Server ist gerade überlastet. Bitte versuche es gleich noch einmal."
            
        elements = resp.json().get('elements', [])
        added_counter = 0
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        heute = datetime.now().strftime("%d.%m.%Y")
        
        for el in elements:
            tags = el.get('tags', {})
            f_name = tags.get('name', tags.get('operator', None))
            if not f_name:
                if tags.get('amenity') == 'townhall': f_name = f"Rathaus / Gemeinde ({suchbegriff})"
                else: continue
            
            street = tags.get('addr:street', 'Gewerbegebiet')
            nr = tags.get('addr:housenumber', '')
            p_code = tags.get('addr:postcode', suchbegriff)
            city = tags.get('addr:city', '')
            f_addr = f"{street} {nr}, {p_code} {city}".strip(", ")
            phone = tags.get('phone', tags.get('contact:phone', 'Nicht hinterlegt'))
            
            try:
                cursor.execute("""
                    INSERT INTO leads (projekt, firmenname, adresse, telefon, suchort, eingetragen_am)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (projekt, f_name, f_addr, phone, suchbegriff, heute))
                
                lead_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO history (lead_id, timestamp, bearbeiter, notiz)
                    VALUES (?, ?, ?, ?)
                """, (lead_id, heute, 'System', 'In den CRM-Pool geladen.'))
                added_counter += 1
            except sqlite3.IntegrityError:
                continue
                
        conn.commit()
        conn.close()
        return added_counter
    except Exception as e:
        return f"Fehler bei der Suche: {str(e)}"

# --- INTEGRATION: LEAD-POOL-SIMULATOR ---
def generate_mock_leads(suchbegriff, projekt):
    if "Solar" in projekt:
        pool = [
            "Zentrallager Logistikpark Nord", "Hagebaumarkt Großfläche", "EDEKA Logistikzentrum",
            "Amazon Verteilzentrum", "Gewerbepark Hallendachgesellschaft", "Spedition & Transport Garbsen GmbH",
            "Rathaus Gebäudemanagement", "Städtischer Bauhof", "Metro Großmarkt Liegenschaft"
        ]
        addr_style = "Industriestraße"
    else:
        pool = [
            "CNC-Technik Nord & Co. KG", "Metallbau Schmidt & Söhne", "Dreherei Wagner e.K.", 
            "Präzisionsdrehteile GmbH", "Zerspanungstechnik Krause", "Werkzeugbau Lehrte GmbH",
            "Zylinderkopffabrik Hannover", "Maschinenbau Meier & Partner", "Formenbau Müller"
        ]
        addr_style = "Werkstraße"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    heute = datetime.now().strftime("%d.%m.%Y")
    added_counter = 0

    for i in range(30):
        name = f"{random.choice(pool)} ({i+1})"
        f_addr = f"{addr_style} {random.randint(1,180)}, {suchbegriff}"
        phone = f"05131 / {random.randint(10000, 99999)}"
        try:
            cursor.execute("""
                INSERT INTO leads (projekt, firmenname, adresse, telefon, suchort, eingetragen_am)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (projekt, name, f_addr, phone, suchbegriff, heute))
            
            lead_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO history (lead_id, timestamp, bearbeiter, notiz)
                VALUES (?, ?, ?, ?)
            """, (lead_id, heute, 'System', 'Test-Lead generiert.'))
            added_counter += 1
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()
    return added_counter


# --- MODERNES DESIGN SETUP ---
st.set_page_config(
    page_title="FeineMundArt / Eco Lead Manager Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        firmen_liste = df_filtered['firmenname'].tolist()
        wahl_firma = st.selectbox(f"Wähle eine Firma aus ({len(firmen_liste)} Treffer):", firmen_liste)
        
        lead_row = df_filtered[df_filtered['firmenname'] == wahl_firma].iloc[0]
        lead_id = int(lead_row['id'])
        
        badge_style = "badge-solar" if "Solar" in projekt else "badge-3nine"
        proj_label = "☀️ SOLAR" if "Solar" in projekt else "🌀 3NINE"
        
        html_card = f"""
            <div class="lead-card">
                <span class="{badge_style}">{proj_label}</span>
                <div class="lead-header">{lead_row['firmenname']}</div>
                <div class="lead-sub">📍 {lead_row['adresse']} &nbsp;|&nbsp; 📞 Telefon: {lead_row['telefon']}</div>
                <div class="lead-meta" style="color: #a1b5ab;">👤 <b>Bearbeiter:</b> {lead_row['bearbeiter']} &nbsp;|&nbsp; ⏳ <b>WV am:</b> {lead_row['wiedervorlage']} &nbsp;|&nbsp; 📅 <b>Termin:</b> {lead_row['termin']}</div>
            </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            neuer_status = st.selectbox(
                "Status ändern:", 
                ["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"],
                index=["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"].index(lead_row['status'])
            )
        with col_s2:
            wv_check = st.checkbox("Wiedervorlage setzen", value=(lead_row['wiedervorlage'] != "Keine"))
            if wv_check:
                try:
                    def_date = datetime.strptime(lead_row['wiedervorlage'], "%d.%m.%Y").date()
                except Exception:
                    def_date = date.today()
                wv_datum = st.date_input("Anrufen am:", value=def_date, format="DD.MM.YYYY")
                wv_text = wv_datum.strftime("%d.%m.%Y")
            else:
                wv_text = "Keine"
        with col_s3:
            termin_text = st.text_input("Fixer Besprechungstermin:", value=lead_row['termin'], placeholder="z.B. 14.08. um 09:30")
            
        notiz_text = st.text_input("Telefon-Notiz hinzufügen:", placeholder="z.B. Rückruf nächste Woche...")
        
        if st.button("💾 Lead-Status & Notiz speichern", type="primary", use_container_width=True):
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE leads 
                SET status = ?, bearbeiter = ?, wiedervorlage = ?, termin = ?
                WHERE id = ?
            """, (neuer_status, aktueller_nutzer, wv_text, termin_text, lead_id))
            
            if notiz_text.strip() != "":
                zeitstempel = datetime.now().strftime("%d.%m.%Y %H:%M")
                cursor.execute("""
                    INSERT INTO history (lead_id, timestamp, bearbeiter, notiz)
                    VALUES (?, ?, ?, ?)
                """, (lead_id, zeitstempel, aktueller_nutzer, notiz_text))
                
            conn.commit()
            conn.close()
            st.success("Änderungen erfolgreich in der Datenbank gespeichert!")
            st.rerun()
            
        try:
            conn = sqlite3.connect(DB_PATH)
            history_df = pd.read_sql_query("SELECT timestamp, bearbeiter, notiz FROM history WHERE lead_id = ? ORDER BY id DESC", conn, params=(lead_id,))
            conn.close()
            if not history_df.empty:
                st.markdown("##### 📜 Telefon-Verlauf für diesen Betrieb:")
                for _, h_row in history_df.iterrows():
                    st.write(f"⏱️ `{h_row['timestamp']}` - **{h_row['bearbeiter']}**: {h_row['notiz']}")
        except Exception:
            pass
else:
    st.info(f"Der Daten-Pool für '{projekt.split()[0]}' ist noch komplett leer. Gib links eine Region ein und klicke auf Suchen oder Würfeln.")
