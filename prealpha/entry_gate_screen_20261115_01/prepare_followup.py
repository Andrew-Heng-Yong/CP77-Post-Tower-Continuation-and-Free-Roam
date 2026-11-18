"""Read-only current journal and entry receipt query for the nine screened entries."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

def main():
    output = HERE / 'probe_02'
    if output.exists():
        raise RuntimeError('Fresh output required')
    entries = json.loads((HERE / 'sources_01/inventory.json').read_bytes())['entries']
    catalogue = json.loads((ROOT / 'prealpha/installed_qualification_20261115_01/run_01/catalogue.json').read_bytes())
    rows = []
    for entry in entries:
        paths = [j['path'] for r in catalogue['entries'] if r['id'] == entry['id']
                 for j in r['journals'] if j['class'] == 'gameJournalQuest' and j['path'].endswith('/' + entry['id'])]
        assert len(paths) == 1, entry['id']
        rows.append((entry['tag'], paths[0]))
    lua_rows = ','.join('{' + json.dumps(tag) + ',' + json.dumps(path) + '}' for tag, path in rows)
    command = ('do local q=Game.GetQuestsSystem(); local j=Game.GetJournalManager(); '
               'print("PTFR_SCREEN_02 BEGIN"); for _,r in ipairs({' + lua_rows + '}) do '
               'local e=j:GetEntryByString(r[2],"gameJournalQuest"); '
               'print(r[1].." entered="..q:GetFactStr(r[1].."_Entered").." journal="..'
               '(IsDefined(e) and tostring(j:GetEntryState(e)) or "missing")) end; '
               'for _,f in ipairs({"wst_ep1_09_active","wst_ep1_02_active","mq015_active"}) do '
               'print(f.."="..q:GetFactStr(f)) end; print("PTFR_SCREEN_02 END") end')
    sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
    from lupa.lua54 import LuaRuntime
    LuaRuntime().execute('return function() ' + command + ' end')
    output.mkdir()
    (output / 'screen.command.txt').write_text(command + '\n', encoding='utf-8')
    print(command)

if __name__ == '__main__':
    main()
