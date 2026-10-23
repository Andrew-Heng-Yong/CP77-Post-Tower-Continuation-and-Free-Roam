"""Record a revision2 live acquisition/return result from durable S3 JSONL."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('log',type=Path)
    args=ap.parse_args()
    rows=[json.loads(s) for s in args.log.read_text(encoding='utf-8').splitlines() if s.strip()]
    start=[r for r in rows if r['event']=='STARTED']
    finish=[r for r in rows if r['event']=='FINISHED']
    assert len(start)==len(finish)==1 and finish[0]['detail']['pass'] is True
    active=[r for r in rows if r['event']=='STATE_CHANGE' and r['state']['markers']['Active']==1]
    assert active and active[0]['state']['scene'] is True
    required={'PostTowerFreeRoamActive':1,'PTFRP0_DR13':1,'q307_active':0,'q307_done':1,
              'q307_finished':1,'q307_2079':1,'q305_johnny_scene_active':0,'q000_done':1,
              'PTFRSKS1_Enabled':0,'PTFRSKS2_Enabled':0,'PTFRSKS3_Revision':2}
    for r in rows[start[0]['seq']-1:finish[0]['seq']]:
        assert r.get('revision')==2
        assert all(r['state']['facts'][n]==v for n,v in required.items())
    s=finish[0]['state']
    assert s['scene'] is s['workspot'] is s['combat'] is False
    expected={'Ready':1,'Boot':1,'Enabled':0,'SceneRequests':1,'SceneReturns':1,'Completed':1,'Interrupted':0,'Active':0}
    assert s['markers']==expected
    install=json.loads((ROOT/'research/b0_streetkid_scene_load_s3/install_receipt_revision2.json').read_text(encoding='utf-8'))
    assert install['revision']==2
    assert hashlib.sha256(Path(install['additive_files'][0]).read_bytes()).hexdigest().upper()==install['additive_sha256'][0]
    result={'status':'PASS_S3_REVISION2','log':args.log.name,'log_sha256':hashlib.sha256(args.log.read_bytes()).hexdigest().upper(),
            'finished_utc':finish[0]['utc'],'scene_duration_observed_seconds':next(r['elapsed_s'] for r in rows if r['seq']>active[0]['seq'] and r['state'].get('markers',{}).get('Completed')==1)-active[0]['elapsed_s'],
            'markers':expected,'scene':False,'workspot':False,'required_facts_unchanged':True,
            's3_archive_sha256':install['additive_sha256'][0],
            'limitation':'Acquisition/return only; seating, fix nose, exit animation and reflection not validated.'}
    folder=ROOT/'research/b0_streetkid_scene_load_s3/live_revision2_pass'
    folder.mkdir(exist_ok=True)
    # Evidence copy only; never read or copy game saves.
    (folder/args.log.name).write_bytes(args.log.read_bytes())
    (ROOT/'research/b0_streetkid_scene_load_s3/live_revision2_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
