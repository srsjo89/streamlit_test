"""위키 점검(lint). 규칙서 11장.

사용법:
  python tools/lint.py            # 점검 결과만 보고
  python tools/lint.py --fix      # 한쪽 방향 링크를 반대쪽 '## 관련'에 자동 추가
"""
import sys
import os
import re
import datetime
from itertools import combinations

sys.path.insert(0, os.path.dirname(__file__))
from wikilib import load_wiki, MANAGE  # noqa: E402

WIKI = os.path.join(os.path.dirname(__file__), "..", "wiki")
TODAY = datetime.date.today()


def main(fix=False):
    pages = load_wiki(WIKI)
    names = set(pages)
    content = {n: p for n, p in pages.items() if n not in MANAGE}

    # 1) 끊어진 링크
    broken = sorted((n, l) for n, p in pages.items() for l in p["links"] if l not in names)

    # 2) 한쪽 방향 링크 (관리 문서 제외)
    oneway = {}
    for a, p in content.items():
        for b in p["links"]:
            if b in content and a not in content[b]["links"]:
                oneway.setdefault(b, set()).add(a)
    if fix and oneway:
        for b, srcs in oneway.items():
            t = open(content[b]["path"], encoding="utf-8").read().rstrip("\n")
            t += "\n" + "\n".join(f"- [[{s}]]" for s in sorted(srcs)) + "\n"
            open(content[b]["path"], "w", encoding="utf-8").write(t)

    # 3) 고아 페이지 (index 외에는 아무도 링크하지 않음)
    inbound = {n: 0 for n in content}
    for a, p in content.items():
        for b in p["links"]:
            if b in inbound and b != a:
                inbound[b] += 1
    orphans = sorted(n for n, c in inbound.items() if c == 0)

    # 4) index.md에 빠진 페이지
    idx = pages.get("index")
    missing_idx = sorted(n for n in content if idx and n not in idx["links"])

    # 5) 중복 후보: 제목·별칭이 겹치는 페이지 쌍
    def keys(p):
        ks = {p["name"].replace("-", " ").lower(), str(p["fm"].get("title", "")).lower()}
        for a in p["fm"].get("aliases", []):
            ks.add(re.sub(r"\s*\[확인필요\]", "", a).strip().lower())
        return {k for k in ks if k}
    dup = []
    for (a, pa), (b, pb) in combinations(content.items(), 2):
        common = keys(pa) & keys(pb)
        if common:
            dup.append((a, b, sorted(common)))

    # 6) 유통기한 지난 페이지
    stale = []
    for n, p in content.items():
        s = str(p["fm"].get("stale_after", ""))
        try:
            if datetime.date.fromisoformat(s) < TODAY:
                stale.append((n, s))
        except ValueError:
            pass

    # 7) 상충 표시가 남은 페이지
    conflicts = sorted(n for n, p in content.items() if "⚠️ 상충" in p["body"])

    # 8) 근거 없는 페이지
    nosrc = sorted(n for n, p in content.items() if not p["fm"].get("sources"))

    print("# Lint 결과", TODAY)
    print(f"- 끊어진 링크: {len(broken)}")
    for n, l in broken:
        print(f"  - {n} → [[{l}]]")
    print(f"- 한쪽 방향 링크: {sum(len(v) for v in oneway.values())}" + (" (자동 수정함)" if fix else ""))
    print(f"- index.md 누락: {missing_idx}")
    print(f"- 고아 페이지: {orphans}")
    print(f"- 중복 후보: {len(dup)}")
    for a, b, c in dup:
        print(f"  - {a} ↔ {b} (겹치는 이름: {', '.join(c)})")
    print(f"- 유통기한 지난 페이지: {stale}")
    print(f"- 상충 표시 남은 페이지: {conflicts}")
    print(f"- 근거(sources) 없는 페이지: {nosrc}")


if __name__ == "__main__":
    main(fix="--fix" in sys.argv)
