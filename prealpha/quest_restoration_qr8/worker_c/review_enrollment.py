"""Independent QR8 C review of B's source-confirmed first-enrollment gap."""
from pathlib import Path
import argparse,copy,struct,sys,collections
from prepare import ROOT,HERE,Q7,read,sha,write
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from model import Resource
from common import walk,value

def reach(g,seeds):
    out=set();todo=list(seeds)
    while todo:
        i=todo.pop()
        if i in out:continue
        out.add(i);todo.extend(e[2] for e in g['edges'] if e[0]==i)
    return out

def main(out):
    assert out.resolve().is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
    checks=[];pins=[]
    def ck(n,v,ev=None):checks.append({'check':n,'pass':bool(v),'evidence':ev});assert v,n
    def pin(p,h=None):
        p=Path(p);actual=sha(p);ck('Exact source pin '+p.name,h is None or actual==h);pins.append({'path':str(p.resolve()),'sha256':actual});return p
    source=ROOT/'prealpha/quest_restoration_qr8/worker_b/enrollment_verification_03/evidence.json';e=read(pin(source));models={};docs={}
    for r in e['source_pins']:
        pin(r['raw'],r['raw_sha256']);pin(r['json'],r['json_sha256']);docs[r['depot']]=read(r['json']);models[r['depot']]=Resource(docs[r['depot']]).normalize()
    fresh=read(pin(HERE/'reviews/enrollment_01/current_providers/manifest.json'));provider_checks=[]
    for r in e['source_pins']:
        if r['depot'].startswith('towercontinued'):continue
        candidates=[x for x in fresh['resources'] if x['depot']==r['depot']]
        for x in candidates:pin(x['raw'],x['raw_sha256'])
        matching=[x for x in candidates if x['raw_sha256']==r['raw_sha256']]
        ck('Fresh current provider contains exact native donor '+r['depot'],len(matching)==1)
        provider_checks.append({'depot':r['depot'],'matched_provider':matching[0]['provider'],'sha256':r['raw_sha256'],'all_provider_sha256':[{'provider':x['provider'],'sha256':x['raw_sha256']} for x in candidates]})
    actor=e['actor_provider'];pin(actor['source_pin']['raw'],actor['source_pin']['raw_sha256']);pin(ROOT/actor['json'],actor['json_sha256'])
    ac=[x for x in fresh['resources'] if x['depot']==actor['source_pin']['depot'] and x['raw_sha256']==actor['source_pin']['raw_sha256']]
    ck('Fresh current EP1 actor registry bytes equal known-default decoded source',len(ac)==1 and ac[0]['status']=='OPAQUE')
    ck('Known-default acceptance is explicit, not a universal parser success',bool(actor['accepted_events']))
    RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase';NS=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene';BO=r'towercontinued\b0_story_eight\ronald.questphase';BS=r'towercontinued\b0_story_eight\ronald.scene';NEWS=r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'
    g=models[BS]['graphs']['scene'];ng=models[NS]['graphs']['scene'];bo=models[BO];rn=models[RN]
    starts=[i for i,n in g['nodes'].items() if n['type']=='scnStartNode'];ck('Seven current actual entry nodes preserved',set(starts)=={'1','920','1219','1415','2339','2707','3754'})
    maps={value(x['name']):str(x['nodeId']['id']) for x in models[BS]['metadata']['entryPoints']}
    ck('B0 actual called scene socket maps to entry920',maps['q302_05_ronald_in']=='920')
    cg=reach(g,starts);nn=reach(ng,starts)
    ck('Current all-entry traversal cannot reach consent1750/writer1755',not {'1750','1755'}&cg)
    ck('Native all-entry traversal reaches consent1750/writer1755',{'1750','1755'}<=nn)
    ck('Native intended entry920 reaches consent; current does not',{'1750','1755'}<=reach(ng,['920']) and not {'1750','1755'}&reach(g,['920']))
    for opt,dst in [(3,'1422'),(4,'1451')]:
        edge=['839','0:'+str(opt),dst,'0:0'];ck('Lost native lore edge '+str(opt),edge in ng['edges'] and not any(x[0]=='839' and x[1]=='0:'+str(opt) for x in g['edges']))
        ck('Choice payload has explicit current hidden predicate '+str(opt),g['nodes']['839']['payload']['options'][opt]!=ng['nodes']['839']['payload']['options'][opt])
    ck('Native genuine Yes event/writer preserved', ['1750','2:0','1755','0:1'] in g['edges'] and g['nodes']['1755']['writes']==[{'$type':'questSetVar_NodeType','factName':'q302_ronald_messages_enabled','setExactValue':1,'value':1}])
    # Independent actual-resource control: restore one authored choice and socket in private JSON only.
    mutated=copy.deepcopy(docs[BS]);mr=Resource(mutated);nr=Resource(docs[NS])
    find=lambda r:next(r.d(x) for x in r.d(r.root['sceneGraph'])['graph'] if r.d(x)['nodeId']['id']==839)
    cn,nnn=find(mr),find(nr);cn['options'][3]=copy.deepcopy(nnn['options'][3]);cn['outputSockets'][3]=copy.deepcopy(nnn['outputSockets'][3])
    mg=mr.normalize()['graphs']['scene'];ck('Actual restored native option3 control reconnects consent1755', '1755' in reach(mg,['920']))
    write(out/'control_restored_choice3.json',mutated)
    # Trace complete owner ancestry instead of equating killed receipt with independent retirement.
    ep=models[r'ep1\quest\ep1.questphase']['graphs']['root/10'];ad=models[r'ep1\quest\ep1_additional_game_elements.questphase']['graphs']['root'];pc=models[r'ep1\quest\ep1_persistent_content.questphase']['graphs']['root/30']
    ck('Actual Tower retirement predicate includes completed native Tower journal',ep['nodes']['8']['payload']['condition']['operation']=='OR' and ep['nodes']['8']['journal_paths']==['ep1/quests/main_quest/q307_before_tomorrow'] and ep['nodes']['8']['reads'][0]['state']=='Succeeded')
    ck('Native retirement route cuts additional owner before killed receipt',all(x in ep['edges'] for x in [['8','Out','9','In'],['9','CutSource','4','CutDestination'],['9','Out','10','In']]) and ep['nodes']['10']['writes'][0]['factName']=='q307_ep1_killed')
    ck('Cut owner chain reaches exact original Ronald parent',ep['nodes']['4']['refs']==[r'ep1\quest\ep1_additional_game_elements.questphase'] and ad['nodes']['2']['refs']==[r'ep1\quest\ep1_persistent_content.questphase'] and pc['nodes']['26']['refs']==[RN] and ['11','Out','26','In1'] in pc['edges'])
    ck('Original Ronald bar root lease is absent from B0 root and every nested owner',rn['root_prefabs']==['#q302_pr_bar'] and bo['root_prefabs']==[] and all(not n['prefabs'] for v in bo['graphs'].values() for n in v['nodes'].values()))
    b=bo['graphs']['root/5'];ck('B0 preserves exact Activate/WaitSpawn and near-trigger obligation',all(b['nodes'][i]['payload']==rn['graphs']['root']['nodes'][i]['payload'] for i in ['6','7','8']) and b['nodes']['2']['node_refs']==['#q302_tr_ronald_area_02'] and ['8','Out','2','In'] in b['edges'] and ['2','Out','200','In'] in b['edges'])
    xl=pin(Q7/'candidate_01/package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl');text=xl.read_text(encoding='utf-8-sig')
    ck('B0 registered directly on EP1 root1 Out',('- path: '+BO+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out') in text)
    block=Resource(docs[r'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock']);desc=block.root['descriptors'][1995];bar=next(r for r in e['source_pins'] if r['depot'].endswith('quest_7abca2b8d18f8562.streamingsector'));full=value(desc['questPrefabNodeRef'])
    ck('Native bar descriptor is quest-owned original resource',desc['category']=='Quest' and full.endswith('/#q302_pr_bar') and value(desc['data']['DepotPath'])==bar['depot'])
    for depot in [d for d in models if 'world_support_wa3' in d]:ck('Current WA3 does not supply native bar '+depot,not any(value(x.get('questPrefabNodeRef'))==full or value(x.get('data',{}).get('DepotPath',{}))==bar['depot'] for x in models[depot]['metadata']['descriptors']))
    # Independent packed identity review for actual original AISpot and two required triggers.
    bp=next(x for x in e['buffer_pins'] if x['name']=='bar');raw=pin(bp['buffer'],bp['buffer_sha256']).read_bytes();rr=Resource(docs[bar['depot']]);setups=[]
    for ix,expectedtype in [(0,'worldAISpotNode'),(1,'worldTriggerAreaNode'),(3,'worldTriggerAreaNode')]:
        packed=raw[ix*144:(ix+1)*144];di=struct.unpack_from('<Q',packed,0x70)[0]&0x7ffff;gid=struct.unpack_from('<Q',packed,0x58)[0];node=rr.d(rr.root['nodes'][di]);ref=value(rr.root['nodeData']['Data'][ix]['QuestPrefabRefHash'])
        ck('Actual original packed setup '+str(ix),di==ix and node['$type']==expectedtype and '/#q302_pr_bar/' in ref and str(gid)==next(x['global_id'] for x in e['selected_native_placements'] if x['setup']==ix));setups.append({'setup':ix,'definition':di,'global_id':str(gid),'ref':ref,'type':node['$type']})
    registry=Resource(read(ROOT/actor['json']));reg=registry.d(registry.root['nodes'][3495]);pd=registry.clean(reg['workspotsPersistentData'][47255]);ck('Retained enabled persistent workspot is real counterevidence',pd['globalNodeId']['hash']=='7106761085964620863' and pd['isEnabled']==1,pd)
    # Additional lore performer/workspot closure is scene-local, not a bar lease substitute.
    seen=set();todo=['1422','1451'];boundaries={'839','827','920','3811','3258'}
    while todo:
        i=todo.pop()
        if i in seen:continue
        seen.add(i)
        if i not in boundaries:todo.extend(x[2] for x in ng['edges'] if x[0]==i)
    performers={v['id'] for i in seen for v in walk(ng['nodes'][i]['payload']) if v.get('$type')=='scnPerformerId'}
    ck('Bounded new lore slice has Ronald5/player15/sentinel performers, no actor0 performer',len(seen)==179 and performers=={1281,3841,4294967040},sorted(performers))
    ck('Workspot tables retain exact native scene-local bindings',models[BS]['metadata']['workspots']==models[NS]['metadata']['workspots'] and models[BS]['metadata']['workspotInstances']==models[NS]['metadata']['workspotInstances'])
    sg=rn['graphs']['root/11'];ck('Native contact bootstrap is actual conditional AddContact/NonCallable chain',all(x in sg['edges'] for x in [['158','True','154','In'],['154','Out','23','In'],['158','False','159','In'],['159','Out','121','NonCallable'],['23','Out','121','NonCallable'],['23','Out','155','In'],['155','Out','156','In']]))
    ck('B0 omitted native contact child11; current news keeps actual existing-contact predicate',set(bo['graphs'])=={'root','root/5'} and 'contacts/ronald' in str(models[NEWS]['graphs']['root']['nodes']['200']))
    historical=pin(ROOT/'tools/plan_b0_story_eight.py');history=historical.read_text();ck('Historical S4 explicitly authored hide3/4/5 and root subset',"'hide':[(839,i)for i in [3,4,5]]" in history and "if key=='ronald':subset(route,[0,2,3,4,5,6,7,8,9,10,13])" in history)
    boundary=read(pin(ROOT/'prealpha/quest_restoration_qr8/worker_a/trigger_boundary_01/result.json'));ck('Native dynamic resolver boundary remains explicitly unbound',boundary['native_resolution_boundary']['unbound_service_vslot']=='0x190' and any('Implicit' in x and 'NOT proved absent' in x for x in boundary['limits']))
    statuses=[{'quest_id':q,'stage':s,'parent_status':'CONDITIONAL','supported_scope':'Already-active Ronald contact, positive prospective QR7 Armed future-event scope only.','unsupported_subroute_status':'FAIL','unsupported_scope':'New first-time enrollment/physical owner lease and native contact bootstrap extension is blocked; no actor/trigger absence or regression of QR7 future-news helper is asserted.'} for q in ['sts_ep1_01','sts_ep1_03','sts_ep1_08','sts_ep1_12'] for s in ['communications','shared_dependencies']]
    write(out/'parent_scope_recommendations.json',statuses);write(out/'source_pins.json',pins)
    write(out/'review.json',{'status':'APPROVE_SOURCE_FINDING_AND_HELD_EXTENSION_WITH_EXPLICIT_RUNTIME_LIMITS','checks':checks,'checks_passed':len(checks),'actual_resource_controls':1,'current_provider_comparisons':provider_checks,'actual_packed_setups':setups,
        'adjudication':['Confirmed existing B0 first-consent route is disconnected; native writer/outcomes are preserved but unreachable.','Confirmed B0 explicit native-bar ownership/support obligation omitted; original owner lies within genuine EP1 retirement envelope.','Historical S4 deliberately authored service-only exclusions. QR8 first-subscription objective exposes the unsupported extension; QR7 future-news helper did not introduce these omissions.','Retain eight parent CONDITIONAL statuses only for prospective already-active-contact scope; publish first-enrollment subroute FAIL and hold.','No safe filtered physical/first-contact owner is proven and no repair integration is approved.'],
        'limits':['Current all-block and AlwaysLoaded1 have differing basegame/EP1 providers; selected EP1 matches prior provider adjudication, not directory enumeration precedence.','Enabled persistent native workspot position/yaw and AlwaysLoaded scene marker counterbalance any unconditional missing-actor claim.','Actual trigger resolver dynamic virtual190 through context1E0 has unbound implementation/implicit-acquisition effects; runtime trigger absence is not proven.','Scene performer metadata and workspot closure do not prove actor spawning, original saved owner retirement in every history, or gameplay success.','No game/save/fact/candidate/deploy/release writes.'], 'runtime_changes':[],'integration_approved':False,'code_sha256':sha(__file__)})
    print({'checks':len(checks),'actual_resource_controls':1,'parents':len(statuses),'out':str(out)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
