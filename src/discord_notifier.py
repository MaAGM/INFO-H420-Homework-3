"""Discord notification using webhook."""
import requests


def notify_paper_processed(webhook_url: str, title: str, category: str,
                           filename: str, summary: str) -> None:
    """Send a Discord message for a processed article. Does nothing if the URL is empty."""
    if not webhook_url:
        return
    payload = {
        "embeds": [{
            "title": f"New article processed : {title}"[:256],
            "description": summary[:1000],
            "color": 0x2ECC71,
            "fields": [
                {"name": "Category", "value": category[:1000] or "-", "inline": True},
                {"name": "File", "value": filename[:1000], "inline": True},
            ],
        }]
    }
    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()
