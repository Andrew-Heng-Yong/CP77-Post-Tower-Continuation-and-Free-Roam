"""Report audited U10 native component scope and its explicit live limits."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from catalog_gig_rollout_r2 import read,sha,walk
HERE=ROOT/'research/gigs_u10/native'

def main():
    build=ROOT/'prealpha/gigs_u10/native/build/native_05'
    component=read(build/'component.json');test=read(build/'tests.json');plan=read(HERE/'build_plan_01.json');contracts=read(HERE/'contracts_02.json')
    assert test['component_sha256']==sha(build/'component.json')
    rows=[]
    for j in plan['jobs']:
        parent_nodes=j['parent']['ancestors']+[n for g in j['parent']['nested'] for n in g['nodes']]
        parentfacts=sorted({x['factName'] for x in walk(parent_nodes) if isinstance(x.get('factName'),str)})
        journal_ops=[x for x in walk(parent_nodes) if x.get('$type') in ('questJournalEntryState_ConditionType','questJournalQuestEntry_NodeType','questJournalEntry_NodeType')]
        rows.append(dict(id=j['id'],title=j['title'],original_parent=j['parent']['binding'],original_main=j['resources'][0]['depot'],restored_native_reference=next(r['native'] for r in component['recipes'] if r['kind']=='entry' and r['id']==j['id']),
            native_parent_fact_predicates=parentfacts,native_parent_journal_operations=journal_ops,
            exact_original_lifecycle_companions=[{k:v for k,v in c.items() if k!='embedded'} for c in j['companions']],
            resolved_quest_resources=[dict(depot=r['depot'],source=r['binding']['source'],embedded_index=r['binding']['embedded_index']) for r in j['resources']],
            resolved_scenes=[s['depot'] for s in j['scenes']],source_reference_gaps=[],
            source_credit_branch=j['credit_branch'],source_map_branches=j['map_count'],
            native_calls_choices_items_rewards='Original gameplay remains referenced, except the separately audited Psychofan presentation-only clones.',
            admitted_state='Actual own quest/phase/objective Inactive, exact native fresh fact guards, two stable runtime observations, native synchronous preflight, valid Tower/profile/phone support.',
            existing_progress='No supported reentry point proven. Preserve earned state and defer; never silently reset/restart.',
            completed='Own root Succeeded or terminal/progress facts fail fresh admission; no reward replay.',
            pre_tower_parent_history='Family requires genuine pre-Tower Ghost Town completion witness; current after-ending facts alone cannot qualify.' if j['id']=='sts_wbr_hil_06' else None))
    report=dict(status='PASS_U10_NATIVE_COMPONENT_NOT_INSTALLED_OR_LIVE_PROOF',component='prealpha/gigs_u10/native/build/native_05/component.json',component_sha256=sha(build/'component.json'),tests=test,
        source_counts=dict(jobs=len(rows),quest_resources=sum(len(j['resources']) for j in plan['jobs']),scene_resources=sum(len(j['scenes']) for j in plan['jobs']),resources=len(component['resources']),boots=len(component['boots']),credits=len(plan['credits']),maps=len(plan['maps'])),
        rows=rows,retaliation=dict(component['overlay'],scope='Exactly two missing selector startup edges restored, each AND owned U10 Started. All other predecessor nodes, graph IDs, conditions and edges compare equal; old Error404 exclusion retained.',
            idle_boundary='Fresh new-gig preparation/admission requires affected gang pending=0, mws_chase_active=0, cancellation=0; existing issued owner reused. Native queue clear is followed only by original checkpoint bookkeeping and terminating output.',
            no_reissue='The overlay is not an XL boot. It preserves the existing boot/resource/graph identity; U10 only monotonically requests the existing service if needed.',
            live_limit='Engine adoption of newly connected dormant selectors inside saved existing owners requires live verification.'),
        native_writes='Original authored parent POI/native activation operations and seven original district credit increments; added code writes own markers and existing U9 service/tier requests only. No native start/terminal/pending reset, quest reset, save rewrite, item grant or synthetic reward.',
        reuse='Existing U9 phone and tier/retaliation services retained; no parallel duplicate global service owner.',
        source_scope='Only connected original normal input, exact main references, connected output companions, original completion and map slices. Adjacent seed-only resources do not imply a connected gameplay owner.',
        family_counter='Original hil_06_finished waiter root/2/6 node5 is unconnected to the Wakako increment; no synthetic Family Heirloom counter credit added.',
        inventory_evidence='research/gigs_u10/native/inventory_guard_02.json',independent_item_evidence='research/gigs_u10/presentation/item_assessment_01.json',validation_limits=['Static/source/policy checks are not engine simulation or gameplay proof.','Six exact unique Quest-item contradictions are guarded by runtime and cloned native player-inventory Equal0 checks.','Family Heirloom current post-Tower save without a genuine pre-Tower witness defers.','All eight unsupported existing-progress states defer without restart.'],
        game_writes=0,save_writes=0,launches=0)
    (HERE/'assessment_02.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['source_counts']))

if __name__=='__main__':main()
