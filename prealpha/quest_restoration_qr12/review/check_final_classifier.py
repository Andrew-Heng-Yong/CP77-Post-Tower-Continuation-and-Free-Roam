"""Independent in-memory readiness boundaries; never reads/writes a save body."""
from pathlib import Path
import collections,copy,hashlib,importlib.util,json
H=Path(__file__).resolve().parent;Q=H.parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
 spec=importlib.util.spec_from_file_location('qr12_classifier_review',Q/'classify.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 data=read(Q/'analysis_final_02/verified_fixture_inventory.json');working=next(x for x in data['rows']if x['kind']=='GAME_SAVE'and x['slot_directory']=='ManualSave-24')
 state=working['saved_parse'];negative='BRENDAN_unearned_fresh_containment';earned='BRENDAN_earned_descendant_preservation';checks=[]
 def scenario(row,st,answer,key):return next(x for x in module.classify(row,st,answer)if x['scenario']==key)
 def ck(label,value):assert value,label;checks.append(label)
 ck('actual DontRemember plus private admission is not a clean fresh fixture',scenario(working,state,'Don’t remember',negative)['status']=='BLOCKED_BY_HISTORY')
 ck('actual private admission is not promoted into earned native history',scenario(working,state,'Don’t remember',earned)['status']=='UNKNOWN')
 clean=copy.deepcopy(state)
 for n in ('mq037_brendan_introduced','mq037_01_05Sure','mq037_vandal_painted_brendan','mq037_done','PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered'):
  clean['facts'][n]=[{'value_u32':0,'table_path':'SYNTHETIC_ONLY','table_ordinal':1,'hash':'SYNTHETIC'}]
 ck('hypothetical clean known NeverStarted can qualify only negative containment',scenario(working,clean,'Never started any Brendan job',negative)['status']=='READY')
 for name in ('PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered'):
  contradictory=copy.deepcopy(clean);contradictory['facts'][name][0]['value_u32']=1
  ck(name+' independently prevents false fresh READY',scenario(working,contradictory,'Never started any Brendan job',negative)['status']!='READY')
  ck(name+' independently does not certify earned native history',scenario(working,contradictory,'Never started any Brendan job',earned)['status']=='UNKNOWN')
 unbound={**working,'lineage':'NOT_INDEPENDENTLY_CONFIRMED'}
 ck('same-name unbound fixture never promoted to READY',scenario(unbound,clean,'Never started any Brendan job',negative)['status']!='READY')
 statuses=collections.Counter(c['status']for r in data['rows']if r['kind']=='GAME_SAVE'for c in r['scenarios'])
 ck('all102current slots have nine distinct scenario rows',sum(statuses.values())==918 and all(len(r['scenarios'])==9 and len({c['scenario']for c in r['scenarios']})==9 for r in data['rows']if r['kind']=='GAME_SAVE'))
 ck('final actual evidence produces no READY without hardcoded noREADY assertion',statuses['READY']==0 and 'assert not any'not in(Q/'classify.py').read_text())
 result={'status':'PASS_INDEPENDENT_FINAL_CLASSIFICATION_BOUNDARIES','checks':checks,'final_current_classifications':dict(statuses),
  'classifier_sha256':sha(Q/'classify.py'),'final_inventory_sha256':sha(Q/'analysis_final_02/verified_fixture_inventory.json'),
  'limits':'Synthetic memory copies only; hypothetical READY is not a real save or a human claim. No game/API/DLL/save-body access. Actual user still does not remember Brendan.'}
 dest=H/'final_classifier_controls_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({'status':result['status'],'checks':len(checks),'actual_statuses':dict(statuses)})
if __name__=='__main__':main()
