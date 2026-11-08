"""Pin existing evidence and prepare the bounded next-test queue. Read-only inputs."""
from pathlib import Path
import hashlib, json
from preflight import fresh_output
H=Path(__file__).resolve().parent;W=H.parents[1];Q9=W/'prealpha/quest_restoration_qr9'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def main():
    queue_path=fresh_output('runtime_queue.json');evidence_path=fresh_output('fixture_evidence.json');provenance_path=fresh_output('provenance.json')
    b=read(H/'baseline.json');game=Path(b['game_root'])
    snapshot=sorted((game/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1').glob('snapshot_hs1_*.json'))[-1]
    raw=read(snapshot)
    selected=[]
    for row in raw['rows']:
        d=row['definition']
        if d['id']in ('mq037_brendan','mq037_brendan_hooligan001','mq007_smartgun','sts_pac_cvi_02','mq060_nitro'):
            assert len(d.get('fact_names',[]))==len(row.get('facts',[]))
            selected.append({'id':d['id'],'title':d.get('title'),'states':row['states'],
                'journals':d['journals'],'facts':dict(zip(d.get('fact_names',[]),row.get('facts',[]))),
                'stable':row.get('stable'),'legacy_pre_ending_certificate':row.get('legacy_pre_ending_certificate')})
    observations={}
    for card,name in [('S00','QR9_capture_20261102T164434Z_0001.jsonl'),('S03','QR9_capture_20261102T195951Z_0001.jsonl')]:
        directory='S00_20261102_01'if card=='S00'else'S03_20261102_01';p=Q9/'observations'/directory/'logs'/name
        rows=[json.loads(x)for x in p.read_text().splitlines()]
        observations[card]={'path':str(p),'sha256':sha(p),'baseline':next(r['data']for r in rows if r['event']=='ATTACHED_BASELINE'),
            'state':next(r['data']for r in rows if r['event']=='ATTACHED_STATE')}
    evidence={'latest_existing_snapshot':{'path':str(snapshot),'sha256':sha(snapshot),'origin':raw['origin'],'revision':raw['revision'],
        'limits':'Post-ending fallback snapshot, not an earned pre-Tower certificate, save-slot identity, exact native node or live executing-owner proof.'},
        'selected_rows':selected,'earlier_QR9_observations':observations,
        'master':'ManualSave-23 user-confirmed genuine Tower lineage; protected original is not a test work slot.',
        'slot_limit':'Latest HS1 revision36 is not independently bound to a save slot. Do not infer a slot from player1ULL.'}
    evidence_path.write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    cards=read(Q9/'worker_c/card_spec.json');by_id={c['id']:c for c in cards['cards']}
    queue=[]
    def add(id,priority,status,why,needs):
        queue.append({'id':id,'priority':priority,'status':status,'basis':why,'missing_prerequisites':needs,
            'manual_card_issued':False,'QR9_card_reused':by_id.get(id),
            'rule':'No setters, resets, old-clock adoption, fabricated history, automatic gameplay or repeated successful fixtures.'})
    add('S01',1,'NOT_TESTABLE_SELECTED_HISTORY','CVI02 cvi_02_finished1 and native completion in genuine selected lineage; recent snapshot agrees.',
        ['Another genuine fresh, not-admitted CVI02 fixture with earned prerequisites and no old owner/request. Current saves do not supply one.'])
    add('S02',2,'BLOCKED_SUBSCRIPTION_AND_STAGE_EVIDENCE','S00 Ronald contact Inactive; messages_enabled0; Issued0. Later evidence does not prove earned active subscription. Saints/Spy are completed.',
        ['Genuine existing subscription + Active Ronald contact, no first-enrollment fabrication.',
         'Verify actual fresh status/owner/prerequisites for sts_ep1_03 or sts_ep1_12; absence from finished metadata is insufficient.',
         'For late future: actual supported first200–203/pre220 stage and genuine Armed; no old sent1 timer adoption.'])
    add('S04',3,'UNKNOWN_UNSUPPORTED_OR_UNPROVEN_STAGE','Latest MQ007 shows total97/nonlethal51, defeated50=1, owner_known0, done0, reacquiring0, Issued0, ModeTalkConfirmed0; journals Inactive. Kill totals do not identify future1101.',
        ['Genuine exact supported pre1101 return/handoff stage and earned Regina history; exclude old11/51/95/opaque-loot seams.',
         'No changes to kills, mode, item ownership or quest facts to create the fixture.'])
    add('S06',4,'BLOCKED_HISTORY_EVIDENCE','Latest Brendan/Spray Paint journals all Inactive and watched facts0. Post-ending fallback cannot prove unearned fresh history or an earned progressed descendant.',
        ['Genuine known unearned pre-Tower history for negative containment OR separately proven earned/progressed descendant.',
         'No general fresh/sequel adapter is approved. Do not treat inactive post-Tower history as the certificate.'])
    add('S08',5,'BLOCKED_GENUINE_PENDING_OWNER','Successful Wilson/Bullets completion and reload behavior remain accepted. No currently demonstrated separate eligible pending request/timer/cleanup fixture.',
        ['A genuinely supported pending stage from a qualified S01/S02/S04 route; native save option at that stage.',
         'Separate real branch for interruption/reload; explicit before/after item/currency/reward evidence for idempotence.',
         'Do not repeat completed Wilson/Bullets/Zane/reload tests.'])
    add('S03',6,'NOT_TESTABLE_FRESH_NITRO','QR9S03 Issued1/Entered0, purchase counter1, all4 native unlock gettersfalse. Already-issued preservation is distinct from fresh eligibility.',
        ['Genuine independent not-Issued fixture with earned allowed Kusanagi and >=3 native purchases (not available).',
         'Actual existing-owner selector/liveness evidence before asking for an already-issued continuation test.'])
    queue_doc={'schema':1,'status':'NO_QUALIFIED_NEW_QUEST_CARD','source_epoch':'QR8:02','diagnostic_successor':'QR10D01 candidate_02 NOT_INSTALLED',
        'fixture_evidence':str(evidence_path),'prioritized':queue,
        'diagnostic_validation':{'id':'D00','status':'CONDITIONAL_AFTER_AUTHORIZED_INSTALL_AND_EXISTING_CALL_OPTION',
            'card':'TEST_CARDS.md','native_fact':'phonecall_player_with_regina_jones',
            'boundary':'Regina availability is not observed offline; see existing Call option first. No Call -> skip, no substitute eligibility or repeat completed quests.'},
        'accepted_do_not_repeat':['Until Death Do Us Part observed completion','Cynthia/Wilson delivered calls','Shoot to Thrill win/reward receipt',
            'Wilson eventual shop and completed-state reload','Bullets completion','Zane shop return, completed-state reload and post-Bullets line'],
        'coverage':'No new gameplay executed. QR9 original26-subcase/functional9-row results preserved; no inflated percentage or161-quest runtime PASS.'}
    queue_path.write_text(json.dumps(queue_doc,indent=2)+'\n',encoding='utf-8')
    inputs=[snapshot,Q9/'worker_c/card_spec.json',Q9/'stage_report_01/coverage.json',Q9/'report.md',
        W/'research/b0_missing_content/regina/json/base/open_world/fixers/reggie/phases/reggie.questphase.json',
        W/'research/b0_missing_content/regina/inventory.json',
        W/'research/finalboards_dismissal/decompiled/cyberpunk/systems/phoneSystem.script',
        W/'research/finalboards_dismissal/decompiled/cyberpunk/UI/fullscreen/phone_sms/messengerUtils.script',
        W/'research/finalboards_dismissal/decompiled/cyberpunk/UI/hud/phone/newHudPhoneGameController.script',
        W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/RTTITypes.hpp',
        W/'research/framework_pr63_01/codeware/scripts/Quest/QuestsSystem.reds',
        W/'research/finalboards_dismissal/tooling/python/capstone/lib/capstone.dll',
        Q9/'worker_b/tooling/lupa/luajit21.cp314-win_amd64.pyd']
    sources=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}for p in inputs]
    provenance={'local_inputs':sources,'installed_binaries':read(H/'review/review_result.json').get('installed_binaries','Exact hashes in review installed_game_guard.json + installed_cet_proxy_02.json'),
        'upstream':{'repository':'maximegmd/CyberEngineTweaks','commit':'b160d68cf923f2535cb3a6ebe006de86ef21e359',
            'files':[{'path':str(p),'sha256':sha(p),'url':'https://github.com/maximegmd/CyberEngineTweaks/blob/b160d68cf923f2535cb3a6ebe006de86ef21e359/src/reverse/'+p.name}for p in (H/'evidence/cet/src/reverse').glob('*')],
            'limits':'Pinned official source corroborates installed binary evidence; not asserted to be the installed full build. Local saved text is line-normalized.'},
        'phone_card_limits':'Historical pinned native exports/decompiled scripts establish contact/fact naming. Current compiled PhoneSystem/callability not certified; natural validation still required.',
        'engine_overlay':'Unversioned third-party engine-overlay source used only for discovery, not retained as installed-contract proof. Exact installed disassembly independently establishes class guard.'}
    provenance_path.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
    print({'queue':len(queue),'qualified_new_quest_cards':0,'conditional_diagnostic_cards':1,'source_pins':len(sources),'snapshot_revision':raw['revision']})

if __name__=='__main__':main()
