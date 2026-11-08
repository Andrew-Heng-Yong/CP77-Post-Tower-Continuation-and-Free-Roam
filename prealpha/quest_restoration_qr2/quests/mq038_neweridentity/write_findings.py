"""Materialize the reviewed MQ038 findings; does not build or edit resources."""
from investigate import *
from verify import P,JD,N,MP,DI,DH,DS,DC,UC,NC,V,VS,E,ES
def result(status,proven,differences,remaining,evidence,live_only=()):
 return {'status':status,'proven':proven,'approved_differences':differences,'remaining':remaining,'evidence':evidence,'live_only':list(live_only)}
def ev(d,gp,nodes,detail):
 return {'resource':d,'resource_sha256':INDEX[d]['sha256'],'source_json':INDEX[d]['json'],'graph':gp,'nodes':list(map(str,nodes)),'detail':detail}
C={}
C['entry']=result('APPROVED_DEVIATION',[
 'Actual entry In1:1000Ã¢â€ â€™1001 ReadyÃ¢â€ â€™1002 admissionÃ¢â€ â€™1003 dependencyÃ¢â€ â€™54(q001_done>0)Ã¢â€ â€™80(q005_done>0)Ã¢â€ â€™55(q101_enable_side_content>0)Ã¢â€ â€™1004 identical admission recheckÃ¢â€ â€™1005 IssuedÃ¢â€ â€™1006 EnteredÃ¢â€ â€™11 native In1.',
 'Native minorquests parent node11 payload, external target and empty phaseInstancePrefabs exactly match current wrapper node11. Native prerequisite nodes54/80/55 payloads are identical.',
 'Native MQ038 root retains In1 briefing, village_in and ending_in. The wrapper uses only original In1, without relabelling or replaying a resume socket.'
 ],['Private Tower/2079/support guards, all-inactive fresh seam, one-time receipts and JD1 listener dependency are the established S23/JD1 adaptation. No native prerequisite is waived.'],[],[
 ev(P,'root',[1000,1002,1003,54,80,55,1004,1005,1006,11],'Actual connected entry'),ev(MP,'root',[54,80,55,11],'Native parent prerequisite/binding comparison')],['Hook trigger proximity, native dialogue selection and player acceptance require runtime.'])
C['eligibility']=result('APPROVED_DEVIATION',[
 'Both admission nodes1002/1004 require seven native facts exactly zero: mq038_active,deliver_inactive,done,dumpster_opened,fake_01_opened,fake_02_opened,hide_inactive.',
 'All thirteen exact journal paths in the contract are required Inactive, including the call objective and description. Active/Succeeded/Failed roots or changed child objectives cannot match the fresh adapter.',
 'S23 Permit scheduler denies missing/unsettled journals, observes two consecutive samples, requires StartupReady/HS1 admits/native profile readiness and stops changing Permit after durable Issued. Native q001/q005/q101 prerequisites remain actual graph waits.'
 ],['Only the bounded fresh Inactive seam is admitted after Tower; unsupported progressed states defer.'],[],[
 ev(P,'root',[1002,1004,54,80,55],'Serialized predicates including AND/OR structure;39 per-journal Active/Succeeded/Failed and7 progressed-fact refusals verified'),{'file':'prealpha/phone_studios_ph3/candidate_01/package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds','lines':'Permit/Common/Read/Ready/Poll and Paths12/FactNames12; SHA in tests_04.json'}],['A particular save history/HS1 sample is not read or altered by this investigation.'])
C['communications']=result('PASS',[
 'Native village call scene entry call:122Ã¢â€ â€™143 writes holo_dennis_calls_v_start_activate=1Ã¢â€ â€™137 waits start_done>0Ã¢â€ â€™138 clears that acknowledgement before dialogue. Ordinary end144Ã¢â€ â€™139 waits end_doneÃ¢â€ â€™140 clears it. Interrupt branch285Ã¢â€ â€™272 also requests endÃ¢â€ â€™268 waits end_doneÃ¢â€ â€™270 clears it.',
 'Native Dennis controller waits actual start/end requests at32/2, clears requests at9/10 and invokes exact scene sockets. Native scene start480 reaches real start acknowledgement41; end481 reaches end acknowledgement42, with original counters, rejection and interruption handling unchanged.',
 'JD1 node106 exactly equals native initializer106. Wrapper rechecks its full condition before once-only receipt1004. Fresh owners wait idle interruption flags; already-issued/entered MQ038 owners may carry those flags and pending start requests. Terminal roots, mq038_done, already-issued Dennis, active setup and pending end are refused.',
 'Current shared cleanup1301/1302 exactly matches native439/303 modulo node IDs, owned by JD1 receipt1300 and connected to the later current cleanup chain. Actual Dennis cleanup compares matching start/end counters and invokes original end scene; no fabricated reset added.',
 'Failure SMS is native village126Ã¢â€ â€™157 Active contacts/darryl/00_msg/00_msgÃ¢â€ â€™43 Failed rootÃ¢â€ â€™2 quest_ends. Call objective contact marker remains native159.'
 ],[],[],[
 ev(VS,'scene',[122,143,137,138,144,139,140,285,272,268,270],'Native caller/ack protocol'),ev(DH,'root',[2,9,10,26,32],'Native listener'),ev(DS,'scene',[480,481,41,42,571,573,610,629,618],'Native acks/counters/interrupts'),ev(JD,'root',[1002,1003,1004,106],'Fresh versus already-issued bootstrap'),ev(UC,'root',[1300,1301,1302],'Owned native cleanup integration'),ev(V,'root',[126,157,43,159],'Failure SMS/objective contact')],['Native PhoneSystem callback timing, user rejection, scene rendering, interruption recovery and reload are live behavior.'])
C['ownership']=result('CONDITIONAL',[
 'Original MQ038 executes below native minorquests node11. Current adapter uses a distinct private wrapper with once-only receipts, and does not patch or restart an active journal.',
 'Native minorquests and MQ038 root PhasePrefabs are empty, and parent node11 has no PhaseInstancePrefabs; no omitted MQ038 root/parent prefab obligation was found.',
 'Freshly pinned native main quest ancestry (root review) has journal The Tower SucceededÃ¢â€ â€™109 q307_main_game_killed=1Ã¢â€ â€™107 Terminating; root/82 node6 owns minorquests. This is a real native terminating path, stronger than a killed-fact string alone.'
 ],[],[
 'An actual retained save executing-owner tree was not inspected. Fact/journal guards cannot by themselves prove there is no stranded original MQ038 or Dennis owner in an inconsistent/legacy save.',
 'Need explicit saved-owner retirement/adoption fixture at retained-session boundary, including already-issued MQ038 with JD1 unissued and repeated load. No controller reset or duplicate-owner fix is justified from absent evidence.'
 ],[ev(MP,'root',[11],'Original parent'),ev(P,'root',[1002,1004,1005,11],'Bounded private ownership'),{'file':'prealpha/quest_restoration_qr2/ancestor_review.json','native_root_sha256':'78D8AFD0784575216B090F003610CA973BE9D1781BAB948C9E4DC12006D750B2','route':'cyberpunk2077.questphase root106Ã¢â€ â€™109Ã¢â€ â€™107 and root/82/6 (root integration evidence)'}],['Engine treatment of saved active descendants and later load-resumption.'])
C['progression']=result('PASS',[
 'Current private node11 delegates the exact unmodified native MQ038 body. Four native quest phases plus three MQ038 scenes and native Dennis resources were hash-pinned from binary evidence; all graph handles/interfaces normalize without errors.',
 'Native root2Ã¢â€ â€™96 briefingÃ¢â€ â€™97 villageÃ¢â€ â€™99 ending is preserved. Both quest_ends exits96/97 join116Ã¢â€ â€™117Ã¢â€ â€™104Ã¢â€ â€™105Ã¢â€ â€™122Ã¢â€ â€™121Ã¢â€ â€™102 cleanup. The adapter neither substitutes native village/ending input nor removes optional branches.',
 'Village survivor/death/car routes, embedded root/116 objective repair, Tyger combat, mounting and carrying remain native. Failure SMS/Failed journal route is retained. These are checks of graph delegation and exact binaries, not a gameplay outcome claim.',
 'Historical MQ038 bugfix actions are already present in the current native body: village158 equals loot variant root/1/10, village182/184 equal drive unblock root/12/6, and village202 equals forbidden-trigger root/17/9. Missing private copies of one-time migration handlers are not proof of a missing gameplay action.'
 ],[],[],[ev(N,'root',[2,96,97,99,116,117,104,105,122,121,102],'Native route/early exits'),ev(V,'root',[71,116,126,157,43,158,182,184,202],'Combat/failure/native corrective actions'),{'file':'trace.json','scope':'14 resources,499 normalized nodes, exact node/socket/edge inventory'}],['Trigger physics, combat, carrying and native scene progression still need gameplay observation.'])
C['presentation']=result('CONDITIONAL',[
 'All three MQ038 scene actor acquisition/workspot/reference-point/interrupt definitions and Dennis scene definitions are preserved in actor_bindings.json. Briefing Darryl acquires community #mq038_com_darryl; village actors use Tyger/surgeon communities; ending acquires surgeon/Darryl; Dennis uses the native spawnSet.',
 'Native parent/root prefab obligations are empty. The native body retains actor spawning/awaits, #mq038_tr_hook and scene locations, #wk_04_devices mq038_village and #wnid_01_loot mq038 variants, vehicle controls and #mq038_katana_token.',
 'PH3 shared studio owner is retained, with no removal/renaming of its saved identity or parent dependencies.'
 ],[],[
 'Exact world NodeRef definitions, community entries, marker/workspot/camera placement and effective streamed variant lifetime were not fully resolved by the named quest graphs. dependency_depots.json lists every encountered NodeRef; do not treat native string preservation as placement proof.',
 'Fresh134-archive literal lookup found no direct provider for twelve native-declared en lipsync anim paths (eleven MQ038, one Dennis). These are unchanged native declarations. Localization indirection/engine resolution is unresolved; no missing private archive payload or safe repair follows.'
 ],[{'file':'actor_bindings.json','scope':'4 exact native scene actor/metadata bindings'},{'file':'dependency_depots.json','scope':'All30 direct dependency depots plus roots/shared resources and NodeRefs'},{'file':'../../provider_readback_01/capture.json','scope':'Fresh bounded provider lookup; root report preserves 12 unmatched literal anim paths'}],['Actual spawned actors, lip sync, camera, workspots, streaming and visible token geometry.'])
C['journal']=result('PASS',[
 'Thirteen fresh eligibility paths are exact native quest/objective/description identities and stay Inactive-only; no Reset/Reactivate or journal write exists in the private adapter.',
 'Native briefing POI10 activates after Darryl spawned and before trigger/scene. Native village objectives12/14/15/17/19/20/34/35/38/44/49/50/51/75/80/89/131/132 and embedded root/116 transitions are delegated unchanged.',
 'Failure node157 sends message before root43 Failed. Native ending2 succeeds delivery,39 activates leave-car,8 succeeds talk-cargo,12 succeeds quest. Current listener can attach to an Active issued quest without changing its journal.'
 ],[],[],[ev(P,'root',[1002,1004],'Exact admission journal paths'),ev(V,'root',[12,14,15,17,19,20,34,35,38,44,49,50,51,75,80,89,131,132,157,43],'Native objective/marker changes'),ev(E,'root',[2,39,8,12],'Native final transitions')],['UI notifications and map-marker rendering are engine behavior.'])
C['completion']=result('PASS',[
 'Native ending7 End0Ã¢â€ â€™33 removes Darryl contactÃ¢â€ â€™8 talk objective SucceededÃ¢â€ â€™12 quest SucceededÃ¢â€ â€™16 QuestRewards.mq038_surgeon_savedÃ¢â€ â€™20 checkpoint. There is one GiveReward node and no directed normal cycle returning to it.',
 'Native ending scene222 enables exact #mq038_katana_token; native follow-up waits until Items.Preset_Katana_Surgeon inventory count>0 before optional talk loop. Katana is not invented or directly granted by private code.',
 'Native root normal and early exits clear mq038_active, set mq038_done, spawn token/checkpoint and enter root/102 cleanup. That cleanup preserves spawned checks, native150m distance waits, community deactivation, variant hides and Darryl message-visited gating before contact removal. Only then native Out1 reaches private Finished receipt1007.'
 ],[],[],[ev(E,'root',[7,33,8,12,16,20,41,18],'Success/reward/token sequence'),ev(ES,'scene',[222],'Loot token enable'),ev(N,'root',[104,105,122,121,102,3],'Completion cleanup'),ev(N,'root/102',[22,24,25,26,30,33,34,35,37,38,39,43,44,45,46],'Spawn/distance/message cleanup'),ev(P,'root',[1007],'Once-only private completion receipt')],['Exactly-once reward execution through an actual save/reload transition remains engine/owner-dependent; no synthetic reward replay authorized.'])
C['persistence']=result('CONDITIONAL',[
 'No runtime byte/resource/script identity changed. Private Issued/Entered/Finished receipts and node IDs are preserved; static truth table refuses terminal journals and already-issued fresh roots.',
 'S23 Permit scheduler explicitly stops after durable Issued; it does not restart the native body on Restored. JD1 has its separate once-only receipt and can supply an omitted listener to the existing issued/entered MQ038 owner without changing progress.'
 ],[],[
 'Source parity cannot prove a pre-existing saved owner actually serializes/resumes every native delay, scene, mount/carry state and child handle. Need retained-session upgrade/reload fixtures with native owner identity and reward receipt evidence.',
 'No per-quest saved owner tree was decoded here. Unsupported unfinished states remain excluded, not automatically repaired.'
 ],[ev(P,'root',[1002,1004,1005,1006,1007],'Persistent one-time guards'),ev(JD,'root',[1002,1003,1004],'Owned listener adoption'),{'file':'tests_04.json','scope':'ExactPH3 private source pins and 157 focused controls including4 in-memory mutations'}],['Save/load execution continuity and absence of duplicate spawned native owners.'])
C['shared_dependencies']=result('CONDITIONAL',[
 'Dennis listener/init, actual native start/end acknowledgement scene, native cleanup phase and shared cleanup chain are all present and connected. Cleanup counters exactly use native Dennis labels; no Sandra/Delamain synthetic resets are involved.',
 'Native village writes holo_interrupt_call_manual with the original increment/clear paths167/168/212. JD1 existing-owner branch deliberately does not wait on its own unfinished quest interruption flags; fresh branch still waits. The real-resource mutation test detects reintroducing the self-held flag deadlock.',
 'Native body preserves call/drive/ending token block/unblock operations and original cut/interrupt branches. Established PH3 studio support is unchanged.'
 ],[],[
 'Shared world support leases/streamed sectors and active PhoneSystem ownership on an actual loaded save were not inspected. Render marker #dennis_sm_holocall resolution and per-call streaming/cleanup scheduling remain unproved.',
 'Inherited engine interpretation of localized lipsync references and world variant/actor bindings remains visible in presentation contract; these are not safe speculative repair targets.'
 ],[ev(V,'root',[128,129,167,168,179,182,183,184,211,212],'Native interrupt/token lifecycle'),ev(JD,'root',[1002,1003],'Already-issued exception'),ev(UC,'root',[1300,1301,1302],'Shared cleanup'),{'file':'tests_04.json','scope':'Native comparisons,4 plausible regression mutations'}],['Phone setup contention, interruptions and saved-owner/UI callback recovery.'])
C['completion']['status']='CONDITIONAL'
C['completion']['remaining']=[
 'STATIC: Exact QuestRewards.mq038_surgeon_saved TweakDB definition, existence and numerical/item effects are not independently resolved. The authored branch and reference identity are proven, not the target reward data.',
 'STATIC: #mq038_katana_token placement and #wnid_01_loot mq038 variant binding remain unresolved world evidence. Native scene enable and wait-on-inventory nodes do not prove the token can spawn or be acquired.'
 ]
out={'quest_id':'mq038_neweridentity','title':'Big in Japan','status':'DEEP_REVIEWED_CONDITIONAL','static_verified':False,'confirmed_defects':[],'repairs':[],'contracts':C,'tests':'tests_04.json','test_count':157,'source_trace':'trace.json','source_trace_resources':14,'source_trace_nodes':499,'note':'Five contract rows have specific static proofs/approved adaptations; five retain named owner/presentation/reward-data/persistence/shared-world limitations. No blanket gameplay parity claim.'}
write(OUT/'contracts.json',out)
print(json.dumps({'quest_id':out['quest_id'],'contract_statuses':{k:v['status'] for k,v in C.items()},'static_verified':False,'repairs':0}))
