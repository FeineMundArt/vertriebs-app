with tab2:
    st.write("### 🚀 Industrie-Solar Suche")
    search_loc = st.text_input("Ort oder PLZ für die Suche:", "Garbsen")
    radius = st.slider("Suchradius in Metern:", 1000, 20000, 5000)
    
    if st.button("🔍 Suche starten"):
        # 1. Koordinaten abrufen
        lat, lon = get_coords(search_loc)
        
        if lat and lon:
            with st.spinner("Suche Industrie-Leads..."):
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
                        data = response.json()
                        elements = data.get('elements', [])
                        
                        if elements:
                            # 2. In Datenbank schreiben
                            conn = sqlite3.connect(DB_FILE)
                            cursor = conn.cursor()
                            count = 0
                            for el in elements:
                                name = el.get('tags', {}).get('name', 'Industrie-Objekt')
                                # Nur wenn Name vorhanden
                                if name != 'Industrie-Objekt':
                                    try:
                                        cursor.execute("INSERT OR IGNORE INTO leads (firmenname, adresse) VALUES (?, ?)", 
                                                       (name, search_loc))
                                        count += 1
                                    except: pass
                            conn.commit()
                            conn.close()
                            st.success(f"✅ {count} neue Firmen in den Pool geladen!")
                            st.rerun() # App neu laden, damit die Tabelle in Tab1 erscheint
                        else:
                            st.warning("Keine Ergebnisse in diesem Bereich gefunden.")
                    else:
                        st.error(f"API-Fehler: {response.status_code}")
                except Exception as e:
                    st.error(f"Fehler: {e}")
        else:
            st.error("Ort konnte nicht gefunden werden.")
