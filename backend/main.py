import requests 
import time
import sys
import psycopg2
from datetime import datetime, date, timedelta

def get_connexion():
    return psycopg2.connect(
        host="adresse-infra",
        database="pollution_db",
        user="user",
        password="password"
    )

def interroger_endpoint(url):
    """ """
    try :
        response = requests.get(url, timeout=600)
        response.raise_for_status()
    
        try : 
            return response.json()
        except ValueError:
            return response.text

    except requests.exceptions.RequestException as e:
        print(f"erreur lors de la requête {e}")
        return None

def x_min(url, interval_minutes):
    """ """
    interval_seconds = interval_minutes * 60
    try :
        while True:
            print("nouvelle requête")
            data = interroger_endpoint(url)
            if data is not None:
                sauvegarder(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)

def sauvegarder(data):
    """ """
    con = get_connexion()#nom de la db
    cursor = con.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mesures (
        id SERIAL PRIMARY KEY,
        station_id  TEXT,
        station_name TEXT,
        lat    REAL,
        lon   REAL,
        indice      REAL,
        horaire     TEXT, 
        date        TEXT, 
        UNIQUE(station_id, date)
    )
    """)

    for station in data:
        api_date = datetime.fromisoformat(station.get("date"))
        cursor.execute(
        "INSERT INTO mesures (station_id, station_name, lat, lon, indice, horaire, date) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (station_id, date) DO NOTHING",
        (station.get("station_id"), station.get("station_name"), station.get("lat"), station.get("lon"),
        station.get("indice"), api_date.strftime("%H:%M:%S"), api_date.strftime("%Y-%m-%d"))
    )
    con.commit()
    con.close()

def x_min_avec_date(interval_minutes):
    interval_seconds = interval_minutes * 60
    try:
        while True:
            print("nouvelle requête")
            hier = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"http://localhost:8000/index?date={hier}"
            data = interroger_endpoint(url)
            if data is not None:
                sauvegarder(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)

def db_est_vide():
    try:
        con = get_connexion()
        cursor = con.cursor()
        cursor.execute("SELECT COUNT(*) FROM mesures")
        count = cursor.fetchone()[0]
        con.close()
        return count == 0
    except Exception:
        return True

if __name__ == "__main__":
    if db_est_vide():
        url_init = "http://localhost:8000/init?days=10"#10 au départ
        print("initialisation de la base...")
        data_init = interroger_endpoint(url_init)
        if data_init is not None:
            sauvegarder(data_init)
            print("base initialisée")
    else:
        print("base déjà initialisé")
    url = "http://localhost:8000/index"
    interval = 60
    #x_min(url, interval)
    x_min_avec_date(interval)