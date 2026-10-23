"""S3: isolated native service owners; no full quest/root restoration."""
import copy,json
from audit_b0_claire import ROOT, COMMON, read, sha
from audit_b0_deferred_vendors import walk,graph_at,graph_edges,compact_node
from inspect_story_services import BASE,scene_path,nodes,reach
OUT=ROOT/'research/b0_story_services'
DEFAULT=ROOT/'research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json'

def scene_delta(root,key):
    """Independent expected JSON transform, also used for full export equality."""
    r=copy.deepcopy(root);ns=nodes(r)
    if key=='fred':
        # Vanilla Start 2 -> section 96 -> dialogue/workspot, without mq025 setup.
        ns[1]['outputSockets'][0]['destinations']=copy.deepcopy(ns[534]['outputSockets'][0]['destinations'])
        hidden=[(3,1),(3,2)]
    elif key=='charles':hidden=[(5,2)]
    else:hidden=[]
    for nid,idx in hidden:
        ns[nid]['outputSockets'][idx]['destinations']=[]
        ns[nid]['options'][idx]['questCondition']={'HandleId':'S3disabled','Data':{
            '$type':'questLogicalCondition','operation':'AND','conditions':[
                {'HandleId':'S3false'+str(v),'Data':{'$type':'questFactsDBCondition','type':{'HandleId':'S3cmp'+str(v),'Data':{
                    '$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRB0ST_Never','value':v}}}}
                for v in (0,1)]}}
    return r

def main():
    inv=read(BASE/'expanded_service_inventory.json');sites=[]
    specs=[('fred','Coach Fred','wat_lch_melee_01','root/node7/node33/node2','wat_lch_melee_01_default_on',0),
           ('cassius','Cassius Ryder','wat_nid_ripperdoc_01','root/node7/node37','wat_nid_ripperdoc_01_default_on',0),
           ('pepe','Pepe','elcoyote_barman_default','root/node7/node27/node3','elcoyote_barman_default_on',3),
           ('charles','Charles Bucks','wat_kab_ripperdoc_03_ok','root/node10','wat_kab_ripperdoc_03_default_on',0)]
    for key,label,scene,route,gate,entry_target in specs:
        row=next(v for v in inv if v['scene'].endswith('\\'+scene+'.scene'))
        owner=DEFAULT if row['source']=='base\\quest\\default_dialogs.questphase' else BASE/'regional_sources/json'/ (row['source']+'.json')
        assert owner.exists(),owner
        r=read(owner)['Data']['RootChunk'];hs={str(v['HandleId']):v['Data'] for v in walk(r) if 'HandleId'in v and 'Data'in v}
        graphs={}
        def capture(g,rr):
            graphs[rr]={'nodes':[compact_node(h['Data']) for h in g['nodes']],'edges':graph_edges(g,rr,hs)}
            for h in g['nodes']:
                n=h['Data']
                if n.get('phaseGraph'):capture(n['phaseGraph']['Data'],rr+'/node'+str(n['id']))
        capture(graph_at(r,route),route)
        p=scene_path(scene);sr=read(p)['Data']['RootChunk'];changed=scene_delta(sr,key);ns=nodes(changed)
        starts=[e['nodeId']['id']for e in sr['entryPoints'] if e['name']['$value'] not in ['Start 2','sit_test']]
        # Fred's owner requests only default_start; alternate scene entries aren't wired.
        if key=='fred':starts=[1]
        reachable=reach(ns,starts)
        writes={i:compact_node(ns[i]['questNode']['Data']) for i in sorted(reachable)
                if ns[i].get('questNode',{}).get('Data',{}).get('$type')=='questFactsDBManagerNodeDefinition'}
        assert not any(v['factName'].startswith(('mq','sq','q0','q1','q2','q3','sts_')) for w in writes.values()for v in walk(w)if v.get('$type')=='questSetVar_NodeType')
        assert not any('johnny'in str(a).lower() for a in sr.get('actors',[]))
        inner=graph_at(r,row['graph']);ni={h['Data']['id']:h['Data'] for h in inner['nodes']}
        g=graph_at(r,route);outer={h['Data']['id']:h['Data'] for h in g['nodes']}
        ins=[n for n in outer.values() if n['$type']=='questInputNodeDefinition'];outs=[n for n in outer.values() if n['$type']=='questOutputNodeDefinition']
        assert len(ins)==len(outs)==1
        scene_edges=[e for e in graphs[row['graph']]['edges'] if e['destination_node_id']==row['scene_node'] and e['destination_socket']!='Holocall_in']
        assert len(scene_edges)==1
        inner_out=next(n['id'] for n in ni.values() if n['$type']=='questOutputNodeDefinition')
        sites.append({'key':key,'label':label,'prefix':'PTFRB0ST'+key.upper()+'_','source':row['source'],
            'owner_json':str(owner.relative_to(ROOT)),'owner_raw':str(owner.relative_to(ROOT)).replace('json\\','raw\\').removesuffix('.json'),
            'owner_sha256':sha(owner),'scene_json':str(p.relative_to(ROOT)),'scene_raw':str(p.relative_to(ROOT)).replace('json\\','raw\\').removesuffix('.json'),
            'scene_sha256':sha(p),'scene':row['scene'],'scene_location':row['scene_location'],
            'route':route,'inner_route':row['graph'],'phase':int(route.rsplit('node',1)[1]),'input_socket':ins[0]['socketName']['$value'],
            'output_socket':outs[0]['socketName']['$value'],'entry_target':entry_target,'output_node':inner_out,
            'scene_node':row['scene_node'],'scene_edge':scene_edges[0],'gate':gate,'extra_positive':[],
            'scene_copy':key in ['fred','charles'],'graphs':graphs,'reachable':sorted(reachable),
            'scene_audit':{'actors':[a['actorName'] for a in sr.get('actors',[])],'facts':sorted(set(scalars(sr,'factName'))),'fact_writes':writes}})
    OUT.mkdir(exist_ok=True)
    (OUT/'cohort.json').write_text(json.dumps({'common_guards':COMMON,'sites':sites},indent=2)+'\n')
    print('S3 AUDITED',[(s['key'],len(s['reachable'])) for s in sites])

from report_scene_route import scalars
if __name__=='__main__':main()
