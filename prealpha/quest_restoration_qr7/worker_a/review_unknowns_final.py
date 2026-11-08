"""Independent eight-row disposition gate on actual sources and current epoch."""
from pathlib import Path
import sys,copy,collections,json,struct,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
C=W/'prealpha/quest_restoration_qr7/worker_c'
CUCKOO=r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\phases\sts_std_rcr_02_phase.questphase'
DIXON=r'base\open_world\street_stories\santo_domingo\rancho_corronado\sts_std_rcr_02\scenes\sts_std_rcr_02_dixon.scene'
STASH=r'ep1\quest\main_quests\q304\phases\q304_slider_stash.questphase';BOOT=r'towercontinued\sidejobs_s23\ep1\voodoo_boot.questphase'
CAREER=r'base\open_world\mini_world_stories\watson\mws_wat_08\mws_wat_08.questphase'
def reach(g,start,end):
 seen={start};todo=[start]
 while todo:
  n=todo.pop()
  for a,s,b,t in g['edges']:
   if a==n and s!='CutSource'and t!='CutDestination'and b not in seen:seen.add(b);todo.append(b)
 return end in seen
def run(o):
 assert not o.exists();result=read(C/'results_01/results.json');rows=read(C/'results_01/contract_updates.json');app=read(C/'results_01/effective_applicability.json');R=read(C/'remaining_01/result.json');T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 ck('eight unique assigned contract rows',len(rows)==8 and len({(r['quest_id'],r['stage'])for r in rows})==8);ck('statuses exactly five unresolved, two approved adaptations, one conditional',collections.Counter(r['status']for r in rows)=={'UNKNOWN':5,'APPROVED_DEVIATION':2,'CONDITIONAL':1});ck('published contract file pin',sha(C/'results_01/contract_updates.json')==result['contract_updates_sha256']);ck('effective epoch pin',sha(Path(app['epoch']))==app['epoch_sha256'])
 for pin in result['evidence_units']:ck('frozen evidence unit '+Path(pin['path']).parent.name,sha(Path(pin['path']))==pin['sha256'])
 for item in app['targeted_effective_resources']:ck('actual QR7:01 resource applicability '+item['depot'],sha(Path(item['effective_path']))==item['after'])
 changed=[x for x in app['targeted_effective_resources']if x['changed']];ck('only reviewed Nitro resource changed in this targeted scope',len(changed)==1 and changed[0]['depot']==r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase'and changed[0]['after']=='79FD3A440DFBCE6130AA5E5EA1D71E6E92BEAD27691C0AD0F59EFE7C94214784')
 pins={p['depot']:p for p in R['source_pins']};pins.update({p['depot']:p for p in read(C/'journal_proof_02/result.json')['source_pins']if 'depot'in p});docs={};models={}
 for depot in [CUCKOO,DIXON,STASH,BOOT,CAREER,'towercontinued\\sidejobs_s30\\native\\'+CAREER]:
  p=pins[depot];ck('actual pinned raw resource '+depot,sha(Path(p['raw']))==p['raw_sha256']);ck('actual typed resource pin '+depot,sha(Path(p['json']))==p['json_sha256']);docs[depot]=read(Path(p['json']));models[depot]=Resource(docs[depot]).normalize()
 providers=read(C/'quest_providers_01/manifest.json');ck('all four native targets unique current providers',len(providers['resources'])==4 and len({x['depot']for x in providers['resources']})==4 and len(providers['archive_index_inventory'])==134)
 for x in providers['resources']:ck('fresh native provider exactly equals targeted source '+x['depot'],x['raw_sha256']==pins[x['depot']]['raw_sha256']and sha(Path(x['raw']))==x['raw_sha256'])
 # Null is actually serialized, rather than a normalizer's invented endpoint.
 cr=Resource(docs[CUCKOO]);cg=models[CUCKOO]['graphs']['root'];nulls=[]
 for h,d in cr.handles.items():
  if d.get('$type')=='graphGraphConnectionDefinition'and d.get('source','ABSENT')is None:
   dest=cr.hid(d['destination']);nulls.append((h,dest))
 ck('exact four serialized null source endpoints',set(nulls)=={('2405','2404'),('2425','2424'),('2444','2443'),('2464','2463')},nulls);ck('diagnostics remain exactly inherited null-source recipients',[(x['to'][0],x['to'][1])for x in models[CUCKOO]['errors']if x['kind']=='DANGLING_EDGE']==[('11','In'),('13','In'),('15','In'),('2','In')]);ck('all four recipients unreachable from native input0',all(not reach(cg,'0',i)for i in ['11','13','15','2']))
 dg=models[DIXON]['graphs']['scene'];inventory=[x for x in walk(dg['nodes']['86']['payload'])if x.get('$type')=='questInventory_ConditionType'];ck('Dixon86 is the exact inventory condition, not a grant',len(inventory)==1 and value(inventory[0]['itemID'])=='114327022403'and inventory[0]['quantity']==1 and inventory[0]['comparisonType']=='GreaterOrEqual');dest=[e[2]for e in dg['edges']if e[0]=='86'];ck('both actual inventory outputs reach unchanged choice6',len(dest)==2 and all(reach(dg,i,'6')for i in dest),dest)
 stock=read(C/'stock_01/records.json');missing=[x for x in stock['records']if x['id']=='114327022403'];ck('bounded direct stock lookup records absent in both databases',len(missing)==2 and all(not x['exists']and x['record_type']is None for x in missing));
 for d in stock['databases']:ck('actual current stock database pin '+Path(d['path']).name,sha(Path(d['path']))==d['sha256'])
 # Voodoo cleanup is left ambiguous; do not turn a PS string mismatch into a fix.
 boot=models[BOOT];bg=boot['graphs']['root'];sg=models[STASH]['graphs']['root'];gate=bg['nodes']['90']['payload']['condition'];door=[x for x in walk(gate)if x.get('$type')=='questDevice_ConditionType'];nativeDoor=[x for x in walk(sg['nodes']['3']['payload'])if x.get('$type')=='questDevice_ConditionType'];ck('late guard exact loaded DoorControllerPS identity',len(door)==len(nativeDoor)==1 and door==nativeDoor and value(door[0]['deviceControllerClass'])=='DoorControllerPS'and value(door[0]['objectRef'])=='#q304_dvc_slider_stash_door');ck('late guard explicitly NOR(IsOpen)',gate['operation']=='AND'and any(x.get('$type')=='questLogicalCondition'and x.get('operation')=='NOR'and any(z.get('$type')=='questDevice_ConditionType'for z in walk(x))for x in gate['conditions']));ck('private body is the exact original native reference',boot['graphs']['root/100']['nodes']['4']['refs']==[STASH]and not any(x.get('$type')=='questInjectLoot_NodeTypeParams_OperationData'for x in walk(docs[BOOT])))
 clean=[x for x in walk(sg['nodes']['21']['payload'])if x.get('$type')=='questDeviceManager_NodeTypeParams'];ck('native cleanup21 precisely uses TerminalControllerPS on the same door',len(clean)==1 and value(clean[0]['deviceControllerClass'])=='TerminalControllerPS'and value(clean[0]['deviceAction'])=='ForceDisabled'and value(clean[0]['objectRef'])==value(door[0]['objectRef']))
 ops=[x for x in walk(sg['nodes']['22']['payload'])if x.get('$type')=='questInjectLoot_NodeTypeParams_OperationData'];ck('actual native Inject22 exact quantities and IDs',[(value(x['itemTDBID']),x['quantity'],x['operationType'])for x in ops]==[('51369838828',8000,'Inject'),('127255451537',1,'Inject'),('118124605694',1,'Inject')]);ck('generic hub12 not promoted to invented AND/one-time receipt',sg['nodes']['12']['type']=='questLogicalHubNodeDefinition');ck('native container cleanup path retained',all(any(e[0]==a and e[2]==b for e in sg['edges'])for a,b in [('22','5'),('5','13'),('13','6'),('6','1')]))
 for field in R['native_persistent_fields']:
  cache=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077/r6/cache/final.redscripts');payload=cache.read_bytes()[field['offset']:field['offset']+field['size']];ck('actual serialized persistent field payload '+field['class_name']+'.'+field['name'],payload.hex()==field['raw_payload_hex']and field['field_flags']&0x100!=0)
 # Reuse the already independent exact machine-code review; do not relabel the
 # separate saved-owner contract because a smaller property is now known.
 career=next(r for r in rows if r['quest_id']=='mws_wat_08_trauma_drama');ck('Career persistence remains unknown despite bounded same-state proof',career['status']=='UNKNOWN'and any('owner retirement' in x for x in career['remaining'])and not career['runtime_changes']);jr=read(H/'reviews/career_journal_01/review.json');ck('actual independent journal dispatch proof remains pinned',jr['status']=='APPROVE_NARROW_SAME_ACTIVE_JOURNAL_STATE_AND_NOTIFICATION_IDEMPOTENCE_PROOF'and jr['reviewed_result_sha256']==sha(C/'journal_proof_02/result.json'))
 ng=models[CAREER]['graphs']['root'];rg=models['towercontinued\\sidejobs_s30\\native\\'+CAREER]['graphs']['root'];ck('Career message7/56 payloads and identities preserved',all(ng['nodes'][i]['payload']==rg['nodes'][i]['payload']for i in ['7','56']));ck('Career messages before first-place started writer exact source order',all(any(e[0]==a and e[2]==b for e in ng['edges'])for a,b in [('6','68'),('68','7'),('7','57'),('57','56'),('56','8'),('8','9'),('9','66')])and ng['nodes']['66']['writes'][0]['factName']=='mws_wat_08_started')
 # Independent actual-document mutation: replace a null source by native input.
 mutant=copy.deepcopy(docs[CUCKOO]);mr=Resource(mutant);g=mr.d(mr.root['graph']);inp=next(mr.d(x)for x in g['nodes']if mr.d(x)['id']==0);out=next(s for s in inp['sockets']if value(mr.d(s)['name'])=='Out');mr.handles['2405']['source']={'HandleRefId':mr.hid(out)};mm=Resource(mutant).normalize();ck('actual null-endpoint mutation independently changes inherited diagnostics',len(mm['errors'])!=len(models[CUCKOO]['errors']));write(o/'mutant_cuckoo_source.json',mutant)
 decisions=[]
 for r in rows:
  ck('named residual evidence, no generic pending placeholder '+r['quest_id']+'/'+r['stage'],bool(r['proven'])and bool(r['remaining'])and not any(x.strip().lower()in ['pending','unknown','needs investigation','generic pending']for x in r['remaining']))
  decisions.append({'quest_id':r['quest_id'],'stage':r['stage'],'reviewed_status':r['status'],'decision':'APPROVE_BOUNDED_DISPOSITION','remaining':r['remaining']})
 ck('Nitro independent current raw gate review retained',read(H/'reviews/nitro_serialized_gate_01/review.json')['candidate_raw_sha256']==changed[0]['after'])
 write(o/'tests.json',T);write(o/'review.json',{'status':'APPROVE_EIGHT_BOUNDED_DISPOSITIONS_WITH_FIVE_EXPLICIT_UNKNOWNS','checks':len(T),'actual_document_mutations':1,'reviewed_results':str(C/'results_01/results.json'),'reviewed_results_sha256':sha(C/'results_01/results.json'),'reviewed_rows_sha256':sha(C/'results_01/contract_updates.json'),'effective_epoch':app['epoch'],'effective_epoch_sha256':app['epoch_sha256'],'decisions':decisions,'source_scope':'Direct current-source checks for Cuckoo, Voodoo and Career; independent prior source/actual binary Nitro and Career journal reviews reused. All25 targeted effective successor resource hashes checked.','interpretive_limits':['Cuckoo: source:null means absent serialized endpoints, not proof no possible engine or saved activation exists. Missing stock record is not a reward defect.','Voodoo: exact TerminalControllerPS versus DoorControllerPS mismatch is a binding uncertainty, not permission to change the door or assume claimed histories are reachable. Persistent field flags are not saved identity/owner transition fixtures.','Career: same-state state/notification proof is narrow; residual owner retirement, queued/concurrent state and non-Active history remain UNKNOWN.','Nitro: prospective repaired gate is approved; existing issued descendants intentionally keep old selector behavior, with live scheduler/save validation separate.'],'runtime_changes':[]});print({'checks':len(T),'review':str(o/'review.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
