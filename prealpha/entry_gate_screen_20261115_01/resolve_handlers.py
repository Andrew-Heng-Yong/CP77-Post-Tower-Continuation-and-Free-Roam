"""Bind saved handler paths to exact installed quest graphs, without game/save writes."""
import hashlib
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'prealpha/phone_support_ph1'))
from model import model

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest().upper()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--with-native',action='store_true')
    args=parser.parse_args()
    out=HERE/('trace_02' if args.with_native else 'trace_01')
    if out.exists():
        raise RuntimeError('Fresh output required')
    out.mkdir()
    manifest=read(ROOT/'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json')
    pins={r['depot']:r['sha256'] for r in read(ROOT/'prealpha/mid_quest_resume_retire_20261115_01/stage_03/pack/readback.json')['members']}
    entries=read(HERE/'sources_01/inventory.json')['entries']
    saved=read(HERE/'saved_01/handlers.json')
    exports={r['depot']:HERE/'saved_01'/(r['id']+'.json') for r in entries}
    if args.with_native:
        prior=read(HERE/'trace_01/binding.json')
        for resource in prior['resources']:
            path=Path(resource['json'])
            assert sha(path)==resource['json_sha256']
            assert pins[resource['depot']]==resource['raw_sha256']
            exports[resource['depot']]=path
        providers=read(HERE/'native_sources_01/providers.json')
        assert len(providers['queries'])==len(providers['hits'])==len({r['depot'] for r in providers['hits']})
        for resource in providers['hits']:
            assert sha(Path(resource['raw']))==resource['sha256']
            assert sha(Path(resource['json']))==resource['json_sha256']
            assert resource['depot'] not in pins
            pins[resource['depot']]=resource['sha256']
            exports[resource['depot']]=Path(resource['json'])
    byid={r['id']:r for r in entries}
    models={}
    pending={}
    blockers=[]

    def graph_for(depot):
        if depot in models:
            return models[depot]
        if depot not in exports:
            if depot not in pins:
                blockers.append({'depot':depot,'reason':'Outside pinned combined archive; needs provider review.'})
                return None
            raw=Path(manifest['archive_source'])/depot
            assert sha(raw)==pins[depot]
            pending[depot]={'depot':depot,'raw_path':str(raw),'sha256':pins[depot],
                            'output':str(out/(hashlib.sha256(depot.encode()).hexdigest()[:20]+'.json'))}
            return None
        models[depot]=model(exports[depot])
        return models[depot]

    def external(node):
        ref=node.get('phaseResource',{}).get('DepotPath',{})
        value=ref.get('$value','0')
        return value if value not in ('0',0,None,'') else None

    for iteration in range(8):
        bound=[]
        for handler in saved['handlers']:
            entry=byid[handler['id']]
            assert handler['route']==entry['saved_prefix'] or handler['route'].startswith(entry['saved_prefix']+'/')
            depot=entry['depot']; gp='root'; steps=[]
            graphs=graph_for(depot)
            complete=True
            for component in handler['route'].split('/')[2:]:
                node=graphs[gp]['nodes'][int(component)]
                assert node['$type']=='questPhaseNodeDefinition'
                ref=external(node)
                steps.append({'depot':depot,'graph':gp,'node':int(component),'external':ref})
                # A nonzero resource binds the actual child; some nodes retain an empty inline stub.
                if ref:
                    depot=ref; gp='root'; graphs=graph_for(depot)
                    if graphs is None:
                        complete=False; break
                else:
                    gp+='/'+component
                    assert gp in graphs
            if not complete:
                continue
            node=graphs[gp]['nodes'][handler['node']]
            if external(node):
                graph_for(external(node))  # Inspect registered parent resources even without child handlers.
            bound.append({**handler,'depot':depot,'graph':gp,'steps':steps,
                          'payload':{k:v for k,v in node.items() if k!='phaseGraph'},
                          'edges':[e for e in graphs[gp]['edges'] if e[0]==handler['node'] or e[2]==handler['node']]})
        if not pending:
            break
        plan=out/f'export_{iteration+1:02}.json'
        batch=list(pending.values()); pending.clear()
        plan.write_text(json.dumps(batch,indent=2)+'\n',encoding='utf-8')
        subprocess.run(['C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe',
                        '-NoLogo','-NoProfile','-File',str(HERE/'export_plan.ps1'),'-Plan',str(plan)],check=True)
        for row in batch:
            exports[row['depot']]=Path(row['output'])
    else:
        raise RuntimeError('Resolution exceeded bounded depth')
    result={'status':'BOUND_SAVED_HANDLERS' if len(bound)==len(saved['handlers']) and not blockers else 'PARTIAL',
            'save_sha256':saved['save_sha256'],'handlers':bound,'blockers':blockers,
            'resources':[{'depot':d,'raw_sha256':pins[d],'json':str(p),'json_sha256':sha(p)} for d,p in exports.items()],
            'limits':['Saved registrations are not a live scheduling simulation or full quest lifecycle audit.',
                      'Root and nested prefab ownership remain separate from handler binding.']}
    (out/'binding.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for row in bound:
        if row['payload']['$type']!='questPhaseNodeDefinition':
            print(json.dumps({k:row[k] for k in ('id','route','node','payload')},separators=(',',':')))
    print(result['status'],len(bound),'handlers,',len(exports),'resources,',len(blockers),'blockers')

if __name__=='__main__':
    main()
