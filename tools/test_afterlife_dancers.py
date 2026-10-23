"""Validate exported native dancer ownership and asynchronous readiness races."""
import itertools
import json
from collections import defaultdict
from pathlib import Path
from audit_world_interactions import walk
from test_radio_memorial import canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_access_r10 import eval_stream, read, sha

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/afterlife_world'

class Model:
    def __init__(self, nn, edges, facts, loaded):
        self.nn=nn;self.facts=dict(facts);self.loaded=dict(loaded)
        self.pending={0};self.time=0;self.deadlines={};self.actions=[];self.edges=defaultdict(list)
        for a,s,b,_ in edges:self.edges[a,s].append(b)

    def settle(self, before=None):
        for _ in range(100):
            progress=False
            for i in sorted(self.pending):
                if i==before:return
                n=self.nn[i];kind=n['$type'];socket='Out'
                if kind=='questPauseConditionNodeDefinition':
                    c=n['condition']
                    if c['$type']=='questTimeCondition':
                        p=c['type'];assert p['$type']=='questRealtimeDelay_ConditionType'
                        assert p['hours']==p['minutes']==p['miliseconds']==0
                        self.deadlines.setdefault(i,self.time+p['seconds'])
                        if self.time<self.deadlines[i]:continue
                        del self.deadlines[i]
                    elif not eval_stream(c,self.facts,self.loaded):continue
                elif kind=='questConditionNodeDefinition':
                    socket='True' if eval_stream(n['condition'],self.facts,self.loaded) else 'False'
                elif kind=='questFactsDBManagerNodeDefinition':
                    p=n['type'];assert p['$type']=='questSetVar_NodeType'
                    f=p['factName'];v=p['value'];self.facts[f]=v if p['setExactValue'] else self.facts.get(f,0)+v
                elif kind=='questSpawnManagerNodeDefinition':
                    for a in n['actions']:
                        p=a['type'];self.actions.append((self.time,p['communityEntryName']['$value'],p['action']))
                else:assert kind=='questInputNodeDefinition',kind
                self.pending.remove(i);self.pending.update(self.edges[i,socket]);progress=True
            if not progress:return
        raise AssertionError('Native graph failed to settle')

    def finish(self):
        self.settle();self.time+=31;self.settle()

def main():
    m=read(BASE/'dancers_manifest.json');root=read(BASE/'dancers_phase.json')['Data']['RootChunk']
    assert len(m['resources'])==1 and sha(Path(m['source_root'])/m['resources'][0])==m['sha256']
    assert not root['phasePrefabs'];assert len(root['graph']['Data']['nodes'])==112
    hh=handles(root)
    for obj in walk(root):
        if 'HandleRefId' in obj:assert str(obj['HandleRefId']) in hh
    nn={k:canonical(v,hh) for k,v in nodes(root).items()};edges=quest_edges(root)[0]
    assert edges=={(a,s,b,'In') for a,s,b in m['edges']}
    assert all(o['factName'].startswith('PTFRAL1_') for o in walk(root) if o.get('$type')=='questSetVar_NodeType')
    assert not any(o.get('$type') in ('questSceneNodeDefinition','questTogglePrefabVariant_NodeTypeParams') for o in walk(root))
    refs=[e['ref'] for e in m['entries']];names=[e['entry'] for e in m['entries']]
    assert names==[f'dancer_{i:02}' for i in range(1,11)]
    original=read(BASE/'hologram_vanilla_registry.json')[0]['community']
    assert all(not s['entryActiveOnStart'] for s in original['entriesInitialState'])
    assert [e['Data']['entryName']['$value'] for e in original['template']['Data']['entries']]==names
    for e in original['template']['Data']['entries']:
        assert e['Data']['characterRecordId']['$value']=='Character.ServiceTubeDancerFemale'
        assert e['Data']['phases'][0]['Data']['phaseName']['$value']=='default'
    for e in m['entries']:
        for n,action in ((e['start']+3,'Reactivate'),(e['start']+8,'Deactivate')):
            actions=nn[n]['actions'];assert len(actions)==1
            p=actions[0]['type'];assert p['action']==action
            assert p['communityEntryName']['$value']==e['entry'] and p['communityEntryPhaseName']['$value']=='default'
            assert p['spawnerReference']['$value']==m['spawner']
    facts=m['guards'];loaded=dict.fromkeys(refs,True)
    negative=0
    for key,value in facts.items():
        for bad in (-1,0,1,2):
            if bad==value:continue
            state=facts|{key:bad};m0=Model(nn,edges,state,loaded);m0.finish();assert not m0.actions;negative+=1
    positive=Model(nn,edges,facts,loaded);positive.settle()
    for t in range(1,31):positive.time=t;positive.settle()
    assert positive.actions==[(e['delay'],e['entry'],'Reactivate') for e in m['entries']]
    for bits in itertools.product((False,True),repeat=10):
        mx=Model(nn,edges,facts,dict(zip(refs,bits)));mx.finish()
        assert {a[1] for a in mx.actions}=={n for n,b in zip(names,bits) if b}
    stream_cases=0
    for ref,name in zip(refs,names):
        mx=Model(nn,edges,facts,loaded);mx.finish();mx.actions.clear();mx.loaded[ref]=False;mx.settle()
        assert mx.actions==[(31,name,'Deactivate')]
        mx.actions.clear();mx.loaded[ref]=True;mx.finish();assert [a[1:] for a in mx.actions]==[(name,'Reactivate')];stream_cases+=1
    # One queued delay must not dispatch after stream-out or guard loss.
    race_cases=0
    for e in m['entries']:
        ref=e['ref'];name=e['entry'];i=e['start']+2
        for badguard in list(facts)+[None]:
            mx=Model(nn,edges,facts,loaded);mx.settle(before=i);mx.time=31;mx.settle(before=i)
            prior=len(mx.actions)
            if badguard is None:mx.loaded[ref]=False
            else:mx.facts[badguard]=1-facts[badguard]
            mx.settle();assert (name,'Reactivate') not in [a[1:] for a in mx.actions[prior:]];race_cases+=1
    # Owner handoff cannot deactivate an original entry after guard loss.
    for key,value in facts.items():
        mx=Model(nn,edges,facts,loaded);mx.finish();mx.actions.clear();mx.facts[key]=1-value;mx.settle()
        assert not mx.actions
        mx.facts[key]=value;mx.finish();assert len(mx.actions)==10
    report=dict(status='PASS_DANCERS_OFFLINE_NOT_LIVE',phase_sha256=m['sha256'],nodes=len(nn),entries=10,negative_guards=negative,independent_stream_combinations=1024,stream_rearm_cases=stream_cases,delay_recheck_races=race_cases,guard_handoff_cases=len(facts),vanilla_stagger=[e['delay'] for e in m['entries']],story_writes=0,scene_starts=0,world_overrides=0)
    (BASE/'dancers_tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
