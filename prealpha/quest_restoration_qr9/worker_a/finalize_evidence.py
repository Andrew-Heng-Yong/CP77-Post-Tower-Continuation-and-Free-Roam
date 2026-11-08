"""Freeze A's evidence index only; no installer/game/save invocation."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text())
expected={'core_manifest_02.json':'06CD479C47E32403371E360092648431EAE1BC93DEE3E61BD6822560133CBCF1','diagnostics_manifest_01.json':'C41A1547DB7B33F0F97B68ADC7509E937A6487B85D95E34F7AAFBF83991C38E1','deploy_qr9_guarded_final.ps1':'CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E'}
for name,digest in expected.items():assert sha(H/name)==digest,name
result_specs=[('fixture_result_02.json','PASS_WORKSPACE_ONLY_TRANSACTION_FIXTURES',29),('final_fixture_result_01.json','PASS_FINAL_AFFECTED_PATHS_AND_LOCK_FIXTURES',7),('exact_payload_result_01.json','PASS_ACTUAL_CORE51_AND_ADDON2_WORKSPACE_TRANSACTIONS',2),('receipt_guards_result_01.json','PASS_RECEIPT_BOUNDARIES_AND_EXPLICIT_LOCK_DISPOSAL',4)]
tests=[]
for name,status,count in result_specs:
    p=H/name;r=read(p);assert r['status']==status,name
    if 'planned'in r:assert r['cases']==r['planned']==count
    elif name.startswith('exact_'):assert len(r['results'])==count
    else:assert len(r['cases'])==count
    tests.append(dict(path=str(p),sha256=sha(p),status=status,scenarios=count,script_sha256=r['script_sha256']))
app=H/'evidence/source_applicability.json';assert read(app)['status']=='PASS_EXACT_SOURCE_DELTA_APPLICABILITY'
diag=H/'reviews/diagnostics_01/result.json';assert read(diag)['assertions']==16
core=read(H/'core_manifest_02.json');addon=read(H/'diagnostics_manifest_01.json')
assert len(core['files'])==51 and len(core['changing_paths'])==2 and len(addon['files'])==2
result=dict(schema=1,status='PREPARED_FIXTURE_VERIFIED_NOT_DEPLOYED',source_epoch='QR8:02',
    intended_canonical_script=str(H/'deploy_qr9_guarded.ps1'),final_source=dict(path=str(H/'deploy_qr9_guarded_final.ps1'),sha256=expected['deploy_qr9_guarded_final.ps1']),
    canonical_promotion='Copy exact final bytes only after coordinator/peer confirms all historical C8EE readers have finished. Verify canonical SHA before using future commands.',
    manifests=[dict(path=str(H/n),sha256=expected[n])for n in ['core_manifest_02.json','diagnostics_manifest_01.json']],
    core_managed_paths=51,core_replaced_existing_paths=core['changing_paths'],optional_addon_managed_paths=2,
    diagnostic_preflight='Pins existing CET only; may pass on PH3. Does not observe installed QR8. Separate Core Verify receipt required before gameplay.',
    tests=tests,source_applicability=dict(path=str(app),sha256=sha(app)),independent_diagnostic_review=dict(path=str(diag),sha256=sha(diag),assertions=16),
    independent_installer_review='Coordinator gate: Worker C reviews final CE020 source plus applicable historical controls separately.',
    commands=str(H/'DEPLOYMENT.md'),
    real_installer_actions={k:'NOT_RUN'for k in ['Preflight','Install','Verify','ValidateRollback','Rollback','Recover']},
    real_save_source_copies=0,real_save_writes=0,game_launches=0,GUI_or_simulated_input=0,core_runtime_rebuilds=0,release_modifications=0,
    limits=['Fixtures use private game roots and synthetic saves; actual package bytes are copied only from existing pinned workspace packages.','No real write permissions, runtime API delivery, gameplay result or save compatibility transition is certified.','Each current write transaction exact-hashes saves and critical external dependencies; other unmanaged game files use metadata and bounded write-set checks.','Recovery is journaled per-file atomic replacement, not a globally atomic two-file or power-loss transaction.','A rollback changes files only, never rewinds a save or human working-slot progress.'])
out=H/'prepared_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(out),sha256=sha(out),status=result['status'])))
