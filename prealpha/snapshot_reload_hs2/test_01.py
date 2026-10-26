from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
R='r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotStateHS1.reds';L='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def block(s,pat):
 m=re.search(pat,s);assert m,pat
 i=s.index('{',m.start());j=i+1;n=1
 while n:n+=(s[j]=='{')-(s[j]=='}');j+=1
 return s[m.start():j]
checks=[]
def ck(n,b):assert b,n;checks.append(n)
old=(C/'before'/R).read_text();new=(C/'package'/R).read_text()
ck('All persistent field identities and types preserved',re.findall(r'private persistent let[^;]+;',old)==re.findall(r'private persistent let[^;]+;',new))
for method in ['AckFile','ReportIOFailure','Allows','FreshU9','FamilyPrerequisite','ReadRow','Same','Shape','OnBoundary','Ready','ResetRead']:
 ck(method+' unchanged',block(old,r'  (?:public|private|protected cb) func '+method+r'\b')==block(new,r'  (?:public|private|protected cb) func '+method+r'\b'))
ck('Recovery class unchanged',old[old.index('public class SnapshotRecoveryHS1'):]==new[new.index('public class SnapshotRecoveryHS1'):])
row=block(new,r'  public func RowJSON\b');header=block(new,r'  public func HeaderJSON\b')
ck('CET getters never access persistent row arrays', 'this.rows' not in row+header and 'Serialize' not in row+header and 'jsonRowsHS2[i]' in row)
ck('Export requires transient finished cache and attached system','return this.running && this.jsonReadyHS2 &&' in new)
ck('Cache invalidated first on restore/detach','this.jsonReadyHS2=false;' in block(new,r'  private func OnDetach\b') and block(new,r'  public func Restored\b').split('{',1)[1].strip().startswith('this.jsonReadyHS2=false;'))
serialize=block(new,r'  private func SerializeRowHS2\b').split('{',1)[1]
oldrow=block(old,r'  public func RowJSON\b');ck('JSON row format exactly unchanged',serialize[serialize.index('    let row='):]==oldrow[oldrow.index('    let row='):])
prep=block(new,r'  private func PrepareJSONHS2\b')
ck('Bounded simulation-side producer and no timeout bypass','budget<16' in prep and '!player.IsAttached()' in prep and 'jsonCursorHS2==SnapshotDataHS1.Count()' in prep and new.count('this.PrepareJSONHS2();')==1)
base=(W/'prealpha/h10_h5/candidate_01/compile_01/compiled.script').read_text(encoding='utf-8-sig');compiled=(C/'compile_01/compiled.script').read_text(encoding='utf-8-sig')
for cl in ['PTFR.Housing.HousingState','PTFR.HistorySnapshotHS1.SnapshotRecoveryHS1','PTFR.HistorySnapshotHS1.SnapshotRowHS1']:
 ck('Compiled '+cl+' unchanged',block(base,r'public (?:class|struct) '+re.escape(cl)+r'\b')==block(compiled,r'public (?:class|struct) '+re.escape(cl)+r'\b'))
ck('Full SCC passed',read(C/'compile_01/result.json')['full_scc_equipmentex'])
# Execute the actual Lua exporter with engine stubs and an in-memory filesystem.
sys.path.insert(0,str(W/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
events={};calls=0;attached=false;pregame=false;cache=false;exported=false;epoch=1;revision=2;files={};acks=0
registerForEvent=function(name,fn) events[name]=fn end
json={decode=function(_) return {schema=1,rows={},revision=revision,origin='post_ending_fallback'} end}
json.decode=function(_) local r={};for i=1,158 do r[i]={} end;return {schema=1,rows=r,revision=revision,origin='post_ending_fallback'} end
local s={CanExport=function() return cache end,Exported=function() return exported end,Epoch=function() return epoch end,Revision=function() return revision end,Count=function() return 158 end,HeaderJSON=function() return '{"schema":1,"rows":[' end,RowJSON=function(_,i) assert(cache);calls=calls+1;return '{}' end,FileToken=function() return 'existing' end,AckFile=function(_,e,r,t) assert(e==epoch and r==revision);acks=acks+1;exported=true;return true end,ReportIOFailure=function() end}
Game={GetPlayer=function() return {IsAttached=function() return attached end} end,GetSystemRequestsHandler=function() return {IsPreGame=function() return pregame end} end,GetScriptableSystemsContainer=function() return {Get=function() return s end} end}
io.open=function(path,mode)
 if mode=='rb' then if files[path]==nil then return nil end;return {read=function() return files[path] end,close=function() return true end} end
 return {write=function(_,d) files[path]=d;return true end,flush=function() return true end,close=function() return true end}
end
os.rename=function(a,b) assert(files[b]==nil);files[b]=files[a];files[a]=nil;return true end
''')
lua.execute((C/'package'/L).read_text())
lua.execute('cache=true;events.onUpdate(1)');ck('No system payload reads before player attachment',lua.globals().calls==0)
lua.execute('attached=true;pregame=true;events.onUpdate(1)');ck('No system payload reads at main menu',lua.globals().calls==0)
lua.execute('pregame=false;cache=false;events.onUpdate(1)');ck('No payload reads while cache building',lua.globals().calls==0)
lua.execute('cache=true;events.onUpdate(1)');ck('Bounded 16 row consumption',lua.globals().calls==16 and lua.globals().acks==0)
lua.execute('attached=false;events.onUpdate(1);epoch=epoch+1;attached=true;calls=0;for i=1,10 do events.onUpdate(1) end');ck('Load transition discards partial export, verifies full new epoch',lua.globals().calls==158 and lua.globals().acks==1)
lua.execute('events.onUpdate(1)');ck('No repeated export/ack after completion',lua.globals().calls==158 and lua.globals().acks==1)
for f in read(C/'changes_01.json'):ck('Exact source hash '+f['target'],sha(C/'package'/f['target'])==f['after'])
out=dict(status='PASS_HS2_OFFLINE_LIVE_PENDING',checks=checks,count=len(checks),compiled_sha256=sha(C/'compile_01/cache/compiled.redscripts'))
(C/'tests_01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
