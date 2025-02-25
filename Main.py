from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import csv

app = Flask(__name__)

# Lecture du CSV des épisodes
episodes_df = pd.read_csv("static/data/onepiece_episode.csv")

# Convertir la colonne Episode_Number en string
episodes_df['Episode_Number'] = episodes_df['Episode_Number'].astype(str)

# Afficher les colonnes disponibles
print("Colonnes disponibles dans le CSV:", episodes_df.columns.tolist())

# Création de la liste des épisodes
episodes = []
for index, row in episodes_df.iterrows():
    try:
        # Extraire le numéro d'épisode
        episode_num = str(row["Episode_Number"])
        
        # S'assurer que le titre est une chaîne de caractères
        title = str(row["Title"]) if pd.notna(row["Title"]) else ""
        
        episode = { 
            "episode_number": episode_num,
            "title": title
        }
        episodes.append(episode)
    except:
        continue

# Tri par numéro d'épisode
episodes.sort(key=lambda x: float(x["episode_number"]))

print(f"Nombre d'épisodes chargés : {len(episodes)}")  # Debug

def get_chapters_by_volume():
    chapters_by_volume = {}
    
    # Liste des encodages à essayer
    encodings = ['utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open('static/data/Chapters.csv', 'r', encoding=encoding) as file:
                print(f"Tentative avec l'encodage: {encoding}")
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        volume = row['Volume']
                        chapter = row['Chapter_Number']
                        
                        # Debug print
                        print(f"Lu: Volume {volume}, Chapitre {chapter}")
                        
                        # Convertir en entiers
                        volume = int(volume)
                        chapter = int(chapter)
                        
                        # Stocker les chapitres par volume
                        if volume not in chapters_by_volume:
                            chapters_by_volume[volume] = []
                        chapters_by_volume[volume].append(chapter)
                        
                    except (ValueError, KeyError) as e:
                        print(f"Erreur sur une ligne: {e}")
                        continue
                
                # Si on arrive ici, la lecture a réussi
                break
                    
        except Exception as e:
            print(f"Erreur avec l'encodage {encoding}: {e}")
            continue

    if not chapters_by_volume:
        print("Aucun encodage n'a fonctionné")
        return {}

    # Debug print pour voir le contenu final
    print("\nContenu de chapters_by_volume:")
    for volume, chapters in sorted(chapters_by_volume.items()):
        print(f"Volume {volume}: {chapters}")

    # Formater les chapitres pour chaque tome
    formatted_chapters = {}
    for volume in range(1, 106):
        if volume in chapters_by_volume and chapters_by_volume[volume]:
            min_chapter = min(chapters_by_volume[volume])
            max_chapter = max(chapters_by_volume[volume])
            # Créer la liste de tous les chapitres dans l'intervalle
            all_chapters = list(range(min_chapter, max_chapter + 1))
            formatted_chapters[volume] = all_chapters
        else:
            formatted_chapters[volume] = []
    
    # Debug print pour voir le résultat final
    print("\nContenu de formatted_chapters:")
    for volume, chapters in sorted(formatted_chapters.items()):
        print(f"Volume {volume}: {chapters}")
    
    return formatted_chapters

@app.route('/')
def index():
    volume_data = {}
    chapters_by_volume = get_chapters_by_volume()
    
    # Lire le CSV qui contient les associations chapitre-épisodes
    chapters_episodes_df = pd.read_csv("static/data/onepiece_chapters_episodes_sorted.csv")
    
    # Créer un dictionnaire qui associe les chapitres à leurs épisodes
    chapter_to_episodes = {}
    
    # Remplir le dictionnaire avec les données du CSV
    for _, row in chapters_episodes_df.iterrows():
        chapter = int(row['Chapitre'])
        episodes_str = str(row['Épisodes'])
        episodes = []
        for ep in episodes_str.split(', '):
            if ep.startswith('Episode ') and not any(x in ep for x in ['of', 'East', 'Blue']):
                ep_num = ep.split('Episode ')[1]
                episodes.append(ep_num)
        chapter_to_episodes[chapter] = episodes
    
    # Créer les données pour chaque volume
    for volume in range(1, 106):
        chapters = chapters_by_volume.get(volume, [])
        episodes = []
        
        # Récupérer tous les épisodes pour les chapitres de ce volume
        for chapter in chapters:
            if chapter in chapter_to_episodes:
                episodes.extend(chapter_to_episodes[chapter])
        
        # Enlever les doublons et trier
        episodes = sorted(list(set(episodes)), key=int)
        
        volume_data[volume] = {
            'chapters': chapters,
            'episodes': episodes
        }
    
    # Créer le dictionnaire des détails d'épisodes
    episode_details = {}
    
    # Afficher un exemple de ligne pour debug
    print("Exemple de ligne du DataFrame:")
    print(episodes_df.iloc[0])
    
    for _, row in episodes_df.iterrows():
        try:
            episode_num = str(row['Episode_num'])  # Convertir en string pour éviter les problèmes de type
            if episode_num.startswith('Episode '):
                num = episode_num.split('Episode ')[1]
                episode_details[num] = {
                    'title': str(row['Title']) if pd.notna(row['Title']) else 'Titre non disponible',
                    'release_date': str(row['Release_Date']) if pd.notna(row['Release_Date']) else 'Date non disponible',
                    'duration': str(row['Duration']) if pd.notna(row['Duration']) else 'Durée non disponible',
                    'synopsis': str(row['Synopsis']) if pd.notna(row['Synopsis']) else 'Synopsis non disponible'
                }
        except Exception as e:
            print(f"Erreur lors du traitement d'une ligne: {e}")
            continue
    
    return render_template('index.html', volume_data=volume_data, episode_details=episode_details)

@app.route('/episodes')
def episodes_page():
    # Convertir les épisodes en format plus détaillé
    episodes_list = []
    for _, row in episodes_df.iterrows():
        episode = {
            'episode_number': str(row['Episode_Number']).replace('.0', ''),
            'title': str(row['Title']) if pd.notna(row['Title']) else 'Non disponible',
            'screenplay': str(row['Screenplay']) if pd.notna(row['Screenplay']) else 'Non disponible',
            'direction': str(row['Direction']) if pd.notna(row['Direction']) else 'Non disponible',
            'animation': str(row['Animation']) if pd.notna(row['Animation']) else 'Non disponible',
            'art': str(row['Art']) if pd.notna(row['Art']) else 'Non disponible',
            'kanji': str(row['Kanji']) if pd.notna(row['Kanji']) else 'Non disponible',
            'romaji': str(row['Romaji']) if pd.notna(row['Romaji']) else 'Non disponible'
        }
        episodes_list.append(episode)
    
    return render_template('episodes.html', episodes=episodes_list)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    if query:
        filtered_episodes = []
        for _, row in episodes_df.iterrows():
            title = str(row['Title']).lower() if pd.notna(row['Title']) else ''
            episode_num = str(row['Episode_Number']).replace('.0', '')
            
            if query in title or query in episode_num:
                episode = {
                    'episode_number': episode_num,
                    'title': str(row['Title']) if pd.notna(row['Title']) else 'Non disponible',
                    'screenplay': str(row['Screenplay']) if pd.notna(row['Screenplay']) else 'Non disponible',
                    'direction': str(row['Direction']) if pd.notna(row['Direction']) else 'Non disponible',
                    'animation': str(row['Animation']) if pd.notna(row['Animation']) else 'Non disponible',
                    'art': str(row['Art']) if pd.notna(row['Art']) else 'Non disponible',
                    'kanji': str(row['Kanji']) if pd.notna(row['Kanji']) else 'Non disponible',
                    'romaji': str(row['Romaji']) if pd.notna(row['Romaji']) else 'Non disponible'
                }
                filtered_episodes.append(episode)
        return jsonify(filtered_episodes)
    return jsonify([])

@app.route('/api/episode/all')
def get_all_episodes():
    episodes_list = []
    for _, row in episodes_df.iterrows():
        # Ne pas inclure les chapitres si c'est "nan"
        chapters = str(row['Chapter_Numbers']) if pd.notna(row['Chapter_Numbers']) and str(row['Chapter_Numbers']).lower() != 'nan' else ''
        
        episode_data = {
            'episode_number': str(row['Episode_Number']).replace('.0', '') if pd.notna(row['Episode_Number']) else '',
            'title': str(row['Title']) if pd.notna(row['Title']) and str(row['Title']).lower() != 'nan' else '',
            'chapters': chapters
        }
        episodes_list.append(episode_data)
    return jsonify(episodes_list)

@app.route('/api/episode/<episode_number>')
def get_episode_details(episode_number):
    # Vérifier si la colonne existe
    if 'Episode_Number' not in episodes_df.columns:
        print("La colonne Episode_Number n'existe pas!")
        print("Colonnes disponibles:", episodes_df.columns.tolist())
        return jsonify({"error": "Column not found"}), 404
    
    # Ajouter ".0" au numéro d'épisode pour correspondre au format du CSV
    episode_num = str(episode_number) + ".0"
    print(f"Recherche de l'épisode: {episode_num}")
    
    # Chercher l'épisode
    episode = episodes_df[episodes_df['Episode_Number'] == episode_num]
    
    print(f"Résultat de la recherche: {len(episode)} lignes trouvées")
    if not episode.empty:
        episode_data = episode.iloc[0]
        
        # Fonction helper pour vérifier si une valeur est valide
        def clean_value(value, default='Non disponible'):
            if pd.notna(value) and str(value).lower() != 'nan':
                return str(value)
            return default
        
        # Nettoyer et dédupliquer les chapitres
        chapters = clean_value(episode_data['Chapters'])
        if chapters != 'Non disponible':
            # Séparer les chapitres (ils sont séparés par ':::')
            chapter_list = chapters.split(':::')
            # Nettoyer chaque chapitre et enlever les doublons
            clean_chapters = []
            seen_chapters = set()
            for chapter in chapter_list:
                # Nettoyer le chapitre
                clean_chapter = chapter.strip()
                if clean_chapter and clean_chapter not in seen_chapters and clean_chapter.lower() != 'nan':
                    clean_chapters.append(clean_chapter)
                    seen_chapters.add(clean_chapter)
            # Rejoindre les chapitres uniques
            chapters = ' ::: '.join(clean_chapters) if clean_chapters else 'Non disponible'
        
        return jsonify({
            "found": True,
            "title": clean_value(episode_data['Title']),
            "episode_number": episode_number,
            "screenplay": clean_value(episode_data['Screenplay']),
            "direction": clean_value(episode_data['Direction']),
            "animation": clean_value(episode_data['Animation']),
            "art": clean_value(episode_data['Art']),
            "chapters": chapters,
            "kanji": clean_value(episode_data['Kanji']),
            "romaji": clean_value(episode_data['Romaji'])
        })
    else:
        print(f"Épisode {episode_num} non trouvé")
        return jsonify({"found": False})

if __name__ == '__main__':
    app.run(debug=True)