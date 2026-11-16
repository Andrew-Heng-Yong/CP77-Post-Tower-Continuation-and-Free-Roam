"""Pin the current three-case preservation experiment; only workspace writes."""
from pathlib import Path
from hashlib import file_digest
import json,stat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REGISTRY=ROOT/'prealpha/quest_resume_registry_20261112_01'
BASE=ROOT/'prealpha/history_file_loader_hs4_20261112_01'
CASES={'mq007_smartgun':'BASE_ACTIVE','q304_car_retrieval':'EP1_ACTIVE','mq029_tourist':'INACTIVE'}

def sha(p):
    with Path(p).open('rb') as f:return file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,d):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2);f.write('\n')
def plain(p):
    for x in (p,*p.parents):assert not x.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,x

def main():
    out=HERE/'evidence_01';assert not out.exists()
    manifest=BASE/'deployment_01/installed_manifest_01.json'
    assert sha(manifest)=='638948D80D2AEA77BF78F04B70E8C4914E4941A6812B9AA359E004FD326BB38C'
    m=read(manifest);game=Path(m['game_root']);pins={str(manifest):sha(manifest)}
    for row in m['core_files']+m['required_files']:
        p=game/row['path'];plain(p);assert sha(p)==row['sha256'];pins[str(p)]=row['sha256']
    exe=game/'bin/x64/Cyberpunk2077.exe'
    assert sha(exe)=='D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4'
    pins[str(exe)]=sha(exe)
    selected=read(REGISTRY/'checkpoint.json');db=REGISTRY/selected['registry']/'registry.sqlite3'
    expected=read(REGISTRY/'contexts_01/summary.json')['source_registry_sha256']
    assert sha(db)==expected;pins[str(db)]=expected
    snapshot=game/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/snapshot_hs1_20261112T193921Z_151_2.json'
    assert sha(snapshot)=='C1CFCBB5FF3BFB13D718C4FF0735D5A0E22A6C84C434E791F4F89C6C17BD26BE'
    pins[str(snapshot)]=sha(snapshot);rows=[r for r in read(snapshot)['rows'] if r['definition']['id'] in CASES]
    assert len(rows)==3 and all(r['stable'] for r in rows)
    for r in rows:assert r['states'][0]==(1 if CASES[r['definition']['id']]=='INACTIVE' else 2)
    saves=[]
    for slot in ('ManualSave-26','AutoSave-10','AutoSave-11','AutoSave-5'):
        p=Path(m['save_root'])/slot/'sav.dat';meta=p.with_name('metadata.9.json');plain(p);plain(meta)
        saves.append({'slot':slot,'source':str(p),'source_sha256':sha(p),'metadata':str(meta),'metadata_sha256':sha(meta),'summary':read(meta)['Data']['metadata']})
    journals=sorted({p[0] for r in rows for p in r['definition']['journals']})
    facts=sorted({str(p) for r in rows for p in r['definition']['fact_names']}|{'q307_point_of_no_return','q115_point_of_no_return','q307_main_game_killed','q307_ep1_killed','q307_2079','q307_done','q307_finished','q307_active','PTFR_Done','PTFR_Active'})
    out.mkdir();write(out/'inputs.json',{'scope':'Step 3 native-handler preservation qualification; no runtime patch, game launch or save edits.','installed_epoch':m['core_epoch'],'pins':pins,'registry':str(db),'cases':CASES,'snapshot_rows':rows,'saves':saves,'journals':journals,'facts':facts})
    print('Pinned HS4, matching engine, three cases and four historical save bodies.')

if __name__=='__main__':main()
