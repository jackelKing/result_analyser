import re, requests
from urllib.parse import urlparse, parse_qs

def to_direct_url(url: str) -> str | None:
    """Convert any GDrive share link to a direct download URL."""
    if not url or not isinstance(url, str):
        return None
    # Standard /file/d/<id>/view pattern
    m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
    if m:
        fid = m.group(1)
        return f"https://drive.google.com/uc?export=download&id={fid}&confirm=t"
    # ?id=<id> pattern
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "id" in qs:
        fid = qs["id"][0]
        return f"https://drive.google.com/uc?export=download&id={fid}&confirm=t"
    return None

def download_pdf(url: str, dest_path: str) -> bool:
    direct = to_direct_url(url)
    if not direct:
        return False
    try:
        session = requests.Session()
        r = session.get(direct, stream=True, timeout=30)
        # Handle Google's virus-scan warning page for large files
        if "text/html" in r.headers.get("Content-Type", ""):
            # Extract confirmation token
            m = re.search(r'confirm=([0-9A-Za-z_-]+)', r.text)
            if m:
                token = m.group(1)
                fid = re.search(r"id=([a-zA-Z0-9_-]+)", direct).group(1)
                r = session.get(
                    f"https://drive.google.com/uc?export=download&id={fid}&confirm={token}",
                    stream=True, timeout=30
                )
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=32768):
                if chunk:
                    f.write(chunk)
        return True
    except Exception:
        return False
