"""Adversarial producer-family inventory, including non-generic call requests.

This is a coverage check over pinned investigation fact tables, not a new
executing-owner proof and not a replacement for actual-resource group reviews.
"""
from pathlib import Path
import sys,json,re,argparse
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk

def run(out):
 assert not out.exists();p=read(O/'progress.json');rows=[];limitations=[];pins={}
 for gid,g in p['groups'].items():
  if g['status']not in ['REVIEWED_WITH_LIMITS','INVESTIGATED_AWAITING_REVIEW']:continue
  for ident in g['ids']:
   fp=O/'groups'/gid/'quests'/ident/'contracts.json';d=read(fp);candidates=[]
   for obj in walk(d):
    for key in ['path','source','evidence_path']:
     s=obj.get(key)
     if isinstance(s,str)and s.endswith('graph_evidence.json'):candidates.append((Path(s),obj.get('sha256')))
   for v in d['contracts'].values():
    for item in v.get('evidence',[]):
     if isinstance(item,str)and item.endswith(('graph_evidence.json','handler_inventory.json')):
      f=Path(item);candidates.append((f if f.is_absolute()else(fp.parent/f).resolve(),None))
   selected=[]
   for f,h in dict.fromkeys(candidates):
    if not f.is_file():continue
    if h:assert sha(f)==h
    data=read(f);q=data.get('quests',{}).get(ident)
    if q is None and ident in data and isinstance(data[ident],list):q={'facts':data[ident]}
    if q is None and isinstance(data.get('handlers'),list):
     subset=[x for x in data['handlers']if ident in x.get('depot','')]
     if subset:q={'facts':subset}
    if q is not None:selected.append((f,q))
   if not selected:
    limitations.append({'quest_id':ident,'reason':'This verifier does not support this group evidence schema; actual group/peer review remains separate.'});continue
   found={}
   for f,q in selected:
    pins[str(f)]=sha(f);covered={str(x.get('request',''))for x in q.get('phone_protocols',[])}
    for node in q.get('facts',[]):
     for w in node.get('writes',[]):
      fact=w.get('factName','')
      if not re.search(r'holo|phone|sms|(^|_)call($|_)',fact,re.I):continue
      key=(node.get('resource',node.get('depot')),node.get('graph'),str(node.get('node')),fact)
      found[key]={'quest_id':ident,'resource':key[0],'graph':key[1],'node':key[2],'fact':fact,'write':w,'incoming':node.get('incoming',[]),'outgoing':node.get('outgoing',[]),'generic_protocol_table_explicit_request':fact in covered,'family':'CUSTOM_HOLOCALL_FACT_CANDIDATE'if'holocall'in fact and not fact.startswith(('holo_','audio_'))else'OTHER_PHONE_RELATED_FACT','disposition':'INVENTORY_ONLY_REQUIRES_SPECIFIC_ROUTE_LISTENER_AND_OWNER_EVIDENCE','evidence':str(f)}
   rows+=list(found.values())
 custom=[r for r in rows if r['family']=='CUSTOM_HOLOCALL_FACT_CANDIDATE']
 # Known actual-source regression: an incoming/outgoing generic-only family
 # filter omits these three real request writers. Never call that full coverage.
 cvi={r['fact']for r in custom if r['quest_id']=='sts_pac_cvi_02'}
 expected={'new_sts_pac_cvi_02_holocall_'+s for s in ['prebrief','debrief_failed','debrief_perfect']}
 assert expected<=cvi
 write(out/'inventory.json',{'status':'BOUNDED_PHONE_FAMILY_COVERAGE_CENSUS_WITH_EXPLICIT_SCHEMA_LIMITS','rows':rows,'custom_phone_fact_candidates':custom,'unsupported_quest_evidence_schemas':limitations,'input_pins':pins,'regression_control':{'actual_CVI02_three_custom_producers_detected':True,'generic_only_filter_would_miss':sorted(expected)},'limits':['Name patterns are a triage aid, not exhaustive semantic call detection; candidates include after-call receipts as well as requests.','Fact tables are pinned reports; actual native/effective raw source comparisons and owner evidence reside in group/peer verifiers.','A writer or listener occurrence does not establish a live owner, callback admission or engine execution.']})
 return {'inventoried_quests':len({r['quest_id']for r in rows}),'rows':len(rows),'custom_phone_fact_candidates':len(custom),'unsupported_schemas':len(limitations)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(run(Path(a.output).resolve()))
