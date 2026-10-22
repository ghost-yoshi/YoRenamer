import os
import hashlib

class AudioCleaner:
    def __init__(self, directory):
        self.directory = directory

    def get_file_hash(self, filepath):
        """Génère le hash MD5 d'un fichier pour vérifier son contenu exact."""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as afile:
                buf = afile.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(65536)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Erreur de lecture pour le hash de {filepath}: {e}")
            return None

    def remove_exact_duplicates(self):
        """Identifie et supprime les fichiers ayant le même contenu binaire."""
        print("\n--- Début du scan des doublons exacts (Hash MD5) ---")
        hashes = {}
        duplicates_removed = 0

        for filename in os.listdir(self.directory):
            if not filename.lower().endswith('.mp3'):
                continue

            filepath = os.path.join(self.directory, filename)
            file_hash = self.get_file_hash(filepath)

            if not file_hash:
                continue

            if file_hash in hashes:
                original_file = hashes[file_hash]
                print(f"  [Doublon trouvé] Suppression de : {filename}")
                print(f"  -> (Identique à : {os.path.basename(original_file)})")
                try:
                    os.remove(filepath)
                    duplicates_removed += 1
                except Exception as e:
                    print(f"  Erreur lors de la suppression : {e}")
            else:
                hashes[file_hash] = filepath

        print(f"\n--- Scan terminé. {duplicates_removed} doublon(s) supprimé(s). ---")