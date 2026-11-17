"""위키 구조 지표. ingest할 때마다 돌려서 추세를 본다.

사용법:
  python tools/metrics.py              # 표로 출력
  python tools/metrics.py --label 서선화 --save   # tools/metrics_history.csv에 한 줄 추가

지표 설명은 wiki 밖의 README가 아니라 이 파일 하단 DOC에 있다.
"""
import sys
import os
import re
import csv
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
from wikilib import load_wiki, raw_sources, MANAGE  # noqa: E402

HERE = os.path.dirname(__file__)
WIKI = os.path.join(HERE, "..", "wiki")
HIST = os.path.join(HERE, "metrics_history.csv")


def components(nodes, edges):
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        parent[find(a)] = find(b)
    groups = Counter(find(n) for n in nodes)
    return sorted(groups.values(), reverse=True)


def compute():
    pages = load_wiki(WIKI)
    content = {n: p for n, p in pages.items() if n not in MANAGE}
    # 주제 그래프: 출처 페이지는 모든 페이지와 연결되므로 제외하고 본다
    topical = {n: p for n, p in content.items() if p["fm"].get("type") != "출처"}

    nbr = {n: set() for n in topical}
    edges = set()
    for a, p in topical.items():
        for b in p["links"]:
            if b in topical and b != a:
                nbr[a].add(b)
                nbr[b].add(a)
                edges.add(tuple(sorted((a, b))))
    n = len(topical)
    degs = {k: len(v) for k, v in nbr.items()}
    avg_deg = sum(degs.values()) / n if n else 0
    weak = [k for k, d in degs.items() if d <= 2]
    top = sorted(degs.items(), key=lambda x: -x[1])[:3]
    comps = components(list(topical), edges)

    raws = set()
    multi_src = []
    for k, p in topical.items():
        rs = raw_sources(p)
        raws |= rs
        if len(rs) >= 2:
            multi_src.append(k)

    # 근거 문장 수: 본문에서 (출처: ...) 표기 개수
    evid = {k: len(re.findall(r"\(출처:", p["body"])) for k, p in topical.items()}
    stubs = [k for k, c in evid.items() if c < 2]

    flagged = [k for k, p in topical.items() if "[확인필요]" in p["text"] or "확인필요" in p["body"]]
    open_q = len(re.findall(r"^- \[ \]", pages["확인필요"]["body"], re.M)) if "확인필요" in pages else 0

    types = Counter(p["fm"].get("type", "?") for p in topical.values())

    return {
        "원본수": len(raws),
        "페이지수": n,
        "평균연결수": round(avg_deg, 2),
        "약연결비율": round(len(weak) / n, 2) if n else 0,
        "최대허브점유": round(top[0][1] / (n - 1), 2) if n > 1 else 0,
        "섬개수": len(comps),
        "교차출처비율": round(len(multi_src) / n, 2) if n else 0,
        "스텁비율": round(len(stubs) / n, 2) if n else 0,
        "확인필요페이지비율": round(len(flagged) / n, 2) if n else 0,
        "미해결질문": open_q,
        "_top": top,
        "_comps": comps,
        "_weak": sorted(weak),
        "_stubs": sorted(stubs),
        "_multi": sorted(multi_src),
        "_types": dict(types),
    }


def main():
    m = compute()
    label = sys.argv[sys.argv.index("--label") + 1] if "--label" in sys.argv else ""
    print(f"# 구조 지표 {label}")
    for k, v in m.items():
        if not k.startswith("_"):
            print(f"- {k}: {v}")
    print(f"- 상위 허브: {m['_top']}")
    print(f"- 섬 크기: {m['_comps']}")
    print(f"- type 분포: {m['_types']}")
    print(f"- 교차출처 페이지: {m['_multi']}")
    print(f"- 스텁 페이지: {m['_stubs']}")
    if "--save" in sys.argv:
        row = {"label": label, **{k: v for k, v in m.items() if not k.startswith("_")}}
        new = not os.path.exists(HIST)
        with open(HIST, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)


DOC = """
지표 정의 (출처 페이지와 index/log/확인필요는 제외하고 계산)
- 평균연결수: 페이지 하나가 연결된 다른 페이지 수의 평균. 높을수록 지식이 엮여 있음.
- 약연결비율: 연결이 2개 이하인 페이지 비율. 높으면 따로 노는 페이지가 많음.
- 최대허브점유: 가장 많이 연결된 페이지가 전체 페이지 중 몇 %와 연결되는지.
  너무 높으면(예: 0.6 이상) 모든 게 한 페이지로 몰림 → 분할 검토.
- 섬개수: 서로 링크로 이어지지 않는 덩어리 수. 업무가 실제로 분리되어 있으면 여러 개가 정상이지만,
  같은 업무인데 섬이 갈라져 있으면 링크 누락.
- 교차출처비율: 원본 2개 이상에서 근거를 받은 페이지 비율. ingest할수록 올라가야 '누적'이 되는 것.
- 스텁비율: 본문 근거(출처 표기)가 2개 미만인 빈약한 페이지 비율.
- 확인필요페이지비율 / 미해결질문: 검수·질문으로 줄여가야 하는 불확실성의 양.
"""

if __name__ == "__main__":
    main()
