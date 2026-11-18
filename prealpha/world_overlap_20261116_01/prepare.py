"""Prepare a guarded native cleanup successor; no game or save writes."""
from pathlib import Path
import hashlib,json,stat

HERE=Path(__file__).resolve().parent
WORK=HERE/'work'
WS=HERE.parents[1]
BASE=WS/'prealpha/kold_mirage_gate_20261116_01/work/deployment_01/installed_manifest_01.json'
BASE_SHA='D7D6EDC420052701621F9EE409075302E6AF5B1B931EABA5EF9A911526F2C7FF'
DEPOT=r'towercontinued\street_overlap_wo1\cleanup.questphase'
SCRIPT='r6/scripts/PTFR_Consolidated/PTFR_MistyViktorAuto.reds'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
XL=ARCHIVE+'.xl'
OWNER='$/03_night_city/c_watson/little_china/wlc_01/wlc_01_b_env_prefab6TCITNI/#wlc_01_b_decoration'
NATIVE_OWNER='$/03_night_city/c_watson/little_china/wlc_01/wlc_01_b_env_prefab6TCITNI/wlc_01_b_decoration_prefabAEJ25LI'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def plain(p):
 for x in (Path(p),*Path(p).parents):
  if x.exists():assert not x.lstat().st_file_attributes&stat.FILE_ATTRIBUTE_REPARSE_POINT,x
def write(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def baseline():
 assert sha(BASE)==BASE_SHA
 b=read(BASE);game=Path(b['game_root'])
 for r in b['core_files']+b['required_files']:
  p=game/r['path'];plain(p);assert sha(p)==r['sha256'] and p.stat().st_size==r['bytes'],p
 return b
def main():
 b=baseline();game=Path(b['game_root']);audit=read(WORK/'audit_01.json')
 assert audit['status']=='SOURCE_CONFIRMED_TRANSLATED_FINAL_SCENE_GEOMETRY' and len(audit['screenshot_matches'])==2
 capture=read(WORK/'sources_01/providers.json')
 native=next(r for r in capture['hits'] if r['depot'].endswith('q307_cleanup.questphase'))
 shell=next(r for r in capture['hits'] if r['depot'].endswith('shell_optin.questphase'))
 for r in (native,shell):assert sha(r['raw'])==r['sha256'] and sha(r['json'])==r['json_sha256']
 stage=WORK/'stage_01';stage.mkdir()
 original=(game/SCRIPT).read_text(encoding='utf-8-sig')
 attach='    this.running = true;\n    this.Schedule(this.epoch, 1.0);'
 assert original.count(attach)==1
 staged=original.replace(attach,'    this.running = true;\n    let q = GameInstance.GetQuestsSystem(this.GetGameInstance());\n    if IsDefined(q) && q.GetFact(n"PTFRWO1_CleanupPermit") != 0 {\n      q.SetFact(n"PTFRWO1_CleanupPermit", 0);\n    }\n    this.Schedule(this.epoch, 1.0);',1)
 anchor='  public func Poll(expectedEpoch: Int32) -> Void {'
 helper='''  // The native ending set is displaced from the ordinary streets. Its authored
  // cleanup runs only after genuine completion and while the player is away.
  private func RefreshStreetCleanupPermit(q: ref<QuestsSystem>, p: ref<PlayerPuppet>) -> Void {
    let permit = 0;
    if this.Completed(q) && this.Safe(p) &&
      q.GetFact(n"PTFRMV_Applied") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupRegistered") == 1 &&
      q.GetFact(n"PTFRWO1_CleanupDone") == 0 {
      let pos = p.GetWorldPosition();
      let dx = pos.X + 1475.0;
      let dy = pos.Y - 1080.0;
      if dx * dx + dy * dy > 250000.0 { permit = 1; }
    }
    if q.GetFact(n"PTFRWO1_CleanupPermit") != permit {
      q.SetFact(n"PTFRWO1_CleanupPermit", permit);
    }
  }
'''
 assert staged.count(anchor)==1;staged=staged.replace(anchor,helper+anchor,1)
 anchor='    this.Schedule(expectedEpoch, 2.0);'
 assert staged.count(anchor)==1
 staged=staged.replace(anchor,'    if IsDefined(q) { this.RefreshStreetCleanupPermit(q, p); }\n'+anchor,1)
 path=stage/'package'/SCRIPT;path.parent.mkdir(parents=True)
 with path.open('x',encoding='utf-8',newline='\r\n') as f:f.write(staged)
 oldxl=(game/XL).read_bytes()
 newline=b'\r\n' if b'\r\n' in oldxl else b'\n'
 entry=('    - path: '+DEPOT+'\n      parent: ep1\\quest\\ep1.quest\n      input:\n        node: [1]\n        socket: Out\n').replace('\n',newline.decode()).encode()
 marker=b'streaming:'+newline
 assert oldxl.count(marker)==1 and DEPOT.encode() not in oldxl
 newxl=oldxl.replace(marker,entry+marker,1)
 assert newxl.replace(entry,b'',1)==oldxl
 target=stage/'package'/XL;target.parent.mkdir(parents=True)
 with target.open('xb') as f:f.write(newxl)
 packed=read(WS/'prealpha/kold_mirage_gate_20261116_01/work/archive_01/readback.json')
 assert packed['archive_sha256']==b['archive_sha256'] and len(packed['members'])==1748
 pins=dict(status='PREPARED',baseline=str(BASE),baseline_sha256=BASE_SHA,game=b['game_root'],
  save=b['save_root'],archive_sha256=b['archive_sha256'],archive_source=b['archive_source'],
  members={r['depot']:r['sha256'] for r in packed['members']},native_cleanup=native,shell=shell,
  depot=DEPOT,owner=OWNER,native_cleanup_owner=NATIVE_OWNER,
  script=dict(path=str(path),relative=SCRIPT,before=sha(game/SCRIPT),after=sha(path)),
  xl=dict(path=str(target),relative=XL,before=sha(game/XL),after=sha(target),addition=entry.decode()),
  audit_sha256=sha(WORK/'audit_01.json'),game_writes=0,save_writes=0)
 write(WORK/'inputs.json',pins)
 print('Prepared one native cleanup phase, one additive XL registration and a distance-gated permit in the existing world driver.')
if __name__=='__main__':main()
