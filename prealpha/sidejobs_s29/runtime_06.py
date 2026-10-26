"""Generate bounded two-observation admission; never write story state."""
from common import *
import importlib.util
source=ROOT/'prealpha/sidejobs_s28/runtime/generate_03.py'
spec=importlib.util.spec_from_file_location('s28gen',source);gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
prepared=ROOT/'prealpha/sidejobs_s29/prepared_04/prepared.json';rows=read(prepared)['jobs']
text=gen.template().split('// These read-only prerequisites')[0]
text=text.replace('S28','S29').replace('Side jobs S29:', 'Side jobs S29:')
assert text.count('import PTFR.ActivityStateR3.*')==1
text=text.replace('import PTFR.ActivityStateR3.*', 'import PTFR.ActivityStateR3.*\nimport PTFR.HistorySnapshotHS1.*\nimport PTFR.LoadingCoverLC1.*')
text=text.replace('if !IsDefined(GameInstance.GetQuestsSystem(this.GetGameInstance())) { return false; }','if !IsDefined(GameInstance.GetQuestsSystem(this.GetGameInstance())) || !SnapshotStateHS1.StartupReady(this.GetGameInstance()) || !StartupCoverLC1.GameplayReleased(this.GetGameInstance()) { return false; }')
text=text.replace('  private func FreshOwner(i: Int32) -> Bool {','''  private func FreshOwner(i: Int32) -> Bool {
    let snapshot=SnapshotStateHS1.Get(this.GetGameInstance());
    if !IsDefined(snapshot) { return false; }
    let ids=SideJobDataS29.BaselineIDs(i);let k=0;
    while k<ArraySize(ids) { if !snapshot.FreshS29(ids[k]) { return false; }; k+=1; }''')
text=text.replace('ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished"))', 'ToString(this.Own(i, "Issued")) + "/" + ToString(this.Own(i, "Finished"))')
text=text.replace('" currentMatch="','" entered=" + ToString(this.Own(i,"Entered")) + " baselineFresh=" + ToString(this.FreshOwner(i)) + " currentMatch="')
data=gen.data_source(rows).replace('S28','S29')
extra='  public static func BaselineIDs(i: Int32) -> array<String> {\n'
for i,r in enumerate(rows):extra+=f'    if i=={i} {{ return {gen.q(r["journal_ids"])}; }}\n'
extra+='    let empty:array<String>;return empty;\n  }\n'
data=data[:data.rfind('}')]+extra+'}\n'
method='''// Additive read-only access. Existing snapshot fields, format and fingerprint
// remain unchanged. An Active baseline cannot be restarted as a fresh quest.
public func FreshS29(id: String) -> Bool {
  let i=SnapshotDataHS1.Index(id);
  if !this.Ready() || i<0 || i>=ArraySize(this.rows) { return false; }
  return this.rows[i].stable && ArraySize(this.rows[i].states)>0 && this.rows[i].states[0]==1;
}

'''
text+=data
out=ROOT/'prealpha/sidejobs_s29/runtime_06';out.mkdir(exist_ok=False)
(out/'SideJobsS29.reds').write_text(text,encoding='utf-8')
installed=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\r6\scripts\TowerContinued_HistorySnapshot_HS1\SnapshotStateHS1.reds')
original=installed.read_bytes();marker=b'  public func Allows(id: String) -> Bool {';assert original.count(marker)==1
updated=original.replace(marker,method.replace('\n','\r\n').encode('utf-8')+marker)
(out/'SnapshotStateHS1.reds').write_bytes(updated)
assert updated.replace(method.replace('\n','\r\n').encode('utf-8'),b'')==original
(out/'manifest.json').write_text(json.dumps(dict(status='GENERATED_NOT_INSTALLED',rows=rows,source_pins={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [prepared,source,gen.TEMPLATE,Path(__file__)]},installed_snapshot=str(installed),before=sha(installed),files={f:sha(out/f) for f in ['SideJobsS29.reds','SnapshotStateHS1.reds']}),indent=2)+'\n')
print('Generated',len(rows),'bounded owners')
