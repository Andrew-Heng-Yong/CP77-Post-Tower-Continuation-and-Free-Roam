"""One-shot coordinator promotion of independently reviewed Ronald04 bytes.

No historical builder, installer, native fact reset, or game write is invoked.
"""
from pathlib import Path
import sys, shutil, copy
W=Path(__file__).resolve().parents[2]; O=Path(__file__).resolve().parent; C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
R=C/'repair_ronald_01'; assert not R.exists()
fp=O/'worker_b/experiments/future_owner_04/NOT_FOR_INTEGRATION.json'
mp=O/'worker_b/experiments/markers_04/NOT_FOR_INTEGRATION.json'
rp=O/'worker_c/reviews/ronald_01/verification_02/review.json'
np=O/'worker_a/reviews/ronald_namespace_03/evidence.json'
ip=O/'worker_a/reviews/ronald_namespace_03/implementation_plan.json'
f,m,r,n,ipd=map(read,[fp,mp,rp,np,ip])
assert sha(rp)=='96925D42960F5855CDC71A3E0CA24DA7E72310402D176A82C4DAC48094CA1AF4'
assert r['status']=='APPROVE_SOURCE_PLAN_REQUIRES_COORDINATOR_FINAL_GATES'
assert all(x['pass']for x in r['checks'])and n['checks']>0
assert n['status']=='PASS_PROVISIONAL_DEPOT_AND_ARCHIVEXL_NAMESPACE_FROZEN_OWNER04_MARKER04'
assert n['new_generated_id']==19913 and not n['new_depot_collisions']and not n['unsupported_quest_YAML']
for p in [fp,mp]:assert any(x.get('path')==str(p)and x['sha256']==sha(p)for x in r['input_pins'])
rows=[{'depot':x['intended_depot'],'source':x['raw'],'after':x['raw_sha256'],'before':x['source']['raw_sha256'],'approved_json':x['json'],'approved_json_sha256':x['json_sha256'],'intent':'Exact future-admission Armed splice; all old admission predicates, nodes and saved identities retained.'}for x in f['arming_producers']]
rows.extend([
 {'depot':f['intended_depot'],'source':f['raw'],'after':f['raw_sha256'],'before':None,'approved_json':f['json'],'approved_json_sha256':f['json_sha256'],'intent':'Future-only four selected native news branches; original two-game-day clocks and callbacks; existing enrolled contact only; no old entered/timer adoption.'},
 {'depot':m['intended_sector_depot'],'source':m['raw'],'after':m['raw_sha256'],'before':None,'approved_json':m['json'],'approved_json_sha256':m['json_sha256'],'intent':'Only two original trigger definitions/shapes/transforms with private global IDs; native source metadata retained.'},
 {'depot':m['intended_block_depot'],'source':m['block_raw'],'after':m['block_raw_sha256'],'before':None,'approved_json':m['block_json'],'approved_json_sha256':m['block_json_sha256'],'intent':'One private Quest descriptor leasing only the two-trigger sector.'}])
ep=O/'source_epoch_02.json'; e=read(ep); beforemap=e['source_resources']; actual={str(p.relative_to(C/'archive_source')):sha(p)for p in (C/'archive_source').rglob('*')if p.is_file()}
assert actual==beforemap
for x in rows:
 assert sha(x['source'])==x['after']and sha(x['approved_json'])==x['approved_json_sha256']
 assert beforemap.get(x['depot'])==x['before']
 assert any(y.get('raw_sha256')==x['after']for y in r['input_pins'])
 dst=C/'archive_source'/x['depot']; assert dst.resolve().is_relative_to((C/'archive_source').resolve())
 for p in [dst,*dst.parents]:
  if p.exists():assert not p.is_symlink()and not p.stat().st_file_attributes&0x400
xl=C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'; old=xl.read_bytes()
assert sha(xl)==ipd['source_guard']['candidate_XL_sha256']==e['xl_sha256']
# This mutation accepts only the already fully parsed/pinned standard candidate.
# Independent final review parses the resulting YAML again using YamlDotNet.
phases=old.split(b'streaming:')[0].count(b'    - path: ')
blocks=old.split(b'  blocks:')[1].split(b'localization:')[0].count(b'    - ')
assert phases==ipd['existing_candidate_phase_count']and blocks==ipd['existing_streaming_block_count']
quest=(O/'worker_a/reviews/ronald_namespace_03/quest_phase_append.txt').read_text().replace('\r\n','\n').rstrip('\n')+'\n'
block=(O/'worker_a/reviews/ronald_namespace_03/streaming_block_append.txt').read_text().replace('\r\n','\n').rstrip('\n')+'\n'
# Insert into the existing two lists without rewriting/reordering the YAML.
nl=b'\r\n'if b'\r\n'in old else b'\n'
qb=quest.encode().replace(b'\n',nl);bb=block.encode().replace(b'\n',nl)
assert old.count(b'streaming:'+nl)==old.count(b'localization:'+nl)==1
new=old.replace(b'streaming:'+nl,qb+b'streaming:'+nl).replace(b'localization:'+nl,bb+b'localization:'+nl)
assert quest==('    - path: '+f['intended_depot']+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out\n')
assert block=='    - '+m['intended_block_depot']+'\n'
assert new.replace(qb,b'',1).replace(bb,b'',1)==old
R.mkdir();(R/'before.archive.xl').write_bytes(old)
for x in rows:
 dst=C/'archive_source'/x['depot'];dst.parent.mkdir(parents=True,exist_ok=True)
 if x['before']:shutil.copyfile(dst,R/(Path(x['depot']).name+'.before'))
 shutil.copyfile(x['source'],dst);assert sha(dst)==x['after']
xl.write_bytes(new)
promotion={'status':'EXACT_APPROVED_RONALD04_PROMOTED_NOT_INSTALLED','rows':rows,'source_review':str(rp),'source_review_sha256':sha(rp),'namespace_review':str(np),'namespace_review_sha256':sha(np),'xl_before_sha256':e['xl_sha256'],'xl_after_sha256':sha(xl),'registration_id':19913,'registration_parent':'ep1\\quest\\ep1.quest','input':'[1].Out','append_only':True,'prior_registrations':phases,'prior_blocks':blocks,'remaining':r['live_limits']+n['limits'],'package_state':'ARCHIVE_PENDING_REBUILD','game_writes':0,'save_writes':0}
write(R/'promotion.json',promotion)
print({'status':promotion['status'],'existing_replacements':sum(x['before']is not None for x in rows),'new_resources':sum(x['before']is None for x in rows),'xl_after':sha(xl)})
