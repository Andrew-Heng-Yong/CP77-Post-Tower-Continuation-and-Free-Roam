"""Stage the pinned official RHT ZIP; never write the game or saves."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import stat
import struct
import zipfile

TASK = Path(__file__).resolve().parent
WORK = TASK / 'work'
ROOT = TASK.parent.parent
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
SAVES = Path('C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077')
TOOL_ROOTS = ['bin/x64/plugins/cyber_engine_tweaks/mods/RedHotTools', 'red4ext/plugins/RedHotTools']
ZIP_SHA = 'EE58F5BB33BF9B650A8D49670CF3BA279D6F8559C0BC3DB85417AF84CD4B7BB2'
BASE = ROOT / 'prealpha/kold_mirage_gate_20261116_01/work'
BASE_SHA = 'D7D6EDC420052701621F9EE409075302E6AF5B1B931EABA5EF9A911526F2C7FF'
TEMPLATE_SHA = 'E04403763302BAC9B39721435359F099C1C8FB96B60C2F5C02751A0524695EB1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()


def no_links(path):
    for parent in [Path(path), *Path(path).parents]:
        if parent.exists() and parent.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise RuntimeError(f'Reparse path refused: {parent}')


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def main():
    for path in [TASK, GAME, SAVES]:
        no_links(path)
    for relative in TOOL_ROOTS:
        target = GAME / relative
        no_links(target)
        assert not target.exists(), f'Existing tool root needs review: {target}'
    baseline_path = BASE / 'deployment_01/installed_manifest_01.json'
    assert sha(baseline_path) == BASE_SHA
    baseline = json.loads(baseline_path.read_text(encoding='utf-8-sig'))
    assert baseline['core_epoch'] == 'KM3_KOLD_PREPARED_ENTRY'
    required = [dict(row, active_only=False) for row in baseline['core_files'] + baseline['required_files']]
    assert len(required) == 77 and len({r['path'].lower() for r in required}) == 77
    for row in required:
        target = GAME / row['path']
        no_links(target)
        assert sha(target) == row['sha256'] and target.stat().st_size == row['bytes'], f'Baseline drift: {target}'
    # Also protect the loader and existing user bindings; neither is an install target.
    for relative in ['red4ext/RED4ext.dll', 'bin/x64/plugins/cyber_engine_tweaks/bindings.json']:
        target = GAME / relative
        no_links(target)
        required.append(dict(path=relative, sha256=sha(target), bytes=target.stat().st_size, active_only=False))
    previous = json.loads((BASE / 'core_manifest_01.json').read_text(encoding='utf-8-sig'))
    compile_inputs = dict(previous['compile_inputs'])
    for path, expected in compile_inputs.items():
        no_links(path)
        if path.endswith('final.redscripts.ts'):
            compile_inputs[path] = sha(path)  # Current sidecar is protected, not reused as compile evidence.
        else:
            assert sha(path) == expected, f'Existing source/compiler/base cache drift: {path}'
    package = WORK / 'package_01'
    assert not package.exists(), 'Fresh stage required'
    archive = WORK / 'download/RedHotTools-1.3.0.zip'
    assert sha(archive) == ZIP_SHA and archive.stat().st_size == 2423642
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members = [i for i in z.infolist() if not i.is_dir()]
        assert len(members) == 18 and len({i.filename.lower() for i in members}) == 18
        for entry in z.infolist():
            p = PurePosixPath(entry.filename)
            assert not p.is_absolute() and not any(s in ('', '.', '..') for s in p.parts)
            assert '\\' not in entry.filename and ':' not in entry.filename
            assert not stat.S_ISLNK(entry.external_attr >> 16)
        rows = []
        for entry in sorted(members, key=lambda i: i.filename):
            assert any(entry.filename.startswith(r + '/') for r in TOOL_ROOTS)
            assert PurePosixPath(entry.filename).suffix in ('.lua', '.dll', '.txt')
            target = package / entry.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(entry)
            with target.open('xb') as stream:
                stream.write(data)
            assert target.read_bytes() == data
            rows.append(dict(path=entry.filename, before=None, before_bytes=None, after=sha(target), after_bytes=len(data)))
    dll = (package / 'red4ext/plugins/RedHotTools/RedHotTools.dll').read_bytes()
    pe = struct.unpack_from('<I', dll, 0x3C)[0]
    assert dll[:2] == b'MZ' and dll[pe:pe+4] == b'PE\0\0'
    assert struct.unpack_from('<H', dll, pe+4)[0] == 0x8664, 'x64 DLL required'
    assert (package / 'bin/x64/plugins/cyber_engine_tweaks/mods/RedHotTools/version.lua').read_text().strip() == "return '1.3.0'"
    inventory_path = WORK / 'package_inventory.json'
    write_json(inventory_path, dict(status='PASS', tag='v1.3.0-rc.7', zip_sha256=ZIP_SHA,
        files=rows, directories=6, x64_pe=True, staged_readback=True, redscript_files=0,
        preserved_core_paths=51, preserved_existing_dependencies=26,
        current_source_files=sum(p.lower().endswith('.reds') for p in compile_inputs), game_writes=0))
    proof_paths = [baseline_path, WORK/'release_api.json', WORK/'download/receipt.json', inventory_path]
    manifest = dict(schema='PTFR_RHT_RC7_INSTALL_V1', component='RHT', source_epoch='RHT_1_3_0_RC7',
        predecessor_epoch='RHT_ABSENT', scope='Official RC7: 18 new files in two absent RedHotTools folders',
        game_root=str(GAME), save_root=str(SAVES), package_root=str(package),
        process_names=previous['process_names'], files=rows, changing_paths=[r['path'] for r in rows],
        required_files=required, protected_saves=[], working_save_files=[],
        zip=str(archive), zip_sha256=ZIP_SHA,
        proofs=[dict(path=str(p), sha256=sha(p)) for p in proof_paths], compile_inputs=compile_inputs)
    manifest_path = WORK / 'tool_manifest_01.json'
    write_json(manifest_path, manifest)
    template = BASE / 'deploy_core.ps1'
    assert sha(template) == TEMPLATE_SHA
    code = template.read_text(encoding='utf-8-sig')
    replacements = {
        "[ValidateSet('Core')][string]$Component='Core'": "[ValidateSet('RHT')][string]$Component='RHT'",
        '# Replace the qualified KOLD entry archive after installation authorization.': '# Install the authorized official RHT RC7 package into two absent tool folders.',
        "$PinnedCoreManifestSHA='07327F59484012AC446196A64CAC44BB5652262010C9F54CE109856041B6009C'": f"$PinnedCoreManifestSHA='{sha(manifest_path)}'",
        "'core_manifest_01.json'": "'tool_manifest_01.json'",
        "'PTFR_KM3_KOLD_PREPARED_ENTRY_CORE_V1'": "'PTFR_RHT_RC7_INSTALL_V1'",
        "'KM3_KOLD_PREPARED_ENTRY'": "'RHT_1_3_0_RC7'",
        "'RD10_MID_QUEST_RESUME_RETIRED'": "'RHT_ABSENT'",
        "'recovery/kold_gate_01'": "'recovery/redhottools_01'",
        "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')": "$wanted=@(" + ','.join("'" + r['path'] + "'" for r in rows) + ')',
        "if($manifest.files.Count -ne 51 -or $changes.Count -ne 1 -or @($manifest.files|Where-Object {$null -eq $_.before}).Count -or (@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'KOLD archive-only scope drift'}":
            "if($manifest.files.Count -ne 18 -or $changes.Count -ne 18 -or @($manifest.files|Where-Object {$null -ne $_.before}).Count -or (@($changes.path|Sort-Object)-join ',') -cne (@($wanted|Sort-Object)-join ',')){throw 'Official RHT new-file scope drift'}",
        " CheckPackage;CheckDependencies 'After';CheckManaged 'Before';CheckWorkingSave":
            " foreach($relative in @('bin/x64/plugins/cyber_engine_tweaks/mods/RedHotTools','red4ext/plugins/RedHotTools')){if(Test-Path -LiteralPath (Safe $game $relative)){throw ('Existing RedHotTools root refused: '+$relative)}}\n CheckPackage;CheckDependencies 'After';CheckManaged 'Before';CheckWorkingSave",
    }
    for old, new in replacements.items():
        assert code.count(old) == 1, f'Template adaptation ambiguity: {old}'
        code = code.replace(old, new, 1)
    installer = WORK / 'install.ps1'
    with installer.open('x', encoding='utf-8', newline='\r\n') as stream:
        stream.write(code)
    write_json(WORK/'scope_review.json', dict(status='PASS', predecessor_installer=str(template),
        predecessor_installer_sha256=TEMPLATE_SHA, installer_sha256=sha(installer),
        manifest_sha256=sha(manifest_path), exact_adaptations=list(replacements),
        writable_game_files=[r['path'] for r in rows], all_targets_previously_absent=True,
        package_source='Official psiberx RC7 release, checksum verified',
        protected_paths=len(required), core_epoch_unchanged='KM3_KOLD_PREPARED_ENTRY',
        no_redscript_changes=True, no_game_launch=True, user_request='if yes, install it pls',
        limits=['Native DLL startup and in-game World Inspector remain untested.']))
    print(json.dumps(dict(status='STAGED_NOT_INSTALLED', files=len(rows), protected_paths=len(required),
        manifest_sha256=sha(manifest_path), installer_sha256=sha(installer))))


if __name__ == '__main__':
    main()
