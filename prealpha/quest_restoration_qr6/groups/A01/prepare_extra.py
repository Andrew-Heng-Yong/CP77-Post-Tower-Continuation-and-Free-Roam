from pathlib import Path
import sys
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));from source_lib import *
if __name__=='__main__':
 a=read(W/'prealpha/consolidation_repair_cr1/raymond/assessment_01.json');out=[]
 for d in [r'base\quest\cyberpunk2077.questphase',r'ep1\quest\main_quests\q307\q307.quest']:
  j=W/'research/q307_extracted/json'/(d+'.json');raw=W/'research/q307_extracted/raw'/d;h=a['sources'][j.relative_to(W).as_posix()]['sha256'];assert sha(j)==h;out.append(dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=h,provenance='Pinned original CR1 Raymond source JSON and existing native raw; fresh export follows'))
 write(H/'extra_inputs.json',out)
