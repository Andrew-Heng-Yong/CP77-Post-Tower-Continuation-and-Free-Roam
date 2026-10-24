"""Pin the current Tower files against the previous release and installed transactions."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from package_release_v011 import allowed_path

GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
TAG='v0.1.1-prealpha.20261024'
DEST=ROOT/f'release/manifest-{TAG}.json'
OLD=json.loads((ROOT/'release/manifest.json').read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()

old={row['path']:row for row in OLD['files']}
add={
 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua',
 'r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotDataHS1.reds',
 'r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds',
 'r6/scripts/TowerContinued_Housing_H1/HousingDoorH2.reds',
 'r6/scripts/TowerContinued_Housing_H1/HousingEntranceH3.reds',
 'r6/scripts/TowerContinued_Housing_H1/WilsonLeaseH2.reds',
 'r6/scripts/TowerContinued_Loading_LC1/SetupAdaptersLC1.reds',
 'r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds',
}
found={p.relative_to(GAME).as_posix():p for root in [GAME/'archive/pc/mod',GAME/'r6/scripts',GAME/'r6/tweaks',GAME/'bin/x64/plugins/cyber_engine_tweaks/mods'] for p in root.rglob('*') if p.is_file() and allowed_path(p.relative_to(GAME).as_posix())}
assert set(found)==set(old)|add,{'new':sorted(set(found)-set(old)),'missing':sorted(set(old)-set(found))}
assert len(found)==117

proofs={}
for m in ROOT.glob('prealpha/*/candidate_*/install_manifest_01.json'):
 d=json.loads(m.read_text(encoding='utf-8-sig'))
 for f in d['files']:
  proofs.setdefault((f['target'],f['after']),[]).append(str(m.relative_to(ROOT)).replace('\\','/'))
rows=[];changed=[]
for name,p in sorted(found.items()):
 row={'path':name,'sha256':sha(p),'bytes':p.stat().st_size}
 if name not in old or row['sha256']!=old[name]['sha256']:
  assert (name,row['sha256']) in proofs,('Unbound installed modification',name,row['sha256'])
  changed.append(name)
 rows.append(row)
assert len(changed)>=30,(len(changed),changed)
assert sha(GAME/'r6/scripts/TowerContinued_Housing_H1/HousingState.reds')=='9E05BA53C51C0614CF167EDAF75D529CDAECA2FF4D1FEC93C725A4D19B91336B'
assert sha(GAME/'archive/pc/mod/TowerContinued_PreAlpha.archive')=='CFB7F613EC15A934B74984B4C26392E7B4B7AC0A38B2C24067C69A395ACF2744'
output={'release':TAG,'status':'EXPERIMENTAL_PREALPHA_H10_PARTIAL_LIVE_PASS','date':'2026-10-24','components_through':['History Snapshot HS1','Loading Cover LC3','H10 Housing H4'],'previous_release':OLD['release'],'file_count':len(rows),'mod_bytes':sum(x['bytes'] for x in rows),'provenance':{'basis':'Closed current development installation; changed and added files match their installed transaction hashes','changed_or_added':len(changed),'current_full_scc_sha256':'528E0F1BC7A23A6F7CA13BECDC7108C9D8309CCB76FDC65AD3B740B801B1ED78','newest_housing_manifest_sha256':'6304F826E3C68BC040B06F723FC28E8EEF1B3CE0D19C81F4BC213B9F94D4501A','live_evidence':'H10 offer/confirm, payment receipt and owned icon observed in 2026-10-24 19:09-19:16 session logs; physical access, services and reload remain unverified','gameplay_verified_by_packaging':False},'omitted':['Third-party frameworks and unrelated mods','Saved games, generated history snapshots, caches and logs','Research, recovery backups and private diagnostics'],'files':rows}
assert not DEST.exists();DEST.write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest':str(DEST),'sha256':sha(DEST),'files':len(rows),'added':len(add),'changed_or_added':len(changed),'mod_bytes':output['mod_bytes']}))
