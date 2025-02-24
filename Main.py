from flask import Flask, render_template, request
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
    
    # S'assurer que tous les volumes ont une entrée
    for i in range(1, 106):
        volume_data[i] = {
            'chapters': chapters_by_volume.get(i, []),
            'episodes': "Episodes correspondants",
            'volume_number': i  # Ajouter le numéro du volume
        }
    
    return render_template('index.html', volume_data=volume_data)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '').lower()
    if query:
        filtered = [ep for ep in episodes if query in str(ep["title"]).lower()]
        return render_template('search_results.html', episodes=filtered)
    return render_template('search_results.html', episodes=episodes)

if __name__ == '__main__':
    