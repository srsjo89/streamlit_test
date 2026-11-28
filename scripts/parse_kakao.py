"""카카오톡 내보내기 txt → 메시지 JSON + 우선검토 후보 추출.
사용: python3 -I scripts/parse_kakao.py raw/chat/kakao_YYYY-MM-DD.txt out.json [--since YYYY-MM-DD]
"""
import re, sys, json
KW = re.compile(r'관리처분|비례율|분담금|게이트|본계약|사업비|이주|대출|판결|총회|추첨|청산|감정평가|공사비|일정')
OFFICIAL = re.compile(r'위원|감사|직무대행')
pat = re.compile(r'^(\d{4})년 (\d{1,2})월 (\d{1,2})일 (오전|오후) (\d{1,2}):(\d{2}), (.+?) : ', re.M)

def parse(path):
    txt = open(path, encoding='utf-8-sig').read()
    ms = list(pat.finditer(txt)); out = []
    for i, m in enumerate(ms):
        end = ms[i+1].start() if i+1 < len(ms) else len(txt)
        body = txt[m.end():end].strip()
        body = re.sub(r'\n\d{4}년 \d{1,2}월 \d{1,2}일 (오전|오후) \d{1,2}:\d{2}$', '', body)
        body = body.replace('메시지가 삭제되었습니다.', '').strip()
        who = m.group(7)
        if '오픈채팅봇' in who or not body:
            continue
        out.append(dict(date=f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}",
                        who=who, official=bool(OFFICIAL.search(who)), text=body))
    return out

def priority(msg):
    return msg['official'] and len(msg['text']) >= 120 or len(msg['text']) >= 250 \
        or ('한국자산신탁' in msg['text'][:60]) or (KW.search(msg['text']) and len(msg['text']) >= 80)

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    since = sys.argv[sys.argv.index('--since')+1] if '--since' in sys.argv else '0000'
    msgs = [m for m in parse(src) if m['date'] >= since]
    for m in msgs: m['priority'] = bool(priority(m))
    json.dump(msgs, open(dst, 'w'), ensure_ascii=False, indent=1)
    print(len(msgs), 'messages,', sum(m['priority'] for m in msgs), 'priority')
