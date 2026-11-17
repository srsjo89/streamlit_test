"""위키 페이지를 읽어 라벨(frontmatter), 링크, 본문을 파싱하는 공통 모듈.
외부 라이브러리 없이 표준 파이썬만 사용한다."""
import os
import re
import glob

LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
MANAGE = {"index", "log", "확인필요"}  # 관리용 문서


def _parse_list(val):
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        return [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
    return [val.strip('"').strip("'")] if val else []


def parse_page(path):
    text = open(path, encoding="utf-8").read()
    fm, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if m:
        raw_fm, body = m.group(1), m.group(2)
        key = None
        for line in raw_fm.split("\n"):
            if re.match(r"^\s+-\s+", line) and key:
                fm.setdefault(key, [])
                if not isinstance(fm[key], list):
                    fm[key] = [fm[key]]
                fm[key].append(re.sub(r"^\s+-\s+", "", line).strip())
                continue
            km = re.match(r"^([^:#\s][^:]*):\s*(.*)$", line)
            if km:
                key, val = km.group(1).strip(), km.group(2)
                val = val.split("  #")[0].strip()
                if key == "aliases":
                    fm[key] = _parse_list(val)
                elif val == "":
                    fm[key] = []
                else:
                    fm[key] = val
    return {
        "path": path,
        "name": os.path.splitext(os.path.basename(path))[0],
        "fm": fm,
        "body": body,
        "text": text,
        "links": set(LINK_RE.findall(text)),
    }


def load_wiki(wiki_dir):
    pages = {}
    for f in glob.glob(os.path.join(wiki_dir, "**", "*.md"), recursive=True):
        p = parse_page(f)
        pages[p["name"]] = p
    return pages


def raw_sources(page):
    """이 페이지가 근거로 삼은 원본 파일 목록 (타임스탬프 제거)."""
    src = page["fm"].get("sources", [])
    if isinstance(src, str):
        src = [src]
    files = set()
    for s in src:
        s = s.strip().strip('"')
        if s.startswith("raw/"):
            files.add(s.split("#")[0])
    return files
