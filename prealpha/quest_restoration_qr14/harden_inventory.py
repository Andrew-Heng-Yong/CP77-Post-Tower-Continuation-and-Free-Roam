"""Preserve tested engine01; bind full148 integration proof and reject extra sources."""
from pathlib import Path
import shutil
from prepare import H, read, sha, write

def main():
    old = H / 'engine_01'; assert not old.exists(); old.mkdir()
    for name in ['deploy_core.ps1', 'test_deployment.py', 'adapt_transaction.py']:
        shutil.copyfile(H / name, old / name)
    first = read(H / 'run_01_results.json')
    assert first['status'] == 'PASS_DEPLOYMENT_FIXTURES' and sha(old / 'deploy_core.ps1') == first['installer_sha256']
    m = read(H / 'core_manifest_01.json')
    cp = H / 'verification/compile_01/result.json'; compile_result = read(cp)
    assert compile_result['status'] == 'PASS_RUNTIME_REGISTERED148_INTEGRATION_COMPILE'
    assert compile_result['source_count'] == len(compile_result['runtime_registered_sources'])
    for p, s in compile_result['input_pins'].items(): assert sha(p) == s, p
    game = Path(m['game_root'])
    for p in compile_result['additional_sources_vs_QR13']:
        m['required_files'].append({'path': Path(p).relative_to(game).as_posix(), 'sha256': sha(p), 'bytes': Path(p).stat().st_size, 'active_only': False})
    m['compile_inputs'] = compile_result['input_pins']
    m['proofs'] += [{'path': str(p), 'sha256': sha(p)} for p in [cp, H / 'verification/compile_01/runtime_redscript.log', H / 'review_01/compile_boundary_01.json']]
    m['compile_coverage'] = {'sources': compile_result['source_count'], 'registered_source_count': len(compile_result['runtime_registered_sources']),
        'compiled_sha256': compile_result['compiled_sha256'], 'replaces_coverage_claim_only': 'QR13 compile131 omitted17 runtime-registered LBD sources. Historical result unchanged; fresh QR14 integration148 passes. Core package bytes unchanged.'}
    write(H / 'core_manifest_02.json', m)
    s = (H / 'deploy_core.ps1').read_text(encoding='utf-8')
    s = s.replace(sha(H / 'core_manifest_01.json'), sha(H / 'core_manifest_02.json')).replace("'core_manifest_01.json'", "'core_manifest_02.json'")
    anchor = 'function CheckPackage {\n'
    assert anchor in s
    guard = """function CheckCompileInventory {
 # Synthetic state-machine fixtures may omit compiler inputs. Real inputs are
 # fixed by the pinned manifest; enumerate both enclosing trees to catch new
 # plugin source roots as well as added/deleted known-root files.
 if($manifest.compile_inputs.Count -eq 0){if(-not $fixture){throw 'Real compiler inventory cannot be empty'};return}
 $expected=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($p in $manifest.compile_inputs.Keys){if([IO.Path]::GetExtension($p) -ieq '.reds'){[void]$expected.Add((Full $p))}}
 $actual=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
 foreach($relative in @('r6/scripts','red4ext/plugins')){
  $root=Safe $game $relative;$tree=TreeSnapshot $root
  foreach($entry in $tree.files){
   if($entry.kind -eq 'REPARSE_NOT_FOLLOWED'){throw ('Linked compiler inventory entry refused: '+$entry.path)}
   if($entry.kind -eq 'file' -and [IO.Path]::GetExtension($entry.path) -ieq '.reds'){[void]$actual.Add((Safe $root $entry.path))}
  }
 }
 if(-not $actual.SetEquals($expected)){throw 'Exact REDscript source inventory drift; compile proof cannot be reused'}
}

"""
    s = s.replace(anchor, guard + anchor + ' CheckCompileInventory\n')
    (H / 'deploy_core.ps1').write_text(s, encoding='utf-8')
    t = (H / 'test_deployment.py').read_text(encoding='utf-8')
    t = t.replace("'core_manifest_01.json'", "'core_manifest_02.json'")
    (H / 'test_deployment.py').write_text(t, encoding='utf-8')
    write(H / 'engine_01_to_02.json', {'source_engine_01': {'path': str(old / 'deploy_core.ps1'), 'sha256': sha(old / 'deploy_core.ps1')},
        'source_engine_02': {'path': str(H / 'deploy_core.ps1'), 'sha256': sha(H / 'deploy_core.ps1')},
        'manifest_01_sha256': sha(H / 'core_manifest_01.json'), 'manifest_02_sha256': sha(H / 'core_manifest_02.json'),
        'original_fixture_result': {'path': str(H / 'run_01_results.json'), 'sha256': sha(H / 'run_01_results.json')},
        'changes': ['Fresh complete runtime-registered148-source integration proof/pins; extra17 LBD dependencies protected.',
            'Before Preflight/Install enumerate all REDscript sources in both enclosing installed trees, reject links and additions/removals.',
            'No transaction state machine changes, no Core/package changes. Final run02 re-executes all fixtures.']})
    print({'status': 'HARDENED_NOT_INSTALLED', 'manifest': sha(H / 'core_manifest_02.json'),
        'installer': sha(H / 'deploy_core.ps1'), 'required': len(m['required_files']), 'compile_inputs': len(m['compile_inputs'])})

if __name__ == '__main__':
    main()
