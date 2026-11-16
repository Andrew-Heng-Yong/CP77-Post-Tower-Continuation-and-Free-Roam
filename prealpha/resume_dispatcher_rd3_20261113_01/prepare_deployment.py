"""Package and bind the qualified candidate without writing to the game."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from capture import HERE, ROOT, BASELINE, BASELINE_SHA, baseline, plain, read, sha, write
from prepare import ARCHIVE, HS1, S22, once

BASE = ROOT / 'prealpha/resume_dispatcher_rd2_20261112_01'
EPOCH = 'RD3_EPISTROPHY_NORTHSIDE_RESUME'
BEFORE = 'RD2_THE_GIG_REWARD_RESUME'
SCHEMA = 'PTFR_RD3_EPISTROPHY_NORTHSIDE_RESUME_CORE_V1'
CHANGES = {ARCHIVE, HS1, S22}
PACKAGE = HERE / 'candidate_01/package'
MANIFEST = HERE / 'core_manifest_01.json'
INSTALLER = HERE / 'deploy_core.ps1'
DEPLOYMENT = HERE / 'deployment_01'
PS = Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

def exclusive(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)

def main():
    assert all(not p.exists() for p in (MANIFEST, INSTALLER, DEPLOYMENT, HERE/'fixtures', HERE/'recovery', HERE/'deploy.py'))
    previous, game = baseline()
    manifest_path = PACKAGE.parent / 'manifest.json'
    assessment_path = HERE / 'assessment.json'
    compiler_path = HERE / 'compile_01/result.json'
    assessment = read(assessment_path)
    candidate = read(manifest_path)
    compiled = read(compiler_path)
    assert candidate['baseline_manifest_sha256'] == BASELINE_SHA
    assert candidate['qualification'] == assessment['status'] == 'PASS_BOUNDED_OFFLINE'
    assert assessment['contract_sha256'] == sha(HERE / 'contract.json')
    assert compiled['status'] == 'PASS' and compiled['source_count'] == 148
    for p, h in compiled['input_pins'].items():
        assert sha(game / p) == h
    for p, h in compiled['staged_hashes'].items():
        assert sha(PACKAGE / p if (PACKAGE / p).is_file() else game / p) == h
    after = {r['path']:r['sha256'] for r in candidate['files']}
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()} == set(after)
    files = []
    for r in previous['core_files']:
        p = PACKAGE / r['path']
        plain(p)
        assert sha(p) == after[r['path']]
        files.append({'path':r['path'], 'before':r['sha256'], 'before_bytes':r['bytes'],
                      'after':after[r['path']], 'after_bytes':p.stat().st_size})
    assert len(files) == 51 and {r['path'] for r in files if r['before'] != r['after']} == CHANGES
    for folder in (DEPLOYMENT, HERE/'fixtures', HERE/'recovery'):
        folder.mkdir()
    zipfile = DEPLOYMENT / 'RD3_candidate_01.zip'
    with ZipFile(zipfile, 'x', ZIP_DEFLATED, compresslevel=6) as z:
        for r in files:
            z.write(PACKAGE / r['path'], r['path'])
    with ZipFile(zipfile) as z:
        assert len(z.namelist()) == 51 and set(z.namelist()) == set(after) and z.testzip() is None
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest().upper() == r['after'] for r in files)
    zip_proof = DEPLOYMENT / 'zip_readback.json'
    write(zip_proof, {'status':'PASS','files':51,'sha256':sha(zipfile)})
    proofs = [BASELINE, manifest_path, assessment_path, compiler_path, zip_proof, HERE/'contract.json', HERE/'archive_01/readback.json']
    write(MANIFEST, {
        'schema':SCHEMA, 'component':'Core', 'source_epoch':EPOCH, 'predecessor_epoch':BEFORE,
        'scope':'Three-file candidate for Epistrophy at the earned Northside find-the-cab objective.',
        'game_root':str(game), 'save_root':previous['save_root'], 'package_root':str(PACKAGE),
        'process_names':read(BASE/'core_manifest_01.json')['process_names'],
        'files':files, 'changing_paths':sorted(CHANGES), 'required_files':previous['required_files'],
        'protected_saves':[], 'working_save_files':[], 'zip':str(zipfile), 'zip_sha256':sha(zipfile),
        'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],
        'compile_inputs':{str(game/p):h for p,h in compiled['input_pins'].items()}
    })
    template = BASE / 'deploy_core.ps1'
    assert sha(template) == '962EFF2A59193B38C82BD08347568C82398C5405A7718E88621912EE03F5AA71'
    source = template.read_text(encoding='utf-8-sig')
    for old, new in (
        ('# Replace the three qualified RD2 files after installation authorization.',
         '# Replace the three qualified RD3 files after installation authorization.'),
        (sha(BASE/'core_manifest_01.json'), sha(MANIFEST)),
        ('PTFR_RD2_THE_GIG_REWARD_RESUME_CORE_V1', SCHEMA),
        ("$manifest.source_epoch -cne 'RD2_THE_GIG_REWARD_RESUME'",f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'TP3_BOUNDED_PRESENTATION_HANDOFF'",f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_resume_rd2_01','recovery/core_resume_rd3_01'),
        ('Core51/three-file RD2 scope drift','Core51/three-file RD3 scope drift'),
    ):
        source = once(source, old, new)
    exclusive(INSTALLER, source)
    source = (BASE / 'deploy.py').read_text(encoding='utf-8')
    for old, new in (
        ('RD2 fixture runner','RD3 fixture runner'),
        ('recovery/core_resume_rd2_01','recovery/core_resume_rd3_01'),
        ('PENDING_THE_GIG_EARNED_REWARD_PLAYTEST','PENDING_EPISTROPHY_NORTHSIDE_RESUME_PLAYTEST'),
    ):
        source = once(source, old, new)
    exclusive(HERE/'deploy.py', source)
    print('Prepared the 51-path local package and three-file transaction.')

if __name__ == '__main__':
    main()
