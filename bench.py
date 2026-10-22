import os, time
import requests
from dotenv import load_dotenv
from ai_cleaner import PROMPT

load_dotenv()
URL, TOKEN = os.getenv('PROXY_URL'), os.getenv('PROXY_TOKEN')

dossier = '/home/yoshi/Musique'
noms = [f for f in os.listdir(dossier) if f.lower().endswith('.mp3')][:12]

for taille in (1, 3, 6, 12):
    lot = noms[:taille]
    lignes = '\n'.join(f'{i}: {n}' for i, n in enumerate(lot, 1))
    debut = time.perf_counter()
    try:
        r = requests.get(URL, params={'prompt': PROMPT + lignes, 'token': TOKEN}, timeout=90)
        duree = time.perf_counter() - debut
        print(f'{taille:>2} noms -> HTTP {r.status_code} en {duree:.1f}s, '
              f'{len(r.text)} caractères reçus')
    except requests.Timeout:
        print(f'{taille:>2} noms -> TIMEOUT après {time.perf_counter() - debut:.1f}s')