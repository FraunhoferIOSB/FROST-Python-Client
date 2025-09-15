from typing import Optional, Dict, Any, Tuple
import requests

def _join(base: str, suffix: str) -> str:
    base = base.rstrip('/')
    suffix = suffix.lstrip('/')
    return f"{base}/{suffix}"

def find_odata_endpoint(base_url: str, auth: Any = None, timeout: int = 10) -> Optional[Dict[str, str]]:
    """Try to detect OData endpoint ($metadata) for a FROST-Server.

    Tries ODATA_4.01 first, then ODATA_4.0. Returns dict with
    {'version': '4.01'|'4.0', 'metadata_url': url} or None.
    """
    candidates = [
        ("4.01", _join(base_url, "ODATA_4.01/$metadata")),
        ("4.0", _join(base_url, "ODATA_4.0/$metadata")),
    ]
    headers = {"Accept": "application/xml, application/xml;q=0.9, */*;q=0.8"}
    for version, url in candidates:
        try:
            resp = requests.get(url, headers=headers, auth=auth, timeout=timeout)
            if resp.status_code == 200:
                # Basic sanity check
                txt = resp.text or ""
                if "<Edmx" in txt or "<edmx:Edmx" in txt:
                    return {"version": version, "metadata_url": url}
        except Exception:
            pass
    return None

def fetch_metadata(metadata_url: str, auth: Any = None, timeout: int = 10) -> str:
    headers = {"Accept": "application/xml"}
    resp = requests.get(metadata_url, headers=headers, auth=auth, timeout=timeout)
    resp.raise_for_status()
    return resp.text
