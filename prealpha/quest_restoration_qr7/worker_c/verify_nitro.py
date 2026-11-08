"""New game-definition authority evidence and a private, unapproved gate experiment.

No production/candidate/resource serialization writes. Fresh JSON evidence only.
"""
from pathlib import Path
import sys,copy,itertools,json,collections
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource,digest
from common import value,walk

ENTRY=r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase'
GLOBAL=r'base\quest\bugfixing\quest_bugfixing.questphase'
STANDALONE=r'base\quest\minor_quests\mq060\mq060.quest'

def path(g,start,end):
    q=collections.deque([(str(start),[])]);seen=set()
    while q:
        i,p=q.popleft()
        if i==str(end):return p
        if i in seen:continue
        seen.add(i)
        q.extend((e[2],p+[e]) for e in g['edges'] if e[0]==i)
    raise AssertionError((start,end,'no route'))

def main():
    out=HERE/'nitro_authority_03';assert not out.exists();out.mkdir()
    regpath=HERE/'startup_01/manifest.json';reg=read(regpath)
    expath=HERE/'resource_exports_01/manifest.json';ex=read(expath)
    rows={r['depot']:r for r in ex['resources']}
    rows.update({r['depot']:r for r in reg['resources']})
    sourcepins=[];objs={};models={};checks=[]
    def check(name,yes,evidence=None):
        checks.append({'check':name,'pass':bool(yes),'evidence':evidence})
        assert yes,name
    for d,r in rows.items():
        if d not in {ENTRY,GLOBAL,STANDALONE,r'base\quest\cyberpunk2077.quest',r'base\quest\cyberpunk2077.questphase',r'base\quest\bugfixing.questphase',r'base\quest\cyberpunk2077.gamedef',r'ep1\quest\ep1_standalone.gamedef'}:continue
        check('Pinned raw and fresh JSON: '+d,sha(r['raw'])==r['raw_sha256'] and sha(r['json'])==r['json_sha256'])
        objs[d]=read(r['json']);models[d]=Resource(objs[d]).normalize();sourcepins.append(r)
    mainroots=[value(x['questFile']['DepotPath']) for x in walk(objs[r'base\quest\cyberpunk2077.gamedef']) if x.get('$type')=='gsmMainQuest']
    ep1roots=[value(x['questFile']['DepotPath']) for x in walk(objs[r'ep1\quest\ep1_standalone.gamedef']) if x.get('$type')=='gsmMainQuest']
    check('Actual main game definition registers only the main Cyberpunk quest',mainroots==[r'base\quest\cyberpunk2077.quest'],mainroots)
    check('Standalone MQ060 is absent from both captured root registries',STANDALONE not in mainroots+ep1roots,ep1roots)
    check('No registry or standalone provider collision in all current archive indexes',all(sum(x['depot']==d for x in reg['resources'])==1 for d in [r'base\quest\cyberpunk2077.gamedef',r'ep1\quest\ep1_standalone.gamedef',STANDALONE]))
    chains=[]
    def chain(d,gp,start,end,ref=None):
        g=models[d]['graphs'][gp];route=path(g,start,end)
        if ref is not None:check('Exact next phase resource '+d+':'+gp+'/'+str(end),g['nodes'][str(end)]['refs']==[ref])
        chains.append({'depot':d,'graph':gp,'start':str(start),'end':str(end),'edges':route,'next_resource':ref})
    chain(r'base\quest\cyberpunk2077.quest','root',0,2,r'base\quest\cyberpunk2077.questphase')
    chain(r'base\quest\cyberpunk2077.questphase','root',0,82)
    chain(r'base\quest\cyberpunk2077.questphase','root/82',2,4,r'base\quest\bugfixing.questphase')
    chain(r'base\quest\bugfixing.questphase','root',0,9,GLOBAL)
    chain(GLOBAL,'root',0,3)
    chain(GLOBAL,'root/3',0,88)
    g=models[GLOBAL]['graphs']['root/3'];gn=g['nodes']
    check('Exact native AND connections 93/104→106→89.Start',all(e in g['edges'] for e in [['88','Out','93','In'],['88','Out','104','In'],['93','Out','106','In1'],['104','Out','106','In2'],['106','Out1','89','Start']]))
    check('Native node106 is AND',gn['106']['type']=='questLogicalAndNodeDefinition')
    native_or=gn['93']['payload']['condition'];native_count=gn['104']['payload']['condition']
    bikes=[x['vehicleName'] for x in walk(native_or) if x.get('$type')=='questVehicleAvailable_ConditionType']
    counter=[x for x in walk(native_count) if x.get('$type')=='questVarComparison_ConditionType']
    check('Registered native selector OR3 exact variants',native_or['operation']=='OR' and bikes==[
        'Vehicle.v_sportbike1_yaiba_kusanagi_player','Vehicle.v_sportbike1_yaiba_kusanagi_player_02','Vehicle.v_sportbike1_yaiba_kusanagi_player_03'])
    check('Registered native purchase prerequisite >=3 exact',counter==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'carbought_counter','value':3}])
    current=models[ENTRY]['graphs']['root'];cn=current['nodes']
    selected_bikes=[x['vehicleName'] for i in ['8','9','10','11'] for x in walk(cn[i]['payload']) if x.get('$type')=='questVehicleAvailable_ConditionType']
    standalone=models[STANDALONE]['graphs']['root']
    check('Current four bike payloads equal standalone donor',all(cn[i]['payload']==standalone['nodes'][i]['payload'] for i in ['8','9','10','11','12']))
    check('Current selector adds Tyger and lacks purchases',len(selected_bikes)==4 and set(selected_bikes)==set(bikes+['Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player']) and not any(x.get('factName')=='carbought_counter' for x in walk(models[ENTRY])))
    native_body=gn['89']['refs'][0]
    check('Both authored routes target the same native body',standalone['nodes']['4']['refs']==[native_body])
    check('Current existing guards execute before the Issued writer',all(e in current['edges'] for e in [['65003','Out','65004','In'],['65004','True','65005','In']]))
    check('Issued writer retains exact existing receipt',cn['65005']['writes'][0]['factName']=='PTFRS29_mq060_nitro_Issued')
    experiment=copy.deepcopy(objs[ENTRY]);r=Resource(experiment)
    donor=Resource(objs[GLOBAL]);donorgraph=donor.d(donor.d(donor.root['graph'])['nodes'][0]) if False else None
    raw_native={str(x['id']):x for x in walk(objs[GLOBAL]) if x.get('id') in [93,104] and 'condition' in x}
    next_handle=max(int(k) for k in r.handles)+1
    def clone_native_handle(obj):
        nonlocal next_handle
        if isinstance(obj,list):return [clone_native_handle(x) for x in obj]
        if not isinstance(obj,dict):return obj
        if 'HandleId' in obj or 'HandleRefId' in obj:
            resolved=donor.d(obj)
            if resolved is None:return None
            hid=next_handle;next_handle+=1
            return {'HandleId':str(hid),'Data':clone_native_handle(resolved)}
        return {k:clone_native_handle(v) for k,v in obj.items()}
    mutated_nodes={str(x['id']):x for x in walk(experiment) if x.get('$type') in ('questPauseConditionNodeDefinition','questConditionNodeDefinition') and str(x.get('id')) in ['65003','65004']}
    for i,n in mutated_nodes.items():
        condition=r.d(n['condition'])
        check('Guard is AND before adding native prerequisites: '+i,condition['operation']=='AND')
        condition['conditions'] += [clone_native_handle(raw_native['93']['condition']),clone_native_handle(raw_native['104']['condition'])]
    proposed=Resource(experiment).normalize()['graphs']['root']
    def correct_guards(graph):
        return all(any(digest(x)==digest(native_or) for x in graph['nodes'][i]['payload']['condition']['conditions']) and
                   any(digest(x)==digest(native_count) for x in graph['nodes'][i]['payload']['condition']['conditions']) for i in ['65003','65004'])
    check('Fail-before: actual current guards do not preserve registered native entry contract',not correct_guards(current))
    check('Private proposal passes exact native guard contract',correct_guards(proposed))
    check('Private proposal preserves all graph edges, saved node IDs and every other payload',proposed['edges']==current['edges'] and proposed['nodes'].keys()==current['nodes'].keys() and all(proposed['nodes'][i]['payload']==current['nodes'][i]['payload'] for i in current['nodes'] if i not in ['65003','65004']))
    fixtures=[]
    for owned in itertools.product([False,True],repeat=4):
        for purchases in range(5):
            original=any(owned[:3]) and purchases>=3
            current_selector=any(owned)
            proposed_selector=current_selector and any(owned[:3]) and purchases>=3
            check('Native/proposed selector semantics match '+str((owned,purchases)),original==proposed_selector)
            fixtures.append({'owned':dict(zip(bikes+['Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player'],owned)),'carbought_counter':purchases,'registered_native':original,'current_standalone_selector':current_selector,'private_proposal':proposed_selector})
    controls=[]
    for nodeid in ['65003','65004']:
        mutant=copy.deepcopy(proposed);mutant['nodes'][nodeid]['payload']['condition']['conditions'].pop()
        controls.append({'mutation':'Remove exact native purchase prerequisite from '+nodeid,'detected':not correct_guards(mutant)})
    registry_mutant=mainroots+[STANDALONE]
    controls.append({'mutation':'Register alternate MQ060 root in copied registry data','detected':registry_mutant!=[r'base\quest\cyberpunk2077.quest']})
    check('All three authority/gate controls detected',all(x['detected'] for x in controls))
    write(out/'private_proposed_resource.json',experiment)
    write(out/'source_pins.json',sourcepins)
    write(out/'evidence.json',{'id':'QR7-MQ060-REGISTERED-ROOT-AUTHORITY','status':'NEW_SOURCE_AUTHORITY_EVIDENCE_REQUIRES_INDEPENDENT_ADJUDICATION',
        'checks':checks,'fixtures':fixtures,'controls':controls,'registered_main_roots':mainroots,'registered_ep1_standalone_roots':ep1roots,
        'registered_route':chains,'native_gate':{'graph':'root/3','nodes':['88','93','104','106','89'],'OR':native_or,'AND_purchase':native_count},
        'source_manifest_pins':[{'path':str(p),'sha256':sha(p)} for p in [regpath,expath]],
        'proposal':{'authority':'Registered main-game root ancestry is executing-owner source evidence. Native standalone file lacks registration in either captured game definition and has no autostart field.',
            'defect':'Current entry preserves an unregistered standalone selector rather than the native gate under the registered retained-session root.',
            'scope':'Proposal only. Add exact native93 OR3 and104 purchases>=3 to current guards65003 and65004, before Issued65005. Keep the original four-bike nodes, all IDs, edges, saved downstream owner and receipts.',
            'risk':'Already-issued owners waiting downstream at the native four-bike selector are deliberately preserved; no retroactive fact/owner rewrite. A policy decision is needed if tightening those owners is desired.',
            'private_json':str(out/'private_proposed_resource.json'),'private_json_sha256':sha(out/'private_proposed_resource.json'),
            'runtime_changes':[]},
        'remaining_evidence_boundary':['Registry membership and registered ancestry are now proven from current unique providers, beyond the old 5136-model reverse census.',
            'Native engine implementation was not universally decompiled. An unnamed hypothetical loader is not concrete contrary source evidence; independent peer must weigh this limit against positive registered-root proof.',
            'A hidden or dynamically registered alternate root has not been observed. Exact current bytecode contains no MQ060 string/resource path; this is bounded evidence, not a universal loader absence proof.',
            'No serialized patch, candidate or game write has occurred. The earlier rejected intersection proposal is not reapproved by this experiment.'],
        'code_sha256':sha(__file__)})
    print({'checks':len(checks),'fixtures':len(fixtures),'divergences':sum(x['registered_native']!=x['current_standalone_selector'] for x in fixtures),'controls':len(controls),'out':str(out)})

if __name__=='__main__':main()
