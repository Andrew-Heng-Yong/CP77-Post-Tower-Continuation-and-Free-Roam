"""Normalize pinned current sources and qualify dialogue via connected scene inputs."""
from pathlib import Path
import collections
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent;WS=HERE.parents[1]
sys.path.insert(0,str(WS/'tools/parity_audit'))
from model import Resource,reachable
from common import walk

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def write(p,d):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2,ensure_ascii=False);f.write('\n')

def main():
    out=HERE/'analysis_01';assert not out.exists();out.mkdir()
    cap=read(HERE/'source_01/manifest.json');assert cap['status']=='PASS_BATCH2_CURRENT_PRIVATE_PROVIDERS' and not cap['issues']
    matches=read(HERE/'matching_01/candidates.json');models={};calls=[]
    for row in cap['resources']:
        assert sha(row['raw'])==row['sha256'] and sha(row['json'])==row['json_sha256']
        resource=Resource(read(row['json']));m=resource.normalize();assert not m['errors'],(row['depot'],m['errors'])
        models[row['depot']]={'source':row,'model':m}
        if row['depot'].endswith('.scene'):continue
        for gp,g in m['graphs'].items():
            for nid,node in g['nodes'].items():
                if node['type']!='questSceneNodeDefinition':continue
                dep=node['payload'].get('sceneFile',{}).get('DepotPath',{}).get('$value')
                if not dep:continue
                incoming=[e for e in g['edges'] if e[2]==nid and e[3]!='CutDestination']
                calls.append({'phase':row['depot'],'phase_sha256':row['sha256'],'graph':gp,'node':nid,'scene':dep,
                              'incoming':incoming,'inputs':sorted({e[3] for e in incoming}),'reachable':nid in g['reachable']})
    scenes=[]
    for dep,row in models.items():
        if not dep.endswith('.scene'):continue
        model=row['model'];g=model['graphs']['scene'];cs=[c for c in calls if c['scene']==dep]
        entries={e for c in cs if c['reachable'] for e in c['inputs'] if e in g['entries']}
        seen=reachable(g['nodes'],g['edges'],[g['entries'][e] for e in entries])
        dialogue=[e for e in matches['dialogue'] if e['depot']==dep]
        for e in dialogue:
            raw=g['nodes'][e['node_id']]['payload']['events'][e['event_ordinal']]
            assert str(raw['id']['id'])==e['event_id'] and str(raw['screenplayLineId']['id'])==e['line_id']
            assert str(raw['startTime'])==e['start_time'] and str(raw['duration'])==e['duration']
        scenes.append({'depot':dep,'source':row['source'],'callers':cs,'called_entries':sorted(entries),'reachable_nodes':sorted(seen),
                       'dialogue_event_keys':[e['item_key'] for e in dialogue if e['node_id'] in seen],
                       'johnny_event_keys':[e['item_key'] for e in dialogue if e['speaker_role']=='JOHNNY' and e['node_id'] in seen],
                       'unqualified_event_keys':[e['item_key'] for e in dialogue if e['node_id'] not in seen],
                       'actors':model['metadata'].get('actors',[]),'playerActors':model['metadata'].get('playerActors',[])})
    write(out/'models.json',models)
    write(out/'scene_callers.json',{'status':'PASS_CURRENT_SOURCE_SCENE_INPUT_MAPPING','scenes':scenes,'phase_calls':calls,
        'limit':'Connected inputs and structural phase reachability. This is not condition feasibility, saved-owner or runtime proof.', 'game_writes':0,'save_writes':0})
    lines=[]
    for dep,row in models.items():
        m=row['model'];lines.append('RESOURCE '+dep)
        for gp,g in m['graphs'].items():
            interesting={n for n,node in g['nodes'].items() if node['type'] in ['questSceneNodeDefinition','questJournalNodeDefinition','questPhaseNodeDefinition'] or
                'johnny' in json.dumps(node['payload']).lower() or any('mq018' in p for p in node['journal_paths'])}
            if dep.endswith('.scene'):
                interesting={n for n,node in g['nodes'].items() if node['type'] in ['scnChoiceNode','scnStartNode','scnEndNode'] or 'johnny' in json.dumps(node['payload'].get('questNode',{})).lower()}
            for nid in sorted(interesting,key=lambda x:int(x)):
                node=g['nodes'][nid];p=node['payload']
                lines.append(gp+'/'+nid+' '+node['type']+' '+json.dumps(p,ensure_ascii=False)[:1000])
                lines.append('  EDGES '+json.dumps([e for e in g['edges'] if e[0]==nid or e[2]==nid]))
    (out/'graph_notes.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'resources':len(models),'scenes':len(scenes),'qualified_johnny':sum(len(s['johnny_event_keys']) for s in scenes),
                      'unqualified_dialogue':sum(len(s['unqualified_event_keys']) for s in scenes),'phase_callers':len(calls)}))

if __name__=='__main__':main()
