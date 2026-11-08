"""Independent expected final source/delta pins; no coordinator checker imported."""
from inspect_archivexl import ROOT,HERE
from pathlib import Path
import json,hashlib
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
 out=HERE/'final_package_01/expected';out.mkdir(parents=True,exist_ok=False)
 ep=ROOT/'prealpha/quest_restoration_qr8/source_epoch_02.json';baseline=ROOT/'prealpha/quest_restoration_qr7/source_epoch_04.json';app=ROOT/'prealpha/quest_restoration_qr8/approved_changes_01.json';E=read(ep);B=read(baseline);A=read(app)
 assert sha(baseline)=='8B0D8249908A9D96CF5564C9581ED466C061350B96A4BEE767D744B01DE28A1F'
 assert E['epoch_key']=='QR8:02' and sha(app)==E['approved_changes_sha256'];assert len(A['resources'])==1 and not A['registration_changed'] and A['new_namespaces']==0
 repair=A['resources'][0];d=repair['depot'];assert d==r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase';assert repair['before']==B['source_resources'][d] and repair['after']==E['source_resources'][d]
 old=B['source_resources'];new=E['source_resources'];changed=sorted(k for k in old.keys()&new.keys() if old[k]!=new[k]);assert changed==[d] and set(old)==set(new)
 assert sha(repair['source_plan'])==repair['source_plan_sha256'] and sha(repair['independent_review'])==repair['independent_review_sha256']
 plan=read(repair['source_plan']);prototype=plan['private_source'];assert sha(prototype['raw'])==prototype['raw_sha256']==repair['after'];assert sha(prototype['json'])==prototype['json_sha256']
 candidate=Path(E['candidate']);manifest=candidate/'package_manifest.json';P=read(manifest);assert sha(manifest)==E['package_manifest_sha256'];assert E['archive_sha256']==P['archive_sha256'];assert E['zip_sha256']==P['zip_sha256']
 inputs={'epoch':str(ep),'epoch_sha256':sha(ep),'baseline':str(baseline),'baseline_sha256':sha(baseline),'approved':str(app),'approved_sha256':sha(app),'package_manifest':str(manifest),'package_manifest_sha256':sha(manifest),'candidate':str(candidate),'source':str(candidate/'archive_source'),'package':str(candidate/'package'),'archive':str(candidate/'package/archive/pc/mod/zzzz_PTFR_Combined.archive'),'archive_sha256':E['archive_sha256'],'zip':E['zip'],'zip_sha256':E['zip_sha256'],'canonical_resources':new,'changed':changed,'added':[],'deleted':[],'prototype':prototype,'prototype_plan':repair['source_plan'],'prototype_plan_sha256':repair['source_plan_sha256'],'independent_source_approval':repair['independent_review'],'independent_source_approval_sha256':repair['independent_review_sha256'],'native_namespace_capture':str(HERE/'namespace_capture_01/manifest.json'),'native_namespace_capture_sha256':sha(HERE/'namespace_capture_01/manifest.json'),'namespace_result':str(HERE/'namespace_verification_01/result.json'),'namespace_result_sha256':sha(HERE/'namespace_verification_01/result.json'),'prior_inherited_gate':str(HERE/'inherited_controls_02/result.json'),'prior_inherited_gate_sha256':sha(HERE/'inherited_controls_02/result.json'),'inherited':B['inherited_repair_resources']}
 (out/'inputs.json').write_text(json.dumps(inputs,indent=2),encoding='utf8');print({'epoch':E['epoch_key'],'resources':len(new),'delta':changed,'inputs':str(out/'inputs.json')})
if __name__=='__main__':main()
