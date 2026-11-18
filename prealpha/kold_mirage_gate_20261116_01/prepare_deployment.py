"""Package the one-resource successor and bind the reviewed transaction."""
from pathlib import Path
from hashlib import sha256
import shutil
from zipfile import ZipFile,ZIP_DEFLATED
from prepare import HERE as TASK,WS,BASELINE,COMPILE,ARCHIVE,DEPOT,baseline,plain,read,sha,write

HERE=TASK/'work'
PACKAGE=HERE/'candidate_01/package'
MANIFEST=HERE/'core_manifest_01.json'
INSTALLER=HERE/'deploy_core.ps1'
DEPLOYMENT=HERE/'deployment_01'
PS=Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
EPOCH='KM3_KOLD_PREPARED_ENTRY'
BEFORE='RD10_MID_QUEST_RESUME_RETIRED'
CHANGES={ARCHIVE}
TEMPLATE=WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_08/deploy_core.ps1'

def main():
 b=baseline();game=Path(b['game_root']);compile_proof=read(COMPILE)
 assert compile_proof['status']=='PASS' and compile_proof['sources']==148
 sources={p.relative_to(game).as_posix() for root in ('r6/scripts','red4ext/plugins') for p in (game/root).rglob('*.reds')}
 assert sources==set(compile_proof['staged'])
 inputs={}
 for rel in sources:
  p=game/rel;plain(p);assert sha(p)==compile_proof['staged'][rel];inputs[str(p)]=sha(p)
 for rel in ('engine/tools/scc.exe','r6/cache/final.redscripts'):
  p=game/rel;plain(p);assert sha(p)==compile_proof['input_pins'][str(p)];inputs[str(p)]=sha(p)
 # Sidecar is a current transaction pin, not proof of unchanged historical logs.
 p=game/'r6/cache/final.redscripts.ts';plain(p);inputs[str(p)]=sha(p)
 write(HERE/'compile_equivalence.json',dict(status='EXACT_COMPILED_SOURCE_EQUIVALENCE',sources=148,compiler_inputs=151,
  compile_result=str(COMPILE),compile_result_sha256=sha(COMPILE),input_pins=inputs,new_compile=False,
  note='148 source bytes, compiler and base bytecode match the recorded compile. Current cache sidecar pinned separately.'))
 pack=read(HERE/'archive_01/readback.json');graph=read(HERE/'assessment.json');pins=read(HERE/'inputs.json')
 assert pack['status']=='MEMBERS_VERIFIED' and graph['status']=='PASS' and pack['changed_depot']==DEPOT
 updated={r['depot']:r['sha256'] for r in pack['members']}
 assert updated.keys()==pins['members'].keys() and {k for k in updated if updated[k]!=pins['members'][k]}=={DEPOT}
 packed=HERE/'archive_01/zzzz_PTFR_Combined.archive';assert sha(packed)==pack['archive_sha256']
 files=[]
 for row in b['core_files']:
  rel=row['path'];dest=PACKAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists()
  shutil.copyfile(packed if rel==ARCHIVE else game/rel,dest)
  files.append(dict(path=rel,before=row['sha256'],before_bytes=row['bytes'],after=sha(dest),after_bytes=dest.stat().st_size))
 assert len(files)==51 and {r['path'] for r in files if r['before']!=r['after']}==CHANGES
 write(PACKAGE.parent/'manifest.json',dict(status='STAGED_OFFLINE',core_files=files,changes=sorted(CHANGES),archive_sha256=pack['archive_sha256'],archive_payloads=1748))
 DEPLOYMENT.mkdir();(HERE/'fixtures').mkdir();(HERE/'recovery').mkdir()
 bundle=DEPLOYMENT/'KM3_Kold_prepared_entry_full_51.zip'
 with ZipFile(bundle,'x',ZIP_DEFLATED,compresslevel=6) as z:
  for r in files:z.write(PACKAGE/r['path'],r['path'])
 with ZipFile(bundle) as z:
  assert len(z.namelist())==51 and z.testzip() is None
  assert all(sha256(z.read(r['path'])).hexdigest().upper()==r['after'] for r in files)
 proofs=[BASELINE,COMPILE,HERE/'compile_equivalence.json',HERE/'inputs.json',HERE/'assessment.json',HERE/'archive_01/readback.json',PACKAGE.parent/'manifest.json']
 prior=read(WS/'prealpha/mid_quest_resume_retire_20261115_01/stage_08/core_manifest_01.json')
 write(MANIFEST,dict(schema=f'PTFR_{EPOCH}_CORE_V1',component='Core',source_epoch=EPOCH,predecessor_epoch=BEFORE,
  scope='User requested: fix kold mirage now. Repair only its unopened prepared entry; preserve fresh token, progress, saved owner and downstream gameplay.',
  game_root=str(game),save_root=b['save_root'],package_root=str(PACKAGE),process_names=prior['process_names'],files=files,
  changing_paths=sorted(CHANGES),required_files=b['required_files'],protected_saves=[],working_save_files=[],
  zip=str(bundle),zip_sha256=sha(bundle),proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],compile_inputs=inputs))
 assert sha(TEMPLATE)=='74FA23EEF48384BDF7D9B097CC9504CE1C514435ABD2B3C9EB53D700F7F7CC0E'
 source=TEMPLATE.read_text(encoding='utf-8-sig')
 oldwanted=next(line for line in source.splitlines() if line.startswith('$wanted='))
 replacements=[
  ('CAC9C468C373F7AAB833E751A22C496C16620D01295D43CEC06DE8DD3F398CE7',sha(MANIFEST)),
  ('PTFR_RD10_MID_QUEST_RESUME_RETIRED_CORE_V1',f'PTFR_{EPOCH}_CORE_V1'),
  ("source_epoch -cne 'RD10_MID_QUEST_RESUME_RETIRED'",f"source_epoch -cne '{EPOCH}'"),
  ("predecessor_epoch -cne 'RD10_EXACT_RESUME_ARCHIVED'",f"predecessor_epoch -cne '{BEFORE}'"),
  ('recovery/mid_quest_resume_01','recovery/kold_gate_01'),
  (oldwanted,f"$wanted=@('{ARCHIVE}')"),
  ('$changes.Count -ne 6 -or','$changes.Count -ne 1 -or'),
  ('Mid-quest retirement scope drift','KOLD archive-only scope drift'),
  ('qualified Meet Kirk archive','qualified KOLD entry archive'),
  ('foreach($row in $changes){CheckFile (Safe $manifest.package_root $row.path)','foreach($row in $manifest.files){CheckFile (Safe $manifest.package_root $row.path)'),
  ('@($changes.path|Sort-Object)-join', '@($manifest.files.path|Sort-Object)-join'),
 ]
 # Last replacement applies only to the package-inventory assertion, not scope.
 for old,new in replacements[:-1]:
  assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new,1)
 old,new=replacements[-1];assert source.count(old)==2
 source=source.replace(old,new,1)
 with INSTALLER.open('x',encoding='utf-8',newline='\r\n') as f:f.write(source)
 write(HERE/'installer_adaptation.json',dict(template=str(TEMPLATE),template_sha256=sha(TEMPLATE),installer_sha256=sha(INSTALLER),replacements=replacements))
 print('Prepared verified Core51 package, unchanged-source compile proof and archive-only installer.')
if __name__=='__main__':main()
