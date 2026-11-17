"""index.md를 페이지 라벨과 첫 요약 줄로 다시 만든다. (규칙서 12장)

사용법: python tools/build_index.py
- entries: 모든 페이지 경로 (OKF index 규격)
- 본문: type별로 [[링크]] — 한 줄 요약
"""
import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))
from wikilib import load_wiki, MANAGE  # noqa: E402

WIKI = os.path.join(os.path.dirname(__file__), "..", "wiki")
ORDER = ["업무", "프로세스", "규칙", "시스템", "용어", "사업", "기관", "조직", "사람", "출처"]


def summary(p):
    for line in p["body"].split("\n"):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith(">"):
            return re.sub(r"\s*\(출처:[^)]*\)", "", s)
    return ""


def main():
    pages = load_wiki(WIKI)
    content = {n: p for n, p in pages.items() if n not in MANAGE}
    rel = lambda p: os.path.relpath(p["path"], WIKI).replace(os.sep, "/")
    entries = sorted(rel(p) for p in content.values())
    version = "0.1.0"
    old = pages.get("index")
    if old:
        m = re.search(r"^version: (.*)$", old["text"], re.M)
        if m:
            version = m.group(1).strip()
    raws = sorted({s.split("#")[0] for p in content.values() for s in (p["fm"].get("sources") or []) if s.startswith("raw/")})

    out = ["---", "title: 데이터사업팀 지식 위키", f"version: {version}", "entries:"]
    out += [f"  - {e}" for e in entries + ["확인필요.md", "log.md"]]
    out += ["---", "", "# 데이터사업팀 지식 위키", "",
            f"데이터사업팀의 업무, 절차, 규칙, 사업 이력을 모은 위키. 원본 {len(raws)}건, 페이지 {len(content)}개. "
            "`초안` 표시 페이지는 검수 전 내용이다.", ""]
    by_type = {}
    for n, p in content.items():
        by_type.setdefault(p["fm"].get("type", "기타"), []).append(n)
    for t in ORDER + sorted(set(by_type) - set(ORDER)):
        if t not in by_type:
            continue
        out += [f"## {t}"]
        for n in sorted(by_type[t]):
            st = content[n]["fm"].get("status", "")
            mark = "" if st == "검수완료" else " ·초안"
            out.append(f"- [[{n}]]{mark} — {summary(content[n])}")
        out.append("")
    out += ["## 관리", "- [[확인필요]] — 물어볼 질문 목록", "- [[log]] — 작업 일지", ""]
    open(os.path.join(WIKI, "index.md"), "w", encoding="utf-8").write("\n".join(out))
    print(f"index.md 갱신: {len(content)}개 페이지")


if __name__ == "__main__":
    main()
