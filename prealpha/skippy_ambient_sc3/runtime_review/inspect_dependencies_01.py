from pathlib import Path
import json
p=Path(__file__).with_name('verify_01.py')
prefix=p.read_text().split('native=Resource(N)')[0]
exec(prefix)
comments=W/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/phases/mq007_gameplay_comments.questphase.json'
r=Resource(comments);nodes=r.nodes(r.graph);edges=r.edges(r.graph)
seen={0}
while True:
    nxt=seen|{c for a,b,c,d in edges if a in seen}
    if nxt==seen:break
    seen=nxt
print('INPUTS',[(i,n.get('socketName')) for i,n in nodes.items() if n['$type']=='questInputNodeDefinition'])
print('ITEM_MANAGERS',[(i,i in seen,n['$type'],[v for v in walk(n) if 'Item' in v.get('$type','')]) for i,n in nodes.items() if 'Item' in str(n) and 'Manager' in n['$type']])
for i,n in nodes.items():
    if 'sceneFile' in n and 'mq007_04' in str(n['sceneFile']):
        print('RETURN',i,[e for e in sorted(edges) if e[2]==i])
for i in [53,55,57,59,76]:
    print('RETURN_GUARD',i,nodes[i].get('condition'))
native=Resource(N);nn=native.nodes(native.graph);ambient=native.deref(nn[3]['phaseGraph']);an=native.nodes(ambient)
print('AMBIENT_EXTERNAL_PHASES',[(i,n.get('phaseResource'),[e for e in sorted(native.edges(ambient)) if e[2]==i]) for i,n in an.items() if 'phaseResource' in n])
print('SAVED_EMO',load(F)['facts'].get('mq007_skippy_goes_emo'))
