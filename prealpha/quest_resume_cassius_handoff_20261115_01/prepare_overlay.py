from pathlib import Path
import hashlib,json
base=Path(__file__).resolve().parent
p=base.parent/'quest_resume_cassius_shared_20261115_01/staged_01/deployment_01/installed_manifest_01.json'
m=json.loads(p.read_bytes())
sha=lambda f: hashlib.sha256(f.read_bytes()).hexdigest().upper()
assert sha(p)=='41672F9EF2EE9C23B9BEEFE445F8D066A36DE098FC2736FF94C7D7BD1BA02DA0'
rows={r['path']:r['sha256'] for r in m['core_files']}
game=Path(m['game_root'])
target=base/'overlay'
target.mkdir(exist_ok=True)

def prepare_exact(path, content):
    if path.exists():
        assert path.read_bytes()==content, f'Prepared source differs: {path}'
    else:
        with path.open('xb') as file:
            file.write(content)
pins=[]
for name in ('PTFR_HistorySnapshotHS1','PTFR_SideJobsS22','PTFR_SideJobsS24'):
    rel=f'r6/scripts/PTFR_Consolidated/{name}.reds'
    installed=game/rel
    assert sha(installed)==rows[rel]
    raw=installed.read_bytes()
    nl='\r\n' if b'\r\n' in raw else '\n'
    text=raw.decode('utf-8').replace('\r\n','\n')
    def change(a,b):
        global text
        assert text.count(a)==1,(name,a,text.count(a))
        text=text.replace(a,b,1)
    if name=='PTFR_HistorySnapshotHS1':
        a='      this.ResetCapture();this.PrepareJSON();return;'
        change(a, '      SharedCassiusResume.Poll(this.GetGameInstance(), player, jm);\n'+a)
        a='      execution = this.ReadExecution(reader, ticket, route, this.revision + 1, this.ReadExecutionPresentation(player));'
        change(a,'''      let presentation = this.ReadExecutionPresentation(player);
      let cassius: array<Uint64>;
      if route == 1 && SharedCassiusResume.Sample(this.GetGameInstance(), player, jm, cassius) {
        let keys = SharedCassiusResume.Keys();
        let i = 0;
        let agrees = true;
        while i < ArraySize(keys) {
          let row = this.journalSample[keys[i]];
          if !row.stable || Cast<Uint64>(row.state) != cassius[i] { agrees = false; }
          i += 1;
        }
        if agrees {
          i = 0;
          while i < ArraySize(cassius) {
            ArrayPush(presentation, cassius[i]);
            i += 1;
          }
        }
      }
      execution = this.ReadExecution(reader, ticket, route, this.revision + 1, presentation);''')
        text+=(base/'CassiusScript.reds.inc').read_text(encoding='utf-8')
    else:
        index=3 if name.endswith('22') else 6
        a='    let value = allowed && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) ? 1 : 0;'
        change(a,f'''    let nativeOwnsCassius = i == {index} && allowed && SharedCassiusResume.AdapterBlocked(this.GetGameInstance());
    let value = allowed && !nativeOwnsCassius && StartupCoverLC1.GameplayReleased(this.GetGameInstance()) ? 1 : 0;''')
    dst=target/rel
    dst.parent.mkdir(parents=True,exist_ok=True)
    prepare_exact(dst, text.replace('\n',nl).encode('utf-8'))
    pins.append((rel,sha(dst)))
h=base/'source_01/CassiusScriptPins.hpp'
prepare_exact(h, ('#pragma once\n\n#include <array>\n#include <string_view>\n\n'
             'inline constexpr std::array<std::pair<std::string_view, std::string_view>, 3> CassiusScriptPins{{\n'
             + ''.join(f'    {{"{path}", "{hash_}"}},\n' for path,hash_ in pins)
             + '}};\n').replace('\n','\r\n').encode('utf-8'))
for row in pins: print(*row)
