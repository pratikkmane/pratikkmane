"""Rebuild the "Popular repositories" cards in README.md from the GitHub API."""
import json
import os
import re
import textwrap
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "pratikkmane")
COUNT = 4
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"
LANG_COLORS = {
    "Python": "#3572A5", "R": "#198CE7", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Java": "#b07219", "C++": "#f34b7d", "C#": "#178600", "Jupyter Notebook": "#DA5B0B",
    "HTML": "#e34c26", "CSS": "#563d7c", "Go": "#00ADD8", "Vue": "#41b883", "Shell": "#89e051",
}


def fetch_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"},
    )
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def pick(repos):
    keep = [r for r in repos if not r["fork"] and not r["archived"] and r["name"].lower() != USER.lower()]
    keep.sort(key=lambda r: (r["stargazers_count"] + r["forks_count"], r["pushed_at"]), reverse=True)
    return keep[:COUNT]


def card(repo):
    W, H = 420, 176
    name = escape(repo["name"])
    desc = repo["description"] or "No description yet."
    lines = textwrap.wrap(desc, 50)[:2]
    if len(textwrap.wrap(desc, 50)) > 2:
        lines[1] = lines[1].rstrip(".,; ")[:47] + "..."
    text = "".join(
        f'<text x="24" y="{84 + i * 20}" font-family="{F}" font-size="13.5" fill="#94a3b8">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    lang = repo["language"]
    meta, x = "", 24
    if lang:
        color = LANG_COLORS.get(lang, "#818cf8")
        meta += f'<circle cx="{x + 5}" cy="140" r="5" fill="{color}"/><text x="{x + 16}" y="144.5" font-family="{F}" font-size="12.5" fill="#cbd5e1">{escape(lang)}</text>'
        x += 16 + len(lang) * 7.2 + 20
    meta += f'<text x="{x}" y="144.5" font-family="{F}" font-size="12.5" fill="#cbd5e1">&#9733; {repo["stargazers_count"]}</text>'
    x += 46
    meta += f'<text x="{x}" y="144.5" font-family="{F}" font-size="12.5" fill="#cbd5e1">&#10543; {repo["forks_count"]}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{name}">
  <defs><linearGradient id="a" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6366f1"/><stop offset="1" stop-color="#8b5cf6"/></linearGradient></defs>
  <rect x=".75" y=".75" width="{W - 1.5}" height="{H - 9.5}" rx="14" fill="#0f172a" stroke="#1e293b" stroke-width="1.5"/>
  <rect x="24" y="22" width="36" height="36" rx="10" fill="url(#a)"/>
  <path d="M33 33.5a2 2 0 0 1 2-2h4l2.5 3H51a2 2 0 0 1 2 2V48a2 2 0 0 1-2 2H35a2 2 0 0 1-2-2z" fill="none" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/>
  <text x="72" y="46" font-family="{F}" font-size="16" font-weight="700" fill="#f1f5f9">{name}</text>
  {text}
  {meta}
</svg>'''


def main():
    repos = pick(fetch_repos())
    if not repos:
        print("No public repositories to show; leaving README unchanged.")
        return
    assets = os.path.join(ROOT, "assets")
    imgs = []
    for i, repo in enumerate(repos, 1):
        with open(os.path.join(assets, f"repo-{i}.svg"), "w") as f:
            f.write(card(repo))
        imgs.append(
            f'<a href="{repo["html_url"]}"><img width="49%" src="./assets/repo-{i}.svg" alt="{escape(repo["name"])}" /></a>'
        )
    rows = []
    for i in range(0, len(imgs), 2):
        rows.append("&nbsp;".join(imgs[i:i + 2]))
    block = "<!-- REPOS:START -->\n" + "\n<br/>\n".join(rows) + "\n<!-- REPOS:END -->"
    path = os.path.join(ROOT, "README.md")
    s = open(path).read()
    s = re.sub(r"<!-- REPOS:START -->.*?<!-- REPOS:END -->", lambda _: block, s, flags=re.S)
    open(path, "w").write(s)
    print("Updated:", ", ".join(r["name"] for r in repos))


if __name__ == "__main__":
    main()
