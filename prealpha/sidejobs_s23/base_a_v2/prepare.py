"""Successor contract: unchanged eight owners plus explicitly confirmed Skippy seam."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'prealpha/sidejobs_s23/base_a'))
from audit import capture,sha,load

def contract():
 old=load(ROOT/'prealpha/sidejobs_s23/base_a/contract.json')
 c=capture()['mq007_smartgun'];s=copy.deepcopy(next(x for x in old['owners'] if x['key']=='MQ007'))
 s.update(key='MQ007_RESUME',tag='PTFRS23_MQ007_RESUME',title='Machine Gun - confirmed post-mode-conversation resume',
  depot='towercontinued\\sidejobs_s23\\base_a_v2\\mq007_resume_boot.questphase',
  resume_depot='towercontinued\\sidejobs_s23\\base_a_v2\\mq007_resume_owner.questphase',
  resume_source='research/activity_state_r3/native_sources/raw/base/quest/minor_quests/mq007/mq007.questphase',
  resume_nodes=[0,1,3,5,7,11,12],
  resume_edges=[[0,'Out',5,'In1'],[0,'Out',11,'In'],[3,'TurnOff',12,'In'],[5,'Out1',7,'In1'],[5,'RetroSkipCleanup',1,'In'],[7,'Out1',1,'In'],[11,'Out',3,'In1'],[12,'Out',3,'In1']],
  native_only_guards=['Player inventory contains original Skippy; native inventory condition >=1'],
  history_confirmation_fact='PTFRS23_MQ007_ModeTalkConfirmed',
  history_evidence='User explicitly confirmed the 50-enemy mode-change conversation already occurred. This is not a general inference from native facts and is not a pre-Tower certificate.',
  route='Explicit opt-in resume at original root/4.Out1 -> root/5.In1 seam. Copy return phase, original oneliners/inventory/equip loop and final cleanup. Do not replay pickup or the 50-enemy conversation. Original return phase retains two-game-day wait, owner reveal, delivery choices and one native reward.',
  limits=['Default confirmation fact 0 refuses this ambiguous stage. User must opt in on the matching save using only the mod-owned confirmation fact.',
   'Captured progress and all six journal states are checked again natively. Active/completed roots and any progressed return child remain protected.',
   'Chosen gun mode, kill counters, existing gun and outcome flags are not reset or granted. No exact remaining pre-Tower two-day timer reconstruction.',
   'Root-only Failed reactivation after Issued; an Inactive root stays inactive until original gameplay activates its objective.',
   'The old fresh owner must be unused; default fresh and resume fact guards are disjoint. Both remain one-shot saved owners.',
   'Only the confirmed captured pre-owner-reveal seam is supported; different halfway stages are protected.'])
 names=list(s['facts_equal'])+['mq007_interrupt_skippy_dialogue','mq007_rapid_interrupt']
 s['facts_equal']={n:c['facts'][n] for n in names}
 s['facts_equal'].update(PTFRS23_MQ007_ModeTalkConfirmed=1,PTFRS23_MQ007_Issued=0)
 s['capture_progress_match']=True
 s['capture_admission_requires_user_opt_in']=True
 return {'schema':1,'component':'base_a_v2','capture_sha256':old['capture_sha256'],
  'reused_manifest':'research/sidejobs_s23/base_a/audit_03/manifest.json',
  'reused_manifest_sha256':sha(ROOT/'research/sidejobs_s23/base_a/audit_03/manifest.json'),
  'owners':copy.deepcopy(old['owners'])+[s]}

if __name__=='__main__':print(json.dumps(contract(),indent=2,ensure_ascii=False))
