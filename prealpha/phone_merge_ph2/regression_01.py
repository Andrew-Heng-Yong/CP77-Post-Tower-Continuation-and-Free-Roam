import sys
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(W/'prealpha/phone_support_ph1'))
from model import *
import binascii
C=H/'candidate_01';B=W/'prealpha/phone_support_ph1/candidate_03';proof=read(H/'id_proof_01.json')
assert set(model(W/'research/q307_extracted/json/ep1/quest/ep1.quest.json')['root']['nodes'])==set(proof['native_ids'])
old=proof['old_path'];new=proof['new_path'];xl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl'
assert (C/'package'/xl).read_bytes()==(B/'package'/xl).read_bytes().replace(old.encode(),new.encode())
assert (C/'archive_source'/old).read_bytes()==(C/'archive_source'/new).read_bytes()
assert sha(C/'archive_source'/new)==read(C/'semantic_verification_01.json')['alias_sha256']
oldregs=proof['inventory'];regs=[dict(r,path=new,id=proof['new_id']) if r['path']==old else r for r in oldregs]
phones=[r for r in regs if r['path'].startswith(('towercontinued\\phone_support_ph1\\','towercontinued\\phone_merge_ph2\\'))]
assert len(phones)==6
for r in phones:
 assert r['id'] not in proof['native_ids']
 assert sum(x['id']==r['id'] for x in regs)==1,r
 assert r['id']==binascii.crc_hqx((r['path']+':1').encode(),65535)
assert len(proof['conflicts'])==2 and proof['conflicts'][0]['id']==40560
assert any(r['path']=='towercontinued\\native_gigs_u9\\sts_wat_kab_101_map1.questphase' for r in regs)
assert len(regs)==len(oldregs)
for f in proof['xl_files']:assert sha(Path(f['path']))==f['sha256'],'Installed XL changed during build'
out={'status':'PASS_ALIAS_REGISTRATION_AND_COLLISION_REGRESSION','old_collision_reproduced':proof['conflicts'],'new_id':proof['new_id'],'all_six_phone_registrations_unique':True,'root_registrations_checked':len(regs),'native_ids':proof['native_ids'],'xl_change':'One path substitution only','alias_payload':'byte-identical','native_map_registration_preserved':True,'scripts_changed':0,'live_result':'PENDING'}
(C/'registration_regression_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
