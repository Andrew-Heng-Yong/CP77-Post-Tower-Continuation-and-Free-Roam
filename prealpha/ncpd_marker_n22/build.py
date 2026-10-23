"""Build one replacement script; no archive, owner or live-game writes."""
import hashlib, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL='r6/scripts/TowerContinued_NCPD_N21/ScannerRepairN21.reds'
OLD='B8B2182CA10EC1B5A4F5C82948FEEE15DD928B970E529D12781BADDC966E32BF'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def main(revision):
 assert re.fullmatch(r'n22_\d{2}',revision)
 out=HERE/'build'/revision;assert not out.exists();out.mkdir(parents=True)
 donor=ROOT/'prealpha/ncpd_repair_n21/build/n21_01/ScannerRepairN21.reds'
 oldmanifest=ROOT/'prealpha/ncpd_repair_n21/build/n21_01/build.json'
 assert sha(donor)==OLD
 assert sha(oldmanifest)=='9D04D0B257FF92A0A8318CBF6F2138CCE50F718607373A2E6078136446FBECE4'
 old=read(oldmanifest)
 original=donor.read_text(encoding='utf-8-sig');marker='public abstract class ScannerDataN21 {'
 assert original.count(marker)==1
 table=marker+original.split(marker)[1]
 base=(HERE/'ScannerRepairN21.reds').read_text(encoding='utf-8-sig')
 target=out/'ScannerRepairN21.reds';target.write_text(base.rstrip()+'\n\n'+table,encoding='utf-8')
 pins=[HERE/'build.py',HERE/'ScannerRepairN21.reds',donor,oldmanifest,ROOT/'research/ncpd_n21_live_20261014/assessment_01.json',ROOT/'research/ncpd_scanners_n2/catalog_v2.json']
 obj={'status':'BUILT_N22_SCRIPT_REPAIR_LIVE_PENDING','relative':REL,'old_sha256':OLD,'sha256':sha(target),'runtime_replacements':1,'additions':0,'archives_changed':0,'owners_changed':0,'supplemental_admission_changed':False,'generated_table_unchanged':True,'dataset':old['dataset'],'source_pins':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in pins},'scope':'Native entry activation for issued unfinished inactive entries with independent completion facts when saved marker record is absent. No owner restarts, native progress resets or synthetic mappins.'}
 (out/'build.json').write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'build':str(out),'sha256':sha(out/'build.json'),'script_sha256':sha(target)},indent=2))
if __name__=='__main__':main(sys.argv[1])
