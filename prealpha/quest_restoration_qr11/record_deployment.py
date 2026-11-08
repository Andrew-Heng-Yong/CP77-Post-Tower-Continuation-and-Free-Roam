"""Read-only real deployment snapshots. Writes fresh QR11/deployment_01 evidence."""
from pathlib import Path
import argparse, datetime, hashlib, json, sys
H=Path(__file__).resolve().parent;W=H.parents[1]
sys.path.insert(0,str(H.parent/'quest_restoration_qr10'))
from capture_baseline import meta,sha
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['before','after']);a=ap.parse_args()
    out=H/'deployment_01';b=read(H/'baseline.json');m=read(H/'diagnostics_manifest_01.json');game=Path(b['game_root']);save=Path(b['save_root'])
    target=out/(a.stage+'.json');assert not target.exists(),'Fresh evidence only'
    if a.stage=='before':
        assert not out.exists(),'Fresh deployment directory only';out.mkdir()
        for p in [W/'docs/knowledge/current-state.md',H/'checkpoint.json']:
            q=out/'documentation_before'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
    else:assert out.is_dir()
    managed={str(game/r['path']):r for r in m['files']}
    protected={}
    for p,digest in b['protected_sha256'].items():
        expected=managed[p]['after']if a.stage=='after'and p in managed else digest
        actual=sha(p);assert actual==expected,('protected drift',p);protected[p]=actual
    saves={str(save/p):sha(save/p)for p,r in meta(save).items()if r['kind']=='file'}
    if a.stage=='before':assert saves==b['save_sha256'],'Save drift: investigate, never restore automatically'
    else:assert saves==read(out/'before.json')['saves_sha256'],'Save bytes changed during deployment'
    result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':a.stage,'protected_sha256':protected,'saves_sha256':saves,
        'game_metadata':meta(game),'save_metadata':meta(save),'QR9_metadata':meta(H.parent/'quest_restoration_qr9'),'QR10_metadata':meta(H.parent/'quest_restoration_qr10'),
        'installer_sha256':sha(H/'deploy_diagnostics.ps1'),'manifest_sha256':sha(H/'diagnostics_manifest_01.json')}
    if a.stage=='after':
        before=read(out/'before.json');wanted={r['path']for r in m['files']}
        changes=sorted(p for p in set(before['game_metadata'])|set(result['game_metadata'])if before['game_metadata'].get(p)!=result['game_metadata'].get(p))
        assert set(changes)==wanted,('unexpected game metadata changes',changes)
        for key in ['save_metadata','QR9_metadata','QR10_metadata']:assert before[key]==result[key],key
        assert result['installer_sha256']==before['installer_sha256']and result['manifest_sha256']==before['manifest_sha256']
        for r in m['files']:assert sha(game/r['path'])==r['after']
        receipt=read(H/'recovery/diagnostics_qr10d01_01/journal.json');j=json.loads(receipt['payload_json'])
        assert hashlib.sha256(receipt['payload_json'].encode()).hexdigest().upper()==receipt['payload_sha256']
        assert j['state']=='INSTALLED_VERIFIED'and j['manifest_sha256']==result['manifest_sha256']
        verification={'status':'PASS_DIAGNOSTICS_DEPLOYMENT_PRESERVATION','game_paths_changed':changes,'saves_byte_equal':len(saves),
            'protected_files_verified':len(protected),'Core':'QR8:02 unchanged','diagnostics':'QR10D01 installed','QR9_QR10_evidence':'metadata unchanged; pinned critical hashes verified',
            'native_callbacks':'UNSUPPORTED_NOT_VERIFIED','live_sampling':'NOT_TESTED','game_launches':0,'save_or_fact_writes':0,'CUA_calls':0,
            'limits':'Full save/protected hashes and complete game/evidence metadata compared; unpinned bulk files not all byte-hashed.'}
        (out/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
        result['verification']=verification
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'stage':a.stage,'protected':len(protected),'saves':len(saves),'status':result.get('verification',{}).get('status','BEFORE_CAPTURED')})
if __name__=='__main__':main()
