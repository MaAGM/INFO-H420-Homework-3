"""Notification Discord via webhook."""
import requests


def notify_paper_processed(webhook_url: str, title: str, category: str,
                           filename: str, summary: str) -> None:
    """Envoie un message Discord pour un article traité. Ne fait rien si l'URL est vide."""
    if not webhook_url:
        return
    payload = {
        "embeds": [{
            "title": f"Nouvel article traité : {title}"[:256],
            "description": summary[:1000],
            "color": 0x2ECC71,
            "fields": [
                {"name": "Catégorie", "value": category[:1000] or "-", "inline": True},
                {"name": "Fichier", "value": filename[:1000], "inline": True},
            ],
        }]
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
