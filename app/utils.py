import requests

def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&addressdetails=1"
        headers = {
            'User-Agent': 'Hornissenportal/1.0 (kontakt@velutina-service.ch)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Fehler abfangen
        data = response.json()
        return data.get('address', {}).get('state', 'Unbekannt')
    except Exception as e:
        print(f"Reverse Geocoding Fehler: {e}")
        return "Unbekannt"
