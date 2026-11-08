"""Independent G08 native/raw review and exhaustive phone-direction check."""
import sys,copy,zlib,re
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import ext
def canon(x):
 if isinstance(x,list):return [canon(v)for v in x]
 if isinstance(x,dict):
  o={k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
  if o.get('$type')=='TweakDBID':
   v=o['$value'];o['$value']=str((len(v.encode('utf8'))<<32)|zlib.crc32(v.encode('utf8')))if o['$storage']=='string'else str(int(v));o['$storage']='uint64'
  return o
 return x
def run():
 O=H/'reviews/G08_evidence_01';assert not O.exists();P=H.parent/'G08';res=read(P/'results.json');ids=read(I.W/'prealpha/quest_restoration_qr5/progress.json')['groups']['G08']['ids'];M={};pins=[];tests=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 ck('frozen_Regina_shared_core',sha(res['shared_core'])==res['shared_core_sha256']=='9F659DCAE5B009EB46952236A067981FD56D8271B906D7F536F67A04E72D6BE2',{'path':res['shared_core'],'sha256':res['shared_core_sha256']})
 rec=[r for r in I.U['recipes']if r['id']in ids]
 for d in sorted({r['depot']for r in rec}|{'recipe:'+r['raw']for r in rec}|{d for d,r in I.IDX.items()if r.get('graphs')and any(q in d for q in ids)}|{I.HC,I.HS,I.CL}):M[d],p=I.load(d);pins.append(p);ck('independent_raw_pin '+d,not M[d]['errors'],p)
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,k,p='root'):return g(d,p)['nodes'][str(k)]
 for r in rec:
  gp=next(gp for gp,gr in M[r['depot']]['graphs'].items()if '65002'in gr['nodes']and gr['nodes']['65002']['type']=='questPauseConditionNodeDefinition')if r['kind']=='entry'else'root'
  for ni in r['ids']:
   if ni:ck('native_selected_payload '+r['depot']+str(ni),n(r['depot'],ni,gp)['payload']==ext(n('recipe:'+r['raw'],ni,r['graph'])['payload']),{'native':r['raw'],'native_graph':r['graph'],'current_graph':gp,'node':ni})
  ck('native_selected_edges '+r['depot'],g(r['depot'],gp)['edges']==sorted([[str(a),s,str(b),t]for a,s,b,t in r['edges']]),r['edges'])
 for x in read(res['raw_readback']):
  ck('fresh_actual_export_pins '+x['depot'],sha(x['raw'])==x['raw_sha256']and sha(x['json'])==x['json_sha256'],x)
  if x['depot']not in M:M[x['depot']],p=I.load(x['depot']);pins.append(p)
  ck('actual_binary_redecode_matches '+x['depot'],canon(Resource(read(x['json'])).normalize())==canon(M[x['depot']]),{'path':x['json'],'allowed_storage_only':'TweakDBID CRC32+UTF8 length, derived hashes removed'})
 # Query all actual positive request writes in all body/scene graphs, not just prebrief names.
 rx=re.compile(r'^(holo|audio)_(?:(.+)_calls_v|v_calls_(.+))_(start|end)_activate$');directions={}
 for q in ids:
  rows=[]
  for d,m in M.items():
   if q not in d or not d.startswith('base'):continue
   for gp,gr in m['graphs'].items():
    for ni,nd in gr['nodes'].items():
     for w in nd['writes']:
      match=rx.fullmatch(w['factName'])if w['value']==1 else None
      if not match:continue
      mode,inc,out,kind=match.groups();contact=inc or out;ack='holo_'+(contact+'_calls_v'if inc else'v_calls_'+contact)+'_'+kind+'_done';listeners=[i for i,nn in g(I.HC)['nodes'].items()if any(r.get('factName')==w['factName']for r in nn['reads'])];writers=[i for i,nn in g(I.HS,'scene')['nodes'].items()if any(ww.get('factName')==ack and ww['value']==1 for ww in nn['writes'])];row={'depot':d,'graph':gp,'node':ni,'request':w['factName'],'mode':mode,'direction':'incoming'if inc else'outgoing','contact':contact,'readers':listeners,'actual_ACK_writers':writers};rows.append(row);ck('all_direction_request_native_ownership '+q+gp+ni,contact=='reggie'and bool(listeners)and bool(writers),row)
  directions[q]=rows;ck('positive_request_sites_enumerated '+q,bool(rows),{'all_sites':len(rows),'outgoing_sites':sum(r['direction']=='outgoing'for r in rows)})
 # Original mandatory earned Tiny Mike prerequisite; no guessed admission bypass.
 tiny=next(r['depot']for r in rec if r['id']=='sts_wat_kab_01'and r['kind']=='entry');nativegate=[{'graph':gp,'node':ni,'read':r}for gp,gr in M[tiny]['graphs'].items()for ni,nd in gr['nodes'].items()for r in nd['reads']if r.get('factName')=='kab_107_finished'];ck('TinyMike_original_earned_prerequisite',bool(nativegate)and all(r['read'].get('comparisonType')=='Greater'for r in nativegate),nativegate)
 # Body fact/scene outcome checks independent of peer verifier code.
 outcome={}
 for q in ids:
  outcome[q]=[{'depot':d,'graph':gp,'node':ni,'writes':nd['writes'],'journals':nd['journal_paths']}for d,m in M.items()if q in d and d.startswith('base')for gp,gr in m['graphs'].items()for ni,nd in gr['nodes'].items()if nd['writes']or nd['reward']]
 ck('William_native_peace_and_gunshot_distinct',any(any(w['factName']=='kab_03_peace'and w['value']==1 for w in row['writes'])for row in outcome['sts_wat_kab_03'])and any(any(w['factName']=='kab_03_gun_shot'and w['value']==1 for w in row['writes'])for row in outcome['sts_wat_kab_03']),'original outcomes not collapsed')
 ck('Ripperdoc_bribe_and_escape_distinct',any(any(w['factName']=='kab_05_bribe_accepted'for w in row['writes'])for row in outcome['sts_wat_kab_05'])and any(any('escap'in w['factName']for w in row['writes'])for row in outcome['sts_wat_kab_05']),'authored bribe and escape receipts retained')
 for q in ids:
  sp=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(sp);pins.append({'path':str(sp),'sha256':sha(sp)});ck('stock_capture_keeps_limits '+q,bool(s['limits']),'runtime overrides and uncaptured children not certified')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'phone_directions.json',directions);write(O/'outcome_inventory.json',outcome);r={'status':'PASS_INDEPENDENT_SOURCE_REVIEW_WITH_EXPLICIT_LIMITS','group':'G08','quest_ids':ids,'checks':len(tests),'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'reviewed_results_sha256':sha(P/'results.json'),'findings':['Original entry/credit/map selected payloads and edges independently match, including DLC nested Tiny Mike entry and mandatory earned kab107-finished condition.','All13 actual raw exports match pinned bytes and independently normalized source models after exact TDBID encoding canonicalization.','All direction-aware native positive phone request sites are enumerated, linked to actual Regina controller readers and real ACK writers; no primary prebrief/debrief-only count is substituted.','Native William peace/gunshot and ripperdoc bribe/escape outcomes remain distinct; no new repair established.'],'remaining':['Tiny Mike earned default owner/R5 cohort, native kitchen prestate saved ownership and snapshot bugfix applicability remain conditional.','World prefab/actor placement, Johnny independent props/performer, phone scheduling, reward descendants and runtime overrides are not verified live.','No blanket static or gameplay PASS is claimed.'],'runtime_changes':[]};write(H/'reviews/G08.json',r);print({'checks':len(tests),'review':str(H/'reviews/G08.json'),'sha256':sha(H/'reviews/G08.json')})
if __name__=='__main__':run()
