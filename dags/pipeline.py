from datetime import datetime
from airflow.decorators import dag, task


@dag(
    dag_id="test_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
)
def test_pipeline():
    @task
    def say_hello():
        print("Hello depuis Airflow")
        return "hello"

    @task
    def say_done(message):
        print(f"Tâche 2 a reçu : {message}")

    say_done(say_hello())


test_pipeline()