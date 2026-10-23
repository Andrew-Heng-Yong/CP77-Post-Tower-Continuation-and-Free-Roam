"""Build the isolated S2.1 authorization repair; no game or save writes."""
import hashlib, json, re, shutil, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds'
OLD='5C687B1356584D17204CA342332E4273D8B18CB1ECDFF6C27CA260397052883E'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main(revision):
 assert re.fullmatch(r's21_\d{2}',revision)
 out=HERE/'build'/revision;assert not out.exists();out.mkdir(parents=True)
 donor=ROOT/'prealpha/sidejobs_s2/build/s2_02/SideJobsS2.reds'
 oldmanifest=ROOT/'prealpha/sidejobs_s2/build/s2_02/build.json'
 assert sha(donor)==OLD
 assert sha(oldmanifest)=='6B3FB20725472BA85C6F210B9EDE0B8681509039B09FE5ED12581CEF6959ABE6'
 old=read(oldmanifest)
 target=out/'SideJobsS2.reds';shutil.copy2(HERE/'SideJobsS2.reds',target)
 marker='public abstract class SideJobDataS2 {'
 original=donor.read_text(encoding='utf-8-sig');new=target.read_text(encoding='utf-8-sig')
 assert original.split(marker)[1]==new.split(marker)[1], 'Native data changed'
 pins=[HERE/'build.py',HERE/'SideJobsS2.reds',donor,oldmanifest,ROOT/'prealpha/sidejobs_s2/admission.json',ROOT/'prealpha/sidejobs_s2/deploy.ps1',ROOT/'research/sidejobs_s21_failed/inventory_01.json',ROOT/'research/activity_state_r3/definition.json',ROOT/'research/gig_restoration/lore_whitelists_v4_cast.json']
 obj={'status':'BUILT_S21_SCRIPT_REPAIR_LIVE_PENDING','relative':REL,'old_sha256':OLD,'sha256':sha(target),'runtime_replacements':1,'additions':0,'archives_changed':0,'owners_changed':0,'native_guards_unchanged':True,'generated_table_unchanged':True,'dataset':[r['key'] for r in old['activities']],'source_pins':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in pins},'scope':'Explicit S2-local disposable fresh-fixture authorization, plus read-only 58-whitelist Failed inventory and available native progress diagnostics. Same production certificate, freshness and native owners; no native progress/journal/reward resets, failed replay or partial migration.'}
 (out/'build.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'build':str(out),'sha256':sha(out/'build.json'),'script_sha256':sha(target)},indent=2))
if __name__=='__main__':main(sys.argv[1])
