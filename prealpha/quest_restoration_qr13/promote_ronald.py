"""Coordinator-only fresh successor creation from approved typed Ronald bytes."""
from pathlib import Path
import hashlib,json,shutil,stat
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def main():
 c=H/'candidate_01';assert not c.exists()
 base=read(H/'baseline.json');old=Path(base['candidate']);ep=read(base['source_epoch'])
 review_path=H/'worker_c/ronald_serialized_01/review.json';review=read(review_path);assert str(review['status']).startswith(('APPROVE','PASS'))
 typed_path=H/'coordinator/ronald_02/serialized_01/manifest.json';typed=read(typed_path)
 # Source and unchanged package identity are checked before any copying.
 assert {str(p.relative_to(old/'archive_source')):sha(p)for p in(old/'archive_source').rglob('*')if p.is_file()}==base['source_resources']
 assert {p.relative_to(old/'package').as_posix():sha(p)for p in(old/'package').rglob('*')if p.is_file()}==base['package_files']
 for root in [old/'archive_source',old/'package']:
  for p in [root,*root.rglob('*')]:assert not p.is_symlink()and not(p.stat().st_file_attributes&0x400)
 c.mkdir();shutil.copytree(old/'archive_source',c/'archive_source');shutil.copytree(old/'package',c/'package')
 changes=[]
 for r in typed['resources']:
  assert sha(r['raw'])==r['raw_sha256']and sha(r['readback_json'])==r['readback_json_sha256']
  target=c/'archive_source'/r['depot'];assert target.resolve().is_relative_to((c/'archive_source').resolve())
  before=sha(target);assert before==base['source_resources'][r['depot']];assert before!=r['raw_sha256']
  shutil.copyfile(r['raw'],target);assert sha(target)==r['raw_sha256'];changes.append({'depot':r['depot'],'before':before,'after':sha(target),'readback':r['readback_json'],'source_review':str(review_path),'source_review_sha256':sha(review_path)})
 promotion={'status':'APPROVED_RONALD_SOURCE_PACKAGE_PENDING_OTHER_COMPONENT_DECISION','relative_to':'QR8:02','resources':changes,'changed_script_paths':[],
  'typed_manifest':str(typed_path),'typed_manifest_sha256':sha(typed_path),'package_state':'COPIED_PREDECESSOR_ARCHIVE_AWAITS_CONSOLIDATED_REBUILD','installed':False,'game_writes':0,'save_writes':0}
 (c/'promotion.json').write_text(json.dumps(promotion,indent=2)+'\n',encoding='utf-8')
 sources={str(p.relative_to(c/'archive_source')):sha(p)for p in(c/'archive_source').rglob('*')if p.is_file()}
 epoch={'epoch_key':'QR13:00','candidate':str(c),'source_resources':sources,'package_files':base['package_files'],'resources_changed':changes,'relative_to':base['source_epoch'],'relative_to_sha256':base['source_epoch_sha256'],
  'package_state':promotion['package_state'],'runtime_source_only':True,'new_depots':[],'XL_unchanged':True,'installed':False}
 (H/'source_epoch_00.json').write_text(json.dumps(epoch,indent=2)+'\n',encoding='utf-8')
 p=H/'checkpoint.json';s=read(p);s.update(state='QR13_RONALD_SOURCE_STAGED_BRENDAN_IMPLEMENTATION_PENDING',staged_successor=str(c),runtime_changes=len(changes),canonical_source_epoch=str(H/'source_epoch_00.json'),next='Finish conservative earned-Brendan implementation/review, then compile if REDS change and rebuild/read back entire consolidated archive; no installation.')
 p.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8');print({'source_resources':len(sources),'changed':len(changes),'candidate':str(c),'package':'PENDING_REBUILD'})
if __name__=='__main__':main()
