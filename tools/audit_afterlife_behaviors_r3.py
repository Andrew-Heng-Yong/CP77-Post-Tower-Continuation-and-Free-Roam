"""Source roster and available trace audit; no runtime writes or census claims."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'
OUT=BASE/'idles_r3'
LOGS=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Afterlife_Audit')

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    roster=[]
    for r in read(BASE/'population_r2/manifest.json')['entries']:
        roster.append(dict(group='ordinary_R2',entry=r['entry'],community=r['spawner'],record=r['record'],
            configured_allocations=r['quantity'],phase=r['phase'],workspots=r['refs'],
            treatment='Preserve accepted R2; all selected spots statically verified default/unvarianted.'))
    r1=read(BASE/'manifest.json')
    for r in r1['population_branches']:
        if r['role']!='patron':
            roster.append(dict(group='named_R1',entry=r['entry'],community=r['private_spawner'],
                workspots=r['refs'],treatment='Preserve existing exact-workspot owner; no new action.'))
    registry=read(BASE/'patron_vanilla_registry.json')
    community=next(r for r in registry if r['community_index']==3027)
    routes=read(BASE/'population_rules_audit.json')['scene_routes']
    for e in community['entries']:
        d=e['data'];name=e['name']
        actions=[dict(input=r['input'],**a) for r in routes for a in r['actions'] if a.get('communityEntryName')==name]
        phases=[]
        for p in d['phases']:
            p=p['Data'];phases.append(dict(phase=p['phaseName']['$value'],spots=[v['$value'] for tp in p['timePeriods'] for v in tp['spotNodeRefs']]))
        roster.append(dict(group='q005_scene_community',entry=name,record=d['characterRecordId']['$value'],
            possible_source_phases=phases,reachable_actions=actions,
            treatment='R3 repairs existing actor only, using scene1 workspot.' if name.startswith('merc_') else
            'Conditional scene actor; reachable is not concurrent/active. Audit if present; no blanket restoration.'))
    dancers=next(r for r in registry if r['community_index']==2821)
    for e in dancers['entries']:
        roster.append(dict(group='original_dancers',entry=e['name'],record=e['data']['characterRecordId']['$value'],
            treatment='Preserve original ten-entry R1 owner and USER visibility pass; NPC record is native.'))
    for name in ('Claire','Nix'):
        roster.append(dict(group='separate_service_owner',entry=name,treatment='Separate service/scene owner; no changes. Nix presence is USER-pass, not trade/animation proof.'))
    logs=[]
    for name in ('afterlife_20261005T002325Z.jsonl','afterlife_20261005T143247Z.jsonl','afterlife_20261005T145301Z.jsonl'):
        p=LOGS/name;data=p.read_bytes();samples=[];errors=0;actors=defaultdict(list)
        for line in data.splitlines():
            try:r=json.loads(line)
            except (ValueError,UnicodeError):errors+=1;continue
            samples.append(r);t=r.get('look_target',{})
            if t.get('present') and t.get('id'):actors[t['id']].append(dict(utc=r.get('utc'),**t))
        rows=[]
        for key,ss in actors.items():
            rows.append(dict(id=key,record=ss[-1].get('record'),samples=len(ss),
                workspot_true=sum(s.get('in_workspot') is True for s in ss),scene_true=sum(s.get('in_scene') is True for s in ss),
                neither_count=sum(s.get('in_workspot') is False and s.get('in_scene') is False for s in ss),first=ss[0]['utc'],last=ss[-1]['utc']))
        logs.append(dict(file=name,sha256=hashlib.sha256(data).hexdigest().upper(),bytes=len(data),rows=len(samples),
            parse_errors=errors,actors=rows,coverage='looked-at samples only, not all bar actors'))
    report=dict(status='STATIC_ROSTER_AND_AVAILABLE_TRACE_AUDIT_NOT_FULL_LIVE_CENSUS',roster=roster,logs=logs,
        findings=['R2 ordinary entries have source-backed default workspots; no blanket command warranted.',
                  'Four scene1 booth entries use three seated spots and one standing spot in a quest-owned prefab.',
                  'Latest post-R2 trace still samples one original mercenary with neither workspot nor scene.',
                  'Earlier R1 traces contain two distinct frozen mercenary IDs and active workspot/scene witnesses for other actors.',
                  'Remaining conditional scene actors are not established absent or broken by this limited trace.',
                  'Bar-wide read-only R3 diagnostic adds enumeration, attach callbacks, exact booth bindings and 24-second candidate classification.'],
        live_completeness_proven=False)
    (OUT/'behavior_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],roster_rows=len(roster),logs=[dict(file=x['file'],rows=x['rows'],unique_targets=len(x['actors'])) for x in logs]),indent=2))

if __name__=='__main__':main()
