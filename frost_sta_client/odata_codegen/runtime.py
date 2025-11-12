from typing import Optional, Dict, Any, Tuple
import re
import requests

def _join(base: str, suffix: str) -> str:
    base = base.rstrip('/')
    suffix = suffix.lstrip('/')
    return f"{base}/{suffix}"

def find_odata_endpoint(base_url: str, auth: Any = None, timeout: int = 10) -> Optional[Dict[str, str]]:
    """Detect OData $metadata endpoint for a FROST-Server or accept direct OData URLs.

    Accepts:
      - Base server URL (e.g., http://host:8080/FROST-Server) → tries ODATA_4.01 then ODATA_4.0
      - Direct OData root (e.g., .../ODATA_4.01) → uses that plus $metadata
      - Direct metadata URL (e.g., .../ODATA_4.01/$metadata) → uses as-is

    Returns dict: {'version': '4.01'|'4.0', 'metadata_url': url} or None.
    """
    # Normalize
    base = base_url.rstrip('/')
    headers = {"Accept": "application/xml, application/xml;q=0.9, */*;q=0.8"}

    def _check_and_return(url: str, hinted_version: Optional[str] = None) -> Optional[Dict[str, str]]:
        try:
            resp = requests.get(url, headers=headers, auth=auth, timeout=timeout)
            if resp.status_code != 200:
                return None
            txt = resp.text or ""
            if "<Edmx" not in txt and "<edmx:Edmx" not in txt:
                return None
            # Try to detect version from content if not hinted.
            version = hinted_version
            if version is None:
                m = re.search(r"Version=\"(4\.01|4\.0)\"", txt)
                if m:
                    version = m.group(1)
            # Fallback: infer from path if still unknown
            if version is None:
                if "/ODATA_4.01/" in url or url.endswith("/ODATA_4.01/$metadata"):
                    version = "4.01"
                elif "/ODATA_4.0/" in url or url.endswith("/ODATA_4.0/$metadata"):
                    version = "4.0"
                else:
                    version = "4.01"  # sensible default
            return {"version": version, "metadata_url": url}
        except Exception:
            return None

    # Case A: already $metadata URL
    if base.endswith("/$metadata"):
        info = _check_and_return(base, hinted_version=None)
        if info:
            return info
        return None

    # Case B: direct ODATA_4.x root given
    if base.endswith("/ODATA_4.01") or base.endswith("/ODATA_4.0"):
        if base.endswith("/ODATA_4.01"):
            url = f"{base}/$metadata"
            info = _check_and_return(url, hinted_version="4.01")
            if info:
                return info
        else:
            url = f"{base}/$metadata"
            info = _check_and_return(url, hinted_version="4.0")
            if info:
                return info
        return None

    # Case C: try discovering from base server URL
    candidates = [
        ("4.01", _join(base, "ODATA_4.01/$metadata")),
        ("4.0", _join(base, "ODATA_4.0/$metadata")),
    ]
    for version, url in candidates:
        info = _check_and_return(url, hinted_version=version)
        if info:
            return info
    return None

def fetch_metadata(metadata_url: str, auth: Any = None, timeout: int = 10) -> str:
    headers = {"Accept": "application/xml"}
    resp = requests.get(metadata_url, headers=headers, auth=auth, timeout=timeout)
    resp.raise_for_status()
    return resp.text
