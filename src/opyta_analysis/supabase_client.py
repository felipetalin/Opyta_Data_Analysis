from __future__ import annotations

import os
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client


def get_client(env_file: Optional[str] = None):
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_ANON_KEY not found")

    return create_client(url, key)


def _rest_url(table: str, select: str, filters: Optional[Dict]) -> str:
    url = os.getenv("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL not found")

    query = {"select": select}
    if filters:
        for key, value in filters.items():
            query[str(key)] = f"eq.{value}"
    encoded_query = urllib.parse.urlencode(query)
    return f"{url.rstrip('/')}/rest/v1/{urllib.parse.quote(table)}?{encoded_query}"


def paginate(sb, table: str, filters: Optional[Dict] = None, select: str = "*", page_size: int = 1000) -> List[dict]:
    all_data = []
    offset = 0
    key = os.getenv("SUPABASE_ANON_KEY")
    if not key:
        raise RuntimeError("SUPABASE_ANON_KEY not found")

    while True:
        url = _rest_url(table, select, filters)
        req = urllib.request.Request(
            url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Range": f"{offset}-{offset + page_size - 1}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                body = res.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase REST query failed for table={table}: HTTP {exc.code} {details}") from exc
        rows = json.loads(body) if body else []
        all_data.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return all_data
