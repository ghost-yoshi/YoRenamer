PROMPT = """Tu nettoies des noms de fichiers audio pour les chercher dans une API musicale.

Pour chaque entrée, renvoie une requête de recherche : "artiste titre".
RÈGLES :
- Supprime uniquement le bruit : extension, bitrate (256k, 48k), numéros d'ID,
  "mp3", "official", "visualizer", "lyrics", "audio", "video", "HD",
  "slowed", "reverb", "sped up", "edit by ...", "demo", "remix de tiers".
- Remplace _ et - de séparation par des espaces.
- N'INVENTE RIEN : n'ajoute aucun mot absent du nom d'origine.
- Si tu ne peux pas identifier de titre, renvoie la chaîne nettoyée telle quelle.
- Réponds UNIQUEMENT par un tableau JSON [{"id": <int>, "query": "<str>"}], un objet par entrée.

EXEMPLES :
1: steve_lacy_dark_red_mp3_73439.mp3
2: X-REHAB__OFFICIAL_Visualizer__-_ICEDMANE(256k).mp3
3: TRILLIUM_-_S3RL___SLOWED___BEST_PART_LOOPED__(48k).mp3
Réponse :
[{"id":1,"query":"steve lacy dark red"},
 {"id":2,"query":"icedmane x-rehab"},
 {"id":3,"query":"s3rl trillium"}]

À TRAITER :
"""

PROXY_URL = "https://ghost-yoshi-proxy-gemini-1gyr.vercel.app/ask"

import json, requests
class QueryCleaner:

    def __init__(self, url, api_key, batch_size=12):
        if not url or not api_key:
            raise ValueError("PROXY_URL ou PROXY_TOKEN manquant : vérifie ton .env")
        self.url = url
        self.api_key = api_key
        self.batch_size = batch_size

    def clean_batch(self, filenames):
        """filenames: liste de noms. Retourne {nom_fichier: requête}."""
        lines = "\n".join(
            f"{i}: {name}" for i, name in enumerate(filenames, 1)
        )

        body = {
            "contents": [ {"parts": [{"text": PROMPT+lines}]}],
            "generationConfig": {
                "temperature":0,
                "responseMimeType": 'application/json'
            }
        }

        r = requests.get(
                    self.url,
                    params={"prompt": PROMPT + lines, "token": self.api_key},
                    timeout=60,
                    )

        r.raise_for_status()
        answer = r.json().get("answer", "")
        items = self._parse_json_list(answer)
        return {
            filenames[it["id"] - 1]: it["query"]
            for it in items if isinstance(it.get("id"), int)
            and 1 <= it["id"] <= len(filenames)
            and str(it.get("query", "")).strip()
        }

    @staticmethod
    def _parse_json_list(text):
        start, end = text.find("["), text.rfind("]")
        if start == -1 or end == -1:
            return []
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return []