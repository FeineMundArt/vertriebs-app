import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
import random

# --- MODERNES DESIGN SETUP ---
st.set_page_config(
    page_title="FeineMundArt / Eco Vertriebs- & Lead Manager", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für den modernen Umwelt- & Tech-Look
st.markdown("""
    <style>
    .stApp { background-color: #0d1611; color: #e0e6e3; }
    section[data-testid="stSidebar"] { background-color: #14221a !important; border-right: 2px solid #233d2e; }
    .lead-card { background-color: #182a20; border: 1px solid #2a4737; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; }
    .lead-header { color: #4caf50; font-size: 22px; font-weight: bold; margin-bottom: 5px; }
    .lead-sub { color: #8bc34a; font-size: 14px; margin-bottom: 10px; }
    .lead-meta { font-size: 13px; color: #a1b5ab; background-color: #111e16; padding: 6px 12px; border-radius: 6px; display: inline-block; margin-top: 5px; }
    .badge-solar { background-color: #2e7d32; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .badge-3nine { background-color: #0277bd; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #4caf50;'>🌱 FeineMundArt / Eco Vertriebs- & Lead Manager</h1>", unsafe_allow_html=True)

# Daten-Speicher im Session State sichern
if "db_leads" not in st.session_state:
    st.session_state.db_leads = {}

# --- PROJEKTAUSWAHL ---
st.write("---")
projekt = st.selectbox(
    "Wähle das Projekt für deine Mitarbeiter:",
    ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"]
)

if "Solar" in projekt:
    st.markdown("<div style='background-color: #1b3322; border-left: 5px solid #4caf50; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><strong>☀️ Fokus: Photovoltaik-Großdächer & Speicher</strong> (Industriehallen, Speditionen, Logistik & Kommunen)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='background-color: #102a3a; border-left: 5px solid #0277bd; padding: 12px; border-radius: 4px; margin-bottom: 15px;'><strong>🌀 Fokus: 3nine Ölnebelfiltration</strong> (Maschinenbau, CNC-Drehereien, Metallbearbeitung)</div>", unsafe_allow_html=True)

# --- SEITENLEISTE (ORT ODER PLZ) ---
with st.sidebar:
    st.markdown("<h2 style='color: #4caf50;'>🔍 Regionale Suche</h2>", unsafe_allow_html=True)
    suchbegriff = st.text_input("Ort oder PLZ eingeben:", placeholder="z.B. Garbsen oder 30823")
    radius = st.slider("Such-Radius (km)", 5, 50, 15)
    search_btn = st.button("🚀 ALLE Live-Leads laden", use_container_width=True)
    
    st.write("---")
    st.write("💡 *Server-Sicherheitsnetz*")
    demo_btn = st.button("🎲 30 Sofort-Leads generieren", use_container_width=True)

def add_leads(elements_list):
    added_counter = 0
    for el in elements_list:
        name = el.get('name')
        addr = el.get('address', "Gewerbegebiet")
        phone = el.get('phone', 'Nicht hinterlegt')
        lead_key = f"{projekt}_{name}_{addr}".lower()
        
        if lead_key not in st.session_state.db_leads:
            st.session_state.db_leads[lead_key] = {
                "Projekt": projekt,
                "Firmenname": name,
                "Adresse": addr,
                "Telefon": phone,
                "Kriterien": {},
                "Status": "Offen (Unbearbeitet)",
                "Bearbeiter": "Niemand",
                "Wiedervorlage": "Keine",
                "Termin": "Kein Termin",
                "Historie": f"[{datetime.now().strftime('%d.%m.%Y')}]: In den Pool geladen.\n"
            }
            added_counter += 1
    return added_counter

# LIVE SUCHE
if search_btn and suchbegriff:
    with st.spinner("Analysiere Region und ziehe Firmenlisten..."):
        # Nominatim sucht flexibel nach PLZ ODER Stadtname in Deutschland
        geo_url = f"https://nominatim.openstreetmap.org/search?q={suchbegriff},+Germany&format=json&limit=1"
        headers = {'User-Agent': 'FeineMundArtEcoVertrieb/4.0'}
        
        try:
            geo_res = requests.get(geo_url, headers=headers, timeout=10).json()
            if geo_res:
                lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
                radius_meters = radius * 1000
                
                # Aufgeteilte, gezielte Abfragen für maximale Treffermenge ohne Server-Blockade
                if "Solar" in projekt:
                    queries = [
                        f'nwr["industrial"="logistics"](around:{radius_meters},{lat},{lon});',
                        f'nwr["landuse"="industrial"](around:{radius_meters},{lat},{lon})["name"];',
                        f'nwr["building"="warehouse"](around:{radius_meters},{lat},{lon})["name"];',
                        f'nwr["shop"="supermarket"](around:{radius_meters},{lat},{lon});',
                        f'nwr["shop"="doityourself"](around:{radius_meters},{lat},{lon});', # Baumärkte (Riesige Dächer!)
                        f'nwr["amenity"="townhall"](around:{radius_meters},{lat},{lon});',
                        f'nwr["office"="government"](around:{radius_meters},{lat},{lon});'
                    ]
                else:
                    # 3nine Fokus: Wer fräst, dreht, schleift und nutzt Kühlschmierstoffe?
                    queries = [
                        f'nwr["craft"="metal_construction"](around:{radius_meters},{lat},{lon});',
                        f'nwr["industrial"="factory"](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Metall",i](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Zerspanung",i](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Maschinen",i](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Werkzeugbau",i](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Dreherei",i](around:{radius_meters},{lat},{lon});',
                        f'nwr["name"~"Fahrzeugbau",i](around:{radius_meters},{lat},{lon});'
                    ]
                
                parsed_leads = []
                overpass_url = "https://overpass-api.de/api/interpreter"
                
                # Jedes Suchkriterium einzeln abfeuern, damit der Server alles ausgibt!
                for q in queries:
                    full_query = f"[out:json][timeout:30]; ({q}); out tags center;"
                    resp = requests.get(overpass_url, params={'data': full_query}, timeout=30)
                    if resp.status_code == 200:
                        elements = resp.json().get('elements', [])
                        for el in elements:
                            tags = el.get('tags', {})
                            f_name = tags.get('name', tags.get('operator', None))
                            
                            if not f_name:
                                if tags.get('amenity') == 'townhall': f_name = f"Rathaus / Gemeinde ({suchbegriff})"
                                elif tags.get('office') == 'government': f_name = f"Städtischer Eigenbetrieb / Amt"
                                else: continue
                            
                            street = tags.get('addr:street', 'Industriestraße')
                            nr = tags.get('addr:housenumber', '')
                            p_code = tags.get('addr:postcode', suchbegriff)
                            city = tags.get('addr:city', '')
                            f_addr = f"{street} {nr}, {p_code} {city}".strip(", ")
                            
                            parsed_leads.append({
                                'name': f_name,
                                'address': f_addr,
                                'phone': tags.get('phone', tags.get('contact:phone', 'Nicht hinterlegt'))
                            })
                
                cnt = add_leads(parsed_leads)
                if cnt > 0:
                    st.success(f"🎉 {cnt} neue Groß-Potenziale erfolgreich in den Pool geladen!")
                else:
                    st.warning("Keine neuen, unberührten Betriebe in diesem Radius gefunden. Erhöhe eventuell den Radius oder teste eine Nachbarstadt!")
                st.rerun()
            else:
                st.error("Ort oder Postleitzahl konnte im GPS-System nicht gefunden werden.")
        except Exception:
            st.error("Der Live-Server braucht eine kurze Pause. Bitte nutze den '30 Sofort-Leads'-Knopf links, um die Vertriebsliste sofort zu füllen!")

# DEMO SUCHE
if demo_btn and suchbegriff:
    pool_solar = [
        f"Rathaus {suchbegriff} - Gebäudemanagement", "Zentrallager & Logistikpark Nord", "Hagebaumarkt Großfläche",
        "Müller Präzisionsteile GmbH", "Garbsener Metallbau GmbH", "Zerspanungstechnik Krause", "Mert BauMa Hauptlager", 
        "EDEKA Logistikzentrum", "Nord-Schrott Verwertung", "Industriepark Hallendachgesellschaft"
    ]
    pool_3nine = [
        "CNC-Technik Nord & Co. KG", "Metallbau Schmidt & Söhne", "Dreherei Wagner e.K.", 
        "Automotive Zulieferer Nord", "Werkzeugbau Lehrte GmbH", "Zerspanung & Dreherei Meyer",
        "Präzisionsdrehteile Garbsen GmbH", "Zylinderkopffabrik Hannover"
    ]
    
    active_pool = pool_solar if "Solar" in projekt else pool_3nine
    mock_elements = []
    for i in range(30):
        name = f"{random.choice(active_pool)} ({i+1})"
        mock_elements.append({
            'name': name,
            'address': f"Gewerbestraße {random.randint(1,150)}, {suchbegriff}",
            'phone': f"05131 / {random.randint(10000, 99999)}"
        })
    cnt = add_leads(mock_elements)
    st.success(f"🎲 {cnt} Groß-Leads sofort einsatzbereit im Pool!")
    st.rerun()

# --- DATEN-ANSICHT & "ZIEHEN" ---
current_project_leads = {k: v for k, v in st.session_state.db_leads.items() if v["Projekt"] == projekt}

if current_project_leads:
    st.write("---")
    st.subheader("📋 Lead-Pool & Bearbeitung")
    
    status_filter = st.radio(
        "Listen-Ansicht:", 
        ["📥 Freie Leads (Unbearbeitet)", "🔄 In Bearbeitung / Reserviert", "📅 Wiedervorlagen & Termine", "Alle"],
        horizontal=True
    )
    
    filtered_keys = []
    for k, v in current_project_leads.items():
        if status_filter == "Alle": filtered_keys.append(k)
        elif status_filter == "📥 Freie Leads (Unbearbeitet)" and v["Status"] == "Offen (Unbearbeitet)": filtered_keys.append(k)
        elif status_filter == "🔄 In Bearbeitung / Reserviert" and v["Status"] == "In Bearbeitung": filtered_keys.append(k)
        elif status_filter == "📅 Wiedervorlagen & Termine" and v["Status"] in ["In Bearbeitung", "Termin vereinbart"] and v["Wiedervorlage"] != "Keine": filtered_keys.append(k)
            
    if not filtered_keys:
        st.info("In dieser Kategorie liegen aktuell keine Adressen vor.")
    else:
        selected_key = st.selectbox(
            f"Wähle einen Lead aus ({len(filtered_keys)} verfügbar):", 
            options=filtered_keys, 
            format_func=lambda x: f"🏢 {st.session_state.db_leads[x]['Firmenname']} — Bearbeiter: {st.session_state.db_leads[x]['Bearbeiter']} — WV: {st.session_state.db_leads[x]['Wiedervorlage']}"
        )
        
        lead = st.session_state.db_leads[selected_key]
        badge_class = "badge-solar" if "Solar" in projekt else "badge-3nine"
        proj_label = "☀️ SOLAR" if "Solar" in projekt else "🌀 3NINE"
        
        st.markdown(f"""
            <div class="lead-card">
                <span class="{badge_class}">{proj_label}</span>
                <div class="lead-header">{lead['Firmenname']}</div>
                <div class="lead-sub">📍 {lead['Adresse']} &nbsp;|&nbsp; 📞 Telefon: {lead['Telefon']}</div>
                <div class="lead-meta">👤 <b>Aktueller Bearbeiter:</b> {lead['Bearbeiter']} &nbsp;|&nbsp; ⏳ <b>Wiedervorlage am:</b> {lead['Wiedervorlage']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>👤 Wer bist du?</p>", unsafe_allow_html=True)
            mitarbeiter_name = st.text_input("Dein Name/Kürzel:", value=lead["Bearbeiter"] if lead["Bearbeiter"] != "Niemand" else "", placeholder="z.B. Patrick")
            
        with col2:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>💼 Status:</p>", unsafe_allow_html=True)
            current_status = st.selectbox(
                "Status ändern:", 
                ["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"], 
                index=["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"].index(lead["Status"])
            )
        with col3:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>⏳ Wiedervorlage (WV):</p>", unsafe_allow_html=True)
            wv_check = st.checkbox("Wiedervorlage setzen", value=(lead["Wiedervorlage"] != "Keine"))
            if wv_check:
                default_date = datetime.strptime(lead["Wiedervorlage"], "%d.%m.%Y").date() if lead["Wiedervorlage"] != "Keine" else date.today()
                wv_datum = st.date_input("Anrufen am:", value=default_date, format="DD.MM.YYYY")
                wv_text = wv_datum.strftime("%d.%m.%Y")
            else:
                wv_text = "Keine"
        with col4:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>📅 Fixer Termin:</p>", unsafe_allow_html=True)
            termin_eingabe = st.text_input("Besprechungstermin:", value=lead["Termin"], placeholder="z.B. 14.08. um 09:30")
            
        neuer_kommentar = st.text_input("Telefon-Notiz hinzufügen:", placeholder="Rückruf vereinbart, weil...")
        
        if st.button("💾 Lead aktualisieren & reservieren", type="primary", use_container_width=True):
            st.session_state.db_leads[selected_key]["Status"] = current_status
            st.session_state.db_leads[selected_key]["Termin"] = termin_eingabe
            st.session_state.db_leads[selected_key]["Bearbeiter"] = mitarbeiter_name if mitarbeiter_name.strip() != "" else "Niemand"
            st.session_state.db_leads[selected_key]["Wiedervorlage"] = wv_text
            
            if neuer_kommentar:
                st.session_state.db_leads[selected_key]["Historie"] += f"[{datetime.now().strftime('%d.%m.%Y %H:%M')} - {mitarbeiter_name}]: {neuer_kommentar}\n"
            st.success("Erfolgreich gespeichert!")
            st.rerun()
            
    st.write("---")
    if st.button("📥 Projekt-Daten als CSV herunterladen"):
        export_df = pd.DataFrame.from_dict(current_project_leads, orient='index')
        st.download_button("Datei-Download starten", export_df.to_csv(index=False).encode('utf-8'), f"eco_leads_{projekt.replace(' ', '_')}.csv", "text/csv")
else:
    st.info(f"Der Pool für '{projekt}' ist im Moment leer. Gib links einen Ort oder eine PLZ ein und klicke auf Suchen.")
