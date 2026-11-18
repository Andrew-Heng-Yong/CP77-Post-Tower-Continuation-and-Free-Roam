"""Freeze the complete Core51 successor and an exact three-file transaction."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib,shutil
from prepare import HERE as TASK,WORK,WS,BASE as BASELINE,DEPOT,SCRIPT,ARCHIVE,XL,baseline,plain,read,sha,write

HERE=WORK
PACKAGE=WORK/'candidate_01/package'
MANIFEST=WORK/'core_manifest_01.json'
INSTALLER=WORK/'deploy_core.ps1'
DEPLOYMENT=WORK/'deployment_01'
COMPILE=WORK/'compile_01/assessment.json'
PS=Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
EPOCH='WO1_STREET_OVERLAP_CLEANUP'
BEFORE='KM3_KOLD_PREPARED_ENTRY'
CHANGES={ARCHIVE,XL,SCRIPT}
TEMPLATE=WS/'prealpha/kold_mirage_gate_20261116_01/work/deploy_core.ps1'

def main():
 b=baseline();game=Path(b['game_root']);pins=read(WORK/'inputs.json')
 compile=read(COMPILE);assessment=read(WORK/'assessment.json');xl=read(WORK/'xl_assessment.json');packed=read(WORK/'archive_01/readback.json')
 assert compile['status']==assessment['status']==xl['status']=='PASS'
 assert packed['status']=='MEMBERS_VERIFIED' and packed['unchanged_members']==1748 and len(packed['members'])==1749
 assert {r['depot']:r['sha256'] for r in packed['members'] if r['depot']!=DEPOT}==pins['members']
 inputs={p:h for p,h in compile['input_pins'].items() if not p.lower().endswith('.log')}
 assert len(inputs)==151
 for p,h in inputs.items():plain(p);assert sha(p)==h,p
 sources={p.relative_to(game).as_posix() for root in ('r6/scripts','red4ext/plugins') for p in (game/root).rglob('*.reds')}
 assert sources==set(compile['staged']) and len(sources)==148
 rht_path=WS/'prealpha/redhottools_rc7_20261116_01/work/installed_manifest_01.json'
 rht=read(rht_path);assert rht['release_tag']=='v1.3.0-rc.7'
 required=[dict(r,active_only=False) for r in b['required_files']+rht['files']]
 for rel in ('red4ext/RED4ext.dll','bin/x64/plugins/cyber_engine_tweaks/bindings.json'):
  p=game/rel;plain(p);required.append(dict(path=rel,sha256=sha(p),bytes=p.stat().st_size,active_only=False))
 assert len(required)==46 and len({r['path'] for r in required})==46
 for r in required:
  p=game/r['path'];plain(p);assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],p
 replacements={ARCHIVE:WORK/'archive_01/zzzz_PTFR_Combined.archive',XL:Path(pins['xl']['path']),SCRIPT:Path(pins['script']['path'])}
 files=[]
 for row in b['core_files']:
  rel=row['path'];dest=PACKAGE/rel;dest.parent.mkdir(parents=True,exist_ok=True)
  assert not dest.exists();shutil.copyfile(replacements.get(rel,game/rel),dest)
  files.append(dict(path=rel,before=row['sha256'],before_bytes=row['bytes'],after=sha(dest),after_bytes=dest.stat().st_size))
 assert len(files)==51 and {r['path'] for r in files if r['before']!=r['after']}==CHANGES
 for p,h in compile['staged'].items():
  if (PACKAGE/p).exists():assert sha(PACKAGE/p)==h,p
 write(PACKAGE.parent/'manifest.json',dict(status='STAGED_OFFLINE',core_files=files,changes=sorted(CHANGES),archive_sha256=packed['archive_sha256'],archive_payloads=1749))
 DEPLOYMENT.mkdir();(WORK/'fixtures').mkdir();(WORK/'recovery').mkdir()
 bundle=DEPLOYMENT/'WO1_Street_overlap_full_51.zip'
 with ZipFile(bundle,'x',ZIP_DEFLATED,compresslevel=6) as z:
  for r in files:z.write(PACKAGE/r['path'],r['path'])
 with ZipFile(bundle) as z:
  assert len(z.namelist())==51 and z.testzip() is None
  for r in files:assert hashlib.sha256(z.read(r['path'])).hexdigest().upper()==r['after']
 proofs=[BASELINE,rht_path,COMPILE,WORK/'inputs.json',WORK/'audit_01.json',WORK/'assessment.json',WORK/'xl_assessment.json',WORK/'archive_01/readback.json',PACKAGE.parent/'manifest.json']
 previous=read(WS/'prealpha/kold_mirage_gate_20261116_01/work/core_manifest_01.json')
 write(MANIFEST,dict(schema=f'PTFR_{EPOCH}_CORE_V1',component='Core',source_epoch=EPOCH,predecessor_epoch=BEFORE,
  scope='User requests auditing and removing raised overlapping meshes from Viktor clinic to Afterlife. Add the reviewed native final-scene cleanup only after genuine Tower completion and an idle player over 500 m away.',
  game_root=str(game),save_root=b['save_root'],package_root=str(PACKAGE),process_names=previous['process_names'],files=files,
  changing_paths=sorted(CHANGES),required_files=required,protected_saves=[],working_save_files=[],zip=str(bundle),zip_sha256=sha(bundle),
  proofs=[dict(path=str(p),sha256=sha(p)) for p in proofs],compile_inputs=inputs))
 assert sha(TEMPLATE)=='E04403763302BAC9B39721435359F099C1C8FB96B60C2F5C02751A0524695EB1'
 source=TEMPLATE.read_text(encoding='utf-8-sig')
 replacements=[
  ('07327F59484012AC446196A64CAC44BB5652262010C9F54CE109856041B6009C',sha(MANIFEST)),
  ('PTFR_KM3_KOLD_PREPARED_ENTRY_CORE_V1',f'PTFR_{EPOCH}_CORE_V1'),
  ("source_epoch -cne 'KM3_KOLD_PREPARED_ENTRY'",f"source_epoch -cne '{EPOCH}'"),
  ("predecessor_epoch -cne 'RD10_MID_QUEST_RESUME_RETIRED'",f"predecessor_epoch -cne '{BEFORE}'"),
  ('recovery/kold_gate_01','recovery/street_overlap_01'),
  ("$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')","$wanted=@("+','.join("'"+p+"'" for p in sorted(CHANGES))+')'),
  ('$changes.Count -ne 1 -or','$changes.Count -ne 3 -or'),
  ('KOLD archive-only scope drift','Street cleanup three-file scope drift'),
  ('# Replace the qualified KOLD entry archive after installation authorization.','# Install the qualified street-cleanup archive, XL entry and existing driver update.'),
 ]
 for old,new in replacements:
  assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new,1)
 with INSTALLER.open('x',encoding='utf-8',newline='\r\n') as f:f.write(source)
 write(WORK/'installer_adaptation.json',dict(template=str(TEMPLATE),template_sha256=sha(TEMPLATE),installer_sha256=sha(INSTALLER),replacements=replacements))
 print('Frozen Core51 package: three replacements; 46 protected dependencies/preferences; matching compile and recovery installer.')
if __name__=='__main__':main()
