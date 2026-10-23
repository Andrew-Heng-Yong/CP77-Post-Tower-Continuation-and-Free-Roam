"""Read-only compact graph inspection for S22's bounded Delamain audit."""
from pathlib import Path
import sys, json
WS=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(WS/'tools'))
from analyze_q307 import walk, unwrap, scalar_details, cname

def graphs(path):
    doc=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    handles={str(x['HandleId']):x['Data'] for x,_,_ in walk(doc) if 'HandleId' in x and isinstance(x.get('Data'),dict)}
    def visit(g,label):
        ns=[unwrap(w,handles)[1] for w in g['nodes']]
        owners={unwrap(w,handles)[0]:(n['id'],cname(unwrap(w,handles)[1].get('name'))) for n in ns for w in n.get('sockets',[])}
        es=set()
        for n in ns:
            for w in n.get('sockets',[]):
                s=unwrap(w,handles)[1]
                for cw in s.get('connections',[]):
                    c=unwrap(cw,handles)[1]
                    a=owners.get(unwrap(c.get('source'),handles)[0]);b=owners.get(unwrap(c.get('destination'),handles)[0])
                    if a and b:es.add((a[0],a[1],b[0],b[1]))
        yield label,ns,sorted(es)
        for n in ns:
            child=unwrap(n.get('phaseGraph'),handles)[1]
            if child:yield from visit(child,f'{label}/{n["id"]}')
    yield from visit(unwrap(doc['Data']['RootChunk']['graph'],handles)[1],'root')

if __name__=='__main__':
    path=sys.argv[1];wanted=sys.argv[2] if len(sys.argv)>2 else None
    if path.endswith('.scene.json'):
        from inspect_scene_nodes import pick
        doc=json.loads(Path(path).read_text(encoding='utf-8-sig'))['Data']['RootChunk']
        nodes=[w['Data'] for w in doc['sceneGraph']['Data']['graph']]
        for n in nodes:
            if wanted and wanted not in json.dumps(n):continue
            print(n['nodeId']['id'],n['$type'], 'facts',pick(n,'factName'),'value',pick(n,'value'),'path',pick(n,'realPath'),'name',pick(n,'name'),'OUT',[(s.get('stamp'),s.get('destinations')) for s in n.get('outputSockets',[])])
        print('entrypoints',json.dumps(doc.get('entryPoints')))
        sys.exit()
    for label,ns,es in graphs(path):
        if wanted and label!=wanted:continue
        for n in ns:
            d=scalar_details(n)
            print(label,n['id'],n['$type'],json.dumps(d,separators=(',',':')),'OUT',[(a,b,c,d) for a,b,c,d in es if a==n['id']])
