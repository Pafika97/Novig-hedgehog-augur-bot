
import os
import requests
import pandas as pd

THE_GRAPH_GATEWAY = "https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

DEFAULT_FIELDS = """
  id
  marketCreator
  universe
  description
  categories
  endTime
  creationBlockNumber
  volume
  openInterest
  reportingState
  outcomes {
    id
    description
    price
    volume
  }
"""

def fetch_augur_markets(limit=200, api_key=None, subgraph_id=None):
    api_key = api_key or os.getenv("THE_GRAPH_API_KEY", "")
    subgraph_id = subgraph_id or os.getenv("AUGUR_SUBGRAPH_ID", "")
    if not subgraph_id:
        raise RuntimeError("AUGUR_SUBGRAPH_ID is not set")

    url = THE_GRAPH_GATEWAY.format(api_key=api_key, subgraph_id=subgraph_id) if api_key else f"https://api.thegraph.com/subgraphs/id/{subgraph_id}"

    query = f"""
    query {{
      markets(first: {limit}, orderBy: volume, orderDirection: desc) {{
        {DEFAULT_FIELDS}
      }}
    }}
    """
    resp = requests.post(url, json={"query": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("data", {}).get("markets", [])
    rows = []
    for m in items:
        outcomes = m.get("outcomes", []) or []
        outcomes_str = "; ".join([f"{o.get('description','')}@{o.get('price','')}" for o in outcomes])
        rows.append({
            "platform": "Augur",
            "market_id": m.get("id"),
            "title": m.get("description"),
            "categories": " | ".join(m.get("categories") or []),
            "endTime": m.get("endTime"),
            "volume": m.get("volume"),
            "openInterest": m.get("openInterest"),
            "reportingState": m.get("reportingState"),
            "marketCreator": m.get("marketCreator"),
            "outcomes": outcomes_str,
        })
    df = pd.DataFrame(rows)
    return df
