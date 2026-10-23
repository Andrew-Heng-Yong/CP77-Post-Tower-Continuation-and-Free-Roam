"""Read-only installed Claire / vanilla sq024 ownership compatibility audit."""
import json, hashlib, sys
from pathlib import Path
from audit_b0_deferred_vendors import ROOT, walk, compact_node, graph_edges, graph_at
from report_scene_route import scalars
from test_b0_ordinary_vendor_batch import canonical, handles

OUT=ROOT/'research/b0_claire'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    results=[]
    for p in sorted((OUT/'quest_compat_sources/json').rglob('*.json')):
        root=read(p)['Data']['RootChunk'];hs=handles(root)
        rows=[]
        def scan(g,route):
            ns={n['Data']['id']:n['Data']for n in g['nodes']};edges=graph_edges(g,route,hs)
            for i,n in ns.items():
                x={k:v for k,v in n.items()if k not in ('sockets','phaseGraph')}
                facts=list(scalars(x,'factName'))
                if any(f in facts for f in ['claire_default_on','sq024_claire_pissed','sq024_intro_dialogues_done','sq024_claire_meeting_garage_active','sq024_claire_afterlife_done','sq024_hook_done']):
                    incoming=[e for e in edges if e['destination_node_id']==i]
                    outgoing=[e for e in edges if e['source_node_id']==i]
                    near={e['source_node_id']for e in incoming}|{e['destination_node_id']for e in outgoing}
                    rows.append({'route':route,'id':i,'node':compact_node(n),'incoming':incoming,'outgoing':outgoing,
                                 'adjacent':[compact_node(ns[j])for j in sorted(near)]})
                if (n.get('phaseGraph')or{}).get('Data'):scan(n['phaseGraph']['Data'],route+'/node'+str(i))
        scan(root['graph']['Data'],'root')
        results.append({'source':str(p.relative_to(ROOT)),'sha256':sha(p),'rows':rows})
    a=read(OUT/'audit.json')
    native={n['id']:n for n in a['graphs']['root/node4/node19']['nodes']}
    assert native[27]['condition']['Data']['type']['Data']=={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'claire_default_on','value':0}
    assert native[1]['type']=='Terminating'
    # Verify the current installed package, not just the design document.
    receipt=read(OUT/'validation/install_receipt.json')
    installed=[]
    for f in receipt['files']:
        p=Path(f['target']);assert sha(p)==f['sha256'],str(p)
        installed.append({'path':f['path'],'sha256':sha(p)})
    built=read(OUT/'validation/claire_service.questphase.json')['Data']['RootChunk'];bh=handles(built)
    wrapper={n['Data']['id']:n['Data']for n in built['graph']['Data']['nodes']}
    assert (5,'Out1',6,'In') in [(e['source_node_id'],e['source_socket'],e['destination_node_id'],e['destination_socket'])for e in graph_edges(built['graph']['Data'],'root',bh)]
    assert wrapper[6]['type']['Data']['factName']=='PTFRB0CLA_OwnerActive' and wrapper[6]['type']['Data']['value']==0
    gates={v['factName']:(v['comparisonType'],v['value'])for v in walk(wrapper[2])if v.get('$type')=='questVarComparison_ConditionType'}
    assert gates['claire_default_on']==('Greater',0)
    runtime=ROOT/'redscript/PTFR_B0_Claire/ClaireDriver.reds'
    text=runtime.read_text();assert 'q.SetFact(n"claire_default_on"' not in text
    assert 'if q.GetFact(n"PTFRB0CLA_Enabled") == 1 { this.running = false; return; }' in text
    # Explicitly distinguish a vanilla off/on handoff from startup-only suspension.
    assert 'QuestOwns' not in text
    report={'status':'STATIC_AUDIT_COMPLETE','installed_hashes':installed,'resource_audits':results,
      'default_owner_exit':'root/node4/node19: 27 -> 33.Inactive -> 1.Terminating',
      'wrapper_exit_ack':'5.Out1 -> 6.OwnerActive=0 -> 2 guarded wait',
      'wrapper_reentry_gate':gates,'scene_routes':a['scene_routes'],
      'verdict':'Structurally follows vanilla Claire availability handoff; actual restored-quest concurrency not live tested.',
      'prohibited_inference':'Neither working Trade nor the absence of a custom lease proves incompatibility/compatibility with all future quest adapters.'}
    (OUT/'quest_compatibility_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    for r in results:
        writes=[]
        for row in r['rows']:
            n=row['node'];t=n.get('type',{}).get('Data',{})
            if n['$type']=='questFactsDBManagerNodeDefinition':writes.append((row['route'],row['id'],t['factName'],t['value']))
        print(Path(r['source']).name, json.dumps(writes))
    print('PASS: installed hashes; vanilla off/on gate, terminating exit and wrapper re-entry; no installed changes')

if __name__=='__main__':main()
