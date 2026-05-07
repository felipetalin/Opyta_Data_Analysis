from __future__ import annotations

import os
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


def paginate(sb, table: str, filters: Optional[Dict] = None, select: str = "*", page_size: int = 1000) -> List[dict]:
    all_data = []
    offset = 0
    while True:
        q = sb.table(table).select(select).range(offset, offset + page_size - 1)
        if filters:
            for k, v in filters.items():
                q = q.eq(k, v)
        res = q.execute()
        rows = res.data or []
        all_data.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return all_data
