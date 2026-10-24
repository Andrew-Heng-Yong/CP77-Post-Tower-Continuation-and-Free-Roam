from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;C=H/'candidate_01';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
rel='r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds';p=G/rel;s=p.read_text(encoding='utf-8-sig')
assert 'import PTFR.Housing.*' in s
needle='    if q.GetFact(n"PTFRB0WV_Enabled") == 1 {';assert s.count(needle)==1
s=s.replace(needle,'    WilsonLeaseH2.Reconcile(game);\n'+needle)
needle='      if q.GetFact(n"mq011_active") != 0 { allowed = false; }';assert s.count(needle)==1
s=s.replace(needle,needle+'\n      if q.GetFact(n"PTFRB0WV_QuestOwns") != 0 { allowed = false; }')
b=C/'before'/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,b)
dest=C/'package'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(s,encoding='utf-8')
changes=json.loads((C/'changes_01.json').read_text());changes.append({'target':rel,'before':sha(p),'after':sha(dest)})
rel='r6/scripts/TowerContinued_Housing_H1/WilsonLeaseH2.reds';dest=C/'package'/rel;assert not (G/rel).exists();shutil.copyfile(H/'WilsonLeaseH2.reds',dest);changes.append({'target':rel,'before':None,'after':sha(dest)})
(C/'changes_02.json').write_text(json.dumps(changes,indent=2)+'\n')
print(json.dumps({'script_changes':len(changes)}))
