import os
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON, TDRC, error

class AudioWorker:
    @staticmethod
    def clean_query_from_filename(filename):
        """Nettoie le nom de fichier pour la recherche API."""
        name, _ = os.path.splitext(filename)
        mots_a_supprimer = [r'official', r'video', r'lyrics', r'audio', r'hd', r'\[.*?\]', r'\(.*?\)']
        for mot in mots_a_supprimer:
            name = re.sub(mot, '', name, flags=re.IGNORECASE)
        return re.sub(r'[_\-]', ' ', name).strip()

    @staticmethod
    def sanitize_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "", name)

    def get_local_duration_ms(self, filepath):
        """Lit la durée du fichier MP3 local en millisecondes pour la comparaison."""
        try:
            audio = MP3(filepath)
            return int(audio.info.length * 1000)
        except Exception:
            return 0

    def process_file(self, filepath, metadata, artwork_bytes=None):
        """Injecte les tags ID3 et renomme le fichier physiquement."""
        try:
            # 1. Gestion stricte des tags ID3
            try:
                audio = ID3(filepath)
            except error:
                audio = ID3()

            audio.add(TIT2(encoding=3, text=metadata['title']))
            audio.add(TPE1(encoding=3, text=metadata['artist']))
            audio.add(TALB(encoding=3, text=metadata['album']))
            
            if metadata.get('genre'):
                audio.add(TCON(encoding=3, text=metadata['genre']))
            if metadata.get('year'):
                audio.add(TDRC(encoding=3, text=metadata['year']))

            # 2. Ajout de la pochette si les bytes ont été fournis par le Main
            if artwork_bytes:
                audio.add(
                    APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=artwork_bytes
                    )
                )

            audio.save(filepath, v2_version=3)

            # 3. Renommage physique sur le disque
            directory = os.path.dirname(filepath)
            safe_artist = self.sanitize_filename(metadata['artist'])
            safe_title = self.sanitize_filename(metadata['title'])
            
            new_filename = f"{safe_artist} - {safe_title}.mp3"
            new_filepath = os.path.join(directory, new_filename)

            if filepath != new_filepath and not os.path.exists(new_filepath):
                os.rename(filepath, new_filepath)
                return new_filename
            return os.path.basename(filepath)
            
        except Exception as e:
            print(f"Erreur lors du traitement local de {filepath}: {e}")
            return None
