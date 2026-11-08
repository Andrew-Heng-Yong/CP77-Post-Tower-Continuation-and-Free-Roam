"""Independent QR5-vs-QR4 package review. Does not import any packer or builder."""
from lib import *
import argparse,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--archive-readback',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh review output required';O.mkdir(parents=True)
C=Path(a.candidate).resolve();B=W/'prealpha/quest_restoration_qr4/candidate_01';EP=read(W/'prealpha/quest_restoration_qr5/source_epoch_00.json');mp=C/'package_manifest.json';assert mp.is_file(),'Wait for root package completion';manifest_hash=sha(mp);M=read(mp);BM=read(B/'package_manifest.json');RB=read(a.archive_readback);checks=[]
ALLOWED={r'towercontinued\native_gigs_u9\sts_std_arr_12_entry.questphase'}
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
def resources(folder):return {p.relative_to(folder).as_posix().replace('/','\\'):sha(p)for p in folder.rglob('*')if p.is_file()}
before=resources(B/'archive_source');after=resources(C/'archive_source');ck('same_exact_1574_depots',set(before)==set(after)and len(after)==1574,{'before':len(before),'after':len(after)});ck('QR4_source_matches_frozen_epoch00',before==EP['source_resources'],'Exact baseline pinned independently of new manifest')
delta=[{'depot':d,'before':before[d],'after':after[d]}for d in sorted(after)if before[d]!=after[d]];ck('only_one_approved_ARR12_payload_change',{r['depot']for r in delta}==ALLOWED,delta)
for row in EP['prior_repairs']:ck('all_four_prior_repairs_preserved '+row['depot'],after[row['depot']]==row['after'],{'expected':row['after'],'actual':after[row['depot']]})
ck('all_other_1573_payloads_unchanged',sum(before[d]==after[d]for d in before)==1573,'No changed official/world/native-controller resource')
readback={r['depot']:r['packed_sha256']for r in RB['resources']};ck('independent_packed_1574_keys_payloads',readback==after and RB['count']==1574,'WolvenKit ArchiveReader/Extract into memory, independent script and FNV map')
oldfiles={p.relative_to(B/'package').as_posix():sha(p)for p in(B/'package').rglob('*')if p.is_file()};ck('QR4_manifest_matches_actual_baseline51',oldfiles=={r['path']:r['sha256']for r in BM['files']},'Actual predecessor files read independently');newfiles={r['path']:r['sha256']for r in M['files']};actualfiles={p.relative_to(C/'package').as_posix():sha(p)for p in(C/'package').rglob('*')if p.is_file()};ck('same_exact_51_managed_paths',set(oldfiles)==set(newfiles)==set(actualfiles)and len(newfiles)==51,{'before':len(oldfiles),'after':len(newfiles),'actual':len(actualfiles)})
ck('manifest_matches_actual51',newfiles==actualfiles,'All actual managed files hashed')
filedelta=[{'path':p,'before':oldfiles[p],'after':newfiles[p]}for p in sorted(newfiles)if oldfiles[p]!=newfiles[p]];ck('only_archive_file_changed',[r['path']for r in filedelta]==['archive/pc/mod/zzzz_PTFR_Combined.archive'],filedelta)
ck('50_other_files_including_REDS_XL_unchanged',sum(oldfiles[p]==newfiles[p]for p in oldfiles)==50,'46 REDscript files, XL, Lua and all other managed paths unchanged')
arc=C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive';ck('archive_readback_manifest_actual_hash_agree',sha(arc)==RB['archive_sha256']==M['archive_sha256']==newfiles['archive/pc/mod/zzzz_PTFR_Combined.archive'],sha(arc))
zp=Path(M['zip']);zp=zp if zp.is_absolute()else C/zp
if not zp.is_file()and not Path(M['zip']).is_absolute():zp=W/M['zip']
ck('zip_exists_and_hash_matches',zp.is_file()and sha(zp)==M['zip_sha256'],{'zip':str(zp),'sha256':sha(zp)if zp.is_file()else None})
with zipfile.ZipFile(zp)as z:
 entries=[i for i in z.infolist()if not i.is_dir()];names=[i.filename for i in entries];ck('ZIP_CRC',z.testzip()is None,'Every ZIP entry CRC checked');ck('ZIP_exact51_unique_paths',len(names)==len(set(names))==51 and set(names)==set(newfiles),names)
 for entry in entries:ck('ZIP_payload '+entry.filename,hashlib.sha256(z.read(entry.filename)).hexdigest().upper()==newfiles[entry.filename],{'bytes':entry.file_size,'crc':entry.CRC})
ck('manifest_not_changed_during_review',sha(mp)==manifest_hash,manifest_hash)
# Canonical current linkage and bounded compilation reuse, independent of root packer.
Q=W/'prealpha/quest_restoration_qr5';A=read(Q/'approved_changes_02.json');CE=read(Q/'source_epoch_02.json');ck('approved_allowlist_exact_actual_delta',A['resources'][0]['depot']==delta[0]['depot']and A['resources'][0]['before']==delta[0]['before']and A['resources'][0]['after']==delta[0]['after']and len(A['resources'])==1,A['resources'])
for row in A['resources']:
 rr=Path(row['independent_serialized_review']);ck('independent_serialized_review_pin',sha(rr)==row['independent_serialized_review_sha256']and read(rr)['after_sha256']==row['after'],str(rr))
ck('canonical_epoch02_resource_map',CE['source_resources']==after,'Canonical staged resources, actual source bytes')
ck('canonical_epoch02_actual_archive_hash',CE['archive_sha256']==sha(arc),'Current archive field is current actual, not predecessor')
ck('canonical_epoch02_packagefiles', {r['path']:r['sha256']for r in CE['package_files']}==actualfiles,'Current51paths actualbytes')
ck('canonical_epoch02_manifest_allowlist_linkage',CE['package_manifest_sha256']==sha(mp)and CE['approved_changes_sha256']==sha(Q/'approved_changes_02.json'),'No stale top-level epoch hash')
xl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl';ck('no_new_ArchiveXL_generated_IDs_or_registrations',(C/'package'/xl).read_bytes()==(B/'package'/xl).read_bytes(),'XL exact bytes, no new depot keys, same generated-ID namespace')
reuse=read(Q/'compile_reuse.json');prior=Path(reuse['prior_result']);ck('successful_compile_result_pin',sha(prior)==reuse['prior_result_sha256'],str(prior));pc=read(prior);ck('prior_success131_sources',pc['status']=='PASS'and pc['exit_code']==0 and pc['source_count']==131,'No SCC rerun; success reused only with exact current inputs')
for path,h in pc['input_pins'].items():ck('compiler_cache_source_pin '+path,sha(path)==h,h)
stagedroot=prior.parent/'scripts/game';staged={str(Path(k).resolve()):v for k,v in pc['staged_sources'].items()};scripts=list((C/'package/r6/scripts').rglob('*.reds'));ck('actual_managed46',len(scripts)==46,'Staged package sources')
for p in scripts:
 oldpath=str((stagedroot/p.relative_to(C/'package/r6/scripts')).resolve());ck('managed_source_exact_compile_fixture '+p.name,oldpath in staged and sha(p)==staged[oldpath]['sha256'],oldpath)
ck('compile_reuse_record_counts',reuse['sources']==131 and reuse['staged_managed_sources']==46 and reuse['compiler_cache_input_pins']==len(pc['input_pins'])==134 and reuse['fresh_SCC_invocation']is False,'131source/134input/46managed, no unchanged rebuild')
out={'status':'PASS_INDEPENDENT_QR5_PACKAGE_DIFF_NOT_GAMEPLAY_CERTIFICATION','candidate':str(C),'baseline':str(B),'manifest_sha256':manifest_hash,'canonical_epoch':str(Q/'source_epoch_02.json'),'canonical_epoch_sha256':sha(Q/'source_epoch_02.json'),'resource_count':len(after),'changed_resources':delta,'unchanged_resources':1573,'managed_paths':51,'changed_managed_files':filedelta,'unchanged_managed_files':50,'archive_sha256':sha(arc),'zip':str(zp),'zip_sha256':sha(zp),'checks':len(checks),'check_results':checks,'archive_readback':str(Path(a.archive_readback).resolve()),'archive_readback_sha256':sha(a.archive_readback),'preserved_all_four_prior_repairs':EP['prior_repairs'],'compile_reuse':{'sources':131,'input_pins':134,'managed_sources':46,'fresh_SCC':False},'limits':['Package keys/bytes and all prior repair resources are verified separately from semantic repair/source review','No gameplay, saved owner liveness, sector placement or runtime TweakDB override proof','ARR12 supports only new future entry event; already entered/progressed saves are not retroactively enrolled','No game/save/install/release writes or game launch; no root packer imported or run']}
save(O/'REPORT.json',out);save(O/'resource_delta.json',delta);save(O/'package_pins.json',{'files':actualfiles,'resources':after});print(json.dumps({'status':out['status'],'checks':len(checks),'archive_sha256':sha(arc),'zip_sha256':sha(zp)}))
