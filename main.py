import requests 
import time
import sys

def interroger_endpoint(url):
    """ """
    try :
        response = requests.get(url, timeout=10)
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
                print(data)
            else:
                print("aucune donnée reçue")
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("arrêt demandé")
        sys.exit(0)

if __name__ == "__main__":
    #url = url
    interval = 2
    x_min(url, interval)
        

# a stocker : id / coordonné / date-heure