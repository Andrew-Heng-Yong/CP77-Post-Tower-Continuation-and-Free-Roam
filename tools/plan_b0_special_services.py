"""Freeze narrow EP1 service owners; exclude roots, initialization and Johnny."""
import json,hashlib
from pathlib import Path
from audit_b0_claire import ROOT,COMMON
from audit_b0_deferred_vendors import walk,graph_at,graph_edges,compact_node
from report_scene_route import scalars
BASE=ROOT/'research/b0_vendor_rollout'
OUT=ROOT/'research/b0_special_services'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    inventory=read(BASE/'expanded_service_inventory.json')
    scene_audit={s['scene']:s for s in read(BASE/'service_scene_audit.json')}
    selected={
      'container_zone/container_zone_vendors':[(4,'Leon'),(19,'Satoshi'),(22,'Costin'),(25,'Susanna'),(28,'Laura'),(33,'Longshore food')],
      'stadium/stadium_vendors':[(10,'Sophia and sons'),(12,'Eron'),(14,'David'),(16,'Michal and Marcin'),(18,'Sammy and security'),(20,'Herold and android'),(22,'Saki'),(62,'Stadium packed food'),(63,'Stadium grilled food'),(64,'Stadium drinks')],
      'monument_av/monument_av_vendors':[(7,'Farida'),(11,'Anderson'),(21,'Odell')]}
    sites=[]
    for name,phases in selected.items():
        source='ep1\\openworld\\vendors\\'+name.replace('/','\\')+'.questphase'
        path=BASE/'expanded_sources/json'/Path(source.replace('\\','/'))
        path=Path(str(path)+'.json');r=read(path)['Data']['RootChunk']
        hs={str(v['HandleId']):v['Data'] for v in walk(r) if 'HandleId'in v and 'Data'in v}
        root_edges=graph_edges(r['graph']['Data'],'root',hs)
        root_nodes={n['Data']['id']:n['Data'] for n in r['graph']['Data']['nodes']}
        for phase,label in phases:
            route='root/node'+str(phase)
            incoming=[e for e in root_edges if e['destination_node_id']==phase]
            assert len(incoming)==1
            gate_node=root_nodes[incoming[0]['source_node_id']]
            gate=next(v for v in walk(gate_node['condition']) if v.get('$type')=='questVarComparison_ConditionType')
            assert gate['comparisonType']=='Greater' and gate['value']==0
            occurrences=[v for v in inventory if v['source']==source and v['graph'].startswith(route+'/')]
            assert len(occurrences)==1
            sc=occurrences[0];audit=scene_audit[sc['scene']]
            assert not any('johnny' in a.lower() for a in audit['actors'])
            graphs={}
            def capture(g,rr):
                graphs[rr]={'nodes':[compact_node(h['Data']) for h in g['nodes']], 'edges':graph_edges(g,rr,hs)}
                for h in g['nodes']:
                    n=h['Data']
                    if 'phaseGraph'in n:capture(n['phaseGraph']['Data'],rr+'/node'+str(n['id']))
            capture(graph_at(r,route),route)
            scene_paths=list(BASE.glob('**/json/'+sc['scene'].replace('\\','/')+'.json'))
            assert len(scene_paths)==1,(sc['scene'],scene_paths)
            prefix=f'PTFRB0SP{len(sites)+1:02}_'
            extra=['ep1_side_content']
            if phase==7 and name.startswith('monument_av'):extra+=['q304_out_of_faridas_clinic']
            if phase==11 and name.startswith('monument_av'):extra+=['sts_ep1_01_vendor_active']
            if phase==21 and name.startswith('monument_av'):extra+=['sts_ep1_01_vendor_active_odel']
            inner_route=sc['graph'];inner_nodes={n['Data']['id']:n['Data'] for n in graph_at(r,inner_route)['nodes']}
            input_node=next(n for n in inner_nodes.values() if n['$type']=='questInputNodeDefinition')
            output_node=next(n for n in inner_nodes.values() if n['$type']=='questOutputNodeDefinition')
            owner_in=next(n for n in graph_at(r,route)['nodes'] if n['Data']['$type']=='questInputNodeDefinition')['Data']['socketName']['$value']
            owner_out=next(n for n in graph_at(r,route)['nodes'] if n['Data']['$type']=='questOutputNodeDefinition')['Data']['socketName']['$value']
            sites.append({'key':sc['scene'].split('\\')[-1].replace('.scene',''),'label':label,'prefix':prefix,'source':source,'owner_json':str(path.relative_to(ROOT)),
              'owner_raw':str(path.relative_to(ROOT)).replace('json\\','raw\\').removesuffix('.json'),
              'owner_sha256':sha(path),'phase':phase,'route':route,'input_socket':owner_in,'output_socket':owner_out,'gate':gate['factName'],'extra_positive':extra,
              'scene':sc['scene'],'scene_json':str(scene_paths[0].relative_to(ROOT)),'scene_sha256':sha(scene_paths[0]),'scene_node':sc['scene_node'],'scene_location':sc['scene_location'],
              'inner_route':inner_route,'input_node':input_node['id'],'output_node':output_node['id'],'graphs':graphs,'scene_audit':audit})
    OUT.mkdir(exist_ok=True)
    (OUT/'cohort.json').write_text(json.dumps({'common_guards':{**COMMON,'q307_ep1_killed':1},'sites':sites},indent=2)+'\n')
    for s in sites:
        writers=[(v['factName'],v.get('value')) for g in s['graphs'].values() for n in g['nodes'] for v in walk(n) if v.get('$type')=='questSetVar_NodeType']
        print(s['prefix'],s['label'],'gate',s['gate'],'extra',s['extra_positive'],'owner writes',sorted(set(writers)), 'scene writes',sorted({v['factName'] for v in s['scene_audit']['fact_writes']}))
if __name__=='__main__':main()
