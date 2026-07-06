import sqlite3
import sys
import os

# Damit das Skript die config findet, fügen wir das Hauptverzeichnis zum Pfad hinzu
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

def init_database():
    print(f"Initialisiere Datenbank unter: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tabelle für Benutzer (Login & Rechte)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'Mitarbeiter'
    )
    """)

    # 2. Tabelle für die Leads (CRM Zentrale)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        projekt TEXT NOT NULL,
        firmenname TEXT NOT NULL,
        adresse TEXT NOT NULL,
        telefon TEXT DEFAULT 'Nicht hinterlegt',
        status TEXT DEFAULT 'Offen (Unbearbeitet)',
        bearbeiter TEXT DEFAULT 'Niemand',
        wiedervorlage TEXT DEFAULT 'Keine',
        termin TEXT DEFAULT 'Kein Termin',
        suchort TEXT,
        eingetragen_am TEXT NOT NULL,
        UNIQUE(projekt, firmenname, adresse)
    )
    """)

    # 3. Tabelle für die Telefon-Notizen (Historie)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        bearbeiter TEXT NOT NULL,
        notiz TEXT NOT NULL,
        FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
    )
    """)

    # Standard-Nutzer anlegen, falls die Tabelle leer ist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Passwörter im Prototyp als Klartext, in Phase 1b rüsten wir Hashing nach
        default_users = [
            ('admin', 'eco2026', 'Admin'),
            ('patrick', 'vertrieb1', 'Mitarbeiter'),
            ('elke', 'vertrieb2', 'Mitarbeiter')
        ]
        cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", default_users)
        print("💡 Standard-Benutzer erfolgreich angelegt (admin, patrick, elke).")

    conn.commit()
    conn.close()
    print("✅ Datenbank-Struktur erfolgreich aufgebaut!")

if __name__ == "__main__":
    init_database()
