"""Read native capture pairs; classify conservatively, never perform a restore."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/gig_restoration/rollout_r2'
TOWER=('PostTowerFreeRoamActive','q307_done','q307_finished','q307_2079','q307_main_game_killed')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def classify_markers(f):
    if all(f.get(k)==0 for k in TOWER):return 'PRE_TOWER'
    if all(f.get(k)==1 for k in TOWER):return 'POST_TOWER'
    return 'UNKNOWN_WORLD'
def completed_captures(paths,fingerprint):
    rows=[]
    for p in paths:
        for line in Path(p).read_text(encoding='utf-8-sig').splitlines():
            try:r=json.loads(line)
            except json.JSONDecodeError:continue
            if r.get('event')!='CAPTURE_COMPLETE':continue
            d=r.get('detail',{})
            if d.get('stable') is not True or d.get('selected_count')!=71 or d.get('whitelist')!='ignore_two_year_gap' or d.get('catalogue_fingerprint')!=fingerprint or d.get('errors') not in ({},[]):continue
            rows.append({'source':str(p),'source_sha256':sha(p),'utc':r['utc'],'capture_id':r['capture_id'],'world':classify_markers(d['facts']),'snapshot':d})
    return rows
def assess(job,pre,post):
    path=job['journal_path'];a=pre['journal'];b=post['journal']
    def state(j,p):
        e=j.get(p,{});return e.get('state') if e.get('present') is True else None
    ar,br=state(a,path),state(b,path)
    out={'id':job['id'],'title':job['selected_title'],'pre_root':ar,'post_root':br,'runtime_admitted':False}
    if ar==3 or br==3:return out|{'classification':'PRESERVE_COMPLETED','reason':'Succeeded journal, never restart or replay reward.'}
    if ar==4:return out|{'classification':'PRESERVE_PRIOR_FAILURE','reason':'Failed before ending; not a Tower-cleanup restoration.'}
    entries=[e for e in job['journal_entries'] if e['className'] in ('gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective')]
    if any(state(a,e['path']) not in (1,2,3,4) or state(b,e['path']) not in (1,2,3,4) for e in entries):
        return out|{'classification':'UNKNOWN_REFUSE','reason':'Missing/undefined/failed native state read.'}
    prefixes=(job['id'],job['id'].removeprefix('sts_'),'_'.join(job['id'].split('_')[-2:]))
    failfacts=[f for f in job['fact_names'] if 'fail' in f.lower() and f.startswith(prefixes)]
    if any(pre['facts'].get(f) not in (0,) or post['facts'].get(f) not in (0,) for f in failfacts):
        return out|{'classification':'FAILURE_OR_UNKNOWN_REFUSE','reason':'Native failure marker is nonzero or unresolved.'}
    objectives=[e for e in entries if e['className']=='gameJournalQuestObjective']
    if ar==1 and br==1 and objectives and all(state(a,e['path'])==state(b,e['path'])==1 for e in objectives):
        return out|{'classification':'FRESH_JOURNAL_BASELINE_NATIVE_UNLOCK_REVIEW_PENDING','reason':'Native inactive pre/post baseline; start-fact semantics and exact eligibility still require source review.'}
    active=[e['path'] for e in objectives if state(a,e['path'])==2]
    if ar==2 and br==4 and active and all(state(b,e['path'])==(4 if state(a,e['path'])==2 else state(a,e['path'])) for e in entries):
        return out|{'classification':'STARTED_TOWER_CLEANUP_PATTERN_STAGE_ADAPTER_REQUIRED','active_before':active,'reason':'Preserve stage/terminal children. Not permission to run normal initialization.'}
    if br==4:return out|{'classification':'POST_FAILURE_UNKNOWN_REFUSE','reason':'Does not match the audited cleanup transform; do not erase genuine failure.'}
    return out|{'classification':'UNSUPPORTED_OR_CHANGED_STAGE_REFUSE','reason':'No supported native-stage adapter; no guessed reset.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('logs',nargs='+',type=Path);args=p.parse_args()
    catalogue=json.loads((OUT/'catalogue.json').read_text())
    captures=completed_captures(args.logs,catalogue['fingerprint'])
    pre=[x for x in captures if x['world']=='PRE_TOWER'];post=[x for x in captures if x['world']=='POST_TOWER']
    if not pre or not post:raise SystemExit('Need stable native PRE_TOWER and POST_TOWER captures. No restore is authorized by an incomplete pair.')
    pre=pre[-1];post=post[-1]
    jobs=[assess(j,pre['snapshot'],post['snapshot']) for j in catalogue['jobs']]
    result={'status':'NATIVE_PAIR_CLASSIFICATION_NOT_RESTORATION','pair':[pre,post],'jobs':jobs,'game_writes':0,'save_writes':0,'exact_save_ancestry_proven':False,'runtime_admitted_count':0}
    (OUT/'live_pair.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    from collections import Counter
    print(json.dumps(dict(Counter(j['classification'] for j in jobs)),indent=2))
if __name__=='__main__':main()
