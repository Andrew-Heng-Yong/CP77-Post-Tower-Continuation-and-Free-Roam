"""Independent QR13 final package verifier; expected deltas come from peer pins."""
from pathlib import Path,PurePosixPath
import argparse,copy,datetime,hashlib,json,os,stat,sys,zipfile,zlib
H=Path(__file__).resolve().parent;W=H.parents[2]
sys.path.insert(0,str(W/'tools/parity_audit'))
from model import Resource
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def fnv(s):
    h=0xcbf29ce484222325
    for c in s.encode():h=((h^c)*0x100000001b3)&0xffffffffffffffff
    return str(h)
def canon(x):
    if isinstance(x,dict):
        x=dict(x)
        if x.get('$type')=='TweakDBID':
            s=str(x['$value']);x['$storage']='uint64';x['$value']=str(int(s))if s.isdigit()else str((len(s.encode())<<32)|zlib.crc32(s.encode()))
        return{k:canon(v)for k,v in x.items()if k not in ['payload_sha256','metadata_sha256']}
    if isinstance(x,list):return[canon(v)for v in x]
    return x
def model(p):return canon(Resource(read(p)).normalize())
def inventory(root):
    root=Path(root);rows={}
    for p in [root,*root.rglob('*')]:
        st=p.lstat();assert not p.is_symlink()and not(getattr(st,'st_file_attributes',0)&0x400),'Linked inventory refused'
        if p.is_file():rows[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':st.st_size}
    return rows
def metadata(root):
    rows={};root=Path(root)
    for folder,dirs,files in os.walk(root,followlinks=False):
        for name in list(dirs):
            p=Path(folder)/name;st=p.lstat()
            if p.is_symlink()or getattr(st,'st_file_attributes',0)&0x400:
                rows[p.relative_to(root).as_posix()]={'kind':'REPARSE_NOT_FOLLOWED'};dirs.remove(name)
        for name in files:
            p=Path(folder)/name;st=p.lstat();rows[p.relative_to(root).as_posix()]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'kind':'REPARSE_NOT_FOLLOWED'if p.is_symlink()or getattr(st,'st_file_attributes',0)&0x400 else'file'}
    return rows
def main(a):
    out=Path(a.output).resolve();assert out.is_relative_to(H)and not out.exists();out.mkdir(parents=True)
    I=read(a.inputs);assert I['status']=='FROZEN_INDEPENDENT_QR13_FINAL_PACKAGE_INPUTS';E=read(I['epoch']);B=read(I['baseline']);A=read(a.capture);checks=[]
    def ck(name,ok,evidence=None):checks.append({'name':name,'pass':bool(ok),'evidence':evidence});assert ok,name
    for r in I['frozen_pins']:ck('frozen independent input '+r['path'],sha(r['path'])==r['sha256'])
    ck('independent extraction input binding',A['inputs_sha256']==sha(a.inputs)and A['archive_sha256']==I['archive_sha256']and A['read_status']=='NoError')
    ck('archive/ZIP hashes frozen',sha(I['archive'])==I['archive_sha256']and sha(I['zip'])==I['zip_sha256'])
    if 'archive_sha256'in E:ck('archive matches frozenepoch',E['archive_sha256']==I['archive_sha256'])
    if 'zip_sha256'in E:ck('ZIP matches frozenepoch',E['zip_sha256']==I['zip_sha256'])
    expected=dict(B['source_resources']);approved={r['depot']:r for r in I['approved_resources']}
    ck('approved resource allowlist bounded',set(approved)<=set(B['source_resources'])and set(approved)==set(I['changed_resources'])and len(approved)>0)
    for d,r in approved.items():
        ck('peer-approved actual raw '+d,sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'])
        ck('peer approval pinned '+d,sha(r['peer_review'])==r['peer_review_sha256']and str(read(r['peer_review'])['status']).startswith(('APPROVED','APPROVE','PASS')))
        expected[d]=r['raw_sha256']
    ck('expected source independent baseline+peer overlay',expected==I['expected_resources']==E['source_resources'])
    sources=inventory(I['source']);actual_source={p.replace('/','\\'):v['sha256']for p,v in sources.items()}
    ck('all source bytes match expected',actual_source==expected)
    ck('depot keys unchanged andFNVunique',set(actual_source)==set(B['source_resources'])and len({fnv(p)for p in expected})==len(expected))
    members=A['members'];ck('every actual member independently extracted exactlyonce',len(members)==len(expected)and len({r['fnv64']for r in members})==len(members)and all(r['expected_key']for r in members))
    actual={}
    for r in members:
        d=r['depot'];ck('actual extracted raw '+d,sha(r['raw'])==r['raw_sha256']==expected[d]and fnv(d)==r['fnv64']);actual[d]=r['raw_sha256']
        if d in approved:
            ck('actual changed member typed readback '+d,r.get('typed_status')=='ACTUAL_FINAL_ARCHIVE_MEMBER_READ_BACK'and sha(r['json'])==r['json_sha256'])
            normalized=model(r['json']);ck('whole actual final resource equals peer approved '+d,not normalized['errors']and normalized==model(approved[d]['json']))
    ck('all unmodified QR8 payloads exact',all(actual[d]==h for d,h in B['source_resources'].items()if d not in approved))
    ck('only independently approved payloads changed',{d for d in actual if actual[d]!=B['source_resources'][d]}==set(approved))
    inherited=read(B['source_epoch'])['inherited_repair_resources'];inherited_rows=[]
    for r in inherited:
        d=r['depot'];ck('inherited repair exact orpeer-reviewed semantic successor '+d,actual[d]==B['source_resources'][d]or d in approved);inherited_rows.append({'depot':d,'baseline_sha256':B['source_resources'][d],'actual_sha256':actual[d],'reviewed_exception':d in approved})
    package=inventory(I['package']);oldpkg={p.replace('\\','/'):h for p,h in B['package_files'].items()};expectedpkg=dict(oldpkg);expectedpkg['archive/pc/mod/zzzz_PTFR_Combined.archive']=I['archive_sha256']
    scriptpaths={r['path']:r for r in I.get('approved_scripts',[])}
    allowed_scripts={'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'}
    ck('script changes only approved existing managed files',set(scriptpaths)<=allowed_scripts)
    for p,r in scriptpaths.items():
        ck('peer reviewed scriptbytes '+p,sha(r['source'])==r['sha256']and sha(r['peer_review'])==r['peer_review_sha256']and str(read(r['peer_review'])['status']).startswith(('APPROVED','APPROVE','PASS')));expectedpkg[p]=r['sha256']
    ck('all51package paths retained',set(package)==set(oldpkg)and len(package)==51)
    ck('every package file equals oldorapproved bytes',{p:r['sha256']for p,r in package.items()}==expectedpkg)
    ck('unchanged entireXL bytes/order/registrations',package['archive/pc/mod/zzzz_PTFR_Combined.archive.xl']['sha256']==oldpkg['archive/pc/mod/zzzz_PTFR_Combined.archive.xl'])
    ziprows=[]
    with zipfile.ZipFile(I['zip'])as z:
        infos=z.infolist();names=[x.filename for x in infos];ck('ZIP exact fileinventory,noextras/dirs/duplicates',set(names)==set(package)and len(names)==len(package)and len({n.casefold()for n in names})==len(names)and all(not x.is_dir()for x in infos))
        ck('ZIP contained paths andallCRCs',all(not PurePosixPath(n).is_absolute()and'..'not in PurePosixPath(n).parts and'\\'not in n for n in names)and z.testzip()is None)
        for info in infos:
            data=z.read(info);digest=hashlib.sha256(data).hexdigest().upper();ck('ZIP member '+info.filename,digest==package[info.filename]['sha256']and len(data)==package[info.filename]['bytes']==info.file_size and(zlib.crc32(data)&0xffffffff)==info.CRC);ziprows.append({'path':info.filename,'sha256':digest,'bytes':len(data),'CRC32':f'{info.CRC:08X}'})
    cr=read(I['compile_result']);ck('actual compile/equality evidence PASS',str(cr['status']).startswith('PASS'))
    ck('actual compiled output pinned',sha(I['compiled_output'])==I['compiled_output_sha256'])
    if I.get('compile_log'):ck('actual compiler success log',cr.get('exit_code')==0 and'Compilation complete'in Path(I['compile_log']).read_text(encoding='utf-8-sig'))
    for p,h in cr['input_pins'].items():ck('complete current compiler/source/cache input '+p,sha(p)==h)
    staged=cr['staged_sources']
    def staged_digest(v):return v if isinstance(v,str)else v['sha256']
    for p,r in staged.items():ck('actual compiled stagedsource '+p,sha(p)==staged_digest(r))
    for p,r in package.items():
        if p.endswith('.reds'):
            hits=[f for f,x in staged.items()if Path(f).name==Path(p).name and staged_digest(x)==r['sha256']];ck('candidate managed sourceincludedincompile '+p,len(hits)==1,hits)
    # Reuse previously independent CR1/PH1/PH2/PH3 controls only onexactpreserved bytes.
    prior=read(I['prior_inherited_review']);ck('CR1/PH control evidence retained',prior['CR1_exact_donors']==25 and prior['PH2_corrected_generated_id']==61197 and prior['PH3_studio_generated_id']==22195 and all(actual[d]==h or d in approved for d,h in B['source_resources'].items()))
    for p,h in B['protected_installed_sha256'].items():ck('installed Core/diagnostic/dependency unchanged '+p,sha(p)==h)
    for p,h in B['save_sha256'].items():ck('saved bytes unchanged '+p,sha(p)==h)
    game=Path(I['game_root']);save=Path(I['save_root'])
    ck('entire game filemetadata unchanged',metadata(game)==B['game_metadata']);ck('entire save filemetadata unchanged',metadata(save)==B['save_metadata'])
    for number,before in B['QR3_to_QR12_metadata'].items():ck('historic QR'+number+' filemetadata unchanged',metadata(W/'prealpha'/('quest_restoration_qr'+number))==before)
    # Old source payloads directly preserved innewarchive retain oldfixes; no oldbuild rerun.
    result={'status':'PASS_INDEPENDENT_FINAL_QR13_COMPLETE_ARCHIVE_ZIP_SOURCE_SCRIPT_AND_PRESERVATION','source_epoch':I['epoch'],'source_epoch_sha256':sha(I['epoch']),'checks':len(checks),'archive_payloads':len(actual),'package_paths':len(package),'changed_resources':sorted(approved),'changed_scripts':sorted(scriptpaths),'unchanged_XL':True,'new_depots_or_registrations':0,'actual_typed_changed_resources_checked':len(approved),'inherited_repairs':inherited_rows,'compiler_sources_checked':len(staged),'input_pins_checked':len(cr['input_pins']),'installed_pins_checked':len(B['protected_installed_sha256']),'save_files_checked':len(B['save_sha256']),'input_manifest':str(Path(a.inputs).resolve()),'input_manifest_sha256':sha(a.inputs),'archive_extraction':str(Path(a.capture).resolve()),'archive_extraction_sha256':sha(a.capture),'archive_sha256':I['archive_sha256'],'zip_sha256':I['zip_sha256'],'reviewer_runtime_or_candidate_writes':0,'limits':['Static actual package/source andpreservation approval; no gameplay, nativecallbacks, executingowner, save-transition orall-save PASS.','Approved component saved-owner/prefab/acquisition/cleanup limits remain intact; nofixturefabrication ordeployment.']}
    for n,v in [('review.json',result),('checks.json',checks),('payload_hashes.json',actual),('zip_members.json',ziprows)]: (out/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k]for k in ['status','checks','archive_payloads','package_paths','changed_resources','changed_scripts','installed_pins_checked','save_files_checked']},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',required=True);ap.add_argument('--capture',required=True);ap.add_argument('--output',required=True);main(ap.parse_args())
