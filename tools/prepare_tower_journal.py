"""Generate a bounded exact journal manifest and native-API redscript candidate."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ep1/quests/main_quest/q307_tomorrow'
SOURCE = ROOT / 'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json'
GUARDS = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
              q307_done=1, q307_finished=1, q307_2079=1,
              q307_main_game_killed=1, q307_ep1_killed=1,
              q305_johnny_scene_active=0, q115_point_of_no_return=0,
              PTFRBASE_Suspended=0, PTFRTJ_Suspended=0)
MUTABLE = {'gameJournalQuest', 'gameJournalQuestPhase', 'gameJournalQuestObjective'}

def find(value):
    result = []
    if isinstance(value, dict):
        if value.get('id') == 'q307_tomorrow' and value.get('$type') == 'gameJournalQuest':
            result.append(value)
        for child in value.values():
            result.extend(find(child))
    elif isinstance(value, list):
        for child in value:
            result.extend(find(child))
    return result

def inventory(node, parent):
    path = parent + '/' + node['id']
    rows = [dict(path=path, parent=parent if path != BASE else '',
                 id=node['id'], className=node['$type'], mutable=node['$type'] in MUTABLE)]
    for handle in node.get('entries', []):
        rows.extend(inventory(handle['Data'], path))
    return rows

def main():
    roots = find(json.loads(SOURCE.read_text(encoding='utf-8-sig')))
    assert len(roots) == 1
    rows = inventory(roots[0], 'ep1/quests/main_quest')
    assert len({r['path'] for r in rows}) == len(rows)
    assert sum(r['className'] == 'gameJournalQuestPhase' for r in rows) == 2
    assert sum(r['className'] == 'gameJournalQuestObjective' for r in rows) == 20
    template = (ROOT/'redscript/PTFR_TowerJournal/TowerJournalCleanup.reds.in').read_text()
    statements = []
    for r in rows:
        args = ','.join(json.dumps(r[k]) for k in ('path', 'className', 'parent', 'id'))
        statements.append(f'    ArrayPush(result,this.Row(j,{args},{str(r["mutable"]).lower()}));')
    text = template.replace('@@ROWS@@', '\n'.join(statements)).replace('@@COUNT@@', str(len(rows)))
    text = text.replace('@@GUARDS@@', '\n'.join(
        f'    if q.GetFact(n"{name}") != {value} {{ return false; }}' for name,value in GUARDS.items()))
    target = ROOT/'redscript/PTFR_TowerJournal/TowerJournalCleanup.reds'
    target.write_text(text, encoding='utf-8')
    audit = ROOT/'research/tower_journal_cleanup'
    audit.mkdir(parents=True, exist_ok=True)
    manifest = dict(status='MANUAL_CANDIDATE_NOT_LIVE_VALIDATED', root=BASE, rows=rows,
                    guards=GUARDS, source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    redscript_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                    automatic=False, quest_fact_writes=False, save_file_writes=False)
    (audit/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),objectives=20,phases=2,status=manifest['status'])))

if __name__ == '__main__': main()
