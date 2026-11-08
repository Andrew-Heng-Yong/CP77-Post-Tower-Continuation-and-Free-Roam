"""Focused predecessor outcomes and Rinder's conditional garage SMS; no gameplay edits."""
from pathlib import Path
import sys,copy,argparse,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource,reachable
def run(O):
 assert not O.exists();tests=[];pins=[]
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 d=r'ep1\openworld\street_stories\sts_ep1_03\phases\sts_ep1_03_openworld.questphase';m,p=I.load(d);pins.append(p);g=m['graphs']['root/4/59'];n=g['nodes']
 ck('actual dogtag inventory acknowledgment101→102',['101','Out','102','In']in g['edges']and n['101']['payload']['condition']['type']['$type']=='questInventory_ConditionType'and n['101']['payload']['condition']['type']['quantity']==1,'Items.sts_ep1_03_rinder_dogtag real inventory, native receipt1 only')
 ck('native garage-code refusal OR preserved',n['132']['payload']['condition']['operation']=='OR'and {x['factName']for x in n['132']['reads']}=={'sts_ep1_03_wagner_no_garage_number','sts_ep1_03_wagner_called_regina'},n['132']['payload'])
 ck('only false native branch offers contact/code SMS',all(e in g['edges']for e in [['132','False','135','In'],['135','Out','133','In'],['133','Out','134','Active']]),'do not send a code after explicit no-garage/Regina outcome')
 ck('original outside-content trigger before code', '#sts_ep1_03_tr_content_init'in n['135']['node_refs'],n['135']['payload'])
 ck('native contact and garage SMS source',n['133']['payload']['type']['params'][0]['addContact']==1 and n['134']['journal_paths']==['ep1/contacts/rinder/sts_ep1_03/rinder_garage_info_code']and n['134']['sms'],n['134']['payload'])
 boot,p=I.load(r'towercontinued\sidejobs_s23\ep1\rinder_boot.questphase');pins.append(p)
 ck('Rinder adapter does not replay garage SMS',not any(x['sms']or x['journal_paths']and any('contacts/'in p for p in x['journal_paths'])for gr in boot['graphs'].values()for x in gr['nodes'].values()),'own input positive native dogtag; predecessor message history preserved, not fabricated')
 h,p=I.load(r'ep1\openworld\street_stories\sts_ep1_04\phases\sts_ep1_04_cleanup.questphase');pins.append(p);hg=h['graphs']['root'];ck('Hasan real default producer after both outside triggers',['22','Out','12','In']in hg['edges']and hg['nodes']['22']['payload']['condition']['operation']=='AND'and {'#wst_ep1_05_tr_start','#wst_ep1_06_tr_start'}<=set(hg['nodes']['22']['node_refs']),hg['nodes']['22']['payload'])
 ck('Hasan real default producer uses native1',hg['nodes']['12']['writes']==[{'$type':'questSetVar_NodeType','factName':'hasan_default_on','setExactValue':1,'value':1}],'no initial default flag fabricated by adapter')
 rr,p=I.load(r'ep1\openworld\world_stories\wst_ep1_04\wst_ep1_04.questphase');pins.append(p);p24=rr['graphs']['root']['nodes']['24']['payload']['condition']['type'];ck('Rinder original loot-table inventory0 predicate explicit',p24['$type']=='questInventory_ConditionType'and p24['itemID']['$value']=='LootTables.wst_ep1_04_reward_loot_table'and p24['quantity']==0,'Preserved original odd target/quantity, engine/container interpretation remains conditional; do not rewrite it as weapon-possession1.')
 hh,p=I.load(r'ep1\openworld\world_stories\wst_ep1_05\wst_ep1_05.questphase');pins.append(p);p52=hh['graphs']['root']['nodes']['52']['payload']['condition']['type'];ck('Hasan exact iconic inventory1 prerequisite',p52['$type']=='questInventory_ConditionType'and p52['itemID']['$value']=='Items.Preset_Kenshin_Spy'and p52['quantity']==1,'Native pickup acknowledgement then53gunTaken1; no grant.')
 bb,p=I.load(r'ep1\quest\tertiary_characters\default_dialogs\bill_default\sts_10_bill_default.scene');pins.append(p);sg=bb['graphs']['scene'];ee=[e for e in sg['edges']if not(sg['nodes'][e[0]]['type']=='scnCutControlNode'and e[1].startswith('1:'))];ck('Bill real reward path only native Dodger-dead entry','329'in reachable(sg['nodes'],ee,[sg['entries']['dodger_dead']])and'329'not in reachable(sg['nodes'],ee,[sg['entries']['dodger_alive']]),'Native reward329 on327.0→329.In, not a generic every-branch reward; exclude scene cut cancellation outputs.')
 # One actual raw mutation of the conditional SMS path, distinct from the main6 controls.
 r=copy.deepcopy(read(pins[0]['json']));changed=0
 for x in walk(r):
  if x.get('factName')=='sts_ep1_03_wagner_no_garage_number':x['factName']='QR5_lost_native_garage_choice';changed+=1
 mm=Resource(r).normalize();ck('raw missing prior choice predicate detected',changed>0 and not any(x.get('factName')=='sts_ep1_03_wagner_no_garage_number'for x in mm['graphs']['root/4/59']['nodes']['132']['reads']),{'resource':d,'graph':'root/4/59','node':'132'})
 write(O/'mutated_native.json',r);write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'Rinder_SMS_scope.json',{'depot':d,'graph':'root/4/59','native_gate':n['132'],'native_trigger':n['135'],'contact':n['133'],'SMS':n['134'],'status':'NATIVE_CONDITIONAL_PRIOR_JOB_PRODUCER_PRESERVED_NOT_REPLAYED','limit':'Dogtag receipt alone does not prove optional code SMS delivered; explicit no-garage/Regina choices suppress it. Old unfinished predecessor/message states and live callback timing remain conditional, no speculative reset/replay authorized.'});write(O/'summary.json',{'status':'PASS_SPECIFIC_PRIOR_MESSAGE_AND_OUTCOME_SCOPE','checks':len(tests),'mutations':1,'fully_static_verified':False,'runtime_changes':[]});print({'checks':len(tests),'mutations':1})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
