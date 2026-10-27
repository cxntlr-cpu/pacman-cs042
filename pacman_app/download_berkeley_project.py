"""Download the official starter once, keeping it out of the published repo."""
import hashlib
import io
from pathlib import Path
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "berkeley_pacman"
SOURCE = "https://inst.eecs.berkeley.edu/~cs188/sp26/assets/projects/search.zip"
SHA256 = "d212f664b97ee38548dd868dfc5ce187f1a2147cfb90b0469e4fffe6e0a160c3"
REQUIRED = ("pacman.py", "game.py", "search.py", "searchAgents.py", "layouts/tinyMaze.lay")


def install_archive(data, target=ENGINE):
    """Verify before extraction; never overwrite a student's existing work."""
    target = Path(target)
    if target.exists():
        raise ValueError(f"{target} already exists. Setup never overwrites student work.")
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("The Berkeley download changed. Ask your instructor to update the download checksum.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pacman-setup-", dir=target.parent) as temp:
        stage = Path(temp) / "berkeley"
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                path = Path(item.filename)
                if not path.parts or path.parts[0] != "search" or ".." in path.parts or path.is_absolute():
                    raise ValueError("The download contains an unexpected path.")
                relative = Path(*path.parts[1:])
                if relative == Path("."):
                    continue
                destination = stage / relative
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(item))
        if not all((stage / name).is_file() for name in REQUIRED):
            raise ValueError("The Berkeley starter is incomplete.")
        shutil.move(str(stage), str(target))


def ensure_engine(quiet=False):
    if all((ENGINE / name).is_file() for name in REQUIRED):
        return ENGINE
    if ENGINE.exists():
        raise ValueError("berkeley_pacman is incomplete. Rename that folder to keep a backup, then run install again.")
    if not quiet:
        print("Downloading Berkeley's official starter (once)…", flush=True)
    try:
        with urllib.request.urlopen(SOURCE, timeout=30) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError("The download is unexpectedly large.")
        install_archive(data)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("Could not download Berkeley's starter. Check your internet connection and run install again.") from exc
    return ENGINE
