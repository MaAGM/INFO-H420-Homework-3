import json

from typing import Any
from openai import OpenAI

MAX_CHARS = 8000  # only the beginning of the article is kept (title, summary, intro)

SYSTEM_PROMPT = (
    "You are an assistant that catalogs research articles. "
    "Respond ONLY with a valid JSON object, without any surrounding text, in the form: "
    '{"title": "article title", "summary": "short summary in 2-4 sentences", '
    '"keywords": ["keyword 1", "keyword 2"], "category": "a category, e.g. Data Engineering"}'
)


REQUIRED_FIELDS = {"title": str, "summary": str, "keywords": list, "category": str}


def validate_metadata(data: Any) -> dict:
    """Verify the presence and basic type of the required fields ; raise ValueError otherwise."""
    if not isinstance(data, dict):
        raise ValueError("The JSON must be an object")
    for field, expected in REQUIRED_FIELDS.items():
        if field not in data:
            raise ValueError(f"Missing field : {field}")
        if not isinstance(data[field], expected):
            raise ValueError(f"Field '{field}' : type {expected.__name__} expected")
    if not all(isinstance(k, str) for k in data["keywords"]):
        raise ValueError("All keywords must be strings")
    return {field: data[field] for field in REQUIRED_FIELDS}



def _ask_model(client: OpenAI, model: str, text: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Here is the content of the article :\n\n{text[:MAX_CHARS]}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=800,
    )
    return response.choices[0].message.content or ""


def extract_metadata(markdown: str, base_url: str, model: str) -> dict:
    """Call the local LLM and return a dict {title, summary, keywords, category}.

    In case of parsing or validation failure, only one additional attempt is made.
    """
    client = OpenAI(base_url=base_url, api_key="ollama", timeout=180, max_retries=0) # Key ignored by Ollama
    last_error: Exception | None = None
    for _attempt in range(2):  # 1 try + 1 retry
        raw = _ask_model(client, model, markdown)
        try:
            return validate_metadata(json.loads(raw))
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
    raise RuntimeError(f"Invalid LLM response after 2 attempts : {last_error}")
