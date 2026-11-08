"""Fresh bounded resolution of coordinator fixes, no publisher execution."""
from pathlib import Path
import sys,ast,json,argparse
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
def run(O):
 assert not O.exists();tests=[];pins=[]
 def take(rel):
  p=F/rel;pins.append({'path':str(p),'sha256':sha(p)});return read(p)
 def ck(k,v,e):tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 q=take('queue.json');d=take('defects_and_repairs.json');a=take('adjudications/G03_02_crosswriter.json');m=take('contract_status_matrix.json');ep=take('source_epoch_08.json');man=take('candidate_03/package_manifest.json');p=take('progress.json')
 cv=next(x for x in q['quests']if x['id']=='sts_pac_cvi_02');sp=next(x for x in q['quests']if x['id']=='sts_hey_spr_01');co=take('groups/G13/corrections/G02_SPR01/verification_02/correction.json')
 for k in ['journal','shared_dependencies']:
  ck('CVI02 native crosswriter link applied '+k,'Native NID02 OW graphroot/4/138 node72'in' '.join(cv['contracts'][k]['proven'])and any('CONDITIONAL_FOREIGN_NATIVE_WRITER'in str(z)for z in cv['contracts'][k]['remaining'])and cv['contracts'][k]['status']==a['updated_contracts'][k]['status'],cv['contracts'][k]['remaining'])
  rr=next(r for r in m if r.get('quest_id')==cv['id']and r['stage']==k);ck('CVI02 matrix retains crosswriter '+k,'Native NID02 OW graphroot/4/138 node72'in' '.join(rr['proven']),rr['status'])
 ck('CVI02 five branch failures retained',sum(v['status']=='FAIL'for v in cv['contracts'].values())==5,'crosswriter is unchanged native conditional behavior, independent of confirmed alternate EP1 call failure')
 cc=sp['contracts']['communications'];ck('G02 outgoing correction source preserved',cc['status']=='CONDITIONAL'and cc['findings_source']==co['corrected']and cc['findings_source_sha256']==co['corrected_sha256']==sha(co['corrected'])and cc['source_correction']['independent_review_sha256']==sha(cc['source_correction']['independent_review']),cc['source_correction'])
 fs=(F/'finalize_qr5.py').read_text(encoding='utf-8-sig');ws=(F/'write_reports.py').read_text(encoding='utf-8-sig');ast.parse(fs);ast.parse(ws)
 for name in ['finalize_qr5.py','write_reports.py']:pins.append({'path':str(F/name),'sha256':sha(F/name)})
 ck('finalizer preserves active G02 source and separate original',"v['original_findings_source']=str(fp)"in fs and "if v.get('source_correction'):"in fs and "v['findings_source']==cp['corrected']"in fs and 'v.update(findings_source=str(fp),findings_source_sha256=sha(fp),'not in fs,'source_correction independently reviewed pointer remains explicit; base peer can coexist')
 ck('finalizer exact package and ledger gate',"defs['new_repaired_unique_defects']==len(manifest['changed_resources'])==len(e['changes'])"in fs and "defs['new_confirmed_unique_defects']==defs['new_repaired_unique_defects']+defs['new_blocked_unique_defects']"in fs,'fails closed before publishing counts')
 ck('current ledger reconciles7confirmed5repaired2blocked',d['new_confirmed_unique_defects']==7 and d['new_repaired_unique_defects']==len(man['changed_resources'])==len(ep['changes'])==5 and d['new_blocked_unique_defects']==2,'new Ronald family adds one unique blocked family/four affected selected gigs; five runtime repairs unchanged')
 ck('report reads latest ledger count, not stale6',"full ledger has{defs['new_confirmed_unique_defects']}"in ws and "both blocked families"in ws and 'Ronald' in ws,'package manifest5 means packaged repairs; final ledger7 means all confirmed defects')
 ck('original integration findings retained',sha(H/'verification_01/review.json')=='20320CD108C0873EDC4BA0A230674A51D11ED863FC5C81F87ECD06AE0823C7D4','fresh resolution; original issue snapshot not overwritten')
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);out={'status':'PASS_BOUNDED_CENTRAL_CORRECTION_RESOLUTION','checks':len(tests),'supersedes_review_disposition_only':str(H/'verification_01/review.json'),'findings_closed':['CVI02 native crosswriter affected-contract cross-link','G02 corrected-source provenance overwrite','promoted candidate03 ledger finalization gate'],'current_counts':{'confirmed_new':7,'repaired_new':5,'blocked_new':2},'limits':['Read-only metadata/script inspection; no central publisher executed and no runtime inputs changed.','Original review01 remains exact historical snapshot; current mutable queue may receive final coordinator-only metadata publication.'],'runtime_changes':[],'code_sha256':sha(__file__)};write(O/'review.json',out);print(json.dumps(out))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
