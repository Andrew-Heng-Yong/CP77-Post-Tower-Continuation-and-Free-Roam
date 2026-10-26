from pathlib import Path
import hashlib,json,shutil
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
R='r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds'
L='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
C.mkdir(exist_ok=False);old=(G/R).read_text(encoding='utf-8-sig');new=old
new=new.replace('  private let running: Bool;','''  // HS2: CET reads only completed transient JSON, never live saved row arrays.
  private let jsonRowsHS2: array<String>;
  private let jsonHeaderHS2: String;
  private let jsonReadyHS2: Bool;
  private let jsonCursorHS2: Int32;
  private let running: Bool;''',1)
new=new.replace('this.Unregister(); this.running=false;', 'this.jsonReadyHS2=false; this.Unregister(); this.running=false;',1)
new=new.replace('    this.Unregister();this.epoch+=1;', '    this.jsonReadyHS2=false;this.jsonCursorHS2=0;ArrayClear(this.jsonRowsHS2);this.jsonHeaderHS2="";\n    this.Unregister();this.epoch+=1;',1)
new=new.replace('    if this.faulted || this.frozen { return; }','    if this.faulted { return; }\n    if this.frozen { this.PrepareJSONHS2(); return; }',1)
new=new.replace('public func CanExport() -> Bool { return !this.faulted && this.ready && this.frozen; }','public func CanExport() -> Bool { return this.running && this.jsonReadyHS2 && !this.faulted && this.ready && this.frozen; }',1)
a=new.index('  public func HeaderJSON()');b=new.index('  public func Status()',a)
oldjson=new[a:b]
header=oldjson[oldjson.index('    return "{'):oldjson.index('  public func RowJSON')].rsplit('  }',1)[0]
row=oldjson[oldjson.index('    let row=this.rows[i];'):].rsplit('  }',1)[0]
cache='''  private func PrepareJSONHS2() -> Void {
    if this.jsonReadyHS2 || !this.running || this.faulted || !this.ready || !this.frozen { return; }
    let player=GetPlayer(this.GetGameInstance()) as PlayerPuppet;
    if !IsDefined(player) || !player.IsAttached() { return; }
    // Delay callbacks run in the game simulation after attach/restore. Publish
    // only after the entire frozen payload has been serialized in that context.
    let budget=0;
    while budget<16 && this.jsonCursorHS2<SnapshotDataHS1.Count() {
      ArrayPush(this.jsonRowsHS2,this.SerializeRowHS2(this.jsonCursorHS2));
      this.jsonCursorHS2+=1;budget+=1;
    }
    if this.jsonCursorHS2==SnapshotDataHS1.Count() {
      this.jsonHeaderHS2=this.SerializeHeaderHS2();
      this.jsonReadyHS2=true;
    }
  }
  private func SerializeHeaderHS2() -> String {
'''+header+'''  }
  private func SerializeRowHS2(i: Int32) -> String {
'''+row+'''  }
  public func HeaderJSON() -> String {
    if !this.CanExport() { return ""; }
    return this.jsonHeaderHS2;
  }
  public func RowJSON(i: Int32) -> String {
    if !this.CanExport() || i<0 || i>=ArraySize(this.jsonRowsHS2) { return ""; }
    return this.jsonRowsHS2[i];
  }
'''
new=new[:a]+cache+new[b:]
lua=(G/L).read_text(encoding='utf-8-sig')
needle='  local c = Game.GetScriptableSystemsContainer()'
assert lua.count(needle)==1
lua=lua.replace(needle,'''  -- Do not enter a restored script system from CET during load/teardown.
  local player = Game.GetPlayer()
  if not player or not player:IsAttached() then return nil end
  local handler = Game.GetSystemRequestsHandler()
  if not handler or handler:IsPreGame() then return nil end
'''+needle)
changes=[]
for rel,txt in [(R,new),(L,lua)]:
 for folder in ['before','package']:(C/folder/rel).parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(G/rel,C/'before'/rel);(C/'package'/rel).write_text(txt,encoding='utf-8',newline='\n')
 changes.append(dict(target=rel,before=sha(G/rel),after=sha(C/'package'/rel)))
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
shutil.copyfile(W/'prealpha/h10_h5/compile_01.py',H/'compile_01.py')
print('Built two-file HS2 reload fix; no game writes.')
