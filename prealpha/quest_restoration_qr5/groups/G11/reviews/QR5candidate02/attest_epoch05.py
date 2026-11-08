"""Bounded linkage attestation after a metadata-only canonical epoch correction."""
from pathlib import Path
import json,hashlib,argparse
H=Path(__file__).resolve().parent;Q=H.parents[3]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def run(O):
 assert not O.exists();O.mkdir(parents=True);T=[]
 def ck(k,v,e):T.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 old=Q/'source_epoch_04.json';new=Q/'source_epoch_05.json';A=read(old);B=read(new);prior=H/'verification_01/REPORT.json';P=read(prior);C=Path(B['candidate']);mp=C/'package_manifest.json';M=read(mp);allow=Q/'approved_changes_03.json'
 ck('frozen independent280-control package report',sha(prior)=='755D3CE2D80EC8336C6574417020C10B2D41C9E31DDBC1655D7268E98C33297E'and P['checks']==280 and all(x['status']=='PASS'for x in P['check_results']),str(prior))
 ck('exact04predecessor pin',Path(B['predecessor_epoch_path']).resolve()==old.resolve()and B['predecessor_epoch_sha256']==sha(old),str(old))
 changed={k for k in set(A)|set(B)if A.get(k)!=B.get(k)}
 ck('metadata correction bounded fields',changed=={'epoch','epoch_key','predecessor_epoch_path','predecessor_epoch_sha256','scope','metadata_only','metadata_correction'},sorted(changed))
 ck('canonical05four-repair scope',B['metadata_only']is True and B['epoch']==5 and 'four independently reviewed private-resource repairs'in B['scope']and'after one'not in B['scope'],B['scope'])
 ck('source1574map04equals05',A['source_resources']==B['source_resources']and len(B['source_resources'])==1574,'No source map changed for prose correction')
 ck('all51packagepins04equals05',A['package_files']==B['package_files']and len(B['package_files'])==51,'No package bytes changed for prose correction')
 actual={p.relative_to(C/'archive_source').as_posix().replace('/','\\'):sha(p)for p in(C/'archive_source').rglob('*')if p.is_file()}
 ck('actualsource1574stillmatchespriorreviewandcanonical05',actual==B['source_resources']==read(H/'verification_01/package_pins.json')['resources'],'Source bytes measured again; no archive re-extraction needed')
 files={p.relative_to(C/'package').as_posix():sha(p)for p in(C/'package').rglob('*')if p.is_file()}
 ck('actualpackage51stillmatches05',files=={x['path']:x['sha256']for x in B['package_files']}=={x['path']:x['sha256']for x in M['files']},'All actual staged managed files measured')
 ck('archivehashactualreadback05',sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive')==B['archive_sha256']==M['archive_sha256']==P['archive_sha256'],P['archive_sha256'])
 ck('ZIPactualunchanged',sha(M['zip'])==M['zip_sha256']==P['zip_sha256'],P['zip_sha256'])
 ck('canonicalmanifestandallowlistlinks',B['package_manifest_sha256']==sha(mp)==P['manifest_sha256']and B['approved_changes_sha256']==sha(allow),{'manifest':sha(mp),'allowlist':sha(allow)})
 ck('fourapprovedchangesunmodified',A['changes']==B['changes']==read(allow)['resources']and len(B['changes'])==4,'Includes exact before/after and independent source/serialized reviews')
 ck('fourpriorrepairpinsstillpreserved',all(actual[r['depot']]==r['after']for r in B['prior_repairs'])and A['prior_repairs']==B['prior_repairs'],'QR3MQ030/MQ037 and both QR4MQ007 bytes preserved')
 ck('metadataambiguityresolvedwithoutsourcechanges',P['metadata_scope_limit']is True and B['metadata_correction']['previous_scope']==A['scope'],'Original epoch04 reviewed contradiction retained as evidence; epoch05 supersedes only metadata')
 out={'status':'PASS_CANONICAL_EPOCH05_AND_FINAL_PACKAGE_LINKAGE','checks':len(T),'tests':T,'package_review':str(prior),'package_review_sha256':sha(prior),'canonical_epoch':str(new),'canonical_epoch_sha256':sha(new),'archive_sha256':P['archive_sha256'],'zip_sha256':P['zip_sha256'],'source_resources':1574,'changed_resources':4,'unchanged_resources':1570,'managed_paths':51,'unchanged_managed_paths':50,'compile_reuse':P['compile_reuse'],'no_deployment':True,'limits':P['limits']+['CVI02 EP1 custom Hands controller defect remains blocked by exact marker/default lease and actor acquisition evidence; package byte PASS does not clear it.']}
 (O/'review.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'status':out['status'],'checks':len(T),'sha256':sha(O/'review.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(Path(a.output).resolve())
