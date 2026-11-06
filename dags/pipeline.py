from datetime import datetime, timedelta
from airflow.decorators import dag, task

from src.db_manager import init_db

# Configuration globale propre
default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

@dag(
    # Paramètre du DAG généraux, se renseigner sur ça
    # + décorateur de la fonction paper_pipeline() pour qu'Airflow la détecte comme DAG
    dag_id='paper_pipeline',
    default_args=default_args,
    description='Pipeline de test : initialisation SQLite propre (TaskFlow API)',
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False)
def paper_pipeline():

    # Définition des tâches du DAG pour encapsuler la logique de la pipeline
    @task
    def run_init_db():
        init_db()

    # Faire les appels aux tâches ici
    run_init_db()

# Instanciation du DAG pour qu'Airflow le détecte
dag = paper_pipeline()