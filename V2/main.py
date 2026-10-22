import os
import argparse
import asyncio
import aiohttp
from client import AsyncMusicClient
from worker import AudioWorker
from cleaner import AudioCleaner

async def process_single_file(filename, filepath, client, worker, session, semaphore):
    """Gère le cycle de vie complet d'un seul fichier."""
    async with semaphore: # Limite le nombre de fichiers traités en même temps
        try:
            # 1. Préparation
            query = worker.clean_query_from_filename(filename)
            
            # 2. Requête API (Réseau = await direct)
            results = await client.fetch_metadata(session, query)
            
            if not results:
                return f"[{filename}] Ignoré : Aucune métadonnée."

            # 3. Opérations Disque (I/O = exécuté dans un thread séparé pour ne pas bloquer async)
            local_duration = await asyncio.to_thread(worker.get_local_duration_ms, filepath)
            
            if local_duration > 0:
                best_match = min(results, key=lambda x: abs(x['duration_ms'] - local_duration))
            else:
                best_match = results[0]

            # 4. Téléchargement image (Réseau = await direct)
            artwork_bytes = await client.download_artwork(session, best_match.get('artwork_url'))

            # 5. Injection Tags et Renommage (Disque = thread séparé)
            new_name = await asyncio.to_thread(worker.process_file, filepath, best_match, artwork_bytes)
            
            if new_name:
                return f"[{filename}] -> Succès : {new_name}"
            return f"[{filename}] -> Échec de l'écriture locale."

        except Exception as e:
            return f"[{filename}] -> Erreur inattendue : {e}"


async def run_orchestrator(target_dir):
    print(f"--- Démarrage YORENAMER (Mode Asynchrone Haute Performance) ---")
    
    # Étape 1 : Nettoyage synchrone des doublons exacts
    cleaner = AudioCleaner(target_dir)
    cleaner.remove_exact_duplicates()

    # Étape 2 : Préparation des tâches asynchrones
    client = AsyncMusicClient()
    worker = AudioWorker()
    
    # Limite fixée à 20 requêtes simultanées pour éviter le Rate Limiting (Ban IP)
    semaphore = asyncio.Semaphore(20) 
    tasks = []

    files_to_process = [f for f in os.listdir(target_dir) if f.lower().endswith('.mp3')]
    print(f"\nTraitement asynchrone de {len(files_to_process)} fichiers en cours...")

    # Ouverture de la session HTTP globale
    async with aiohttp.ClientSession() as session:
        for filename in files_to_process:
            filepath = os.path.join(target_dir, filename)
            task = asyncio.create_task(
                process_single_file(filename, filepath, client, worker, session, semaphore)
            )
            tasks.append(task)
        
        # Exécution de toutes les tâches en parallèle et récupération des résultats
        results = await asyncio.gather(*tasks)

    # Affichage propre des logs à la fin pour éviter que les textes ne se mélangent
    print("\n--- RAPPORTS DE TRAITEMENT ---")
    for res in results:
        print(res)
    print("\n--- TERMINÉ ---")


def main():
    parser = argparse.ArgumentParser(description="Normalise les musiques (Haute Performance).")
    parser.add_argument("dossier", help="Chemin vers le dossier contenant les MP3")
    args = parser.parse_args()

    target_dir = args.dossier
    if not os.path.isdir(target_dir):
        print(f"Erreur : Le dossier '{target_dir}' n'existe pas.")
        return

    # Lancement de la boucle asynchrone
    asyncio.run(run_orchestrator(target_dir))

if __name__ == "__main__":
    main()