
import os, re, json, requests, pandas as pd
from bs4 import BeautifulSoup

def _try_direct_endpoint():
    url = os.getenv("HEDGEHOG_MARKETS_URL", "").strip()
    if not url:
        return []
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    try:
        data = r.json()
    except Exception:
        return []
    # попытка нормализовать
    items = []
    if isinstance(data, dict):
        # часто markets под ключами data/markets
        cand_keys = ["markets", "data", "result"]
        for ck in cand_keys:
            node = data.get(ck)
            if isinstance(node, list):
                for m in node:
                    items.append(m)
            elif isinstance(node, dict):
                mk = node.get("markets")
                if isinstance(mk, list):
                    items.extend(mk)
        if not items and "edges" in data:
            for edge in data["edges"]:
                node = edge.get("node", {})
                items.append(node)
    elif isinstance(data, list):
        items = data
    return items

def _extract_json_blobs(html: str):
    blobs = []
    # Next.js preloaded data
    for m in re.finditer(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, flags=re.S):
        try:
            blobs.append(json.loads(m.group(1)))
        except Exception:
            pass
    # Apollo cache
    for m in re.finditer(r'__APOLLO_STATE__\s*=\s*(\{.*?\});', html, flags=re.S):
        js = m.group(1)
        try:
            blobs.append(json.loads(js))
        except Exception:
            pass
    return blobs

def _markets_from_blobs(blobs):
    rows = []
    def push(m):
        if not isinstance(m, dict):
            return
        title = m.get("title") or m.get("name") or m.get("question") or ""
        if not title:
            return
        market_id = m.get("id") or m.get("marketId") or m.get("_id")
        status = m.get("status") or m.get("state")
        outcomes = m.get("outcomes") or m.get("options") or []
        if isinstance(outcomes, dict):
            outcomes = list(outcomes.values())
        if isinstance(outcomes, list):
            out_str = "; ".join([str(x) for x in outcomes])
        else:
            out_str = str(outcomes)
        rows.append({
            "platform": "Hedgehog",
            "market_id": market_id,
            "title": title,
            "status": status,
            "endTime": m.get("endTime") or m.get("expiry") or m.get("expiration"),
            "category": m.get("category"),
            "liquidity": m.get("liquidity") or m.get("tvl") or m.get("volume"),
            "outcomes": out_str
        })

    for blob in blobs:
        # try common places
        for key in ["props", "pageProps", "initialState", "data", "apolloState"]:
            node = blob.get(key) if isinstance(blob, dict) else None
            if isinstance(node, dict):
                # breadth-first search for arrays of dicts with "title"/"name"
                stack = [node]
                seen = set()
                while stack:
                    cur = stack.pop()
                    if id(cur) in seen:
                        continue
                    seen.add(id(cur))
                    if isinstance(cur, list):
                        for it in cur:
                            if isinstance(it, dict):
                                # heuristic: a "market-like" object
                                if any(k in it for k in ("title","name","question")) and any(k in it for k in ("outcomes","options")):
                                    push(it)
                                stack.append(it)
                    elif isinstance(cur, dict):
                        for v in cur.values():
                            if isinstance(v, (list, dict)):
                                stack.append(v)
    return rows

def fetch_hedgehog_markets(limit=200):
    # 1) прямой эндпоинт (если задан)
    items = _try_direct_endpoint()
    if items:
        pass
    else:
        # 2) парсинг публичной страницы
        url = "https://www.hedgehog.markets/markets"
        r = requests.get(url, timeout=30, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        html = r.text
        blobs = _extract_json_blobs(html)
        items = _markets_from_blobs(blobs)

    # Нормализуем в DataFrame
    if items and isinstance(items[0], dict) and "platform" in items[0]:
        df = pd.DataFrame(items)
    else:
        rows = []
        if isinstance(items, list):
            for m in items[:limit]:
                title = m.get("title") or m.get("name") or m.get("question")
                outcomes = m.get("outcomes") or m.get("options")
                if isinstance(outcomes, list):
                    out_str = "; ".join([str(x) for x in outcomes])
                else:
                    out_str = str(outcomes)
                rows.append({
                    "platform": "Hedgehog",
                    "market_id": m.get("id") or m.get("marketId"),
                    "title": title,
                    "status": m.get("status") or m.get("state"),
                    "endTime": m.get("endTime") or m.get("expiry"),
                    "category": m.get("category"),
                    "liquidity": m.get("liquidity") or m.get("tvl") or m.get("volume"),
                    "outcomes": out_str
                })
        df = pd.DataFrame(rows)
    return df
