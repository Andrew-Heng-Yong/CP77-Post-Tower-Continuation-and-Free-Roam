"""Summarize immutable pre-fix getter evidence without game/save mutation."""
import json,math
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT,sha
OUT=ROOT/'research/side_job_cleanup_s1_1'
LOG=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_SideJobPilotS1\side_pilot_s1_20261010T142851Z_1.jsonl')

def main():
    before=sha(LOG);rows=[json.loads(line) for line in LOG.read_text(encoding='utf-8').splitlines() if line.strip()]
    complete=[r for r in rows if r['facts'].get('mq005_done')==1 and isinstance(r.get('position'),dict)]
    distances=[(r,math.hypot(r['position']['x']+998.80719,r['position']['y']+81.47656)) for r in complete]
    far=[(r,d) for r,d in distances if d>200];assert far
    latest=complete[-1]
    assert latest['facts']['PTFRS1_OwnerFinished']==0 and latest['facts']['PTFRS1_RewardClaim']==latest['facts']['PTFRS1_RewardAck']==1
    assert before==sha(LOG),'Source log changed while reading'
    result={'status':'PRE_FIX_RELEASE_ACK_STILL_ZERO_AFTER_DISTANT_DEPARTURE','source':str(LOG),'sha256':before,'rows':len(rows),'completed_rows':len(complete),'rows_with_read_errors':sum(bool(r.get('errors')) for r in rows),'authored_start_waypoint_xy':[-998.80719,-81.47656],'max_horizontal_distance_metres':max(d for r,d in distances),'over_200m_rows':len(far),'first_over_200m_utc':far[0][0]['utc'],'last_over_200m_utc':far[-1][0]['utc'],'latest':{'utc':latest['utc'],'position':latest['position'],'facts':latest['facts'],'journal':latest['journal'],'status':latest['status']},'interpretation':'Insufficient departure is not a sufficient explanation. Source waits use dynamic actor/car distance; loss of those references is a plausible blocker, not proven. The read-only save parser exposes running quest/event data as opaque arrays, not decoded execution position. S1.1 tests a completed-route-only alternative on existing native waits, with acknowledgements to localize remaining blockers.'}
    path=OUT/'pre_fix_live_evidence.json';assert not path.exists(),'Preserve pinned evidence'
    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('latest','interpretation')},indent=2))
if __name__=='__main__':main()
