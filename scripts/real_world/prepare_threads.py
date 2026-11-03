"""Reproduce the registered Threads selection; raw posts never enter Git.

This reads the Owner's ignored collection, not the Threads API. Paraphrases
are human-authored separately, before independent gold and model execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict, deque
from pathlib import Path

SEED = "dappgo-threads-2026-11-02-v1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def order(value: str) -> str:
    return sha((SEED + value).encode())


def stratum(text: str) -> tuple[str, str]:
    lines = text.splitlines()[2:]
    main = " ".join(lines).split("The latest delayed quote")[0]
    first = lines[0] if lines else ""
    ticker = first.split(":")[0] if ":" in first else first.split(" 2026-")[0]
    ticker = re.sub(r"What does.*", "", ticker).strip()
    if "The Magnificent Seven, page" in main:
        return "carousel", "TSLA/SPCX" if "page 1" in main else "NVDA/GOOG"
    if "chatgpt dot" in main:
        return "personal", "none"
    if re.search(r"insider|director|share sale|exercises options|holdings|capital management|bought|sells", main, re.I):
        kind = "insider"
    elif re.search(r"earnings|revenue|EPS|profit|income|margin|cash flow|fundraising|equity fundraising", main, re.I):
        kind = "earnings"
    elif re.search(r"prediction|if you invest|if apple grows|worth more|prospects|analysts say|means absolutely|winning the cloud|should investors", main, re.I):
        kind = "opinion"
    else:
        kind = "other_news"
    return kind, ticker


def sample(posts: list[dict], count: int = 30) -> list[dict]:
    certainty = [p for p in posts if p["url"].endswith(("De9xVYqmdev", "De9yipeGUJw"))]
    if len(certainty) != 2 or len({p["url"] for p in posts}) != len(posts):
        raise ValueError("expected two unique media-linked own posts")
    groups = defaultdict(lambda: defaultdict(list))
    for post in posts:
        if post not in certainty:
            kind, ticker = stratum(post["text"])
            groups[kind][ticker].append(post)
    queues = {}
    for kind, tickers in groups.items():
        subs = {t: deque(sorted(ps, key=lambda p: order(p["url"]))) for t, ps in tickers.items()}
        queue = []
        while any(subs.values()):
            for ticker in sorted(subs, key=order):
                if subs[ticker]:
                    queue.append(subs[ticker].popleft())
        queues[kind] = deque(queue)
    selected = list(certainty)
    while len(selected) < count and any(queues.values()):
        for kind in sorted(queues, key=order):
            if queues[kind] and len(selected) < count:
                selected.append(queues[kind].popleft())
    return sorted(selected, key=lambda p: order(p["url"]))


def prepare(source: Path, out: Path) -> list[dict]:
    if (out / "FREEZE.json").exists():
        raise RuntimeError("inputs frozen")
    raw = source / "mcv-threads-dappgo-posts.json"
    posts = json.loads(raw.read_text())["posts"]
    selected = sample(posts)
    ids = {p["url"]: f"O{i:02d}" for i, p in enumerate(selected, 1)}
    population = []
    for post in posts:
        kind, ticker = stratum(post["text"])
        population.append({"url": post["url"], "posted": post["time"], "text_sha256": sha(post["text"].encode()),
                           "post_type": kind, "ticker_stratum": ticker, "selected_id": ids.get(post["url"]),
                           "certainty_media": post["url"].endswith(("De9xVYqmdev", "De9yipeGUJw"))})
    value = {"seed": SEED, "own_input_sha256": sha(raw.read_bytes()), "own_population": len(posts),
             "external_input_sha256": sha((source / "external-selected.jsonl").read_bytes()),
             "own_selected": len(selected), "engagement_metrics": None,
             "collection": "Owner-authorised logged-in browsing, 2026-11-02 LA; Threads search Top ordering; external selection supplied by Claude",
             "search_queries": ["財報 營收", "美股 財報 EPS", "earnings revenue beat EPS", "輝達 蘋果 營收 億美元"],
             "population": population}
    (out / "selection.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print("selected", len(prepare(args.source, args.out)))
