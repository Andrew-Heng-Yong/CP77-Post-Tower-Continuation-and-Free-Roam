"""Independent source/serialized/packed review of frozen Ronald owner04.

Read-only outside worker_c. No worker builder/checker is imported.
"""
from pathlib import Path
import sys,copy,struct,re,collections,itertools,math,argparse
from prepare import ROOT,HERE,read,write,sha
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from common import walk,value
from model import Resource,digest,compare_graph

RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'
GIGS=['sts_ep1_12','sts_ep1_08','sts_ep1_03','sts_ep1_01']

def nodehash(s):
    s=re.sub(r';[^/]*','',s).replace('#','');h=0xcbf29ce484222325
    for c in s.encode():h=((h^c)*0x100000001b3)&0xffffffffffffffff
    return h if s else 0

def ev(c,f):
    t=c['$type']
    if t=='questLogicalCondition':
        x=[ev(a,f) for a in c['conditions']]
        return all(x) if c['operation']=='AND' else any(x) if c['operation']=='OR' else not any(x) if c['operation']=='NOR' else (_ for _ in()).throw(ValueError(c))
    if t=='questFactsDBCondition':return ev(c['type'],f)
    if t=='questVarComparison_ConditionType':
        a=f[c['factName']];b=c['value'];return {'Equal':a==b,'GreaterOrEqual':a>=b,'Less':a<b,'Greater':a>b}[c['comparisonType']]
    raise ValueError(c)

def main(out):
    assert not out.exists();out.mkdir()
    review=HERE/'reviews/ronald_01';plan=read(review/'plan.json');future=read(plan['future_manifest']);markers=read(plan['markers_manifest']);spec=read(plan['spec'])
    checks=[];controls=[];pins=[]
    def ck(name,yes,evidence=None):checks.append({'check':name,'pass':bool(yes),'evidence':evidence});assert yes,name
    for key in ['future_manifest','markers_manifest','spec']:
        ck('Frozen '+key+' pin',sha(plan[key])==plan[key+'_sha256']);pins.append({'path':plan[key],'sha256':plan[key+'_sha256']})
    own=read(review/'raw_exports_01/manifest.json');rs={r['label']:r for r in own['targets']};models={};objects={}
    for label,r in rs.items():
        ck('Own raw/JSON hash '+label,sha(r['raw'])==r['raw_sha256'] and sha(r['json'])==r['json_sha256'])
        objects[label]=read(r['json'])
        if r['kind']=='quest':
            models[label]=Resource(objects[label]).normalize();ck('No graph errors '+label,not models[label]['errors'])
        if 'buffer' in r:ck('Own actual packed-buffer pin '+label,sha(r['buffer'])==r['buffer_sha256'])
        pins.append(r)
    providers=read(HERE/'ronald_current_providers_01/manifest.json');raw_inputs=read(ROOT/'prealpha/quest_restoration_qr7/worker_b/raw_inputs_01.json');old={r['depot']:r for r in raw_inputs}
    native={}
    for r in providers['resources']:
        ck('Native unique current provider matches worker donor '+r['depot'],len([x for x in providers['resources'] if x['depot']==r['depot']])==1 and r['raw_sha256']==old[r['depot']]['raw_sha256'])
        ck('Current provider fresh JSON/raw still pinned '+r['depot'],sha(r['raw'])==r['raw_sha256'] and sha(r['json'])==r['json_sha256'])
        native[r['depot']]=Resource(read(r['json'])).normalize();pins.append(r)
    nm=native[RN];ng=nm['graphs']['root/11'];fm=models['future04'];fg=fm['graphs']['root/202'];rg=fm['graphs']['root']
    keep={str(x) for x in spec['kept_native_ids']}
    ck('Exactly73 source-selected native nodes plus explicit ten private routing nodes',len(keep)==73 and set(fg['nodes'])==keep|{'0','200','201','202','203','210','211','212','213','220'})
    ck('No native contact bootstrap121/fluff29 or other story nodes copied',not {'121','158','159','29'}&set(fg['nodes']))
    def relocated(x):
        if isinstance(x,dict):return {k:relocated(v) for k,v in x.items()}
        if isinstance(x,list):return [relocated(v) for v in x]
        return markers['private_refs'][0] if x=='#q302_tr_ronald_area_02' else x
    for i in sorted(keep,key=int):
        expected=relocated(ng['nodes'][i]['payload'])
        if i=='67':expected['inputSocketCount']=4
        ck('Exact native selected payload '+i,fg['nodes'][i]['payload']==expected)
        expected_sockets=[x for x in ng['nodes'][i]['sockets'] if not (i=='67' and x['name']=='In5')]
        ck('Exact native selected sockets '+i,fg['nodes'][i]['sockets']==expected_sockets)
    native_edges=sorted(e for e in ng['edges'] if e[0] in keep and e[2] in keep)
    observed_edges=sorted(e for e in fg['edges'] if e[0] in keep and e[2] in keep)
    ck('Every native edge among selected nodes preserved independently of worker edge catalogue',observed_edges==native_edges)
    ck('All selected phase dependencies are the four original SMS assets',{r for i in keep for r in fg['nodes'][i]['refs']}==set(native)-{RN})
    ck('All four native SMS resources have no omitted root prefab lease',all(not native[d]['root_prefabs'] for d in native if d!=RN))
    ck('Root retains one private child-owned marker lease and no whole-bar root lease',fm['root_prefabs']==[] and rg['nodes']['202']['prefabs']==[markers['private_parent']] and all('#q302_pr_bar' not in p for g in fm['graphs'].values() for n in g['nodes'].values() for p in n['prefabs']))
    ck('Private owner retirement follows terminating four-case native fan-in',fg['nodes']['1']['payload']['type']=='Terminating' and fg['nodes']['67']['payload']['inputSocketCount']==4 and ['67','Out1','1','In'] in fg['edges'] and ['202','Out1','203','In'] in rg['edges'] and rg['nodes']['203']['writes'][0]['factName']=='PTFRQR7_RonaldNews_Retired')
    ck('Both marker nodes must load before any case listener',fg['nodes']['220']['payload']['condition']['operation']=='AND' and {value(x['objectRef']) for x in walk(fg['nodes']['220']['payload']) if x.get('$type')=='questNodeLoadingCondition'}==set(markers['private_refs']) and sorted(e for e in fg['edges'] if e[0]=='0')==[['0','Out','220','In']] and all(['220','Out',str(200+i),'In'] in fg['edges'] for i in range(4)))
    case_fixtures=[]
    for index,q in enumerate(GIGS):
        gate=fg['nodes'][str(200+index)]['payload']['condition'];wait=fg['nodes'][str(210+index)]
        arm='PTFRQR7_RonaldNews_Armed_'+q;parent='PTFRU9_'+q+'_ParentEntered';done=q+'_done';sent='q302_msg_ronald_'+q
        ck('Case'+q+' waits for exact new Armed receipt',wait['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':arm,'value':1}] and [str(200+index),'True',str(210+index),'In'] in fg['edges'])
        for pa,ar,do,se in itertools.product([0,1],repeat=4):
            facts={parent:pa,arm:ar,done:do,sent:se};actual=ev(gate,facts);expected=do==0 and se==0 and (pa==0 or ar==1)
            ck('Actual case truth table '+q+str((pa,ar,do,se)),actual==expected)
            case_fixtures.append({'quest_id':q,'facts':facts,'eligible_to_wait':actual,'new_armed_wait_satisfied':ar==1,'old_entered_unarmed_rejected':not actual if pa==1 and ar==0 else None})
        before=models['before_'+q];after=models['arm_'+q];bg=before['graphs']['root/50'];ag=after['graphs']['root/50']
        ck('Armed writer only after unchanged original fresh eligibility '+q,ag['nodes']['65002']['payload']==bg['nodes']['65002']['payload'] and ['65002','Out','65007','In'] in ag['edges'] and ['65007','Out','65003','In'] in ag['edges'] and ['65002','Out','65003','In'] not in ag['edges'])
        ck('Armed writer uses one new local ID and exact private once value '+q,'65007' not in bg['nodes'] and ag['nodes']['65007']['writes']==[{'$type':'questSetVar_NodeType','factName':arm,'setExactValue':1,'value':1}])
        restored=copy.deepcopy(after);sg=restored['graphs']['root/50'];del sg['nodes']['65007'];sg['edges']=[e for e in sg['edges'] if e[0]!='65007' and e[2]!='65007']+[['65002','Out','65003','In']];sg['edges'].sort();sg['reachable']=[x for x in sg['reachable'] if x!='65007'];sg['unreachable']=[x for x in sg['unreachable'] if x!='65007']
        ck('Removing only approved arming splice restores every original graph/payload/metadata '+q,not compare_graph(before,restored))
        if '64999' in before['graphs']['root']['nodes']:
            ck('Existing outer64999 is byte-semantically unchanged '+q,before['graphs']['root']['nodes']['64999']==after['graphs']['root']['nodes']['64999'])
    b0=models['b0_current'];basegate=b0['graphs']['root']['nodes']['2']['payload']['condition'];rootgate=rg['nodes']['200']['payload']['condition']
    names=['PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q305_johnny_scene_active','q115_point_of_no_return','q000_done','q307_ep1_killed','q302_done','q302_ronald_tree']
    def atom(condition,name):return [x for x in condition['conditions'] if any(y.get('factName')==name for y in walk(x))]
    for name in names:ck('Exact existing retained-session/native predicate '+name,atom(rootgate,name)==atom(basegate,name) and len(atom(rootgate,name))==1)
    ck('Native actual subscription preserved, not a new subscription writer',any(x==nm['graphs']['root']['nodes']['12']['payload']['condition'] for x in rootgate['conditions']) and not any(x.get('factName')=='q302_ronald_messages_enabled' for g in fm['graphs'].values() for n in g['nodes'].values() for x in n['writes']))
    ck('Shared old queue is initially idle and new owner once unissued',atom(rootgate,'q302_ronald_message_pause')[0]['type']['value']==0 and atom(rootgate,'PTFRQR7_RonaldNews_Issued')[0]['type']['value']==0)
    contacts=[x for x in walk(rootgate) if x.get('$type')=='questJournalEntryState_ConditionType']
    ck('Contact guard reuses exact original121 path as existingActive, inverted0',len(contacts)==1 and contacts[0]['path']==ng['nodes']['121']['payload']['type']['path'] and contacts[0]['state']=='Active' and contacts[0]['inverted']==0)
    state_fn=(HERE/'contact_state_followup_01/function_00362544.asm').read_text();path_fn=(HERE/'contact_state_lookup_02/function_00362584.asm').read_text()
    ck('Actual generic native predicate performs state-by-path equality, with null-path false','call qword ptr [rax + 0x2b8]' in state_fn and 'cmp eax, dword ptr [rbx + 0x18]' in state_fn and 'sete al' in state_fn and 'xor al, al' in state_fn and '[rdx + 0x2a8]' in path_fn)
    # Marker descriptors and all actual compiled placement bytes, not WK's obsolete NodeIndex field.
    sr=Resource(objects['private_sector']);nr=Resource(objects['native_sector']);private=sr.root;native_sector=nr.root
    ck('Exactly two worldTriggerArea nodes and no actors/devices/workspots copied',len(private['nodes'])==2 and all(sr.d(x)['$type']=='worldTriggerAreaNode' for x in private['nodes']))
    pb=Path(rs['private_sector']['buffer']).read_bytes();nb=Path(rs['native_sector']['buffer']).read_bytes()
    ck('Actual current compiled record widths and counts',len(pb)==2*0x90 and len(nb)==75*0x90)
    placements=[]
    for dest,source in enumerate([1,3]):
        ck('Exact native trigger payload including outline/source metadata '+str(dest),sr.clean(sr.d(private['nodes'][dest]))==nr.clean(nr.d(native_sector['nodes'][source])))
        old=nb[source*0x90:(source+1)*0x90];new=pb[dest*0x90:(dest+1)*0x90]
        outside=[i for i in range(0x90) if i not in set(range(0x58,0x60))|set(range(0x70,0x78))]
        ck('All native placement bytes preserved except new global/private index '+str(dest),all(old[i]==new[i] for i in outside))
        oi=struct.unpack_from('<Q',old,0x70)[0];ni=struct.unpack_from('<Q',new,0x70)[0]
        ck('Modern19-bit packed index only changes to new descriptor order '+str(dest),(oi&0x7ffff)==source and (ni&0x7ffff)==dest and oi&~0x7ffff==ni&~0x7ffff)
        globalid=struct.unpack_from('<Q',new,0x58)[0]
        ck('Private global reference matches canonical NodeRef hashing '+str(dest),globalid==nodehash(markers['private_refs'][dest]) and struct.unpack_from('<Q',new,0x60)[0]==0)
        placements.append({'source_setup':source,'private_setup':dest,'position':struct.unpack_from('<fff',new),'private_global_id':globalid,'source_prefab_hash':sr.d(private['nodes'][dest]).get('sourcePrefabHash')})
    ck('Sector declares exact private NodeRefs',{value(x) for x in private['nodeRefs']}==set(markers['private_refs']))
    br=objects['private_block']['Data']['RootChunk'];bn=objects['native_block']['Data']['RootChunk'];des=br['descriptors']
    ck('One private quest-category descriptor, no native full-bar block copy',len(des)==1 and des[0]['category']=='Quest' and value(des[0]['data']['DepotPath'])==markers['intended_sector_depot'] and value(des[0]['questPrefabNodeRef'])==markers['private_parent'] and des[0]['variants']==[])
    olddesc=next(x for x in bn['descriptors'] if value(x['data']['DepotPath'])==markers['native']['depot']);expected=copy.deepcopy(olddesc);expected['data']=des[0]['data'];expected['questPrefabNodeRef']=des[0]['questPrefabNodeRef']
    ck('Private descriptor preserves all other current native descriptor fields',des[0]==expected)
    # Negative controls operate on actual loaded raw/resource representations.
    mutant=copy.deepcopy(objects['arm_sts_ep1_01']);target=next(x for x in walk(mutant) if x.get('$type')=='questSetVar_NodeType' and x.get('factName')=='PTFRQR7_RonaldNews_Armed_sts_ep1_01');target['value']=0
    bad=Resource(mutant).normalize()['graphs']['root/50']['nodes']['65007']['writes'][0]
    controls.append({'mutation':'Actual serialized entry Armed value1→0','detected':bad['value']!=1})
    mutant=copy.deepcopy(objects['future04']);mr=Resource(mutant);loadnode=next(x for x in walk(mutant) if x.get('$type')=='questPauseConditionNodeDefinition' and x.get('id')==220);mr.d(loadnode['condition'])['conditions'].pop()
    loaded={value(x['objectRef']) for x in walk(Resource(mutant).normalize()['graphs']['root/202']['nodes']['220']['payload']) if x.get('$type')=='questNodeLoadingCondition'}
    controls.append({'mutation':'Remove actual second marker-loading predicate','detected':loaded!=set(markers['private_refs'])})
    mutant=bytearray(pb);mutant[0x58]^=1
    controls.append({'mutation':'Flip actual private packed global identity byte','detected':struct.unpack_from('<Q',mutant,0x58)[0]!=nodehash(markers['private_refs'][0])})
    mutant=copy.deepcopy(fg['nodes']['200']['payload']['condition']);mutant['conditions'][2]['operation']='AND';q=GIGS[0]
    controls.append({'mutation':'Change actual case history OR to AND','detected':not ev(mutant,{q+'_done':0,'q302_msg_ronald_'+q:0,'PTFRU9_'+q+'_ParentEntered':0,'PTFRQR7_RonaldNews_Armed_'+q:0})})
    ck('Four independent raw/serialized/packed controls detected',all(x['detected'] for x in controls))
    # No worker-owned publication changes the frozen proposal during review.
    ck('Frozen owner/marker manifests unchanged after review',sha(plan['future_manifest'])==plan['future_manifest_sha256'] and sha(plan['markers_manifest'])==plan['markers_manifest_sha256'])
    result={'status':'APPROVE_SOURCE_PLAN_REQUIRES_COORDINATOR_FINAL_GATES','checks':checks,'controls':controls,'case_truth_table_fixtures':case_fixtures,'placements':placements,
        'plan':str(review/'plan.json'),'plan_sha256':sha(review/'plan.json'),'input_pins':pins,
        'positive_scope':['Real new Armed writes are attached to exact existing fresh admission edges; done0/sent0 are not the sole future-event evidence.',
          'Already-entered/Armed0, old done1, old sent1 and a busy old Ronald queue are not adopted or reset. All original selected timer, sent-before-timer, message-child and queue cleanup payloads/edges are preserved.',
          'Current contact guard uses the original native path with a generic existing-state predicate. Actual current native lookup/comparison supports the contact path; no add-contact/notification bootstrap is copied.',
          'Own packed readback preserves exact two native trigger payloads/shapes/transforms, modern indices and private global identities. Child202 owns only their private descriptor group and terminates after four completed/skipped branches.'],
        'source_prefab_hash_scope':{'preserved':8425604133833249267,'evidence':'Both private world-node payloads equal exact native trigger payloads. Ownership support is descriptor.questPrefabNodeRef plus child phaseInstancePrefabs and new globalNodeID hierarchy, not sourcePrefabHash.',
          'source_boundary':'Captured RED4ext worldNode has size0x38 and no sourcePrefabHash runtime field; the exact current executable has no sourcePrefabHash RTTI string. This supports treating it as retained source metadata, but is not a universal disassembly proof of engine lease internals.',
          'decision':'No source-confirmed basis to rewrite native source metadata. Its runtime interaction with private streaming remains a disclosed live boundary.'},
        'required_coordinator_gates':['Actual append-only XL quest registration at EP1.quest node1.Out and new block registration; preserve all prior order.',
          'Final resource-provider, ArchiveXL generated-node19913, private NodeRef/global IDs and all installed-addition collision inventory.',
          'Fresh integrated payload serialization/readback, complete package/source hash match, relevant compile and preservation gates.'],
        'live_limits':['Private marker streaming/acquisition/release and IsOutside occupancy, asynchronous queue scheduling, actual SMS delivery and gameplay.',
          'Exact old save concurrency/owner retirement is not proven merely by q307 facts. This prospective plan refuses observable old entry/timer/message states and does not reset native facts, contacts, counters, rewards or progress.',
          'This is approval of frozen source/serialized proposal04, not deployment or a claim of final packaged success.'],
        'runtime_changes':[],'code_sha256':sha(__file__)}
    write(out/'review.json',result);print({'status':result['status'],'checks':len(checks),'controls':len(controls),'fixtures':len(case_fixtures),'out':str(out)})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);main(ap.parse_args().output)
