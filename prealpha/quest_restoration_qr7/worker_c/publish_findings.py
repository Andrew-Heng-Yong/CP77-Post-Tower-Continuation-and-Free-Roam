"""Publish only eight investigated contract updates; no central matrix writes."""
from pathlib import Path
import argparse,json,collections,csv
from prepare import ROOT,HERE,read,write,sha

def main(out):
    assert not out.exists();out.mkdir()
    prior=read(HERE/'baseline_01/original_unknowns.json')
    q7=ROOT/'prealpha/quest_restoration_qr7';epath=q7/'source_epoch_01.json';epoch=read(epath)
    approved_path=q7/'approved_changes_01.json';approved=read(approved_path)
    nitro=next(x for x in approved['resources'] if x['id']=='QR7-MQ060-REGISTERED-NATIVE-ENTRY-GATE')
    for key in ['source_evidence','source_review','serialized_checks','independent_serialized_review']:
        assert sha(nitro[key])==nitro[key+'_sha256']
    assert nitro['after']=='79FD3A440DFBCE6130AA5E5EA1D71E6E92BEAD27691C0AD0F59EFE7C94214784'
    candidate=Path(epoch['candidate']);baseline=read(HERE/'baseline_01/baseline.json');app=[]
    for row in baseline['source_pins']:
        d=row['depot'];path=candidate/'archive_source'/d.replace('\\','/');now=sha(path)
        assert now==epoch['source_resources'][d]
        assert now==row['sha256'] or d==nitro['depot']
        app.append({'depot':d,'before':row['sha256'],'after':now,'changed':now!=row['sha256'],'effective_path':str(path)})
    assert len([x for x in app if x['changed']])==1
    evidence_files=[HERE/p for p in ['nitro_authority_03/evidence.json','journal_proof_02/result.json','remaining_01/result.json',
        'remaining_controls_01/result.json','quest_providers_01/manifest.json','stock_01/records.json']]
    for p in evidence_files: assert p.is_file()
    journal=read(HERE/'journal_proof_02/result.json');remaining=read(HERE/'remaining_01/result.json')
    assert all(x['pass'] for x in journal['checks']) and all(x['pass'] for x in remaining['checks'])
    updates=[]
    for old in prior:
        q=old['quest_id'];stage=old['stage']
        row={'quest_id':q,'title':old['title'],'stage':stage,'previous_status':'UNKNOWN','status':'UNKNOWN',
            'source_epoch_investigated':'QR6:00 exact baseline with targeted QR7:01 repair applicability',
            'effective_source_epoch':'QR7:01','proven':[],'approved_differences':[],'remaining':[],'evidence':[],
            'resolved_unknowns':[],'remaining_unknowns':[],'runtime_changes':[]}
        if q=='mq060_nitro':
            row['status']='APPROVED_DEVIATION' if stage in ['entry','eligibility'] else 'CONDITIONAL'
            row['resolved_unknowns']=['Winning native source authority: current unique main .gamedef registers cyberpunk2077.quest; its connected root82/4→bugfixing9→root/3 reaches native OR3 AND purchases>=3→89.Start. Standalone mq060.quest is absent from both captured game-definition root lists.',
                'Prospective source defect: current S29 used the standalone OR4 selector without purchases. Independent A source review approved positive registered ancestry; coordinator typed/serialized the exact native93/104 suffix into both pre-Issued65003/65004 guards.']
            row['proven']=[
                'Current .gamedef, main .quest and standalone have unique providers in134 current archive indexes. Exact source paths, payload hashes, nodes and socket chains are pinned; this is positive registered-root evidence beyond QR6 reverse-reference absence.',
                'QR7:01 corrected entry SHA79FD3A440DFBCE6130AA5E5EA1D71E6E92BEAD27691C0AD0F59EFE7C94214784 retains every old node/edge/receipt/body binding, appending only the exact OR3 and carbought_counter>=3 native conditions before Issued65005.',
                'Coordinator actual serialized tests and independent A review pass. Across80 actual-condition fixtures, old47 native selector discrepancies become0. Existing native-body dependencies, emails prefab, customer contact, scans and vehicle entitlement are unchanged and retain QR6 per-quest source evidence.']
            row['approved_differences']=['Existing approved Tower fresh-owner/history adaptation is retained. The new gate restores the registered vanilla eligibility for prospective, not-yet-issued owners; it preserves the existing standalone selector nodes downstream for saved compatibility.']
            row['remaining']=['LIVE_ONLY: actual native gate wakeup, engine scheduling and supported save transitions were not exercised.',
                'Already-issued owners waiting downstream retain their original four-bike selector and progress. This repair does not retroactively tighten, restart, reset or migrate them.',
                'Worker C does not certify the successor package rebuild, compile, archive readback or deployment. Those coordinator gates are separate.']
            row['evidence']=[str(HERE/'nitro_authority_03/evidence.json'),str(HERE/'nitro_authority_03/source_pins.json'),str(approved_path)]+[nitro[k] for k in ['source_review','serialized_checks','independent_serialized_review']]+old['evidence']
            row['runtime_changes']=[{'id':nitro['id'],'depot':nitro['depot'],'before':nitro['before'],'after':nitro['after'],'implemented_by':'coordinator only','scope':nitro['scope']}]
        elif q=='mws_wat_08_trauma_drama':
            row['resolved_unknowns']=['Native JournalManager same-state rejection and actual graph-operation applicability are proven on the exact current executable, rather than inferred from an API declaration.']
            row['proven']=[
                'Native/current SMS7 and56 are identical journal identities and sendNotification1/trackQuest0 writes. Native6→68→7→57(two seconds)→56→8 occurs before first-place8→9→started66, so early completed message histories are source-realizable.',
                'Current RTTI/constructor/vtable evidence ties JournalQuestEntry_NodeType vfunc108 to processing56455C, which calls JournalManager290→565DFC→268→6C1A48→Active6543EC→common654C0C→guard6545D0.',
                'The actual machine-code guard compares old/new states and immediately returns false when equal, before state writes/listener notifications. Five native-state equality fixtures and a flipped actual JNE negative control verify this property; the current input executable remains unchanged.',
                'No duplicate notification or reward was asserted. No SMS receipt, native counter or synthetic acknowledgement was added.']
            row['remaining_unknowns']=['Saved early native-owner retirement and concurrent/queued owner state for the exact pre-first-place history remain unproved; the new proof does not create an old-owner transition fixture.']
            row['remaining']=row['remaining_unknowns']+['LIVE_ONLY: separate tracking callbacks, other journal ancestor states, game notifications and future-version save transitions remain outside this bounded equality proof.']
            row['evidence']=[str(HERE/'journal_proof_02/result.json'),str(HERE/'journal_node_03/manifest.json'),str(HERE/'quest_providers_01/manifest.json')]+old['evidence']
        elif q=='sts_std_rcr_02':
            f=remaining['findings'][q];row['proven']=f['new_proven'];row['remaining_unknowns']=f['remaining'];row['remaining']=f['remaining']
            row['resolved_unknowns']=['Decoder-versus-native ambiguity is resolved: actual serialized source:null connections, not missing normalized names, cause the four inherited diagnostics. Direct provider/stock lookup now pins their current applicability.']
            row['evidence']=[str(HERE/'remaining_01/result.json'),str(HERE/'remaining_controls_01/result.json'),str(HERE/'quest_providers_01/manifest.json'),str(HERE/'stock_01/records.json')]+old['evidence']
        else:
            f=remaining['findings'][q];row['proven']=f['new_proven'];row['remaining_unknowns']=f['remaining'];row['remaining']=f['remaining']
            row['resolved_unknowns']=['Current late door predicate, original body binding, actual persistent PS field flags and generic door handler behavior are now source-proven. None proves a historical container was unclaimed.']
            row['evidence']=[str(HERE/'remaining_01/result.json'),str(HERE/'remaining_controls_01/result.json'),str(HERE/'inject_node_02/manifest.json'),str(HERE/'transaction_01/manifest.json'),str(HERE/'inject_followup_01/manifest.json')]+old['evidence']
        row['original_findings_source']=old['findings_source'];row['original_findings_source_sha256']=old['findings_source_sha256']
        row['independent_review']='Pending worker review for new Career/Cuckoo/Voodoo properties; Nitro accepted source and serialized review separately pinned.'
        updates.append(row)
    write(out/'contract_updates.json',updates)
    for q in sorted({x['quest_id'] for x in updates}):
        rows=[x for x in updates if x['quest_id']==q]
        write(out/'quests'/q/'contracts.json',{'quest_id':q,'title':rows[0]['title'],'scope':'Only named QR6 UNKNOWN contract updates; other contracts retain QR6 findings and are not re-audited here.',
            'effective_source_epoch':'QR7:01','fully_static_verified':False,'contracts':{x['stage']:{k:v for k,v in x.items() if k not in ['quest_id','title','stage']} for x in rows}})
    with (out/'contract_updates.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['quest_id','stage','previous_status','status','resolved_unknowns','remaining_unknowns']);w.writeheader()
        for x in updates:w.writerow({k:json.dumps(x[k],ensure_ascii=False) if isinstance(x[k],list) else x[k] for k in w.fieldnames})
    write(out/'effective_applicability.json',{'epoch':str(epath),'epoch_sha256':sha(epath),'targeted_effective_resources':app,
        'limits':['Only25 targeted resources rehashed here; whole-candidate preservation is the coordinator gate.','Installed PH3 remains distinct from this staged QR7 candidate.']})
    write(out/'results.json',{'status':'EIGHT_TARGETED_UNKNOWN_DISPOSITIONS_RECORDED_WITH_LIMITS','assigned_contracts':8,'quest_count':4,
        'status_counts':dict(collections.Counter(x['status'] for x in updates)),
        'contract_updates':str(out/'contract_updates.json'),'contract_updates_sha256':sha(out/'contract_updates.json'),
        'evidence_units':[{'path':str(p),'sha256':sha(p)} for p in evidence_files],
        'effective_applicability':str(out/'effective_applicability.json'),'effective_applicability_sha256':sha(out/'effective_applicability.json'),
        'runtime_changes_by_worker_c':[],'coordinator_repair':[nitro],
        'fully_static_verified_quests':[],'remaining':{'UNKNOWN_rows':5,'details':'Career1, Cuckoo1, Voodoo3; no UNKNOWN was relabelled to reduce a count.'},
        'code_sha256':sha(__file__)})
    (out/'REPORT.md').write_text('''# QR7 Worker C — eight UNKNOWN resolutions

Three Nitro contracts now have evidence-backed dispositions after the coordinator's approved prospective repair. Five UNKNOWN rows remain: Career persistence, Cuckoo shared dependencies and three Voodoo history/reward contracts. No quest is claimed fully static-verified.

- **Nitro:** New unique game-definition providers establish the registered main root and connected native OR3 plus purchases>=3 gate. Independent A source/serialized reviews accepted that authority. The coordinator added exact native predicates only to pre-Issued guards65003/65004. Existing saved downstream owners remain unchanged. The earlier rejected proposal was not retried without the new evidence and peer gate.
- **Career:** Current native binary implementation and graph dispatch prove repeated same-state journal writes skip state changes and state-listener notifications. Exact early SMS identities remain native. Saved early-owner retirement/concurrency remains a specific UNKNOWN; no receipt or reset is invented.
- **Cuckoo:** Direct current stock lookup still lacks item114327022403, an inventory predicate rather than a grant. Both native inventory routes reach the same choice. Four missing sources are actual serialized nulls on unreachable native root branches, not decoder omissions. No restoration-specific source defect is proven.
- **Voodoo:** Late admission rejects an open native door and keeps the original stash resource. Persistent door fields and generic close/disable handlers are proven, but native cleanup21 specifies TerminalControllerPS where query3 specifies DoorControllerPS on the same NodeRef. Actual binding, historical container/door state, generic-hub dispatch and downstream Inject idempotence remain unresolved. No duplicate grant is claimed or patched.

All writes stayed inside worker_c. Fresh readbacks cover56 targeted resources; two134-index provider captures found unique providers for eight targeted startup/quest resources. Native executable, bytecode and stock databases were read only. Four raw-resource and one native-field negative controls supplement the equality-guard machine-code mutation and exact Career message-identity control. Counts are separate evidence events, not gameplay coverage.

Run the supplied preparation/capture scripts only with fresh output paths. The fixed-reader script representation is analysis-only, preserves all209157 existing definition payloads and string pools, and is never an engine/cache input. No game, save, release, installed file or existing candidate was written by this worker. The coordinator owns final compile/package/readback/preservation gates.
''',encoding='utf-8')
    print({'rows':len(updates),'statuses':dict(collections.Counter(x['status'] for x in updates)),'out':str(out)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
