# repo.py — front-end adapter for WordloomFrontend/streamlit
from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests

try:
    from app import API_BASE  # exported by your front-end app.py
except Exception:
    API_BASE = "http://127.0.0.1:8000"  # fallback

@dataclass
class Client:
    api_base: str

    def add_entry(
        self,
        src: str,
        tgt: str,
        ls: str,
        lt: str,
        source_name: str,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "src": src,
            "tgt": tgt,
            "ls": ls,
            "lt": lt,
            "source_name": source_name,
            "created_at": created_at,
        }
        r = requests.post(f"{self.api_base}/entries", json=payload, timeout=15)
        r.raise_for_status()
        try:
            return r.json()
        except Exception:
            return {"status": "ok"}

client = Client(API_BASE)
