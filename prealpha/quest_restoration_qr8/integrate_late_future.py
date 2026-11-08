"""One-shot promotion of the independently approved four-guard serialized bytes."""
from pathlib import Path
import sys,shutil,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not C.exists(),'Fresh successor only'
pp=O/'worker_b/late_future_plan_01.json';p=read(pp);rp=O/'worker_c/reviews/late_future_02/review.json';r=read(rp);ep=O/'source_epoch_00.json';e=read(ep);prior=Path(e['candidate']);s=p['private_source']
assert sha(pp)=='044C3AA43946A2EA417199C1CFCFDA4A1DD03DF79919CCE507D8EC5D4B45D8DA'
assert r['status']=='APPROVED_MINIMAL_SOURCE_CONFIRMED_FOUR_GATE_REPAIR_FOR_COORDINATOR_INTEGRATION'and all(x['pass']for x in r['checks'])
assert r['approved_proposal']['raw_sha256']==s['raw_sha256']=='6CEB6AC9FA2909771AEEF09D33A36241E1396D26A072725317374837AB79B0EC'
assert sha(s['raw'])==s['raw_sha256']and sha(s['json'])==s['json_sha256']==r['approved_proposal']['json_sha256']
assert r['approved_proposal']['manifest']==p['hash_observations'][0]['path']and sha(r['approved_proposal']['manifest'])==p['hash_observations'][0]['sha256']
assert sha(p['verification']['path'])==p['verification']['sha256']
actual={str(f.relative_to(prior/'archive_source')):sha(f)for f in(prior/'archive_source').rglob('*')if f.is_file()};assert actual==e['source_resources']
assert all(sha(prior/'package'/x['path'])==x['sha256']for x in e['package_files'])
depot=s['intended_depot'];assert depot==r'towercontinued\quest_restoration_qr7\ronald_news_future.questphase'
assert e['source_resources'][depot]==s['source']['raw_sha256']==sha(s['source']['raw'])
for root in [prior/'archive_source',prior/'package']:
 for f in [root,*root.rglob('*')]:assert not f.is_symlink()and not f.stat().st_file_attributes&0x400
C.mkdir();shutil.copytree(prior/'archive_source',C/'archive_source');shutil.copytree(prior/'package',C/'package');D=C/'repair_late_future_01';D.mkdir()
dest=C/'archive_source'/depot;assert dest.resolve().is_relative_to((C/'archive_source').resolve())
shutil.copyfile(dest,D/'before.questphase');shutil.copyfile(s['raw'],dest);assert sha(dest)==s['raw_sha256']
promotion={'status':'PROMOTED_EXACT_C_APPROVED_SERIALIZED_FOUR_GUARD_REPAIR_NOT_INSTALLED','depot':depot,'before':s['source']['raw_sha256'],'after':sha(dest),'approved_json':s['json'],'approved_json_sha256':s['json_sha256'],'plan':str(pp),'plan_sha256':sha(pp),'source_review':str(rp),'source_review_sha256':sha(rp),'verification':p['verification'],'source_scope':s['scope'],'limits':r['limits'],'unchanged_XL_sha256':e['xl_sha256'],'package_state':'PREDECESSOR_ARCHIVE_COPIED_AWAITS_REBUILD','game_writes':0,'save_writes':0}
write(D/'promotion.json',promotion)
print({'status':promotion['status'],'changed_existing_resources':1,'new_resources':0,'depot':depot})
