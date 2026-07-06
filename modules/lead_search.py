import streamlit as st
import requests
import sqlite3
from datetime import datetime
from config import DB_PATH

def search_live_leads(suchbegriff, radius_km, projekt):
    """
    Sucht via OpenStreetMap Overpass-API nach passenden Großflächen (PV) 
    oder metallverarbeitenden Betrieben (3nine) und speichert sie in der Datenbank.
    """
    # 1. GPS-Koordinaten für den Ort/PLZ holen
    geo_url = f"https://nominatim.openstreetmap.org/search?q={suchbegriff},+Germany&format=json&limit=1"
    headers = {'User-Agent': 'EcoLeadCRM_SearchSystem/1.0'}
    
    try:
        geo_res = requests.get(geo_url, headers=headers, timeout=10).json()
        if not geo_res:
            return "Ort oder PLZ konnte nicht gefunden werden."
        
        lat, lon = float(geo_res[0]['lat']), float(geo_res[0]['lon'])
        radius_meters = radius_km * 1000
        
        # 2. Suchkriterien nach Projekt trennen
        if "Solar" in projekt:
            # PV sucht riesige Dachflächen: Logistik, Hallen, Supermärkte, Baumärkte, Behörden
            osm_query = f"""
            nwr["industrial"="logistics"](around:{radius_meters},{lat},{lon});
            nwr["building"="warehouse"](around:{radius_meters},{lat},{lon})["name"];
            nwr["shop"="supermarket"](around:{radius_meters},{lat},{lon})["name"];
            nwr["shop"="doityourself"](around:{radius_meters},{lat},{lon})["name"];
            nwr["amenity"="townhall"](around:{radius_meters},{lat},{lon});
            nwr["landuse"="industrial"](around:{radius_meters},{lat},{lon})["name"];
            """
        else:
            # 3nine sucht Ölnebel-Erzeuger: CNC, Drehereien, Metallbau, Fabriken
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
        
        # 3. Verbindung zur echten Datenbank herstellen
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        heute = datetime.now().strftime("%d.%m.%Y")
        
        for el in elements:
            tags = el.get('tags', {})
            f_name = tags.get('name', tags.get('operator', None))
            
            if not f_name:
                if tags.get('amenity') == 'townhall': f_name = f"Rathaus / Gemeinde ({suchbegriff})"
                else: continue
            
            # Adressdaten zusammensetzen
            street = tags.get('addr:street', 'Gewerbegebiet')
            nr = tags.get('addr:housenumber', '')
            p_code = tags.get('addr:postcode', suchbegriff)
            city = tags.get('addr:city', '')
            f_addr = f"{street} {nr}, {p_code} {city}".strip(", ")
            
            phone = tags.get('phone', tags.get('contact:phone', 'Nicht hinterlegt'))
            
            # Lead in die Datenbank schreiben (UNIQUE verhindert doppelte Einträge automatisch)
            try:
                cursor.execute("""
                    INSERT INTO leads (projekt, firmenname, adresse, telefon, suchort, eingetragen_am)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (projekt, f_name, f_addr, phone, suchbegriff, heute))
                
                # Direkt den ersten leeren Verlaufseintrag mitspeichern
                lead_id = cursor.lastrowid
                cursor.execute("""
                    INSERT INTO history (lead_id, timestamp, bearbeiter, notiz)
                    VALUES (?, ?, ?, ?)
                """, (lead_id, heute, 'System', 'In den CRM-Pool geladen.'))
                
                added_counter += 1
            except sqlite3.IntegrityError:
                # Firma existiert schon für dieses Projekt, wird übersprungen
                continue
                
        conn.commit()
        conn.close()
        return added_counter
        
    except Exception as e:
        return f"Fehler bei der Suche: {str(e)}"
