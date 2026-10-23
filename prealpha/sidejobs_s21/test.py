"""Bind focused policy tests to an immutable S2.1 build and unchanged native owners."""
import json, subprocess, sys
from pathlib import Path
from build import HERE, ROOT, REL, OLD, sha, read
def main(revision):
 out=HERE/'build'/revision;dest=out/'tests.json';assert not dest.exists()
 m=read(out/'build.json');assert m['relative']==REL and m['old_sha256']==OLD
 assert sha(out/'SideJobsS2.reds')==m['sha256']==sha(HERE/'SideJobsS2.reds')
 for path,digest in m['source_pins'].items(): assert sha(ROOT/path)==digest,path
 evidence=out/'policy.json'
 run=subprocess.run([sys.executable,str(HERE/'test_policy.py'),'--output',str(evidence)],capture_output=True,text=True,timeout=90)
 assert run.returncode==0,run.stdout+run.stderr
 p=read(evidence);assert p['status']=='PASS' and p['modeled_cases']>=855
 old=read(ROOT/'prealpha/sidejobs_s2/build/s2_02/build.json')
 game=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
 unchanged={}
 for row in old['files'][:2]:
  target=game/row['relative'];assert sha(target)==row['sha256'];unchanged[str(target)]=sha(target)
 report={'status':'PASS_NOT_LIVE','build_sha256':sha(out/'build.json'),'tester_sha256':sha(Path(__file__)),'policy_tester_sha256':sha(HERE/'test_policy.py'),'policy_cases':p['modeled_cases'],'checks':p['checks'],'generated_table_unchanged':True,'owners_unchanged':True,'native_archives':unchanged,'limitations':['Offline source/model/compiler proof does not establish in-game admission or interaction delivery.','Failed and halfway side-job replay not implemented by this authorization repair.']}
 dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main(sys.argv[1])
