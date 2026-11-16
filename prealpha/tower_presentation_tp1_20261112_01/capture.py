"""Pin RD1, the reported session logs and matching native script evidence."""
from pathlib import Path
import hashlib,json,re,shutil,sqlite3,stat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASELINE=ROOT/'prealpha/resume_dispatcher_rd1_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA='DCC4C8958756DDBA54C1F98404B96F2EBDF16E48F8CE3DEC6BB98A0DA6B30864'

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')

def plain(path):
    for p in (path,*path.parents):assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,p

def class_source(text,name):
    pattern=r'(?m)^[ \t]*(?:(?:public|private|protected|native|abstract|importonly|final)[ \t]+)*class[ \t]+'+re.escape(name)+r'\b[^{}]*\{'
    matches=list(re.finditer(pattern,text));assert len(matches)==1,(name,len(matches))
    start=matches[0].start();opening=text.index('{',start);level=0
    for token in re.finditer(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|[{}]',text[opening:]):
        t=token.group()
        if t=='{':level+=1
        elif t=='}':
            level-=1
            if level==0:return text[start:opening+token.end()]+'\n'
    raise AssertionError(name)

def main():
    out=HERE/'evidence_02';base=HERE/'base_02/package';assert not out.exists() and not base.exists()
    assert sha(BASELINE)==BASELINE_SHA;manifest=read(BASELINE);game=Path(manifest['game_root'])
    for row in manifest['core_files']+manifest['required_files']:
        p=game/row['path'];plain(p);assert sha(p)==row['sha256'],p
    out.mkdir();logs=[]
    relatives=['bin/x64/plugins/cyber_engine_tweaks/'+n for n in ('gamelog.log','scripting.log','cyber_engine_tweaks.log')]
    relatives+=['r6/logs/redscript_rCURRENT.log','red4ext/logs/red4ext-2026-11-12-17-42-49.log','red4ext/plugins/ArchiveXL/ArchiveXL-2026-11-12-17-42-50.log']
    for rel in relatives:
        p=game/rel;plain(p);pin=sha(p);dest=out/'logs'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
        assert sha(dest)==sha(p)==pin;logs.append({'path':rel,'sha256':pin,'bytes':dest.stat().st_size})
    for row in manifest['core_files']:
        dest=base/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(game/row['path'],dest);assert sha(dest)==row['sha256']
    native=ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01'
    pin=read(native/'manifest.json')
    assert sha(game/'r6/cache/final.redscripts')==pin['input_sha256'] and sha(native/'base.script')==pin['decompiled_sha256']
    assert sha(game/'bin/x64/Cyberpunk2077.exe')==pin['exe_sha256']
    source=(native/'base.script').read_text(encoding='utf-8-sig');classes=[]
    for name in ('FastTravelSystem','CyberwareCustomizationSystem','EquipmentSystemPlayerData','PlayerPuppet','UISystem'):
        path=out/(name+'.script');path.write_text(class_source(source,name),encoding='utf-8');classes.append({'class':name,'sha256':sha(path)})
    registry=ROOT/'prealpha/quest_resume_registry_20261112_01/registry_02/registry.sqlite3'
    conn=sqlite3.connect(registry.as_uri()+'?mode=ro',uri=True);conn.row_factory=sqlite3.Row
    resource=dict(conn.execute('select * from resources where rid=8735').fetchone())
    assert sha(resource['export_path'])==resource['export_sha256']
    shutil.copyfile(resource['export_path'],out/'open_world_fast_travel.questphase.json')
    write(out/'inputs.json',{'baseline_manifest':str(BASELINE),'baseline_manifest_sha256':BASELINE_SHA,'core_epoch':manifest['core_epoch'],
        'game_root':str(game),'core_files':manifest['core_files'],'required_files':manifest['required_files'],'logs':logs,
        'native_cache_sha256':pin['input_sha256'],'native_export_sha256':pin['decompiled_sha256'],'native_exe_sha256':pin['exe_sha256'],
        'classes':classes,'fast_travel_resource':resource,'game_writes':0,'save_writes':0})
    write(out/'user_report.json',{'machine_gun':'Works fine (user report; do not infer every route/reward/reload).',
        'arms':'Missing arms model immediately after ending.','fast_travel':'Everything black, including menus.',
        'scope':'Investigate presentation and native fast-travel faults; preserve working RD1 quest route.'})
    print('Pinned 51 Core files, 26 dependencies, six logs and matching native script classes; no game/save writes.')

if __name__=='__main__':main()
