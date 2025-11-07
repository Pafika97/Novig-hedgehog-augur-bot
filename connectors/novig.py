
import os, re, json, requests, pandas as pd

def _try_direct_endpoint():
    url = os.getenv("NOVIG_MARKETS_URL", "").strip()
    if not url:
        return []
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return []

def _extract_json_blobs(html: str):
    blobs = []
    for m in re.finditer(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, flags=re.S):
        try:
            blobs.append(json.loads(m.group(1)))
        except Exception:
            pass
    for m in re.finditer(r'__APOLLO_STATE__\s*=\s*(\{.*?\});', html, flags=re.S):
        try:
            blobs.append(json.loads(m.group(1)))
        except Exception:
            pass
    return blobs

def _markets_from_blobs(blobs):
    rows = []
    def push(m):
        if not isinstance(m, dict):
            return
        title = m.get("name") or m.get("title") or m.get("eventName") or ""
        if not title:
            return
        market_id = m.get("id") or m.get("marketId") or m.get("_id")
        status = m.get("status") or m.get("state")
        selections = m.get("selections") or m.get("outcomes") or []
        if isinstance(selections, dict):
            selections = list(selections.values())
        if isinstance(selections, list):
            out_str = "; ".join([str(x) for x in selections])
        else:
            out_str = str(selections)
        liquidity = m.get("liquidity") or m.get("maxStake") or m.get("availableToBet")
        rows.append({
            "platform": "Novig",
            "market_id": market_id,
            "event": m.get("event") or m.get("league") or m.get("competition"),
            "title": title,
            "status": status,
            "startTime": m.get("startTime") or m.get("kickoff"),
            "liquidity": liquidity,
            "outcomes": out_str
        })

    for blob in blobs:
        node = blob if isinstance(blob, dict) else {}
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
                        if any(k in it for k in ("name","title","eventName")) and any(k in it for k in ("selections","outcomes")):
                            push(it)
                        stack.append(it)
            elif isinstance(cur, dict):
                for v in cur.values():
                    if isinstance(v, (list, dict)):
                        stack.append(v)
    return rows

def fetch_novig_markets(limit=200):
    items = _try_direct_endpoint()
    if not items:
        # попробуем публичную страницу. Доступные рынки обычно внутри приложений /sports или /markets
        urls = [
            "https://novig.us/markets",
            "https://www.novig.us/markets",
            "https://novig.com/markets",
            "https://www.novig.com/markets",
            "https://app.novig.us/",
        ]
        html = ""
        for u in urls:
            try:
                r = requests.get(u, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
                if r.ok and len(r.text) > 1000:
                    html = r.text
                    break
            except Exception:
                continue
        if not html:
            return pd.DataFrame([])
        blobs = _extract_json_blobs(html)
        items = _markets_from_blobs(blobs)

    if items and isinstance(items[0], dict) and "platform" in items[0]:
        df = pd.DataFrame(items[:limit])
    else:
        rows = []
        for m in items[:limit]:
            title = m.get("name") or m.get("title") or m.get("eventName")
            outcomes = m.get("selections") or m.get("outcomes")
            if isinstance(outcomes, list):
                out_str = "; ".join([str(x) for x in outcomes])
            else:
                out_str = str(outcomes)
            rows.append({
                "platform": "Novig",
                "market_id": m.get("id") or m.get("marketId"),
                "event": m.get("event") or m.get("league"),
                "title": title,
                "status": m.get("status") or m.get("state"),
                "startTime": m.get("startTime"),
                "liquidity": m.get("liquidity") or m.get("maxStake"),
                "outcomes": out_str
            })
        df = pd.DataFrame(rows)
    return df
