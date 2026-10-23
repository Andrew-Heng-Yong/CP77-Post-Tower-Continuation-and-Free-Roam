"""Read a durable Tower journal trace; native readbacks do not prove HUD/reload."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ep1/quests/main_quest/q307_tomorrow'

def journal(snapshot):
    states={}
    for line in snapshot.get('journal',[]):
        fields=line.split('|')
        if fields[0].startswith(BASE) and len(fields)==4:
            states[fields[0]]=dict(className=fields[1],state=int(fields[2]),hash=int(fields[3]))
    return states

def analyze(path):
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    snapshots=[r for r in rows if r.get('snapshot',{}).get('player_present')]
    assert snapshots,'No player-present snapshots'
    before=snapshots[0]['snapshot'];after=snapshots[-1]['snapshot']
    initial,final=journal(before),journal(after)
    changes=[]
    for name,old in initial.items():
        new=final.get(name)
        if new and old['state']!=new['state']:
            changes.append(dict(path=name,**old,after=new['state']))
    mutable={'gameJournalQuest','gameJournalQuestPhase','gameJournalQuestObjective'}
    progress_changes=[c for c in changes if c['className'] in mutable]
    inactive_failed_changes=[c for c in progress_changes if c['state']!=2]
    fact_changes={k:[v,after.get('facts',{}).get(k)] for k,v in before.get('facts',{}).items()
                  if after.get('facts',{}).get(k)!=v}
    def other(snapshot):
        return {s.split('|')[0]:s.split('|')[1] for s in snapshot.get('other_quests',[]) if '|' in s}
    old_quests,new_quests=other(before),other(after)
    other_changes={k:[v,new_quests.get(k)] for k,v in old_quests.items() if new_quests.get(k)!=v}
    track=[s for s in after.get('journal',[]) if s.startswith('TRACK|')]
    requests=[r['detail'].split('|',1)[1] for r in rows
              if r.get('event')=='NATIVE_STEP' and str(r.get('detail','')).startswith('REQUEST|')]
    active=[name for name,r in final.items() if r['className'] in mutable and r['state']==2]
    return dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=len(rows),
                initial_entries=len(initial),final_entries=len(final),root=final.get(BASE),
                active_progress=active,changes=changes,unexpected_progress_changes=inactive_failed_changes,
                fact_changes=fact_changes,other_quest_changes=other_changes,final_tracking=track,
                requests=requests,all_requests_within_scope=all(p==BASE or p.startswith(BASE+'/') for p in requests),
                no_duplicate_requests=len(requests)==len(set(requests)),
                statuses=[r.get('detail') for r in rows if r.get('event')=='STATUS'],
                errors=[r for r in rows if 'ERROR' in r.get('event','') or r.get('snapshot',{}).get('errors')],
                evidence_limit='This trace does not establish visible HUD/history or cold-reload provenance without user confirmation.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('log',type=Path);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=analyze(args.log)
    text=json.dumps(report,indent=2)+'\n'
    if args.output:
        resolved=args.output.resolve();resolved.relative_to(ROOT.resolve())
        resolved.parent.mkdir(parents=True,exist_ok=True);resolved.write_text(text,encoding='utf-8')
    print(text)
