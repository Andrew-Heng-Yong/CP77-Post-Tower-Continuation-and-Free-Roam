"""Read-only installation/rollback preflight. This tool has NO install action.
Writes only a fresh result JSON within QR10. Never changes game files or saves.
"""
from pathlib import Path
import argparse, hashlib, json, os, re, stat, subprocess
H=Path(__file__).resolve().parent
W=H.parents[1]
REL='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/'
EXPECTED={REL+'init.lua',REL+'watch.json'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def contained(root,p):
    root=Path(root).absolute();p=Path(p).absolute()
    assert p.is_relative_to(root),'outside target root'
    cur=p
    while True:
        s=cur.lstat()
        assert not stat.S_ISLNK(s.st_mode)and not(getattr(s,'st_file_attributes',0)&0x400),'reparse/link path refused'
        if cur==root:break
        cur=cur.parent
    assert p.resolve().is_relative_to(root.resolve())

def fresh_output(name):
    # A single leaf under the checked task root; no lexical '..', drive/ADS,
    # separator or nested existing junction can redirect a report write.
    assert isinstance(name,str)and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}',name),'simple fresh QR10 output name required'
    assert not os.path.isreserved(name),'reserved Windows device/path refused'
    contained(W,H)
    out=H/name
    assert out.resolve().is_relative_to(H.resolve()),'output outside resolved task root'
    try:out.lstat()
    except FileNotFoundError:return out
    raise AssertionError('fresh output only')

def validate(manifest,game,expected='before',processes=()):
    assert expected in ('before','after')
    assert not set(processes)&{'Cyberpunk2077','REDlauncher','REDprelauncher'},'game/RED launcher running'
    files=manifest['files'];assert len(files)==2 and {r['path']for r in files}==EXPECTED,'two diagnostic leaves only'
    result=[]
    for row in files:
        target=Path(game)/row['path'];source=Path(row['source'])
        old=W/'prealpha/quest_restoration_qr9/worker_b/addon'/row['path']
        contained(game,target);contained(H,source);contained(W/'prealpha/quest_restoration_qr9',old)
        assert sha(target)==row[expected+'_sha256'],'installed hash differs: '+row['path']
        assert sha(source)==row['after_sha256']and source.stat().st_size==row['bytes'],'candidate mismatch'
        assert sha(old)==row['before_sha256'],'rollback donor mismatch'
        result.append({'path':row['path'],'target_hash':sha(target),'successor_hash':sha(source),'rollback_donor_hash':sha(old)})
    lua=Path(files[0]['source']).parent/'init.lua'
    watch=read(lua.parent/'watch.json')
    assert watch['schema']==2 and watch['version']=='QR10D01'
    assert watch['declared_build']['source_lua_sha256']==sha(lua)
    assert 'NewProxy('not in lua.read_text()and ':RegisterListener('not in lua.read_text()
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--expected',choices=['before','after'],default='before');p.add_argument('--out',required=True);a=p.parse_args()
    out=fresh_output(a.out)
    baseline=read(H/'baseline.json');game=Path(baseline['game_root'])
    manifest=read(H/'manifest_02.json')
    proc=subprocess.check_output(['powershell','-NoProfile','-Command',
        'Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -in @("Cyberpunk2077","REDlauncher","REDprelauncher") } | ForEach-Object { $_.ProcessName }'],text=True).splitlines()
    rows=validate(manifest,game,a.expected,proc)
    pins={}
    for row in baseline['core_files']:
        q=game/row['path'];contained(game,q);assert sha(q)==row['after'];pins[str(q)]=row['after']
    for row in baseline['external_dependencies']:
        q=game/row['path'];contained(game,q);assert sha(q)==row['sha256'];pins[str(q)]=row['sha256']
    for filename,digest in baseline['save_sha256'].items():assert sha(filename)==digest,'save changed since QR10 baseline; refresh evidence, never restore it automatically'
    result={'status':'PASS_READ_ONLY_'+a.expected.upper()+'_PREFLIGHT','expected_installed_state':a.expected,
        'manifest_sha256':sha(H/'manifest_02.json'),'diagnostic_files':rows,'core_and_dependencies_verified':len(pins),
        'saves_verified_unchanged':len(baseline['save_sha256']),'running_game_or_REDlauncher':proc,
        'rollback':'Original QR9B04 donors match exact before hashes; after-state can be validated with --expected after only after separately authorized deployment.',
        'limitations':'No install/rollback executed. No atomic transaction/crash recovery certification. Actual deployment requires a fresh guarded transaction and recovery receipt; do not rerun QR9 absent-target installer.',
        'write_scope':'fresh QR10 result only; no game/save mutations'}
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print({k:v for k,v in result.items()if k in ('status','core_and_dependencies_verified','saves_verified_unchanged')})

if __name__=='__main__':main()
