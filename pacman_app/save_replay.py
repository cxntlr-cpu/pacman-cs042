"""Package real game output as one offline, shareable HTML replay."""
import json
from pathlib import Path

WEB = Path(__file__).parent / "browser"


def save_replay(result, destination):
    destination = Path(destination).expanduser().resolve()
    if destination.suffix.lower() != ".html":
        raise ValueError("Give the replay a filename ending in .html.")
    html = (WEB / "game_viewer.html").read_text(encoding="utf-8")
    css = (WEB / "game_viewer.css").read_text(encoding="utf-8")
    js = (WEB / "game_viewer.js").read_text(encoding="utf-8")
    payload = json.dumps(result, allow_nan=False).replace("<", "\\u003c")
    html = html.replace('<link rel="stylesheet" href="/game_viewer.css">', "<style>" + css + "</style>")
    html = html.replace('<script src="/game_viewer.js" defer></script>', "")
    html = html.replace('</body>', '<script type="application/json" id="replay-data">' + payload + '</script>\n<script>' + js + '</script>\n</body>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    html = "\n".join(line.rstrip() for line in html.splitlines()) + "\n"
    destination.write_text(html, encoding="utf-8")
    return destination
