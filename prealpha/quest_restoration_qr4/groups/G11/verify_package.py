"""Independent QR4-vs-QR3 package review. Does not import any packer or builder."""
from lib import *
import argparse,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--archive-readback',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists(),'Fresh review output required';O.mkdir(parents=True)
C=Path(a.candidate).resolve();B=W/'prealpha/quest_restoration_qr3/candidate_01';EP=read(W/'prealpha/quest_restoration_qr4/source_epoch_00.json');mp=C/'package_manifest.json';assert mp.is_file(),'Wait for root package completion';manifest_hash=sha(mp);M=read(mp);BM=read(B/'package_manifest.json');RB=read(a.archive_readback);checks=[]
ALLOWED={r'towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase',r'towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase'}
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
def resources(folder):return {p.relative_to(folder).as_posix().replace('/','\\'):sha(p)for p in folder.rglob('*')if p.is_file()}
before=resources(B/'archive_source');after=resources(C/'archive_source');ck('same_exact_1574_depots',set(before)==set(after)and len(after)==1574,{'before':len(before),'after':len(after)});ck('QR3_source_matches_frozen_epoch00',before==EP['source_resources'],'Exact baseline pinned independently of new manifest')
delta=[{'depot':d,'before':before[d],'after':after[d]}for d in sorted(after)if before[d]!=after[d]];ck('only_two_approved_MQ007_payload_changes',{r['depot']for r in delta}==ALLOWED,delta)
for row in EP['qr3_repairs']['resources']:ck('QR3_corrected_donor_preserved '+row['depot'],after[row['depot']]==row['after'],{'expected':row['after'],'actual':after[row['depot']]})
ck('all_other_1572_payloads_unchanged',sum(before[d]==after[d]for d in before)==1572,'No changed official/world/native-controller resource')
readback={r['depot']:r['packed_sha256']for r in RB['resources']};ck('independent_packed_1574_keys_payloads',readback==after and RB['count']==1574,'WolvenKit ArchiveReader/Extract into memory, independent script and FNV map')
oldfiles={r['path']:r['sha256']for r in BM['files']};newfiles={r['path']:r['sha256']for r in M['files']};actualfiles={p.relative_to(C/'package').as_posix():sha(p)for p in(C/'package').rglob('*')if p.is_file()};ck('same_exact_51_managed_paths',set(oldfiles)==set(newfiles)==set(actualfiles)and len(newfiles)==51,{'before':len(oldfiles),'after':len(newfiles),'actual':len(actualfiles)})
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
out={'status':'PASS_INDEPENDENT_QR4_PACKAGE_DIFF_NOT_GAMEPLAY_CERTIFICATION','candidate':str(C),'baseline':str(B),'manifest_sha256':manifest_hash,'resource_count':len(after),'changed_resources':delta,'unchanged_resources':1572,'managed_paths':51,'changed_managed_files':filedelta,'unchanged_managed_files':50,'archive_sha256':sha(arc),'zip':str(zp),'zip_sha256':sha(zp),'checks':len(checks),'check_results':checks,'archive_readback':str(Path(a.archive_readback).resolve()),'archive_readback_sha256':sha(a.archive_readback),'preserved_QR3_repairs':EP['qr3_repairs']['resources'],'limits':['Package keys/bytes and QR3 preservation are verified separately from semantic repair review','No gameplay test, save migration or original owner liveness proof; native world/prefab/TDB opacity remains','No game/save/install/release writes, no game launch, no packer imported or run']}
save(O/'REPORT.json',out);save(O/'resource_delta.json',delta);save(O/'package_pins.json',{'files':actualfiles,'resources':after});print(json.dumps({'status':out['status'],'checks':len(checks),'changed_resources':len(delta),'managed_paths':51,'zip_sha256':sha(zp)}))
