"""Record the two completed vehicle investigations without changing shared state."""
from pathlib import Path
import json,sys,collections
O=Path(__file__).resolve().parent;W=O.parents[3]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
V=O/'verification_01';pins=read(V/'source_pins.json');tests=read(V/'tests.json')
assert tests['count']==210 and tests['status'].startswith('PASS')
evidence=[str(V/'source_pins.json'),str(V/'graph_evidence.json'),str(V/'tests.json')]
def c(status,proven,remaining=(),differences=()):return {'status':status,'proven':list(proven),'approved_differences':list(differences),'remaining':list(remaining),'evidence':evidence}
allresults=[]
for id,title,num,tag,car,body,vo,focus,despawn in [
 ('mq046_cave_vehicle','Murk Man Returns Again Once More Forever','40','PTFRS23_MQ046','Vehicle.v_sport1_rayfield_caliburn_02_player',141,69,71,72),
 ('mq047_ad_vehicle','Dressed to Kill','44','PTFRS23_MQ047','Vehicle.v_standard25_thorton_colby_pickup_02_player',145,45,47,48)]:
 q46=num=='40';sub=O/'quests'/id;assert not (sub/'contracts.json').exists()
 private=next(x for x in pins if x['depot'].endswith(('mq046_boot.questphase' if q46 else 'mq047_boot.questphase')))
 native=next(x for x in pins if x['depot'].endswith('ma_bls_ina_se1_'+num+'_phase.questphase'))
 contracts={
 'entry':c('APPROVED_DEVIATION',[
 f'Effective PH3 boot {private["depot"]} SHA256 {private["sha256"]} retains exact original district nodes173 and{body} in root/100. Native173 has seven tick delay; native{body} references exact activity body via In1. Resource and node prefabs in the district parent are empty; native activity root prefab obligation is separately retained.',
 f'Actual boot route0.Out->1.Ready->2 pause->3 recheck.3.False rearms2;3.True->4.Issued->89(two ticks)->90.90.True->92.Entered then100.In1; inline0->173->{body}.In1.90.False writes owned Fault91 and does not enter the body.',
 f'Body is native {native["depot"]} SHA256 {native["sha256"]}; no resume/debug alternative is used.'],
 ['LIVE_ONLY: ArchiveXL activation/scheduler and streaming are not executed here.'],
 ['Existing S23 post-Tower fresh-only wrapper adds genuine-ending/PA2/U9/history/receipt guards, two-tick postclaim recheck and private receipts; native body, original seven-tick delay and In1 remain unchanged.']),
 'eligibility':c('APPROVED_DEVIATION',[
 f'Boot2/3 require all five quest journal entries Inactive, ma_bls_ina_se1_{num}_start/finished=0, {tag}_Issued/Finished/Fault=0, Permit1 and genuine Tower/context gates.90 retains fresh native/journal/vehicle conditions but recognizes Issued1. No Active/Failed/Succeeded history is converted.',
 f'Exact serialized NOR(questVehicleAvailable SpecificVehicle {car}) is retained across2/3/90, preventing a fresh grant to an already-owned car. Tests evaluate real AND/OR/NOR trees, reject all five journals Active/Succeeded/Failed/missing, changed native facts and receipts, pre-Tower, existing entitlement and unknown availability inputs.',
 ('Native0->30(q103_done>=1)->31(two game days)->34(StreetCredTier.VehicleTier5 GreaterOrEqual)->121->32(outside/in-trigger conditions) remains.14/16 are historical alternative q103/two-day nodes and are retained, not substituted as current entry. No time-of-day/weather gate is encoded in the actual current path.' if q46 else 'Native0->109 deletion marker->72 player-in #ma_bls_ina_se1_44_tr_sp->75 ambient spawns->74 final_loot variant->33 realtime delay->107 deletion->76 player-car spawn remains. No q103, street-cred, weather or time-of-day prerequisite exists in this actual native path; none was invented.'),
 'Current S23 Read rejects absent or delayed journals, validates two matching settled samples and owned readiness/receipts; fresh permit is not an implementation of arbitrary resume.'],
 ([('CONDITIONAL: StreetCredTier.VehicleTier5 target definition/current TweakDB provider is not decoded; exact native predicate/reference is preserved.')] if q46 else [])+['LIVE_ONLY: Actual earned history, engine vehicle availability and safe player state depend on a current save, not inspected here.'],
 ['Fresh-only admission and refusal of existing vehicle entitlement are the existing save-protection adaptation. For Murk Man, native two-day wait begins when this new owner enters; no pre-Tower elapsed timestamp is fabricated or fast-forwarded.']),
 'communications':c('PASS',[
 'Complete native body and private wrapper contain no audio_/holo_ request writers/readers, phone controller, SMS or acknowledgement dependency. The current bodies reference no external scene resource.',
 f'Native world email/Onscreen read is distinct from phone SMS: '+('77 waits onscreens/emails/quests/minor_activities/badlands/se1/ma_bls_ina_se1_40/onscreens/ma_bls_ina_se1_40_onscreen_01 Active before80 investigate Succeeded and81 get_inside_car Active.' if q46 else '53 waits onscreens/emails/quests/minor_activities/badlands/se1/ma_bls_ina_se1_44/onscreens/ma_bls_ina_se1_44_onscreen_01 Active before54 investigate Succeeded and55 get_inside_car Active.'),
 f'Incidental Johnny line is a native voiceset node{vo}, not a missing holocall; phone listener/reset patches are not justified for these quests.'],
 ['LIVE_ONLY: Onscreen/shard interaction delivery and native VO playback are engine behavior.']),
 'ownership':c('CONDITIONAL',[
 f'Original district parent ma_bls_ina_se1_minor_activities owns node{body}; current wrapper preserves its exact payload and descendant reference. Its parent root phasePrefabs[] and node phaseInstancePrefabs[] were checked, avoiding an omitted parent-prefab assumption.',
 f'Native body itself owns #loc_ma_bls_ina_se1_{num}_openworld. Distinct private receipts {tag} and distinct native vehicle/prefab namespace avoid an intentional MQ046/MQ047 duplicate owner.',
 'Two preclaim guards and postclaim recheck prevent fresh reissue for used journals/entitlement/receipt; wrapper writes only owned facts. A killed flag is not used as standalone proof of retirement.'],
 ['CONDITIONAL: Native lower district/activity ancestry is pinned, but direct top-level caller connecting open_world_minor_activities to genuine Tower Terminating subtree is not present in this agent input set. Root is investigating exact additional_game_elements dependency; no assumed retirement from main_game_killed alone.',
 'LIVE_ONLY: Matching saved native/private executing descendants and engine cancellation/adoption/reload require owner/transition evidence, not supplied by inactive journal alone.']),
 'progression':c('PASS',[
 ('Complete native70-node root plus two-node root/10 remain delegated unchanged.0->30->31->34->121->32 reaches prefab/spawn route.81 fans out to vehicle setup, keycard106 and mounting wait48->118->120. Spawned120.True->117,False->119->117.117 is actual player mount;117.Out independently enables vehicle83, resets native mortality49 and succeeds journal88.' if q46 else 'Complete native50-node root remains delegated unchanged.72->75->74 activates native loot variant and ambient vehicles, then76 spawn/106 wait->68 hood/67 trunk locks->36 driver door/105 ten ticks->40 mortality->50 trigger->39 immovability reset->43 Johnny.55 separately fans into player mount preparation41->100->99 plus keycard87/door unlocks.99 fans out to grant57, journal60 and native cleanup96.'),
 'Conditional spawned retry and native deletion-marker/unreachable legacy content are retained exactly in the pinned body; the private adapter does not flatten its branches or author a replacement vehicle controller.'],
 ['LIVE_ONLY: Actual triggers, mount events, spawning, retry timing and vehicle/device commands are not engine simulated.']),
 'presentation':c('OPAQUE',[
 f'Body root retains exact native #loc_ma_bls_ina_se1_{num}_openworld. All vehicle/trigger/loot/AV spline/Johnny NodeRefs, native variant names, mortality and door commands are preserved. Current activity body has no external scene/actor/workspot resource reference to relocate.',
 f'Native Johnny Activate/spawn-wait->voiceset{vo}->3-second delay->{focus} inverted CameraFocus->Deactivate{despawn} is still connected. Current JV1 pins Character.Silverhand and hides IVisualComponent only after genuine Tower, retaining logical actor/audio/timing; no native facts or scene skips are written.',
 ('Native prefab node36 enables original location variant and native door/vehicle binding remains #ma_bls_ina_se1_40_vehicle / #ma_bls_ina_se1_40_car_player.' if q46 else 'Native74 enables final_loot on $/03_night_city/se1/loc_ma_bls_ina_se1_44_prefabCR6GXGI/loc_ma_bls_ina_se1_44_gameplay_prefabTM7LFIY/loc_ma_bls_ina_se1_44_loot_prefabF65Q5TA.75 activates veh01/02/03 plus AV; AV82->83 spline and84->85 despawn remain.')],
 [f'OPAQUE: Exact streamed placement/NodeRef binding and variants inside #loc_ma_bls_ina_se1_{num}_openworld are not independently decoded/correlated here. Preserved reference bytes are not complete placement certification.',
 f'CONDITIONAL: Current TweakDB vehicle target {car} and Keycards.ma_bls_ina_se1_{num}_car_keys definitions are not independently resolved.',
 'LIVE_ONLY: JV1 suppression, native voiceset availability and inverted camera-focus cleanup on an invisible logical actor need runtime observation. Independent props and actor scheduling are outside static visual code proof.'],
 ['Approved supporting voice-only Johnny presentation is implemented by existing JV1/whitelist policy. The logical native supporting actor survives for timing; the rendered projection is suppressed. QR3 adds no engram, visible projection or takeover.']),
 'journal':c('PASS',[
 f'All native journal/objective/description/map-pin paths and Active/Succeeded/Inactive sockets are preserved verbatim in delegated body; wrapper only observes quests/minor_quest/{id} Succeeded at102 then writes private Finished101.',
 ('75 activates investigate,76 description;77 OnscreenActive->80 investigateSucceeded->81 get_inside_carActive.117.Out->88 get_inside_carSucceeded->89 rootSucceeded->87 checkpoint.112 map pin is activated by113;70 clears it before camera cleanup. No private journal reset exists.' if q46 else '92 activates original map pin->51 investigateActive->52 descriptionActive->53 Onscreen wait->54 investigateSucceeded->55 get_inside_carActive.99.Out->60 get_inside_carSucceeded->61 rootSucceeded->59 checkpoint;46 clears map pin92 on native voice cleanup branch. No private journal reset exists.')],
 ['LIVE_ONLY: Journal ancestor auto-propagation, notifications/tracking and UI timing remain engine effects.']),
 'completion_rewards_cleanup':c('CONDITIONAL',[
 f'Native vehicle enable preserves enable1/despawn1/makePlayerActiveVehicle1 for {car}; no private reward/regrant is added. Native quantity-one Keycards.ma_bls_ina_se1_{num}_car_keys item write is retained.',
 ('Exact actual mount117 forks to native reward83 and objective88->root89 Succeeded->checkpoint87->terminating1; vehicle mortality49 and immovability/door native cleanup branches remain.' if q46 else 'Exact mount99 forks to native enable57, objective60->root61 Succeeded->checkpoint59->terminating1 and active-car spawn96. Ambient AV trigger84->Deactivate85 remains; native Johnny deactivation48 is separate.'),
 'Private Finished observer waits original Succeeded, so it does not manufacture quest completion or entitlement. Native source outcome logic is copied by reference, not recreated.'],
 [f'CONDITIONAL: Exact {car} and Keycards.ma_bls_ina_se1_{num}_car_keys TweakDB definitions/current overrides, plus prefab/trigger bindings, remain unresolved static inputs.',
 'LIVE_ONLY: Actual entitlement transaction, once-only delivery under interruption and vehicle persistence/save-load require engine fixtures.']),
 'persistence':c('CONDITIONAL',[
 f'Current private resource SHA256 is pinned to PH3; QR3 changes no node/resource/field/receipt identities. {tag}_Issued1 precedes any native entry, Finished1 follows native success, Fault cut prevents a failed recheck from entering native body.',
 'Current S23 Restored clears transient observation arrays and revokes Permit only for unissued owners; Permit returns without writing when Issued is nonzero. No native journal/fact/vehicle entitlement reset occurs.',
 'Fresh journal and vehicle ownership guards refuse already-used or contradictory states, rather than fabricate an unsupported unfinished resume seam.'],
 ['CONDITIONAL: Saved executing owner adoption and old-version transition fixtures are absent; private/native identity preservation alone is not save-runtime certification.',
 'LIVE_ONLY: Save/reload during delay, spawn retry, mounted reward transaction, voice cleanup or sector unload remains untested.']),
 'shared_dependencies':c('CONDITIONAL',[
 'Both wrappers depend on existing U9 Support_Issued1/Fault0 and current S23 permit/history/safe-state coordinator, but do not require Ozob/Dennis/Viktor phone owners. MQ046/MQ047 script data slots22/23 have distinct IDs, paths, tags and native fact arrays.',
 'Native ma_ina_west_bugfixing is inventoried: MQ046 root/40/3 node11 restores car mortality; current native body already has authored mortality cleanup49. MQ047 root70 owns the same location prefab and is a one-time CYB-662150 guarded correction:0->2.False->3 increments marker->4 checks get_inside_car Succeeded; True->8 unmount->7 Deactivate veh03,False->9 unmount->6 Reactivate veh03. It is not a generic fresh quest initializer.',
 'No one-time corrective graph is restarted and no arbitrary Reactivate/ResetKillCount is substituted for missing support. Existing JV1 visual-only policy remains shared across both native supporting lines.'],
 ['CONDITIONAL: Original world/bugfix owner retirement/survival and shared prefab lease lifetime need exact top ancestry plus saved-owner evidence; one-time corrective facts must remain preserved.',
 'LIVE_ONLY: Concurrent sector streaming, vehicle stub ownership and supporting voice/camera cleanup arbitration require runtime evidence.'])}
 if q46:
  # The native tier pointer is preserved, but full eligibility includes unresolved target data.
  contracts['eligibility']['status']='CONDITIONAL'
 result={'quest_id':id,'title':title,'status':'DEEP_REVIEWED_WITH_STATIC_LIMITS','fully_static_verified':False,'defects':[],'repairs':[],'native_resource':native,'private_resource':private,'contracts':contracts,'tests':str(V/'tests.json'),'no_repair_conclusion':'Native prerequisite/body/vehicle reward/journal routes are preserved. Current static gaps concern unresolved target data/placement/ownership, not a reproducible private implementation defect.'}
 write(sub/'contracts.json',result);allresults.append(result)
 counts=collections.Counter(x['status'] for x in contracts.values())
 report=f'''# {title} — QR3 deep-contract findings

All ten contracts were investigated. **No source-confirmed defect or gameplay repair; not fully STATIC_VERIFIED.**

Native resource: `{native['depot']}` SHA256 `{native['sha256']}`. Private boot: `{private['depot']}` SHA256 `{private['sha256']}`.

{json.dumps(dict(counts))}

The exact nodes, predicates, sockets, progression, journal transitions, item/vehicle grants, cleanup and remaining limits are in [contracts.json](contracts.json). Detailed original/current models and all edges are in [graph evidence](../../verification_01/graph_evidence.json); [source pins](../../verification_01/source_pins.json) bind raw binary, JSON, normalized input and provider identities. The two-quest verifier passed210 checks including8 actual-resource mutation controls; counts describe assertions, not gameplay coverage.

The private wrapper keeps original district173 seven-tick delay and{body}.In1; it adds the already-existing S23 genuine-Tower/fresh-history/vehicle-not-owned/once-only wrapper and two-tick postclaim recheck. It does not alter the native activity body or reset history. Native local Onscreen email interaction is not phone SMS. Native supporting Johnny voiceset is retained under JV1 visual suppression, with rendering/camera scheduling live-only.

Remaining static inputs: exact vehicle/keycard TweakDB targets, streamed prefab/trigger/variant bindings, and full original world-owner retirement path. Saved owner transitions and actual entitlement/VO/unload effects require live evidence. No source change is justified by these gaps.

Reproduce from workspace root into a NEW directory:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -B 'prealpha\\quest_restoration_qr3\\agents\\agent_b\\verify.py' --output 'prealpha\\quest_restoration_qr3\\agents\\agent_b\\verification_next'
```

The command checks both vehicle quests together and refuses an existing output directory. No game/write/build/deploy action is performed.
'''
 (sub/'REPORT.md').write_text(report,encoding='utf-8')
write(O/'results.json',{'agent':'agent_b','quests':[r['quest_id'] for r in allresults],'tests':str(V/'tests.json'),'contract_results':[{'quest_id':r['quest_id'],'contracts':{k:v['status'] for k,v in r['contracts'].items()}} for r in allresults],'runtime_changes':[],'confirmed_defects':[],'proposed_patches':[]})
(O/'REPORT.md').write_text('# Agent B — vehicle activity verification\n\nBoth assigned quests have ten explicit evidence-backed contract dispositions. No source-confirmed defect; no runtime edits. See quests/*/contracts.json and REPORT.md. verification_01/tests.json has210 passing checks including8 mutations against actual private/native resources. Unresolved world placement, target TweakDB records and original world-owner ancestry remain explicit.\n',encoding='utf-8')
print(json.dumps({'quests':len(allresults),'contracts':20,'tests':tests['count'],'repairs':0}))
