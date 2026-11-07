"""GGeneration of the static HTML page listing the articles."""
import json
from pathlib import Path

TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Research Library</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #222; }
  h1 { margin-bottom: .25rem; }
  .controls { display: flex; gap: .5rem; margin: 1rem 0; }
  .controls input, .controls select { padding: .5rem; font-size: 1rem; }
  .controls input { flex: 1; }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .card h2 { margin: 0 0 .25rem; font-size: 1.15rem; }
  .meta { color: #666; font-size: .85rem; }
  .tag { display: inline-block; background: #eef; border-radius: 999px; padding: .1rem .6rem; margin: .15rem .15rem 0 0; font-size: .8rem; }
  .cat { background: #dfd; }
</style>
</head>
<body>
<h1>Research Library</h1>
<div class="meta" id="count"></div>
<div class="controls">
  <input id="search" type="search" placeholder="Search (title, summary, keywords)...">
  <select id="category"><option value="">All categories</option></select>
</div>
<div id="list"></div>
<script>
const PAPERS = __PAPERS_JSON__;
const list = document.getElementById("list");
const search = document.getElementById("search");
const categorySel = document.getElementById("category");
const count = document.getElementById("count");

[...new Set(PAPERS.map(p => p.category))].sort().forEach(c => {
  const o = document.createElement("option"); o.value = c; o.textContent = c; categorySel.appendChild(o);
});

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}

function render() {
  const q = search.value.trim().toLowerCase();
  const cat = categorySel.value;
  const shown = PAPERS.filter(p =>
    (!cat || p.category === cat) &&
    (!q || [p.title, p.summary, p.filename, ...p.keywords].join(" ").toLowerCase().includes(q)));
  list.replaceChildren();
  shown.forEach(p => {
    const card = el("div", "card");
    card.appendChild(el("h2", "", p.title));
    card.appendChild(el("div", "meta", p.filename));
    card.appendChild(el("p", "", p.summary));
    card.appendChild(el("span", "tag cat", p.category));
    p.keywords.forEach(k => card.appendChild(el("span", "tag", k)));
    list.appendChild(card);
  });
  count.textContent = shown.length + " / " + PAPERS.length + " article(s)";
}
search.addEventListener("input", render);
categorySel.addEventListener("change", render);
render();
</script>
</body>
</html>
"""


def generate_html(papers: list[dict], output_path: str) -> str:
    """Write the HTML page to `output_path` (file) and return its path."""
    payload = json.dumps(papers, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__PAPERS_JSON__", payload)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)
