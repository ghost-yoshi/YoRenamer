import os
import argparse
from client import MusicClient
from worker import AudioWorker

def main():
    parser = argparse.ArgumentParser(description="Normalise les noms et tags des fichiers audio.")
    parser.add_argument("dossier", help="Chemin vers le dossier contenant les MP3")
    args = parser.parse_args()

    target_dir = args.dossier
    
    if not os.path.isdir(target_dir):
        print(f"Erreur : Le dossier '{target_dir}' n'existe pas.")
        return

    client = MusicClient()
    worker = AudioWorker()

    print(f"--- Démarrage de YORENAMER dans : {target_dir} ---")

    for filename in os.listdir(target_dir):
        if not filename.lower().endswith('.mp3'):
            continue

        filepath = os.path.join(target_dir, filename)
        print(f"\nTraitement : {filename}")

        # 1. Le Worker prépare la requête
        query = worker.clean_query_from_filename(filename)
        print(f"  Recherche de : '{query}'...")

        # 2. Le Client récupère une liste de métadonnées
        results = client.fetch_metadata(query)

        if results:
            # 3. Le Main orchestre la sélection en demandant la durée locale au Worker
            local_duration = worker.get_local_duration_ms(filepath)
            
            if local_duration > 0:
                # Sélectionne le morceau dont la durée API est la plus proche du fichier local
                best_match = min(results, key=lambda x: abs(x['duration_ms'] - local_duration))
                diff_sec = abs(best_match['duration_ms'] - local_duration) / 1000
                print(f"  Correspondance trouvée (différence de durée : {diff_sec:.1f}s)")
            else:
                # Fallback si mutagen n'arrive pas à lire la durée
                best_match = results[0] 
                print("  Correspondance par défaut (premier résultat)")

            print(f"  Sélection : {best_match['artist']} - {best_match['title']}")

            # 4. Le Client télécharge l'image
            artwork_bytes = None
            if best_match.get('artwork_url'):
                print("  Téléchargement de la pochette HD...")
                artwork_bytes = client.download_artwork(best_match['artwork_url'])

            # 5. Le Worker applique le tout sur le disque
            new_name = worker.process_file(filepath, best_match, artwork_bytes)
            
            if new_name:
                print(f"  Succès -> Renommé en : {new_name}")
            else:
                print("  Échec lors de l'écriture du fichier.")
        else:
            print("  Échec : Aucune métadonnée trouvée sur l'API.")

if __name__ == "__main__":
    main()
