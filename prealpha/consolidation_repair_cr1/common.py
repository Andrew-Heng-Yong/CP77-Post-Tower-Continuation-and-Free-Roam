"""Workspace-only CR1 build helpers; no game mutation functions."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
WS=HERE.parent.parent
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SAVES=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
PRIOR=WS/'prealpha/sidejobs_s30/candidate_02'
AUDIT=WS/'diagnostics/sidejob_entry_phone_audit_20261026_01'
CANDIDATE=HERE/'candidate_01'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    if not p.is_file():return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest().upper()
def write_new(p,data):
    assert not p.exists(),f'Pinned output exists; use successor: {p}'
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def protected_paths():
    paths={Path(r['path']) for r in read(AUDIT/'baseline_01.json')['files'] if Path(r['path']).is_file() and not Path(r['path']).is_relative_to(SAVES)}
    for rel in ['r6/scripts','archive/pc/mod','r6/tweaks','red4ext/plugins/Codeware/Scripts']:
        paths.update(p for p in (GAME/rel).rglob('*') if p.is_file())
    paths.update(p for p in SAVES.rglob('*') if p.is_file())
    return sorted(paths,key=lambda p:str(p).casefold())
