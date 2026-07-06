import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Multi-Projekt Lead-Manager", layout="wide")

st.title("🎯 Multi-Projekt Vertriebs- & Lead-Manager")
st.write("Verwalte verschiedene Vertriebsprojekte und filtere Leads passgenau nach Branche und Region.")

# Sichert, dass die Datenbank im Hintergrund läuft
if "db_leads" not in st.session_state:
    st.session_state.db_leads = {}

# --- PROJEKTAUSWAHL (Zentral für das ganze Team) ---
st.write("---")
projekt = st.selectbox(
    "📊 Bitte wähle das aktuelle Projekt aus:",
    ["Solar & Speicher (Industrie-Solar)", "3nine (Schmierstoff- & Ölnebelfilter)"]
)
st.write(f"Du arbeitest aktuell im Projekt: **{projekt}**")
st.write("---")

# --- SUCHE & GENERIERUNG ---
with st.sidebar:
    st.header("🎯 Neue Leads laden")
    plz = st.text_input("Postleitzahl (PLZ)", placeholder="z.B. 30823")
    radius = st.slider("Radius (km)", 5, 100, 25)
    
    # Suchbegriffe automatisch je nach Projekt anpassen
    if "Solar" in projekt:
        default_kw = "Gewerbe, Industrie, Lager"
        help_text = "Sucht nach großen Dachflächen (Fabriken, Hallen)."
    else:
        default_kw = "Metallbau, Zerspanung, Maschinenbau"
        help_text = "Sucht nach fertigenden Betrieben mit CNC-Maschinen."
        
    keyword = st.text_input("Branche / Fokus", value=default_kw, help=help_text)
    search_btn = st.button("Frische Leads in Datenbank laden")

if search_btn and plz:
    with st.spinner("Suche passende Unternehmen in der Region..."):
        # PLZ in Koordinaten umwandeln
        geo_url = f"https://nominatim.openstreetmap.org/search?postalcode={plz}&country=Germany&format=json"
        headers = {'User-Agent': 'Multi_Lead_App_Bot_1.0'}
        
        try:
            geo_res = requests.get(geo_url, headers=headers).json()
        except Exception:
            geo_res = None
        
        if geo_res:
            lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
            radius_meters = radius * 1000
            
            # Suchanfrage je nach Projekt optimieren
            if "Solar" in projekt:
                osm_query = f"""
                ( nwr["industrial"](around:{radius_meters},{lat},{lon});
                  nwr["building"="industrial"](around:{radius_meters},{lat},{lon}); )
                """
            else:
                # 3nine Fokus: Metallverarbeitung, Werkstätten, Fabriken
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
                        name = tags.get('name', tags.get('operator', f"Gewerbeobjekt ({keyword})"))
                        addr = f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}, {tags.get('addr:postcode', plz)} {tags.get('addr:city', '')}".strip(", ")
                        
                        # Jeder Lead wird eindeutig dem jeweiligen Projekt zugeordnet
                        lead_key = f"{projekt}_{name}_{tags.get('addr:street', '')}".lower()
                        
                        if lead_key not in st.session_state.db_leads:
                            st.session_state.db_leads[lead_key] = {
                                "Projekt": projekt,
                                "Firmenname": name,
                                "Adresse": addr if len(addr) > 5 else f"Region {plz}",
                                "Telefon": tags.get('phone', tags.get('contact:phone', 'Nicht hinterlegt')),
                                "Kriterien": {}, # Dynamische Felder für Projekt-Details
                                "Status": "Offen (Unbearbeitet)",
                                "Termin": "Kein Termin",
                                "Historie": f"[{datetime.now().strftime('%d.%m.%Y')}]: Für Projekt {projekt} erfasst.\n"
                            }
                            added_counter += 1
                    st.success(f"{added_counter} passende Betriebe für {projekt} in die Datenbank geladen!")
                else:
                    st.error("Fehler bei der Serverabfrage. Bitte kurz warten und erneut versuchen.")
            except Exception:
                st.error("Netzwerkfehler bei der Abfrage der Daten.")
        else:
            st.error("Postleitzahl konnte nicht gefunden werden.")

# --- FILTERN DER LEADS NACH AKTUELEM PROJEKT ---
current_project_leads = {k: v for k, v in st.session_state.db_leads.items() if v["Projekt"] == projekt}

if current_project_leads:
    st.subheader(f"📋 Offene Leads für das Projekt: {projekt}")
    status_filter = st.selectbox("Nach Status filtern:", ["Alle", "Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"])
    
    filtered_keys = []
    for k, v in current_project_leads.items():
        if status_filter == "Alle" or v["Status"] == status_filter:
            filtered_keys.append(k)
            
    if not filtered_keys:
        st.info("Keine Leads mit diesem Status für dieses Projekt gefunden.")
    else:
        selected_key = st.selectbox(
            "Wähle das Unternehmen aus, das du gerade bearbeitest:", 
            options=filtered_keys, 
            format_func=lambda x: f"{st.session_state.db_leads[x]['Firmenname']} ({st.session_state.db_leads[x]['Adresse']})"
        )
        
        lead = st.session_state.db_leads[selected_key]
        
        st.markdown(f"### 🏢 Bearbeite: **{lead['Firmenname']}**")
        st.write(f"📍 **Adresse:** {lead['Adresse']} | 📞 **Telefon:** {lead['Telefon']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Bedarfsanalyse / Qualifizierung:**")
            # Zeige projektspezifische Abfragen
            if "Solar" in projekt:
                interessiert_pv = st.checkbox("Interesse an Photovoltaik", value=lead["Kriterien"].get("PV", False))
                interessiert_sp = st.checkbox("Interesse an Energiespeicher", value=lead["Kriterien"].get("Speicher", False))
                lead["Kriterien"]["PV"] = interessiert_pv
                lead["Kriterien"]["Speicher"] = interessiert_sp
            else:
                # 3nine spezifische Kriterien
                nutzt_kss = st.checkbox("Nutzt Kühlschmierstoffe (KSS) / Öle", value=lead["Kriterien"].get("KSS", False))
                hat_rauch = st.checkbox("Problem mit Ölnebel / Rauch in der Halle", value=lead["Kriterien"].get("Ölnebel", False))
                lead["Kriterien"]["KSS"] = nutzt_kss
                lead["Kriterien"]["Ölnebel"] = hat_rauch
                
        with col2:
            current_status = st.selectbox("Aktueller Status:", ["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"], 
                                          index=["Offen (Unbearbeitet)", "In Bearbeitung", "Termin vereinbart", "Kein Interesse"].index(lead["Status"]))
        with col3:
            termin_eingabe = st.text_input("Termindatum / Uhrzeit:", value=lead["Termin"], placeholder="z.B. 14.07. 14:00 Uhr")
            
        st.markdown("**📜 Kontakthistorie & Notizen:**")
        st.text_area("Bisherige Einträge", value=lead["Historie"], height=120, disabled=True)
        
        neuer_kommentar = st.text_input("Neuen Eintrag hinzufügen:", placeholder="z.B.: CNC-Halle besichtigt. Infomaterial übergeben.")
        
        if st.button("Änderungen speichern", type="primary"):
            st.session_state.db_leads[selected_key]["Status"] = current_status
            st.session_state.db_leads[selected_key]["Termin"] = termin_eingabe
            
            if neuer_kommentar:
                zeitstempel = datetime.now().strftime("%d.%m.%Y %H:%M")
                st.session_state.db_leads[selected_key]["Historie"] += f"[{zeitstempel}]: {neuer_kommentar}\n"
                
            st.success("Erfolgreich für dieses Projekt gespeichert!")
            st.rerun()
            
    # Export-Bereich für den Chef
    st.write("---")
    st.subheader("📊 Projekt-Export")
    if st.button(f"Leads für das Projekt '{projekt}' exportieren"):
        export_df = pd.DataFrame.from_dict(current_project_leads, orient='index')
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, f"leads_{projekt.replace(' ', '_')}.csv", "text/csv")
else:
    st.info(f"Für das Projekt '{projekt}' wurden in dieser Region noch keine Leads geladen. Nutze die linke Seitenleiste.")
