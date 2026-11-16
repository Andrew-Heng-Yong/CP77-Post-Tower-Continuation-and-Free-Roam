"""Fresh TP2 evidence and unchanged installed baseline; no game writes."""
from pathlib import Path
import hashlib,json,stat,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASELINE=ROOT/'prealpha/tower_presentation_tp1_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA='D1EFF6EA9B2A98FE1C92C90576D8DCA1BF9A6E371818C68E046966FC90F95A4E'
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,indent=2);f.write('\n')
def plain(path):
    for p in (Path(path),*Path(path).parents):assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,p
def main():
    assert sha(BASELINE)==BASELINE_SHA
    m=read(BASELINE);game=Path(m['game_root']);out=HERE/'evidence_01';assert not out.exists()
    for row in m['core_files']+m['required_files']:
        plain(game/row['path']);assert sha(game/row['path'])==row['sha256'],row['path']
    out.mkdir()
    for row in m['core_files']:
        d=HERE/'base_01/package'/row['path'];d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(game/row['path'],d);assert sha(d)==row['sha256']
    native=ROOT/'prealpha/quest_restoration_qr15/lifecycle_01/script_source/current_01'
    p=read(native/'manifest.json')
    assert sha(native/'base.script')==p['decompiled_sha256']
    assert sha(game/'r6/cache/final.redscripts')==p['input_sha256']
    assert sha(game/'bin/x64/Cyberpunk2077.exe')==p['exe_sha256']
    write(out/'inputs.json',{'baseline_manifest':str(BASELINE),'baseline_sha256':BASELINE_SHA,'core_files':m['core_files'],'required_files':m['required_files'],'native':p,'game_writes':0,'save_writes':0})
    print('Pinned TP1 51 Core files, 26 dependencies and matched native script/binary.')
if __name__=='__main__':main()
