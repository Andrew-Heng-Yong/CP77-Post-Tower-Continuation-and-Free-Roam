"""Independent final zero-delta package and fresh-compile verification. Read-only inputs."""
from pathlib import Path
import sys,json,hashlib,zipfile,re,collections
W=Path(__file__).resolve().parents[4];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
def fnv(s):
 x=14695981039346656037
 for c in s.encode('utf8'):x=((x^c)*1099511628211)&0xffffffffffffffff
 return str(x)
def run(A,O):
 assert not O.exists();F=W/'prealpha/quest_restoration_qr6';ep=F/'source_epoch_00.json';E=read(ep);P=Path(E['candidate']);prior=read(E['predecessor_epoch_path']);PM=read(E['package_manifest_path']);allow=read(F/'approved_changes_00.json');rb=read(A/'readback.json');T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,(n,str(e)[:700])
 ck('canonical QR6:00 points exact QR5:08',sha(E['predecessor_epoch_path'])==E['predecessor_epoch_sha256']=='B8BC8D6630F51E07125789FAB5A54D188EB45CE7044F35E2E6F09DE460B91D83' and Path(prior['candidate'])==P,E['predecessor_epoch_path'])
 ck('zero runtime delta is explicit',allow['resources']==[] and E['changes']==[] and E['source_resources']==prior['source_resources'] and E['package_files']==prior['package_files'],{'allowlist':str(F/'approved_changes_00.json'),'sha256':sha(F/'approved_changes_00.json')})
 ck('candidate package manifest exact pinned bytes',sha(E['package_manifest_path'])==E['package_manifest_sha256'],E['package_manifest_path'])
 expected=E['source_resources'];actual={str(p.relative_to(P/'archive_source')).replace('/','\\'):sha(p) for p in (P/'archive_source').rglob('*') if p.is_file()};ck('complete actual source inventory exact',actual==expected and len(actual)==1574,{'actual':len(actual),'expected':len(expected)})
 ck('independent archive memory inventory exact',rb['count']==1574 and len(rb['resources'])==1574 and {r['depot'] for r in rb['resources']}==set(expected),{'path':str(A/'readback.json'),'sha256':sha(A/'readback.json')})
 ck('independent FNV payload identity collision census',len({fnv(d) for d in expected})==len(expected),len(expected))
 for r in rb['resources']:ck('actual packed payload '+r['depot'],r['key']==fnv(r['depot']) and r['packed_sha256']==r['source_sha256']==expected[r['depot']]==actual[r['depot']],{'key':r['key'],'sha256':r['packed_sha256']})
 archive=P/'package/archive/pc/mod/zzzz_PTFR_Combined.archive';xl=Path(str(archive)+'.xl');ck('archive exact canonical bytes',sha(archive)==rb['archive_sha256']==E['archive_sha256']==PM['archive_sha256'],sha(archive));ck('XL exact predecessor registrations byte identity',sha(xl)==E['xl_sha256']==prior['xl_sha256']==PM['xl_sha256'],sha(xl))
 filemap={x['path']:x['sha256'] for x in E['package_files']};files={p.relative_to(P/'package').as_posix():sha(p) for p in (P/'package').rglob('*') if p.is_file()};ck('all51 managed package paths exact and no extras',files==filemap and len(files)==51 and {x['path']:x['sha256'] for x in PM['files']}==filemap,len(files))
 for path,h in filemap.items():ck('unchanged managed package file '+path,sha(P/'package'/path)==h,{'path':path,'sha256':h})
 reds={p:h for p,h in filemap.items() if p.endswith('.reds')};ck('all46 managed REDS source and identities unchanged',len(reds)==46 and all(prior['package_files'][i]==v for i,v in enumerate(E['package_files'])),len(reds))
 inherited=E['inherited_repair_resources'];ck('all9 prior changed resources retained',len(inherited)==9 and len({x['depot'] for x in inherited})==9,len(inherited))
 for repair in inherited:ck('inherited repair exact current source+packed '+repair['depot'],actual[repair['depot']]==repair['after'] and next(r for r in rb['resources'] if r['depot']==repair['depot'])['packed_sha256']==repair['after'],repair['after'])
 zp=Path(E['zip']);ck('existing QR5 ZIP exact no replacement',sha(zp)==E['zip_sha256']==PM['zip_sha256'],{'zip':str(zp),'sha256':sha(zp)});zr=[]
 with zipfile.ZipFile(zp) as z:
  entries=[x for x in z.infolist() if not x.is_dir()];ck('ZIP51 unique exact paths',len(entries)==len({x.filename for x in entries})==51 and {x.filename for x in entries}==set(filemap),len(entries));ck('ZIP CRC integrity',z.testzip() is None,None)
  for x in entries:
   data=z.read(x);h=hashlib.sha256(data).hexdigest().upper();ck('ZIP member exact payload '+x.filename,h==filemap[x.filename] and len(data)==(P/'package'/x.filename).stat().st_size,{'sha256':h,'crc':x.CRC});zr.append({'path':x.filename,'sha256':h,'crc':x.CRC,'bytes':len(data)})
 # Independently tie the fresh SCC result to actual current inputs, staged sources and candidate sources.
 cp=F/'verification/compile_01/result.json';comp=read(cp);ck('fresh complete-input offline SCC completed',comp['status']=='PASS_CURRENT_INPUTS_OFFLINE_COMPILED' and comp['fresh_SCC_invocation'] is True and comp['source_count']==131 and comp['input_pin_count']==134 and comp['managed_sources']==46,{'path':str(cp),'sha256':sha(cp)})
 for p,h in comp['input_pins'].items():ck('current full compiler/cache input '+p,sha(p)==h,h)
 srcroot=Path(comp['command'][comp['command'].index('-compile')+1]);stage={str(p):sha(p) for p in srcroot.rglob('*.reds')};ck('actual compiled staged source census131 exact',len(stage)==131 and set(stage)==set(comp['staged_sources']) and all(stage[p]==r['sha256'] for p,r in comp['staged_sources'].items()),len(stage))
 mapped={}
 for p,h in comp['input_pins'].items():
  if not p.endswith('.reds'):continue
  if '\\r6\\scripts\\' in p:rel='game/'+p.split('\\r6\\scripts\\',1)[1].replace('\\','/')
  else:
   prefix,tail=p.split('\\red4ext\\plugins\\',1);plugin,tail=tail.split('\\',1);tail=tail.removeprefix('Scripts\\');rel=plugin+'/'+tail.replace('\\','/')
  st=srcroot/rel;ck('fresh compiled source equals current pinned original '+rel,str(st) in stage and sha(st)==h,{'original':p,'staged':str(st),'sha256':h});mapped[str(st)]=p
 ck('no unaccounted compiled source files',set(mapped)==set(stage),len(mapped))
 managed={x['path']:x['sha256'] for x in comp['managed']};ck('fresh compilation covers exact candidate46 source bytes',managed==reds,{'compiled_managed':len(managed),'candidate_managed':len(reds)})
 for rel,h in managed.items():st=srcroot/'game'/Path(rel).relative_to('r6/scripts');ck('compiled managed identity '+rel,sha(st)==h==sha(P/'package'/rel),{'staged':str(st),'sha256':h})
 output=Path(comp['command'][comp['command'].index('-outputCacheFile')+1]);ck('fresh SCC output hash',output.is_relative_to(F/'verification/compile_01') and sha(output)==comp['compiled_sha256'],{'output':str(output),'sha256':sha(output)})
 log=F/'verification/compile_01/scc.log';ck('fresh SCC successful completion log', 'Compilation complete' in log.read_text(encoding='utf8') and 'Output successfully saved to '+str(output) in log.read_text(encoding='utf8'),{'path':str(log),'sha256':sha(log)})
 ck('only preexisting timestamp drift identified',len(comp['changed_input_pins'])==1 and comp['changed_input_pins'][0]['path'].endswith('final.redscripts.ts'),comp['changed_input_pins'])
 ck('new compile uses custom cache and output containment',all(Path(comp['command'][comp['command'].index(flag)+1]).is_relative_to(F/'verification/compile_01') for flag in ['-compile','-compilePathsFile','-customCacheDir','-outputCacheFile']),comp['command'])
 # Installed PH3 remains a separate verified baseline, never described as the staged ZIP.
 baseline=F/'verification/baseline_01/result.json';b=read(baseline);ck('installedPH3/staged boundary source',b['status']=='PASS_INSTALLED_PH3_AND_STAGED_QR5_EXACT_BOUNDARIES' and b['installed_paths']==51 and b['installed_or_runtime_writes']==0,{'path':str(baseline),'sha256':sha(baseline)})
 write(O/'tests.json',T);write(O/'zip_members.json',zr);write(O/'compiler_source_correspondence.json',mapped);write(O/'review.json',{'status':'PASS_INDEPENDENT_ZERO_DELTA_PACKAGE_AND_FRESH_COMPILE_REVIEW','checks':len(T),'failures':0,'source_epoch':str(ep),'source_epoch_sha256':sha(ep),'archive_readback':str(A/'readback.json'),'archive_readback_sha256':sha(A/'readback.json'),'payloads':1574,'managed_paths':51,'managed_REDS':46,'inherited_repair_resources':9,'new_changed_resources':0,'zip':str(zp),'zip_sha256':sha(zp),'archive_sha256':sha(archive),'compiler_result':str(cp),'compiler_result_sha256':sha(cp),'compiler_sources':131,'compiler_input_pins':134,'compiled_sha256':sha(output),'installed_boundary':str(baseline),'installed_boundary_sha256':sha(baseline),'limits':['Package/compile structural verification is not gameplay, saved-owner or streamed placement certification.','No rebuild/new ZIP/copy/serialization/deploy/game/save/fact/release writes performed.','Whole game/save byte preservation is coordinator-owned separate evidence.','Existing prior repair semantics are preserved by exact resource byte identity; no new repair regression is claimed.']});print({'checks':len(T),'review':str(O/'review.json'),'sha256':sha(O/'review.json')})
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
