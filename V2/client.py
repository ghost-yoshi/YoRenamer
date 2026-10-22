import aiohttp

class AsyncMusicClient:
    def __init__(self):
        self.base_url = "https://itunes.apple.com/search"

    async def fetch_metadata(self, session, query, limit=5):
        """Cherche une chanson de manière asynchrone."""
        params = {
            "term": query,
            "media": "music",
            "entity": "song",
            "limit": str(limit)
        }
        
        try:
            async with session.get(self.base_url, params=params, timeout=15) as response:
                response.raise_for_status()
                data = await response.json()
                
                results = []
                if data.get("resultCount", 0) > 0:
                    for track in data["results"]:
                        results.append({
                            "title": track.get("trackName", "Inconnu"),
                            "artist": track.get("artistName", "Inconnu"),
                            "album": track.get("collectionName", "Inconnu"),
                            "year": str(track.get("releaseDate", ""))[:4],
                            "genre": track.get("primaryGenreName", ""),
                            "artwork_url": track.get("artworkUrl100", "").replace("100x100bb.jpg", "600x600bb.jpg"),
                            "duration_ms": track.get("trackTimeMillis", 0)
                        })
                    return results
                return None
        except Exception as e:
            # On ignore silencieusement les erreurs réseaux individuelles pour ne pas polluer la console
            return None

    async def download_artwork(self, session, url):
        """Télécharge la pochette de manière asynchrone."""
        if not url:
            return None
        try:
            async with session.get(url, timeout=15) as response:
                response.raise_for_status()
                return await response.read() # Récupère les bytes
        except Exception:
            return None