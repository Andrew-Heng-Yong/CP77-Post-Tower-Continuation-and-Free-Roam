"""Bind the staged Rite candidate to a fresh guarded two-file transaction."""
import hashlib
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'resume_dispatcher_rd5_gigs_20261113_01'))
from capture import BASELINE, BASELINE_SHA, baseline, plain, read, sha, write
from finish_candidate import ACTIVITY, ARCHIVE

RD4 = BASELINE.parents[1]
EPOCH = 'RD5_RITE_OF_PASSAGE_RESUME'
BEFORE = 'RD4_BEAT_ON_THE_BRAT_RESUME'
SCHEMA = 'PTFR_RD5_RITE_OF_PASSAGE_RESUME_CORE_V1'
CHANGES = {ARCHIVE, ACTIVITY}
PACKAGE = HERE / 'candidate_01/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')


def adapt(template, output, digest, replacements):
    assert sha(template) == digest, template
    source = template.read_text(encoding='utf-8-sig')
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new, 1)
    with output.open('x', encoding='utf-8', newline='\n') as file:
        file.write(source)


def main():
    assert all(not p.exists() for p in (MANIFEST, INSTALLER, DEPLOYMENT, HERE/'fixtures', HERE/'recovery', HERE/'deploy.py'))
    previous, game = baseline()
    candidate_path = PACKAGE.parent / 'manifest.json'
    compiled_path = HERE / 'compile_01/result.json'
    archive_path = HERE / 'archive_01/readback.json'
    wrapper_path = HERE / 'evidence_01/wrapper_assessment.json'
    entrance_path = HERE / 'evidence_01/entrance_assessment.json'
    candidate, compiled, packed = (read(p) for p in (candidate_path, compiled_path, archive_path))
    assert candidate['status'] == 'STAGED_OFFLINE' and candidate['baseline_manifest_sha256'] == BASELINE_SHA
    assert candidate['compile_sha256'] == sha(compiled_path) and candidate['archive_readback_sha256'] == sha(archive_path)
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    assert packed['status'] == 'MEMBERS_VERIFIED' and len(packed['members']) == candidate['archive_payloads'] == 1745
    assert sha(PACKAGE/ARCHIVE) == packed['archive_sha256'] == candidate['archive_sha256']
    assert read(wrapper_path)['status'] == 'PASS_UNPACKED_NATIVE_WRAPPER'
    assert read(entrance_path)['status'] == 'PASS_PRIVATE_PHASE_READBACK'
    assert all(sha(game / p) == h for p, h in compiled['input_pins'].items())
    assert all(sha(PACKAGE / p if (PACKAGE / p).is_file() else game / p) == h for p, h in compiled['staged_hashes'].items())
    staged = {r['path']: r for r in candidate['core_files']}
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()} == set(staged)
    files = []
    for row in previous['core_files']:
        path = row['path']
        item = PACKAGE / path
        plain(item)
        assert sha(item) == staged[path]['sha256'] and item.stat().st_size == staged[path]['bytes']
        files.append({'path': path, 'before': row['sha256'], 'before_bytes': row['bytes'],
                      'after': staged[path]['sha256'], 'after_bytes': staged[path]['bytes']})
    assert len(files) == 51 and {r['path'] for r in files if r['before'] != r['after']} == CHANGES

    for directory in (DEPLOYMENT, HERE/'fixtures', HERE/'recovery'):
        directory.mkdir()
    zipfile = DEPLOYMENT / 'RD5_Rite_candidate_01.zip'
    with ZipFile(zipfile, 'x', ZIP_DEFLATED, compresslevel=6) as archive:
        for row in files:
            archive.write(PACKAGE / row['path'], row['path'])
    with ZipFile(zipfile) as archive:
        assert len(archive.namelist()) == 51 and set(archive.namelist()) == set(staged) and archive.testzip() is None
        assert all(hashlib.sha256(archive.read(r['path'])).hexdigest().upper() == r['after'] for r in files)
    zip_proof = DEPLOYMENT / 'zip_readback.json'
    write(zip_proof, {'status': 'PASS', 'files': 51, 'sha256': sha(zipfile)})
    proofs = [BASELINE, candidate_path, compiled_path, archive_path, wrapper_path, entrance_path, zip_proof,
              HERE/'entrance.json', HERE/'evidence_01/admission.json']
    write(MANIFEST, {'schema': SCHEMA, 'component': 'Core', 'source_epoch': EPOCH, 'predecessor_epoch': BEFORE,
          'scope': 'Install the two-file Rite of Passage candidate for the earned Get to the clinic stage.',
          'game_root': str(game), 'save_root': previous['save_root'], 'package_root': str(PACKAGE),
          'process_names': read(RD4/'core_manifest_01.json')['process_names'],
          'files': files, 'changing_paths': sorted(CHANGES), 'required_files': previous['required_files'],
          'protected_saves': [], 'working_save_files': [], 'zip': str(zipfile), 'zip_sha256': sha(zipfile),
          'proofs': [{'path': str(p), 'sha256': sha(p)} for p in proofs],
          'compile_inputs': {str(game/p): h for p, h in compiled['input_pins'].items()}})
    adapt(RD4/'deploy_core.ps1', INSTALLER, 'F0A63B876779E1545F64EF3D7121DC49237F6361D1666696499E4CB29AE991C7', (
        ('# Replace the three qualified RD4 files after installation authorization.',
         '# Replace the two qualified Rite of Passage files after installation authorization.'),
        (sha(RD4/'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_RD4_BEAT_ON_THE_BRAT_RESUME_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'RD4_BEAT_ON_THE_BRAT_RESUME'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD3_EPISTROPHY_NORTHSIDE_RESUME'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_resume_rd4_01', 'recovery/core_resume_rd5_rite_01'),
        ("'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS22.reds'", f"'{ACTIVITY}'"),
        ('$changes.Count -ne 3', '$changes.Count -ne 2'),
        ('Core51/three-file RD4 scope drift', 'Core51/two-file Rite scope drift'),
    ))
    adapt(RD4/'deploy.py', HERE/'deploy.py', '26779A3B99B3DC99BB8898CB289515CD8DF6C50A83824998C1776F93E2AC6736', (
        ('RD4 fixture runner', 'Rite deployment fixture runner'),
        ('from capture import HERE, BASELINE, plain, read, sha, write', 'from prepare_deployment import HERE, BASELINE, plain, read, sha, write'),
        ('recovery/core_resume_rd4_01', 'recovery/core_resume_rd5_rite_01'),
        ('archive_01/archive_source', 'archive_01/source'),
        ("'archive_payloads': 1742", "'archive_payloads': 1745"),
        ("'unchanged_core_paths': 48", "'unchanged_core_paths': 49"),
        ('PENDING_BEAT_ON_THE_BRAT_RESUME_PLAYTEST', 'PENDING_RITE_OF_PASSAGE_RESUME_PLAYTEST'),
    ))
    print('Verified the 51-path ZIP and prepared the two-file transaction.')


if __name__ == '__main__':
    main()
