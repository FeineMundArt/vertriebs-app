import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- MODERNES DESIGN SETUP ---
st.set_page_config(
    page_title="Eco-Tech Vertriebs-Manager", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS für den modernen Umwelt- & Tech-Look (Dunkelgrün, Clean-Tech)
st.markdown("""
    <style>
    /* Hintergrund und Hauptfarben */
    .stApp {
        background-color: #0d1611;
        color: #e0e6e3;
    }
    /* Seitenleiste Styling */
    section[data-testid="stSidebar"] {
        background-color: #14221a !important;
        border-right: 2px solid #233d2e;
    }
    /* Kacheln für Leads */
    .lead-card {
        background-color: #182a20;
        border: 1px solid #2a4737;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .lead-header {
        color: #4caf50;
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .lead-sub {
        color: #8bc34a;
        font-size: 14px;
        margin-bottom: 15px;
    }
    /* Projekt-Indikatoren */
    .badge-solar {
        background-color: #2e7d32;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-3nine {
        background-color: #0277bd;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP START ---
st.markdown("<h1 style='text-align: center; color: #4caf50;'>🌱 Eco-Tech Vertriebs- & Lead-Manager</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #a1b5ab; font-size: 16px;'>Gemeinsam für saubere Energie und reine Luft. Effizientes Lead-Management für dein Team.</p>", unsafe_allow_html=True)

# Datenbank-Initialisierung
if "db_leads" not in st.session_state:
    st.session_state.db_leads = {}

# --- PROJEKTAUSWAHL ---
st.write("---")
col_proj_left, col_proj_right = st.columns([1, 3])
with col_proj_left:
    st.markdown("<p style='margin-top: 10px; font-weight: bold; color: #8bc34a;'>Aktiviertes Umwelt-Projekt:</p>", unsafe_allow_html=True)
with col_proj_right:
    projekt = st.selectbox(
        "Wähle das Projekt für deine Mitarbeiter:",
        ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"],
        label_visibility="collapsed"
    )

# Visualisierung des aktuellen Projekts als schicke Info-Box
if "Solar" in projekt:
    st.markdown("""
        <div style='background-color: #1b3322; border-left: 5px solid #4caf50; padding: 12px; border-radius: 4px; margin-bottom: 15px;'>
            <strong>☀️ Fokus: Photovoltaik & Speicher</strong> – Wir helfen Industrie-Betrieben, ihren eigenen grünen Strom zu erzeugen und CO₂ einzusparen.
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div style='background-color: #102a3a; border-left: 5px solid #0277bd; padding: 12px; border-radius: 4px; margin-bottom: 15px;'>
            <strong>🌀 Fokus: 3nine Filtration</strong> – Saubere Luft in der Metallverarbeitung. Schutz der Mitarbeiter und Rückgewinnung von wertvollen Kühlschmierstoffen.
        </div>
    """, unsafe_allow_html=True)

# --- SEITENLEISTE: LEADS LADEN ---
with st.sidebar:
    st.markdown("<h2 style='color: #4caf50;'>🔍 Regionale Umkreissuche</h2>", unsafe_allow_html=True)
    plz = st.text_input("Postleitzahl (PLZ)", placeholder="z.B. 30823")
    radius = st.slider("Such-Radius (km)", 5, 100, 25)
    
    if "Solar" in projekt:
        default_kw = "Gewerbe, Industrie, Logistik"
        help_text = "Sucht nach großen Produktionshallen und Dächern."
    else:
        default_kw = "Metallbau, Zerspanung, Maschinenbau"
        help_text = "Sucht nach Fertigungsbetrieben mit CNC-Maschinen."
        
    keyword = st.text_input("Fokus-Branche", value=default_kw, help=help_text)
    
    st.write("")
    search_btn = st.button("🚀 Grüne Potenziale laden", use_container_width=True)

if search_btn and plz:
    with st.spinner("Analysiere Betriebe in der Region..."):
        geo_url = f"https://nominatim.openstreetmap.org/search?postalcode={plz}&country=Germany&format=json"
        headers = {'User-Agent': 'Eco_Lead_App_Bot_2.0'}
        
        try:
            geo_res = requests.get(geo_url, headers=headers).json()
        except Exception:
            geo_res = None
        
        if geo_res:
            lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
            radius_meters = radius * 1000
            
            if "Solar" in projekt:
                osm_query = f"""
                ( nwr["industrial"](around:{radius_meters},{lat},{lon});
                  nwr["building"="industrial"](around:{radius_meters},{lat},{lon}); )
                """
            else:
                osm_query = f"""
                ( nwr["industrial"="metal_construction"](around:{radius_meters},{lat},{lon});
                  nwr["industrial"="factory"](around:{radius_meters},{lat},{lon});
                  nwr["craft"="metal_construction"](around:{radius_meters},{lat},{lon});
                  nwr["name"~"Metall",i](around:{radius_meters},{lat},{lon});
                  nwr["name"~"Zerspanung",i](around:{radius_meters},{lat},{lon}); )
                """
                
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f"[out:json][timeout:90]; {osm_query}; out tags center;"
            
            try:
                response = requests.get(overpass_url, params={'data': query})
                if response.status_code == 200:
                    elements = response.json().get('elements', [])
                    added_counter = 0
                    for el in elements:
                        tags = el.get('tags', {})
                        name = tags.get('name', tags.get('operator', f"Gewerbebetrieb ({keyword})"))
                        addr = f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}, {tags.get('addr:postcode', plz)} {tags.get('addr:city', '')}".strip(", ")
                        
                        lead_key = f"{projekt}_{name}_{tags.get('addr:street', '')}".lower()
                        
                        if lead_key not in st.session_state.db_leads:
                            st.session_state.db_leads[lead_key] = {
                                "Projekt": projekt,
                                "Firmenname": name,
                                "Adresse": addr if len(addr) > 5 else f"Region {plz}",
                                "Telefon": tags.get('phone', tags.get('contact:phone', 'Nicht hinterlegt')),
                                "Kriterien": {},
                                "Status": "Offen (Unbearbeitet)",
                                "Termin": "Kein Termin",
                                "Historie": f"[{datetime.now().strftime('%d.%m.%Y')}]: Betrieb für {projekt} erfasst.\n"
                            }
                            added_counter += 1
                    st.success(f"🎉 {added_counter} neue Öko-Leads erfolgreich geladen!")
                else:
                    st.error("Der Server antwortet gerade nicht. Bitte kurz warten.")
            except Exception:
                st.error("Verbindung zum Daten-Server fehlgeschlagen.")
        else:
            st.error("Diese Postleitzahl wurde nicht gefunden.")

# --- DATEN-ANSICHT & BEARBEITUNG ---
current_project_leads = {k: v for k, v in st.session_state.db_leads.items() if v["Projekt"] == projekt}

if current_project_leads:
    st.subheader("📋 Aktuelle Adressen in der Bearbeitung")
    status_filter = st.selectbox("Filter nach Status:", ["Alle", "Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"])
    
    filtered_keys = []
    for k, v in current_project_leads.items():
        if status_filter == "Alle" or v["Status"] == status_filter:
            filtered_keys.append(k)
            
    if not filtered_keys:
        st.info("Keine Leads mit diesem Status für das aktuelle Projekt vorhanden.")
    else:
        # Schickes Auswahlmenü
        selected_key = st.selectbox(
            "Wähle das Unternehmen für das Telefonat / den Besuch aus:", 
            options=filtered_keys, 
            format_func=lambda x: f"🏢 {st.session_state.db_leads[x]['Firmenname']} — {st.session_state.db_leads[x]['Adresse']}"
        )
        
        lead = st.session_state.db_leads[selected_key]
        badge_class = "badge-solar" if "Solar" in projekt else "badge-3nine"
        proj_label = "☀️ SOLAR" if "Solar" in projekt else "🌀 3NINE"
        
        # Die optische "Kachel" für den ausgewählten Lead
        st.markdown(f"""
            <div class="lead-card">
                <span class="{badge_class}">{proj_label}</span>
                <div class="lead-header">{lead['Firmenname']}</div>
                <div class="lead-sub">📍 {lead['Adresse']} &nbsp;|&nbsp; 📞 Telefon: {lead['Telefon']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Eingabemasken sauber aufgeteilt
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>🌱 Umwelt-Qualifizierung:</p>", unsafe_allow_html=True)
            if "Solar" in projekt:
                interessiert_pv = st.checkbox("Dachfläche geeignet für PV", value=lead["Kriterien"].get("PV", False))
                interessiert_sp = st.checkbox("Interesse an CO₂-Senkung durch Speicher", value=lead["Kriterien"].get("Speicher", False))
                lead["Kriterien"]["PV"] = interessiert_pv
                lead["Kriterien"]["Speicher"] = interessiert_sp
            else:
                nutzt_kss = st.checkbox("Nutzt Kühlschmierstoffe (KSS)", value=lead["Kriterien"].get("KSS", False))
                hat_rauch = st.checkbox("Ölnebel/Hallenluft verbesserungswürdig", value=lead["Kriterien"].get("Ölnebel", False))
                lead["Kriterien"]["KSS"] = nutzt_kss
                lead["Kriterien"]["Ölnebel"] = hat_rauch
                
        with col2:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>📊 Vertriebsstatus:</p>", unsafe_allow_html=True)
            current_status = st.selectbox("Status ändern:", ["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"], 
                                          index=["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"].index(lead["Status"]))
        with col3:
            st.markdown("<p style='color:#8bc34a; font-weight:bold;'>📅 Termine:</p>", unsafe_allow_html=True)
            termin_eingabe = st.text_input("Besprechungstermin:", value=lead["Termin"], placeholder="z.B. 24.07. um 10:00 Uhr")
            
        st.write("")
        st.markdown("<p style='color:#8bc34a; font-weight:bold;'>📝 Kontakthistorie / Protokoll:</p>", unsafe_allow_html=True)
        st.text_area("Bisherige Notizen:", value=lead["Historie"], height=100, disabled=True)
        
        neuer_kommentar = st.text_input("Neues Ereignis protokollieren:", placeholder="z.B. Geschäftsführer am Telefon gehabt. Hat großes Interesse an CO₂-Reduktion...")
        
        st.write("")
        if st.button("💾 Datensatz grün speichern", type="primary", use_container_width=True):
            st.session_state.db_leads[selected_key]["Status"] = current_status
            st.session_state.db_leads[selected_key]["Termin"] = termin_eingabe
            
            if neuer_kommentar:
                zeitstempel = datetime.now().strftime("%d.%m.%Y %H:%M")
                st.session_state.db_leads[selected_key]["Historie"] += f"[{zeitstempel}]: {neuer_kommentar}\n"
                
            st.success("Änderungen wurden erfolgreich in der Eco-Datenbank gesichert!")
            st.rerun()
            
    # Export-Bereich für dich
    st.write("---")
    st.markdown("<h3 style='color: #4caf50;'>📊 Management Export</h3>", unsafe_allow_html=True)
    if st.button(f"Projekt-Daten als CSV herunterladen"):
        export_df = pd.DataFrame.from_dict(current_project_leads, orient='index')
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Datei-Download starten", csv, f"eco_leads_{projekt.replace(' ', '_')}.csv", "text/csv")
else:
    st.info(f"Für das Projekt '{projekt}' wurden in dieser Region noch keine Potenziale geladen. Nutze die linke Seitenleiste.")
