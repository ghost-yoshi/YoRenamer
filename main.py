import os
import argparse
import concurrent.futures
from dotenv import load_dotenv

from ai_cleaner import QueryCleaner
from client import MusicClient
from worker import AudioWorker
from cleaner import AudioCleaner

load_dotenv()

MAX_WORKERS = 3
MAX_DURATION_GAP_MS = 15_000  # écart de durée toléré (15 s)


def traiter_un_fichier(filename, query, target_dir, client, worker, dry_run):
    filepath = os.path.join(target_dir, filename)

    results = client.fetch_metadata(query)
    if not results:
        return f"[{filename}] Échec : aucune métadonnée (requête : {query})"

    local_duration = worker.get_local_duration_ms(filepath)
    ecart = None
    if local_duration > 0:
        best_match = min(results, key=lambda x: abs(x['duration_ms'] - local_duration))
        ecart = abs(best_match['duration_ms'] - local_duration)
        if ecart > MAX_DURATION_GAP_MS:
            return (f"[{filename}] Rejeté : écart de durée {ecart // 1000}s "
                    f"(requête : {query} -> {best_match['artist']} - {best_match['title']})")
    else:
        best_match = results[0]

    if dry_run:
        ecart_txt = f"{ecart // 1000}s" if ecart is not None else "?"
        return (f"[{filename}] (dry-run) -> {best_match['artist']} - {best_match['title']} "
                f"(écart {ecart_txt})")

    artwork_bytes = None
    if best_match.get('artwork_url'):
        artwork_bytes = client.download_artwork(best_match['artwork_url'])

    new_name = worker.process_file(filepath, best_match, artwork_bytes)

    if new_name:
        return f"[{filename}] -> Renommé en : {new_name}"
    return f"[{filename}] -> Échec de l'écriture."


def main():
    parser = argparse.ArgumentParser(description=f"Normalise les audio avec {MAX_WORKERS} workers.")
    parser.add_argument("dossier", help="Chemin vers le dossier MP3")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les changements sans écrire")
    args = parser.parse_args()

    target_dir = args.dossier
    if not os.path.isdir(target_dir):
        print("Erreur : Dossier introuvable.")
        return

    # Nettoyage des doublons (synchrone, destructif -> ignoré en dry-run)
    if args.dry_run:
        print("(dry-run) scan des doublons ignoré")
    else:
        cleaner = AudioCleaner(target_dir)
        cleaner.remove_exact_duplicates()

    client = MusicClient()
    worker = AudioWorker()

    fichiers = [f for f in os.listdir(target_dir) if f.lower().endswith('.mp3')]

    # Nettoyage des noms par l'IA, en lots
    cleaner_ai = QueryCleaner(os.getenv("PROXY_URL"), os.getenv("PROXY_TOKEN"))
    queries = {}
    bs = cleaner_ai.batch_size
    print(f"\n--- Nettoyage IA des noms ({len(fichiers)} fichiers, lots de {bs}) ---")
    for i in range(0, len(fichiers), bs):
        lot = fichiers[i:i + bs]
        try:
            queries.update(cleaner_ai.clean_batch(lot))
        except Exception as e:
            print(f"  Lot {i // bs + 1} échoué : {e} (fallback regex)")
    print(f"  {len(queries)}/{len(fichiers)} requêtes obtenues par l'IA")

    # Pool de workers : ThreadPoolExecutor gère la file et la répartition
    print(f"\n--- Lancement de {MAX_WORKERS} workers sur {len(fichiers)} fichiers ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for filename in fichiers:
            future = executor.submit(
                traiter_un_fichier,
                filename,
                queries.get(filename) or worker.clean_query_from_filename(filename),
                target_dir, client, worker, args.dry_run,
            )
            futures.append(future)

        # Récolte propre des résultats (évite les print entremêlés)
        try:
            for future in concurrent.futures.as_completed(futures):
                print(future.result())
        except KeyboardInterrupt:
            print("\nInterruption : annulation des tâches en attente...")
            executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()