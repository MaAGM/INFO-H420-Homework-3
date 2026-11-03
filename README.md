# ResearchLibrary - Assignment 3 (INFO-H420)

Pipeline local automatisé avec Apache Airflow pour transformer des fichiers PDF de recherche en une bibliothèque d'études consultable.

## Membres du groupe
- Afzal Moaaz
- Bilal El Mouadden
- Mohammed Amine Gomez Melero

---

## Prérequis
- Python 3.10+
- [Ollama](https://ollama.com/) installé localement avec un modèle compatible configuré pour supporter le mode JSON.

## Résumé du projet et du but de chacun des fichiers:

Le but du programme est le suivant: On a un dossier Google Drive sur lequel on reçoit en continu des pdf, À l'aide de apache airflow notre programme va se lancer tous les x temps et check les nouveaux pdf. 

Pour chaque nouveau pdf, on applique les modifications suivantes:
    - Conversion pdf to md
    - Le md est ensuite donné en input à un llm pour qu'il donne en output un json
    - On ajoute ça dans la base de données sqlite
    - On met à jour le fichier .html et on envoi une notif discord

dags/pipeline.py agit comme un fichier main, apache airflow regardera ce fichier pour oragniser les tâches
model choisi: llama3.2 --> ollama run llama3.2

## TODO
Set up un google drive partagé 