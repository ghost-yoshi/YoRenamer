import requests

class MusicClient:
    def __init__(self):
        self.base_url = "https://itunes.apple.com/search"

    def fetch_metadata(self, query, limit=5):
        """Cherche une chanson et retourne une liste de résultats."""
        params = {
            "term": query,
            "media": "music",
            "entity": "song",
            "limit": limit
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if data.get("resultCount", 0) > 0:
                for track in data["results"]:
                    results.append({
                        "title": track.get("trackName", "Inconnu"),
                        "artist": track.get("artistName", "Inconnu"),
                        "album": track.get("collectionName", "Inconnu"),
                        "year": str(track.get("releaseDate", ""))[:4],
                        "genre": track.get("primaryGenreName", ""),
                        # On formate l'URL en HD (600x600) directement ici
                        "artwork_url": track.get("artworkUrl100", "").replace("100x100bb.jpg", "600x600bb.jpg"),
                        "duration_ms": track.get("trackTimeMillis", 0)
                    })
                return results
            return None
        except requests.RequestException as e:
            print(f"Erreur API : {e}")
            return None

    def download_artwork(self, url):
        """Télécharge l'image depuis l'URL et retourne les bytes bruts."""
        if not url:
            return None
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            print(f"Erreur téléchargement pochette : {e}")
            return None
