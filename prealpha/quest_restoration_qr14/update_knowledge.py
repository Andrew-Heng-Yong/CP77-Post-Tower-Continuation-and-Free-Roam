"""Bounded current-state/toolchain correction; keep exact prior document bytes."""
from prepare import H, W

def main():
    state = W / 'docs/knowledge/current-state.md'
    guide = W / 'docs/knowledge/redscript-toolchain.md'
    for p, name in [(state, 'current-state.before.md'), (guide, 'redscript-toolchain.before.md')]:
        dest = H / name; assert not dest.exists(); dest.write_bytes(p.read_bytes())
    s = state.read_text(encoding='utf-8-sig')
    old = 'the 51-path package passed fresh full-input compilation and independent complete archive/ZIP verification.'
    assert old in s
    s = s.replace(old, 'the 51-path package passed its131-source offline compile and independent complete archive/ZIP verification. QR14 later found17 registered LBD sources omitted from that compile; the unchanged candidate passed a fresh148-source integration compile, as recorded below.')
    anchor = '\n## '
    qr13 = s.index('**QR13 staged successor')
    end = s.find(anchor, qr13)
    assert end > qr13
    paragraph = '\n**QR14 deployment preparation — 3 November:** [preparation report](../../prealpha/quest_restoration_qr14/REPORT.md), [guarded deployment procedure](../../prealpha/quest_restoration_qr14/DEPLOYMENT.md), and [readiness](../../prealpha/quest_restoration_qr14/readiness.json) describe the exact three-file QR8:02→QR13:02 transaction. Current runtime compiler logs identify148 registered sources; all148, including17 LBD sources, passed a fresh offline integration compile with the unchanged candidate overlay. The installer pins151 compiler inputs and rejects added/deleted/linked source inventories. This corrects the earlier131-source coverage claim without rewriting QR13 evidence. Preparation does not authorize installation. Installed Core/diagnostics/saves remain unchanged; no immediate new-behavior fixture qualifies. See the [manual plan](../../prealpha/quest_restoration_qr14/MANUAL_TEST_PLAN.md).\n'
    s = s[:end] + paragraph + s[end:]
    state.write_text(s, encoding='utf-8')
    s = guide.read_text(encoding='utf-8-sig')
    old = 'The inspected script stages every `.reds` from:'
    assert old in s
    s = s.replace(old, 'The historical WA3 script stages `.reds` from these five roots. **This list is incomplete for the3November installed runtime:** LizziesBDs adds17 sources. A fresh dependency census is mandatory; see R4. Historical roots:')
    s += '''

## R4 — Current registered-source closure (QR14,3November)

**Status:** verified offline integration PASS for the exact unchanged QR13:02 candidate and current installed dependencies; no installation or gameplay certification.

Independent QR14 review found that `r6/logs/redscript_rCURRENT.log` listed17 `red4ext/plugins/LizziesBDs/Scripts/*.reds` inputs omitted by the earlier five-root offline compile. The logged runtime set is119 ordinary +29 plugin sources =148. QR13's immutable131-source result remains valid only for its narrower input set; its former complete-input wording is superseded.

**Prerequisites:** authorized offline verification, current game compiler/cache and actual registered source evidence, pinned candidate overlay, no source/reparse drift, and a fresh workspace output. Inspect `prealpha/quest_restoration_qr14/compile_integration.py` before adaptation. It verifies the current log set equals both the six staged roots and all `.reds` across enclosing `r6/scripts`/`red4ext/plugins`, copies sources/cache, overlays46candidate scripts and writes only workspace files.

The exact executed command was:

```powershell
& 'C:\\Users\\Ayong\\.local\\bin\\python3.14.exe' -X utf8 -B prealpha/quest_restoration_qr14/compile_integration.py
```

Its occupied `verification/compile_01` refuses rerun. For a later candidate, adapt an inspected copy into a fresh task and reconcile the **current** registered source set; do not hardcode148 or assume the same frameworks remain installed.

**Expected outputs:** `verification/compile_01/{result.json,scc.log,runtime_redscript.log,compile_paths.txt,scripts/,cache/compiled.redscripts}`. The result records151 installed input pins (148sources +SCC +two cache inputs),148staged source hashes, original-to-staged linkage,17added sources, exact runtime-log bytes and installed-input preservation. Current compiled SHA256 is `6185E254BDB1F98A4371A0DEDB76E09D2958EF6006ECA5D5E8C8EABDE83E6F0F`.

**Verify:** exit0, `Compilation complete`, exact candidate46 overlay, all148 registry/inventory/staging identities and151 current input hashes, output hash, and unchanged game/cache/save files. `prealpha/quest_restoration_qr14/verification/compile_01/result.json` is the current proof, with independent review linked from QR14 readiness. Installer manifest02 additionally refuses added/deleted/linked `.reds`, including a new plugin source root. Missing compiler closure must remain a deployment blocker until resolved; a prior successful compile does not cover an omitted source or a changed dependency.
'''
    guide.write_text(s, encoding='utf-8')
    print({'updated': [str(state), str(guide)], 'historical_proofs_changed': False})

if __name__ == '__main__':
    main()
