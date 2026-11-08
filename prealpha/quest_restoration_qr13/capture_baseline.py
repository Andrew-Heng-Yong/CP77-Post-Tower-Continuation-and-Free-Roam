"""QR13 input/preservation baseline. No build, game API, install or save write."""
from pathlib import Path
import concurrent.futures,datetime,json,subprocess,sys
H=Path(__file__).resolve().parent;W=H.parents[1]
sys.path.insert(0,str(H.parent/'quest_restoration_qr10'))
from capture_baseline import meta,sha
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SAVE=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    dest=H/'baseline.json';assert not dest.exists()
    epoch_path=H.parent/'quest_restoration_qr8/source_epoch_02.json';epoch=read(epoch_path);c=Path(epoch['candidate'])
    assert epoch['epoch_key']=='QR8:02'
    actual={str(p.relative_to(c/'archive_source')):sha(p)for p in(c/'archive_source').rglob('*')if p.is_file()}
    assert actual==epoch['source_resources'],'QR8 source input drift'
    package={p.relative_to(c/'package').as_posix():sha(p)for p in(c/'package').rglob('*')if p.is_file()}
    assert len(package)==51
    for r in epoch['package_files']:assert package[r['path'].replace('\\','/')]==r['sha256']
    current_path=H.parent/'quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json';current=read(current_path);protected={}
    for r in current['files']+current['required_files']:
        p=GAME/r['path'];expected=r.get('after',r.get('sha256'));assert sha(p)==expected;protected[str(p)]=expected
    sm=meta(SAVE);files=[SAVE/p for p,r in sm.items()if r['kind']=='file']
    with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool:savepins=dict(zip(map(str,files),pool.map(sha,files)))
    prior={n:meta(H.parent/f'quest_restoration_qr{n}')for n in range(3,13)}
    git=['git','-c','safe.directory='+str(W).replace('\\','/')]
    result={'status':'PASS_QR13_BASELINE','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_epoch':str(epoch_path),'source_epoch_sha256':sha(epoch_path),
        'candidate':str(c),'source_resources':actual,'package_files':package,'current_manifest':str(current_path),'current_manifest_sha256':sha(current_path),
        'protected_installed_sha256':protected,'save_sha256':savepins,'save_metadata':sm,'game_metadata':meta(GAME),'QR3_to_QR12_metadata':prior,
        'git_status_before':subprocess.check_output(git+['status','--short'],cwd=W,text=True),'git_HEAD':subprocess.check_output(git+['rev-parse','HEAD'],cwd=W,text=True).strip(),
        'scope':'QR13 coordinator may change fresh staged source/package only after evidence; never game, installed diagnostics, saves/facts, old candidates, release/publication.'}
    dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (H/'checkpoint.json').write_text(json.dumps({'state':'QR13_TARGETED_SOURCE_INVESTIGATION','baseline':str(dest),'baseline_sha256':sha(dest),'installed':'QR8:02 + validated QR10D01/D00E unchanged',
        'workers':['qr13_ronald','qr13_brendan','qr13_review'],'runtime_changes':0,'staged_successor':None,'no_repeat':['Jinguji/Bullets/Zane','Wilson','Cynthia','D00E'],'next':'Independent source proposals; coordinator-only runtime modifications; cross-review before staging.'},indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'source_payloads':len(actual),'package_paths':len(package),'installed_pins':len(protected),'save_files':len(savepins)})
if __name__=='__main__':main()
