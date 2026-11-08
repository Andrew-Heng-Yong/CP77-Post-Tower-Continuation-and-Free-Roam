"""QR13 C bounded evidence delta/gate inspection; no game/save/body/build access."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent;W=H.parents[2]
Q8=W/'prealpha/quest_restoration_qr8';Q12=W/'prealpha/quest_restoration_qr12'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def put(name,x):
    p=H/name;assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def main():
    ep=Q8/'source_epoch_02.json';assert sha(ep)=='F42680E09E2B61BC926798DD5FA5B4E728CB20057382591D5BD5353B197FC38F'
    epoch=read(ep);candidate=Path(epoch['candidate']);script=candidate/'package/r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
    pin=next(r['sha256']for r in epoch['package_files']if r['path'].replace('\\','/').endswith('/PTFR_SideJobsS23.reds'));assert sha(script)==pin
    text=script.read_text(encoding='utf-8-sig')
    def arr(name):return json.loads(re.search(r'func '+name+r'\(\).*?return (\[[^\]]*\])',text,re.S)[1])
    names,mins,maxs=arr('FactNames8'),arr('FactMin8'),arr('FactMax8');assert len(names)==len(mins)==len(maxs)
    gate={n:{'min':a,'max':b}for n,a,b in zip(names,mins,maxs)}
    assert [gate[x]['min']for x in ['mq007_skippy_enemies_lethal','mq007_skippy_enemies_non_lethal','mq007_skippy_enemies_total']]==[11,51,95]
    assert all(gate[x]['min']==gate[x]['max']for x in gate)
    assert gate['PTFRS23_MQ007_ModeTalkConfirmed']=={'min':1,'max':1}
    assert 'this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 && this.Read(8).valid;'in text
    restored=[]
    for depot,pin in epoch['source_resources'].items():
        if 'skippy'in depot.lower()or'mq007'in depot.lower():
            p=candidate/'archive_source'/depot;assert sha(p)==pin;restored.append({'depot':depot,'path':str(p),'sha256':pin})
    selected=[]
    for r in read(Q12/'selected_fixture_evidence.json')['rows']:
        wanted=['mq007_skippy_enemies_lethal','mq007_skippy_enemies_non_lethal','mq007_skippy_enemies_total','mq007_skippy_50_enemies_defeated','mq007_skippy_owner_known','mq007_done','PTFRS23_MQ007_ModeTalkConfirmed','PTFRS23_MQ007_Issued']
        selected.append({'slot':r['slot'],'body_sha256':r['body_sha256'],'facts':{n:{'rows':r['facts'].get(n,[]),'absent':n not in r['facts']}for n in wanted},'native_quest_system_types':[v['type']for v in r['owner_surface']if v['path']=='questSystem']})
    report=read(Q12/'observations/runtime_eligibility_02/result.json');human=next(r for r in report['observations']if r['scenario']=='SKIPPY_supported_return_1101')
    paths=[ep,script,Q8/'completion.json',Q8/'README.md',Q8/'HANDOFF.md',Q8/'regression_evidence.json',Q8/'remaining_blockers.json',
        Q8/'rebuild_candidate.ps1',Q8/'verify_archive.ps1',Q8/'verify_successor.py',Q8/'package_candidate.py',Q8/'verify_compile_inputs.py',
        Q8/'worker_a/verify_final_gate.py',Q8/'worker_a/extract_final_package.ps1',Q8/'worker_a/verify_inherited_controls.py',Q8/'worker_a/verify_namespace.py',
        Q8/'worker_a/final_package_01/verification/result.json',Q8/'verification/compile_successor_01/result.json',
        W/'prealpha/quest_restoration_qr4/candidate_01/repair_mq007/patch.json',W/'prealpha/quest_restoration_qr4/groups/G08/regina_world_01/ownership.json',
        Q12/'selected_fixture_evidence.json',Q12/'observations/runtime_eligibility_02/result.json',Q12/'REPORT.md',W/'docs/skippy_vanilla_wiki_review_20261028.md']
    pins=[{'path':str(p),'sha256':sha(p)}for p in paths]
    put('skippy_delta.json',{'status':'NO_NEW_EVIDENCE_JUSTIFYING_SKIPPY_RUNTIME_CHANGE','source_pins':pins,'current_source_resources':restored,'current_admission':{'script':str(script),'sha256':sha(script),'driver_index':8,'fact_gate':gate},
        'new_QR12_evidence':selected,'human_report':human,'delta_assessment':[
            'QR12 read-only save inspection adds exact snapshot values and parser surfaces, not a new native stage/owner/reward decoder.',
            '97total/51nonlethal and13lethal do not satisfy current11/51/95 exact seam; absence is not runtime0. This repeats the known mismatch with better pinned serialized evidence, not a new safe widening predicate.',
            'User-reported quest completion is not bound to a saved body/stage or captured Regina follow-up/reacquisition. Preserve completed history and skip replay.',
            'No new decoded persistent sector, entity/container/loot claim identity, saved owner retirement, mode-talk completion receipt or future1101 event input is supplied by QR12.',
            'The opaque native questSystem surface remains NULL/default data. Journal/fact snapshots do not establish executing ownership.'
        ],'blocked_cases':[
            {'case':'Broaden progressed native11/51/95 seam','missing':'An earned native post-mode-dialogue invariant independent of mutable counters, exact old owner/stage retirement or safe reuse, and reward/history mapping. Do not set ModeTalkConfirmed or relax all counters based on 50defeated alone.'},
            {'case':'Retroactively adopt done/returned or pending Regina history','missing':'Exact original/private helper identity, real pending elapsed timer and request/ACK state. Future1101 helper does not certify old adoption; no reset/rearm.'},
            {'case':'Fresh-chain or opaque loot support','missing':'Decoded exact persistent world entity/loot/claim history; registered variant descriptor is identified but sector worldNode content remains opaque.'}
        ],'implemented_changes':[],'runtime_test_cards':[],'scope':'No saved bodies read, no game/API/CUA/build/install/compile/runtime edits. Existing evidence/payload bytes only.'})
    protected=[{'depot':r['depot'],'sha256':epoch['source_resources'][r['depot']],'intent':r['intent']}for r in epoch['inherited_repair_resources']]
    protected += [{'depot':r['depot'],'sha256':epoch['source_resources'][r['depot']],'intent':r['intent']}for r in epoch.get('changes',[])]
    put('successor_gates.json',{'status':'INSPECTED_DERIVATION_NOT_EXECUTED','canonical_epoch':{'path':str(ep),'sha256':sha(ep),'key':'QR8:02'},
        'source_count':len(epoch['source_resources']),'package_count':len(epoch['package_files']),'archive_sha256':epoch['archive_sha256'],'xl_sha256':epoch['xl_sha256'],
        'protected_existing_repairs':protected,'gates':[
            {'id':'G1','action':'Fresh candidate only if a runtime change is approved. Copy complete QR8:02 archive_source and package; verify all source/package bytes against source_epoch02. No baseline-only ZIP.', 'evidence':'source_epoch_02.json; integrate_late_future.py inspected as historical example.'},
            {'id':'G2','action':'Fail-before test from exact pinned original/restored source; approved minimal delta with immutable IDs/edges/receipts and original ownership/prefab obligations. Independent review before integration.','evidence':'verify_successor.py; approved_changes_01.json; actual typed before/after manifest.'},
            {'id':'G3','action':'Serialize altered resource in fresh staging, export actual typed before/after readback and compare entire normalized model plus explicit intended-difference allowlist. Preserve saved identities and copied nested graph edges.','evidence':'readback_late_future.ps1; tools/build_phase2a.ps1 -HelpersOnly -WolvenKitRoot research/sidejobs_s28/tooling/wolvenkit_9_1_0/package.'},
            {'id':'G4','action':'Pack complete staged source with ArchiveWriter.WriteArchive. Reopen and extract EVERY member, compare exact member/FNV-key inventory and bytes against approved successor epoch.','evidence':'rebuild_candidate.ps1; worker_a/extract_final_package.ps1.'},
            {'id':'G5','action':'All retained CR1/PH1/PH2/PH3 and QR3–QR8 repairs remain exact, or receive separately reviewed semantic supersession keeping the original fix. Whole-source delta allowlist and donor controls required.','evidence':'worker_a/verify_inherited_controls.py; worker_a/inherited_controls_02/result.json; protected_existing_repairs.'},
            {'id':'G6','action':'Provider/depot collisions and ArchiveXL generated IDs are separate gates. For changed/new namespaces/registrations inspect all effective providers/additions/native target nodes and unsupported shapes. Preserve old order and IDs.','evidence':'worker_a/verify_namespace.py; namespace_verification_01/result.json (185indexes/76XL is historical scope, not fresh census).'},
            {'id':'G7','action':'If REDS unchanged, reuse actual prior compile only after exact complete compiler/source/cache/dependency pins and compiled output equivalence plus candidate managed sources. Otherwise fresh complete-input SCC outside game.','evidence':'verify_compile_inputs.py; QR6 verification/compile_01/result.json; QR8 verification/compile_successor_01/result.json (131sources/134pins/46managed).'},
            {'id':'G8','action':'Package only changed successor. Verify expected stable51paths plus explicitly authorized additions, ZIP entry uniqueness/CRC/hash equality and actual final archived resource bytes independently. Keep diagnostics outside Core51.','evidence':'package_candidate.py; worker_a/verify_final_gate.py; final_package_01/verification/result.json.'},
            {'id':'G9','action':'Verify protected installed Core, diagnostic sampler/config, saves/cache/external mods and pinned predecessor/evidence unchanged. No deployment/launch/save/fact mutation/release is authorized.','evidence':'current-state; QR11 d00e manifest; QR12 latest observations preservation scope.'}
        ],'pitfalls':[
            'knowledge/consolidated-build.md retains historical PH3 wording; current-state and QR8:02 source_epoch win for current installed source.',
            'QR8 verify_archive.ps1 hardcodes source_epoch00 and labels baselineQR8:00: it cannot certify finalQR8:02 or QR13.',
            'QR8 rebuild_candidate/package_candidate/verify_successor/integrate scripts hardcode old one-shot epochs/output paths: inspect and adapt into a fresh QR13 script, never rerun in place.',
            'Do not add assertion counts as unique quest/gameplay coverage. Structural compile/serialization/package passes are separate from runtime owner proof.'
        ],'runtime_changes':0,'historical_builders_executed':False})
    print({'status':'C_EVIDENCE_DELTA_AND_BUILD_GATES_COMPLETE','Skippy_changes':0,'Skippy_resources_pinned':len(restored),'source_pins':len(pins),'gates':9})
if __name__=='__main__':main()
