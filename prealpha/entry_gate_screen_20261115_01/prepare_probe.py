"""Prepare a bounded, read-only live screen from the exact installed sources."""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MANIFEST = ROOT / 'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deployment_01/installed_manifest_01.json'
EXCLUDE = {'mq018_writer': 'Old Tower-cleared message thread is out of scope.',
           'mq040_biosculpt': 'Raymond marker investigation was excluded by the user.',
           'mq026_conspiracy': 'New admission is excluded by R6.3.'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    output = HERE / 'probe_01'
    if output.exists():
        raise RuntimeError('Fresh output required')
    manifest = json.loads(MANIFEST.read_bytes())
    assert manifest['core_epoch'] == 'RD10_MID_QUEST_RESUME_RETIRED'
    pins = {r['path']: r for r in manifest['core_files']}
    entries, groups, sources = [], [], []
    for family in ('S25', 'S27', 'S28', 'S29', 'S30'):
        source_family = 'S29' if family == 'S30' else family
        rel = f'r6/scripts/PTFR_Consolidated/PTFR_SideJobs{source_family}.reds'
        path = Path(manifest['game_root']) / rel
        assert sha(path) == pins[rel]['sha256']
        source = path.read_text(encoding='utf-8-sig')
        data = source.split(f'public abstract class SideJobData{family} {{', 1)[1]
        if family == 'S29':
            data = data.split('// Three earned native entries added in S30', 1)[0]
        count = int(re.search(r'func Count\(\) -> Int32 \{ return (\d+);', data)[1])
        maps = {}
        for name in ('ID', 'Title', 'Tag'):
            body = re.search(rf'func {name}\(i: Int32\) -> String \{{([\s\S]*?)\n  \}}', data)[1]
            maps[name] = {int(i): text for i, text in re.findall(r'if i == (\d+) \{ return "([^"]+)";', body)}
            assert len(maps[name]) == count
        selected = []
        for i in range(count):
            row = {'family': family, 'id': maps['ID'][i], 'title': maps['Title'][i], 'tag': maps['Tag'][i]}
            row['excluded'] = EXCLUDE.get(row['id'])
            entries.append(row)
            if not row['excluded']:
                selected.append(row['tag'])
        groups.append((family, f'PTFR.SideJobs{source_family}.SideJobs{family}', selected))
        sources.append({'path': rel, 'sha256': sha(path)})
    # Each Inspect/Status method was reviewed: this invocation only reads state.
    rows = ','.join('{' + json.dumps(family) + ',' + json.dumps(system) + ',' + json.dumps(' '.join(tags)) + '}'
                    for family, system, tags in groups)
    command = ('do local q=Game.GetQuestsSystem(); local c=Game.GetScriptableSystemsContainer(); '
               'local n=0; local p=0; print("PTFR_SCREEN_01 BEGIN"); '
               'for _,g in ipairs({' + rows + '}) do local s=c:Get(CName.new(g[2])); '
               'if IsDefined(s) then print(s:Status()); for tag in string.gmatch(g[3],"%S+") do '
               'n=n+1; local issued=q:GetFactStr(tag.."_Issued"); '
               'local finished=q:GetFactStr(tag.."_Finished"); local fault=q:GetFactStr(tag.."_Fault"); '
               'if (issued==1 and finished==0) or fault~=0 then p=p+1; print(s:Inspect(tag)) end end '
               'else print(g[1].." unavailable") end end; local t=Game.GetQuestsContentSystem(); '
               'print("PTFR_SCREEN_01 checked="..n.." listed="..p.." tokensBlocked="..tostring(t:IsTokensActivationBlocked())); '
               'print("PTFR_SCREEN_01 END") end')
    assert not any(word in command for word in ('SetFact', 'ChangeEntry', 'Restored(', 'Poll(', 'GiveItem', 'Request'))
    sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
    from lupa.lua54 import LuaRuntime
    LuaRuntime().execute('return function() ' + command + ' end')  # Parse, never call Game.
    output.mkdir()
    (output / 'screen.command.txt').write_text(command + '\n', encoding='utf-8')
    (output / 'catalogue.json').write_text(json.dumps({'status': 'SOURCE_PINNED_LIVE_SCREEN',
        'manifest_sha256': sha(MANIFEST), 'sources': sources, 'entries': entries,
        'selected_count': sum(r['excluded'] is None for r in entries),
        'limits': ['Listed entries are candidates for review, not proved defects.',
                   'This first screen covers five indexed fresh-entry controller families, not every installed quest.',
                   'Read-only getters and Inspect/Status only; no fact, journal, timer or owner writes.']}, indent=2) + '\n', encoding='utf-8')
    print(f'Prepared {sum(r["excluded"] is None for r in entries)} entries; Lua syntax verified; {len(command)} characters.')

if __name__ == '__main__':
    main()
