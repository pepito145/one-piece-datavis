from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import csv

app = Flask(__name__)

# Lecture du CSV avec pandas pour plus de simplicité
df = pd.read_csv("static/data/onepiece_episode.csv", sep='\t')

# Création de la liste des épisodes
episodes = []
for index, row in df.iterrows():
    try:
        # Extraire le numéro d'épisode
        episode_num = row["Episode_num"]
        if "Episode" in episode_num:
            episode_num = episode_num.split("Episode ")[1].split()[0]
            # Vérifier que c'est bien un nombre
            int(episode_num)  # Test de conversion
            
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
episodes.sort(key=lambda x: int(x["episode_number"]))

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
        # Extraire les numéros d'épisodes (ignorer "Episode of East Blue" etc)
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
    
    return render_template('index.html', volume_data=volume_data)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').lower()
    if query:
        filtered = [ep for ep in episodes if query in str(ep["title"]).lower()]
        return render_template('search_results.html', episodes=filtered)
    return render_template('search_results.html', episodes=episodes)

@app.route('/api/episode/<episode_number>')
def get_episode_details(episode_number):
    # Nettoyer le numéro d'épisode
    episode_number = f"Episode {episode_number}"
    
    # Chercher l'épisode dans le DataFrame
    episode = df[df['Episode_num'] == episode_number].to_dict('records')
    
    if episode:
        return jsonify(episode[0])
    else:
        return jsonify({"error": "Episode not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)