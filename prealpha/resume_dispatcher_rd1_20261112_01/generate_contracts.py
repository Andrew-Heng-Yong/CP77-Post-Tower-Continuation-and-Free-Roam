"""Generate script/native stage predicates from the same reviewed contract data."""
import argparse
import json
import re
from common import HERE, RED_DIR, read, write, sha


def array(source, name):
    match = re.search(r'public static func '+re.escape(name)+r'\(\) -> array<[^>]+> \{ return (\[.*?\]); \}', source)
    assert match, name
    return json.loads(match[1])


def contracts():
    base = HERE / 'base_02/package' / RED_DIR
    s22 = (base / 'PTFR_SideJobsS22.reds').read_text(encoding='utf-8-sig')
    s23 = (base / 'PTFR_SideJobsS23.reds').read_text(encoding='utf-8-sig')
    skippy_paths = array(s23, 'Paths8')
    skippy_classes = array(s23, 'Classes8')
    fixed = {
        'mq007_done': 0, 'mq007_debug': 0, 'mq007_skippy_owner_known': 1,
        'mq007_skippy_50_enemies_defeated': 1, 'mq007_skippy_stash': 0,
        'mq007_skippy_re_acquiring_done': 0,
    }
    skippy = {
        'id': 'mq007_smartgun', 'stage': 'deliver_skippy', 'tag': 'PTFRRD1_MQ007_DELIVERY',
        'native_source': 'base\\quest\\minor_quests\\mq007\\mq007.questphase',
        'entry': {'graph': 'root/5', 'source_outputs': [63], 'destinations': [[11, 'Active'], [72, 'In']],
                  'excluded_setup': [30, 63], 'reason': 'Owner reveal already earned; retain delivery callbacks without granting another Skippy.'},
        'journals': [{'path': p, 'class': c, 'history': [h], 'live': ([1, 2, 4] if i<4 else [1])}
                     for i,(p,c,h) in enumerate(zip(skippy_paths,skippy_classes,[2,2,2,2,1,1]))],
        'fixed_facts': fixed,
        'choice_facts': ['mq007_opt_A', 'mq007_skippy_50_enemies_killed_and_stoneColdKiller',
                         'mq007_skippy_50_enemies_maimed', 'mq007_skippy_annoyed', 'mq007_skippy_goes_emo'],
        'counter_facts': ['mq007_skippy_enemies_lethal', 'mq007_skippy_enemies_non_lethal', 'mq007_skippy_enemies_total'],
        'live_only_facts': {'mq007_interrupt_skippy_dialogue': 0, 'mq007_rapid_interrupt': 0},
        'other_owner_receipts': ['PTFRS23_MQ007_Issued', 'PTFRS23_MQ007_RESUME_Issued', 'PTFRQR4_MQ007_ReacquisitionIssued'],
        'own_receipts': ['PTFRRD1_MQ007_DELIVERY_Issued', 'PTFRRD1_MQ007_DELIVERY_Finished',
                         'PTFRRD1_MQ007_DELIVERY_Refused', 'PTFRRD1_MQ007_DELIVERY_Entered_21', 'PTFRRD1_MQ007_DELIVERY_Fault'],
        'item': 'Items.mq007_skippy',
        'handoff': ['PTFRSKIP_Ambient', 'PTFRSKIP_SC3'],
        'root_after_activation': 2,
    }
    heat_paths = array(s22, 'Paths2')
    heat_classes = array(s22, 'Classes2')
    a,b = array(s22,'StatesA2'),array(s22,'StatesB2')
    heat = {
        'id': 'q304_car_retrieval', 'stage': 'first_door', 'tag': 'PTFRS22_Q304',
        'native_source': 'ep1\\quest\\main_quests\\q304\\phases\\q304_car_retrieval.questphase',
        'entry': {'existing_boot': 'towercontinued\\sidejobs_s22\\moving_heat_boot.questphase',
                  'existing_owner': 'towercontinued\\sidejobs_s22\\moving_heat_resume.questphase',
                  'preserve_owner_bytes': True, 'reason': 'Extend reviewed first-door admission; preserve original messages, later progression and wrapper support.'},
        'journals': [{'path': p, 'class': c, 'history': ([2] if i<3 else sorted({a[i],b[i]})),
                      'live': ([1,2,4] if i<3 else sorted({a[i],b[i]}))}
                     for i,(p,c) in enumerate(zip(heat_paths,heat_classes))],
        'fixed_facts': dict(zip(array(s22,'FactNames2'),array(s22,'FactValues2'))),
        'choice_facts': [], 'counter_facts': [], 'live_only_facts': {},
        'other_owner_receipts': ['PTFRS24_Q304_FRESH_Issued'],
        'own_receipts': ['PTFRS22_Q304_Issued','PTFRS22_Q304_Finished','PTFRS22_Q304_Fault'],
        'item': None, 'handoff': [], 'root_after_activation': 2,
    }
    return [skippy, heat]


def quoted(value):
    return json.dumps(value, ensure_ascii=False)


def alternatives(variable, values):
    return '('+' || '.join(f'{variable}=={v}' for v in values)+')'


def emit_reader(contract, index):
    qid = quoted(contract['id'])
    lines = [f'  public static func Read{index}(game: GameInstance,requireHandoff: Bool) -> ref<ResumeObservationRD1> {{',
        '    let result=new ResumeObservationRD1();',
        '    let history=SnapshotStateHS1.Get(game);let jm=GameInstance.GetJournalManager(game);',
        '    if !IsDefined(history) || !history.Ready() || !IsDefined(jm) || jm.HasAnyDelayedStateChanges() { result.reason="History/journal unavailable.";return result; }',
        '    let past: Int32;let live: Int32;let entry: wref<JournalEntry>;let objective: wref<JournalQuestObjective>;',
        '    result.reason="Stage history or live progress does not match.";']
    for journal in contract['journals']:
        path, cls = quoted(journal['path']), quoted(journal['class'])
        lines += [f'    past=history.HistoryJournalRD1({qid},{path});',
            f'    live=ResumeDispatcherRD1.Journal(game,{path},{cls});',
            '    ArrayPush(result.values,past);ArrayPush(result.values,live);',
            f'    if !{alternatives("past",journal["history"])} || !{alternatives("live",journal["live"])} {{ return result; }}']
        if journal['class'] == 'gameJournalQuestObjective':
            lines += [f'    past=history.HistoryCounterRD1({qid},{path});',
                f'    entry=jm.GetEntryByString({path},{cls});objective=entry as JournalQuestObjective;',
                '    live=IsDefined(objective)?jm.GetObjectiveCurrentCounter(objective):-1;',
                '    ArrayPush(result.values,past);ArrayPush(result.values,live);',
                '    if past!=0 || live!=past { return result; }']
    for name, value in contract['fixed_facts'].items():
        lines += [f'    past=history.HistoryFactRD1({qid},{quoted(name)});live=ResumeDispatcherRD1.Fact(game,{quoted(name)});',
            '    ArrayPush(result.values,past);ArrayPush(result.values,live);',
            f'    if past!={value} || live!={value} {{ return result; }}']
    for name in contract['choice_facts']:
        lines += [f'    past=history.HistoryFactRD1({qid},{quoted(name)});live=ResumeDispatcherRD1.Fact(game,{quoted(name)});',
            '    ArrayPush(result.values,past);ArrayPush(result.values,live);',
            '    if (past!=0 && past!=1) || live!=past { return result; }']
    for name in contract['counter_facts']:
        lines += [f'    past=history.HistoryFactRD1({qid},{quoted(name)});live=ResumeDispatcherRD1.Fact(game,{quoted(name)});',
            '    ArrayPush(result.values,past);ArrayPush(result.values,live);',
            '    if past<0 || live<past { return result; }']
    for name, value in contract['live_only_facts'].items():
        lines += [f'    live=ResumeDispatcherRD1.Fact(game,{quoted(name)});ArrayPush(result.values,live);',
                  f'    if live!={value} {{ return result; }}']
    receipts = contract['other_owner_receipts'] + contract['own_receipts']
    lines += [f'    live=ResumeDispatcherRD1.Receipt(game,{quoted(receipts)});',
        '    ArrayPush(result.values,live);',
        '    if live!=0 { result.reason="Existing controller or receipt retained.";return result; }']
    if contract['item']:
        lines += ['    let player=GetPlayer(game);let tx=GameInstance.GetTransactionSystem(game);',
            '    if !IsDefined(player) || !IsDefined(tx) { return result; }',
            f'    live=tx.GetItemQuantity(player,ItemID.CreateQuery(t{quoted(contract["item"])}));',
            '    ArrayPush(result.values,live);if live!=1 { result.reason="Expected one existing Skippy.";return result; }']
    for tag in contract['handoff']:
        lines += [f'    if requireHandoff && !(ResumeDispatcherRD1.Fact(game,{quoted(tag+"_Stopped")})==1 ||',
            f'      (ResumeDispatcherRD1.Fact(game,{quoted(tag+"_Claimed")})==0 && ResumeDispatcherRD1.Fact(game,{quoted(tag+"_Entered")})==0 &&',
            f'       ResumeDispatcherRD1.Fact(game,{quoted(tag+"_Request")})==0 && ResumeDispatcherRD1.Fact(game,{quoted(tag+"_Stop")})==1)) {{',
            '      result.reason="Waiting for original ambient stop acknowledgement.";return result;',
            '    }']
    lines += ['    if jm.HasAnyDelayedStateChanges() { return result; }',
        '    result.valid=true;result.reason="Earned stage and current progress agree.";return result;', '  }']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    out=HERE/args.out;assert out.parent==HERE and not out.exists()
    values=contracts()
    out.mkdir();write(out/'contracts.json',values)
    source='public abstract class ResumeContractsRD1 {\n'+'\n'.join(emit_reader(c,i) for i,c in enumerate(values))+'\n}\n'
    (out/'contracts.reds').write_text(source,encoding='utf-8')
    write(out/'manifest.json',{'contracts_sha256':sha(out/'contracts.json'),'script_sha256':sha(out/'contracts.reds'),
        'scope':'Two earned stages; journal/fact definitions are shared by REDscript generation and native guard generation. Personal fixture values are not admission rules.'})
    print('Generated two earned-stage contracts and primitive observation readers.')


if __name__=='__main__':main()
