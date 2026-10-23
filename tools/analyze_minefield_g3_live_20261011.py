"""Freeze completed getter-log prefix and report this one G3 route, not all routes.

No game, save or installed artifact writes. Pinned once; no predecessor mains.
"""
import hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/gig_restoration/minefield_g3'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
SOURCE=GAME/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_MinefieldG3/minefield_g3_20261011T035136Z_1.jsonl'
RESULT=OUT/'live_result_20261011.json'
TRACE=OUT/'live_trace_20261011.jsonl'
def sha(data):return hashlib.sha256(data).hexdigest().upper()
def main():
    assert not RESULT.exists() and not TRACE.exists(),'Live evidence already pinned'
    data=SOURCE.read_bytes();prefix=data[:data.rfind(b'\n')+1]
    rows=[json.loads(line) for line in prefix.splitlines()]
    assert rows and not any(row.get('errors') for row in rows)
    keys=['PTFRG3_Request','PTFRG3_Started','PTFRG3_RewardClaim','PTFRG3_RewardAck','PTFRG3_AccountClaim','PTFRG3_AccountAck','PTFRG3_CounterAck','PTFRG3_OwnerFinished','ina_07_finished','ina_07_failed','bls_sts_counter','bls_achievement']
    transitions=[];previous=None;terminal=[];visible_tracking=[]
    for row in rows:
        facts=row['facts'];stage=int(re.search(r'stage=(\d+)',row['status']).group(1))
        assert facts['PTFRG3_Fault']==facts['PTFRG3_RewardReplayRefused']==0
        signature=(stage,tuple(facts[k] for k in keys))
        if signature!=previous:
            transitions.append({'utc':row['utc'],'stage':stage,'facts':{k:facts[k] for k in keys},'money':row.get('money')})
            previous=signature
        if stage==4:terminal.append(row)
        j=row.get('johnny','');m=re.search(r'tracked=(\d+) visualComponentsLastPoll=(\d+)',j)
        if m and int(m.group(1))>0:visible_tracking.append({'utc':row['utc'],'tracked':int(m.group(1)),'visual_component_count':int(m.group(2))})
    assert terminal
    after_ack=[r for r in rows if r['facts']['PTFRG3_CounterAck']==1]
    assert after_ack and all(r['facts']['bls_sts_counter']==r['facts']['bls_achievement']==1 for r in after_ack)
    assert all(r['facts'][k]==1 for r in terminal for k in ('PTFRG3_RewardClaim','PTFRG3_RewardAck','PTFRG3_AccountClaim','PTFRG3_AccountAck','PTFRG3_CounterAck','PTFRG3_OwnerFinished','ina_07_finished'))
    receipt=json.loads((OUT/'install_receipt.json').read_text(encoding='utf-8-sig'))
    actual={f['relative']:sha((GAME/f['relative']).read_bytes()) for f in receipt['files']}
    assert all(actual[f['relative']]==f['sha256'] for f in receipt['files'])
    phase='quests/street_stories/badlands/inland_avenue/sts_bls_ina_07/get_hdd_from_ghost_car'
    journals={p:terminal[-1]['journal'][p]['state'] for p in (phase.rsplit('/',1)[0],phase,phase+'/find_car')}
    assert set(journals.values())=={3}
    result={'status':'USER_AND_GETTER_G3_SUCCESS_ROUTE_PASS_RELOAD_PENDING','source':str(SOURCE),'captured_prefix_sha256':sha(prefix),'rows':len(rows),'first_utc':rows[0]['utc'],'last_utc':rows[-1]['utc'],'getter_errors':0,'stage4_rows':len(terminal),'transitions':transitions,'terminal_journals':journals,'acknowledged_counters':{'baseline':{'fixer':0,'achievement':0},'final':{'fixer':1,'achievement':1},'no_observed_growth_after_ack':True},'johnny':{'user_confirmation':'johnny worked as expected','voice_and_model_behavior_user_pass':True,'tracked_actor_rows':len(visible_tracking),'maximum_root_visual_components':max((r['visual_component_count'] for r in visible_tracking),default=0),'getter_is_not_renderer_or_audio_proof':True},'five_actual_installed_hashes':actual,'save_reload_proven':False,'deployment_changes':0,'direct_save_writes':0,'limitations':['New-test-save/reload still pending','Exact cash/XP attribution not certified; money getters are not isolated reward instrumentation','Alternate, failure and different-baseline routes or concurrent shared actors unproven','Current exclusive ownership of borrowed shared AI roles unproven','JV1 independent props/external effects and other appearances not certified','Automatic pre-ending history/ending transition and full alpha not proven','Other 124 adapters and all completed replay still pending']}
    TRACE.write_bytes(prefix)
    RESULT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('status','rows','stage4_rows','getter_errors','acknowledged_counters','johnny','save_reload_proven')},indent=2))
if __name__=='__main__':main()
