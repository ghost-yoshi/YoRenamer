import os
import argparse
from client import MusicClient
from worker import AudioWorker
from cleaner import AudioCleaner # Ajout du cleaner

def main():
    parser = argparse.ArgumentParser(description="Normalise les noms, tags et supprime les doublons audio.")
    parser.add_argument("dossier", help="Chemin vers le dossier contenant les MP3")
    args = parser.parse_args()

    target_dir = args.dossier
    
    if not os.path.isdir(target_dir):
        print(f"Erreur : Le dossier '{target_dir}' n'existe pas.")
        return

    print(f"--- Démarrage de YORENAMER dans : {target_dir} ---")

    # 1. Nettoyage des doublons AVANT les requêtes API
    cleaner = AudioCleaner(target_dir)
    cleaner.remove_exact_duplicates()

    # Initialisation des autres modules
    client = MusicClient()
    worker = AudioWorker()

    print("\n--- Début du traitement des métadonnées ---")
    for filename in os.listdir(target_dir):
        if not filename.lower().endswith('.mp3'):
            continue

        filepath = os.path.join(target_dir, filename)
        print(f"\nTraitement : {filename}")

        query = worker.clean_query_from_filename(filename)
        print(f"  Recherche de : '{query}'...")

        results = client.fetch_metadata(query)

        if results:
            local_duration = worker.get_local_duration_ms(filepath)
            
            if local_duration > 0:
                best_match = min(results, key=lambda x: abs(x['duration_ms'] - local_duration))
                diff_sec = abs(best_match['duration_ms'] - local_duration) / 1000
                print(f"  Correspondance trouvée (différence : {diff_sec:.1f}s)")
            else:
                best_match = results[0] 
                print("  Correspondance par défaut (premier résultat)")

            print(f"  Sélection : {best_match['artist']} - {best_match['title']}")

            artwork_bytes = None
            if best_match.get('artwork_url'):
                print("  Téléchargement de la pochette...")
                artwork_bytes = client.download_artwork(best_match['artwork_url'])

            new_name = worker.process_file(filepath, best_match, artwork_bytes)
            
            if new_name:
                print(f"  Succès -> Renommé en : {new_name}")
            else:
                print("  Échec de l'écriture.")
        else:
            print("  Échec : Aucune métadonnée trouvée.")

if __name__ == "__main__":
    main()