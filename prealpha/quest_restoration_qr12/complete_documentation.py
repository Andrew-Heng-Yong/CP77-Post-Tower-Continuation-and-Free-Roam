"""Materialize bounded QR12 findings and source pins. No runtime operations."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;W=H.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def put(name,x):
    p=H/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
    paths=['prealpha/quest_restoration_qr7/REPORT.md','prealpha/quest_restoration_qr8/REPORT.md',
        'prealpha/quest_restoration_qr9/worker_c/card_spec.json','prealpha/quest_restoration_qr9/report.md',
        'prealpha/quest_restoration_qr10/REPORT.md','prealpha/quest_restoration_qr10/TEST_CARDS.md',
        'prealpha/quest_restoration_qr11/observations/D00E_20261103_01/result.json',
        'prealpha/quest_restoration_qr11/d00e_01/diagnostics_manifest_01.json',
        'prealpha/quest_restoration_qr11/save_selection.json','docs/whitelist_final_r6.md',
        'tools/inspect_gig_save.ps1','tools/inspect_gig_saved_journal.ps1','tools/read_afterlife_savefacts.ps1',
        'research/gig_restoration/save_audit_20261008.json']
    evidence=[{'path':str(W/p),'sha256':sha(W/p)}for p in paths]
    put('evidence_sources.json',{'status':'PINNED_EXISTING_EVIDENCE_REUSED','sources':evidence,
        'resource_pins':'catalogue.json sources pins exact existing QR9 resource readbacks and selected HS1 definitions; no resource re-export/rebuild.',
        'limits':'Historical preparation statements in predecessor reports remain historical. Current deployment and natural PASS authority are QR11 D00E assessment/current manifest.'})
    put('human_prerequisites.json',{'Brendan_pre_Tower_history':{'initial_answer':'Don’t remember','latest_answer':'i dont remember doing that','classification':'UNKNOWN_NATIVE_EARNED_HISTORY','never_started_confirmed':False,
        'context':'User asked Brendan quest name; clarified I Can See Clearly Now, later Spray Paint and Coin Operated Boy. No request to start/replay a quest.'},
        'D00E':'Reuse accepted normal El Capitan call and requested working-slot confirmation in QR11 assessment. Do not repeat or strengthen save/owner identity proof.'})
    blockers=[
        {'id':'RONALD_FIRST_ENROLLMENT','status':'SOURCE_CONFIRMED_UNIMPLEMENTED_HELD','evidence':['prealpha/quest_restoration_qr7/REPORT.md:30','prealpha/quest_restoration_qr8/REPORT.md:40'],
            'boundary':'Native B0 subscription node1755 remains unreachable. Menu options/bar prefab/contact/history support are not restored by prospective news. QR8 changes only four first-case predicates.',
            'ordinary_play':'No supported instruction to create first enrollment in this installed build. Existing genuine subscription may qualify a different prospective scenario.'},
        {'id':'RONALD_HISTORICAL_ADOPTION','status':'SOURCE_CONFIRMED_UNSUPPORTED_SCOPE','evidence':['prealpha/quest_restoration_qr7/REPORT.md:28','prealpha/quest_restoration_qr8/REPORT.md:22'],
            'boundary':'Already-entered jobs without genuine Armed, sent1/pending old native clocks and already-processed branches are not adopted, reset or reclocked.',
            'ordinary_play':'Preserve existing timers/history. A genuinely subscribed, supported future branch is different from historical adoption.'},
        {'id':'CVI02_OLD_CUSTOM_HISTORY','status':'SOURCE_CONFIRMED_FRESH_ONLY_BOUNDARY','evidence':['prealpha/quest_restoration_qr7/REPORT.md:24','prealpha/quest_restoration_qr9/worker_c/card_spec.json'],
            'boundary':'New specialized owner requires no old entered/request/outcome/private inflight history; retrospective replay/adoption is outside support.',
            'ordinary_play':'Completed jobs stay completed. Needs a separate genuine future-fresh history, never counter resets.'},
        {'id':'SKIPPY_ADMISSION_AND_LOOT','status':'SOURCE_CONFIRMED_UNCERTIFIED_SCOPE','evidence':['prealpha/quest_restoration_qr8/REPORT.md:69','prealpha/quest_restoration_qr9/worker_c/card_spec.json'],
            'boundary':'Native11/51/95 admission seams and opaque loot placement are not certified by the prospective1101 continuation. No general fresh-chain support is established.',
            'ordinary_play':'An already-earned supported return/handoff can supply new evidence. Counts/items alone do not prove its exact stage; no artificial kills/items.'},
        {'id':'BRENDAN_FRESH_AND_SEQUELS','status':'SOURCE_CONFIRMED_EXCLUSION_AND_UNIMPLEMENTED_ADAPTER','evidence':['docs/whitelist_final_r6.md','prealpha/quest_restoration_qr9/worker_c/card_spec.json'],
            'boundary':'I Can See Clearly Now/dumpster is fresh-excluded; earned descendants may be preserved, but no general new sequel adapter is approved/implemented.',
            'ordinary_play':'Report existing earned Spray Paint/Coin Operated Boy objective if encountered. Do not manufacture dumpster entitlement or reset private receipts.'},
        {'id':'NATIVE_CALLBACK_OBSERVATION','status':'SOURCE_CONFIRMED_INTERFACE_LIMIT','evidence':['prealpha/quest_restoration_qr10/REPORT.md','prealpha/quest_restoration_qr11/observations/D00E_20261103_01/result.json'],
            'boundary':'Installed CET NativeProxy receiver flags do not meet QuestsSystem scripted receiver requirement. Native callback delivery unsupported; D00E validates sampled getter differences only.',
            'ordinary_play':'Use validated bounded sampler after fixture qualification. No claim of native events, exact write ordering or executing-owner identity.'}]
    put('development_blockers.json',{'status':'SEPARATE_FROM_MISSING_FIXTURES','sources':evidence,'items':blockers,
        'unresolved_not_confirmed_gameplay_defects':[
            'Actual executing native/private graph owners, listeners, request queue, shared leases, controller termination and saved timer/refresh identity are not decoded by the available read-only reader/sampler.',
            'Five QR8 static UNKNOWN contracts retained: Career original early owner retirement, Cuckoo null-source provenance/invalid-record semantics, Voodoo eligibility/completion/persistence. No broad re-audit performed.',
            'Existing Nitro Issued selector is unobserved; fresh gates must not be reapplied to it.',
            'A missing eligible save or absent saved fact is not a quest defect.']})
    inv=read(H/'analysis_final_02/verified_fixture_inventory.json')
    selected=[r for r in inv['rows']if r['kind']=='GAME_SAVE'and r['slot_directory']in('ManualSave-23','ManualSave-24')]
    put('selected_fixture_evidence.json',{'rows':[{'slot':r['slot_directory'],'body_sha256':r['sha256'],'metadata_sha256':r['metadata_sha256'],'lineage':r['lineage'],
        'facts':r['saved_parse']['facts'],'journal_raw_matches':r['saved_parse']['journal_raw_matches'],'owner_surface':r['saved_parse']['owner_surface'],'scenarios':r['scenarios']}for r in selected],
        'interpretation':'Private MQ037 Issued/Entered1 rules out clean fresh negative fixture, not native earned-history proof. Missing saved entries remain absent. Cached HS1 post_ending_fallback is separately bound but not a pre-Tower certificate.'})
    text='# QR12 development blockers and observation boundaries\n\nThese are distinct from missing test fixtures. No gameplay repair is implemented or authorized in QR12. Source hashes are in evidence_sources.json and development_blockers.json.\n\n'
    for x in blockers:
        text+='## '+x['id']+'\n\n'+x['status']+' — '+x['boundary']+'\n\n'+x['ordinary_play']+'\n\nEvidence: '+', '.join(x['evidence'])+'.\n\n'
    text+='## Unknown observations\n\nExecuting owners/listeners/leases, native queued requests, exact saved timers and controller termination remain opaque. This is an instrumentation boundary, not a demonstrated gameplay defect. Existing Nitro Issued history is preserved. The five QR8 static UNKNOWNs remain unchanged. Missing fixture evidence never proves a broken quest.\n'
    p=H/'DEVELOPMENT_BLOCKERS.md';assert not p.exists();p.write_text(text,encoding='utf-8')
    print({'source_pins':len(evidence),'development_boundaries':len(blockers),'selected_fixtures':len(selected)})
if __name__=='__main__':main()
