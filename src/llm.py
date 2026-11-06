import json

from typing import Any
from openai import OpenAI

MAX_CHARS = 15000  # on ne garde que le début de l'article (titre, résumé, intro)

SYSTEM_PROMPT = (
    "Tu es un assistant qui catalogue des articles de recherche. "
    "Réponds UNIQUEMENT avec un objet JSON valide, sans texte autour, de la forme : "
    '{"title": "titre de l\'article", "summary": "résumé court en 2-4 phrases", '
    '"keywords": ["mot-clé 1", "mot-clé 2"], "category": "une catégorie, ex. Data Engineering"}'
)

REQUIRED_FIELDS = {"title": str, "summary": str, "keywords": list, "category": str}


def validate_metadata(data: Any) -> dict:
    """Vérifie la présence et le type de base des champs requis ; lève ValueError sinon."""
    if not isinstance(data, dict):
        raise ValueError("Le JSON doit être un objet")
    for field, expected in REQUIRED_FIELDS.items():
        if field not in data:
            raise ValueError(f"Champ manquant : {field}")
        if not isinstance(data[field], expected):
            raise ValueError(f"Champ '{field}' : type {expected.__name__} attendu")
    if not all(isinstance(k, str) for k in data["keywords"]):
        raise ValueError("Tous les mots-clés doivent être des chaînes")
    return {field: data[field] for field in REQUIRED_FIELDS}


def _ask_model(client: OpenAI, model: str, text: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Voici le contenu de l'article :\n\n{text[:MAX_CHARS]}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def extract_metadata(markdown: str, base_url: str, model: str) -> dict:
    """Appelle le LLM local et renvoie un dict {title, summary, keywords, category}.

    En cas d'échec de parsing ou de validation, une seule nouvelle tentative est faite.
    """
    client = OpenAI(base_url=base_url, api_key="ollama")  # clé ignorée par Ollama
    last_error: Exception | None = None
    for _attempt in range(2):  # 1 essai + 1 retry
        raw = _ask_model(client, model, markdown)
        try:
            return validate_metadata(json.loads(raw))
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
    raise RuntimeError(f"Réponse LLM invalide après 2 tentatives : {last_error}")
