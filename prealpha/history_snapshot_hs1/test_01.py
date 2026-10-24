"""Exercise the real Lua exporter and check saved-format/source boundaries."""
from pathlib import Path
import importlib.util,json,re,sys,hashlib
H=Path(__file__).resolve().parent;W=H.parent.parent;O=H/'candidate_01';P=O/'package'
sys.path.insert(0,str(W/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
spec=importlib.util.spec_from_file_location('catalogue',H/'build_catalogue_01.py');cat=importlib.util.module_from_spec(spec);spec.loader.exec_module(cat)
results=[]
SETUP=r'''
events={};files={};logs={};acks={};failures=0;renames=0;writes=0;rowCalls=0
function registerForEvent(n,f) events[n]=f end
function print(s) table.insert(logs,s) end
sys={epoch=1,revision=1,token="",origin="post_ending_fallback",can=true,exported=false}
function sys:CanExport() return self.can end
function sys:Epoch() return self.epoch end
function sys:Revision() return self.revision end
function sys:FileToken() return self.token end
function sys:Exported() return self.exported end
function sys:Count() return 158 end
function sys:HeaderJSON() return '{"schema":1,"catalogue":"fixture","origin":"'..self.origin..'","revision":'..self.revision..',"rows":[' end
function sys:RowJSON(i)
  rowCalls=rowCalls+1
  if mutateRow and i==mutateRow then self.epoch=self.epoch+1;mutateRow=nil end
  return '{"definition":{"id":"fixture'..i..'"},"states":[1],"facts":[],"stable":true}'
end
function sys:AckFile(e,r,t)
  assert(e==self.epoch and r==self.revision and self.can)
  self.token=t;self.exported=true;table.insert(acks,{e=e,r=r,t=t});return true
end
function sys:ReportIOFailure(e,r) self.exported=false;failures=failures+1 end
function sys:Status() return self.origin end
container={Get=function(self,name) assert(name=="PTFR.HistorySnapshotHS1.SnapshotStateHS1");return present==false and nil or sys end}
Game={GetScriptableSystemsContainer=function()return container end}
io={open=function(path,mode)
  assert(path:match('^snapshot_hs1_[A-Za-z0-9_-]+%.%w+$'),path)
  if mode=="rb" then
    if files[path]==nil then return nil end
    return {read=function(self,n) local s=files[path];if corruptRead and path:match('%.tmp$') then s=s..'bad' end;return s:sub(1,n) end,close=function()return true end}
  end
  assert(mode=="wb")
  if openFail then return nil end
  files[path]="";writes=writes+1
  return {write=function(self,s) if writeFail then return nil end;files[path]=files[path]..s;return self end,
    flush=function() if flushFail then return nil end;return true end,
    close=function() if mutateClose then sys.epoch=sys.epoch+1;mutateClose=false end;if closeFail then return nil end;return true end}
end}
os={date=function()return "20261024T150000Z" end,rename=function(a,b)
  if renameFail then return nil end
  assert(files[b]==nil and files[a]~=nil);files[b]=files[a];files[a]=nil;renames=renames+1;return true
end}
'''
def scenario():
 lua=LuaRuntime(unpack_returned_tuples=True);lua.execute(SETUP)
 def table(v):
  if isinstance(v,dict):return lua.table_from({k:table(x) for k,x in v.items()})
  if isinstance(v,list):return lua.table_from([table(x) for x in v])
  return v
 lua.globals().json=lua.table_from({'decode':lambda s:table(json.loads(s))})
 lua.execute((H/'init.lua').read_text());return lua
def tick(lua,n=12,dt=.02):
 for _ in range(n):lua.globals().events.onUpdate(dt)
def stored(lua):return dict(lua.globals().files.items())
def ackcount(lua):return len(lua.globals().acks)
def mark(name):results.append(name)

lua=scenario();tick(lua);assert ackcount(lua)==1 and lua.globals().renames==1
files=stored(lua);assert len(files)==1;data=json.loads(next(iter(files.values())))
assert len(data['rows'])==158 and data['origin']=='post_ending_fallback';mark('real exporter: complete fallback and verified file')
tick(lua,100);assert ackcount(lua)==1 and lua.globals().writes==1;mark('no repeated writes after acknowledgement')
lua.globals().sys.exported=False;tick(lua);assert ackcount(lua)==2 and lua.globals().writes==1;mark('reload re-verifies existing exact sidecar')
original=stored(lua);lua.globals().sys.exported=False;lua.globals().sys.revision=2;tick(lua)
assert ackcount(lua)==3 and all(stored(lua)[k]==v for k,v in original.items()) and len(stored(lua))==2;mark('older/newer branch payload collision preserved')
lua=scenario();lua.globals().sys.origin='pre_ending';tick(lua);lua.execute('files={};sys.exported=false');tick(lua)
assert ackcount(lua)==2 and all(json.loads(v)['origin']=='pre_ending' for v in stored(lua).values());mark('missing file regenerated from saved pre-ending payload')
lua=scenario();lua.globals().sys.can=False;tick(lua,40);assert not stored(lua) and ackcount(lua)==0;mark('no baseline cannot be exported or acknowledged')
lua=scenario();lua.globals().sys.token='../foreign';tick(lua);assert ackcount(lua)==1 and '..' not in lua.globals().sys.token;mark('unsafe saved path never opened')
for failure in ['openFail','writeFail','flushFail','closeFail','renameFail','corruptRead']:
 lua=scenario();setattr(lua.globals(),failure,True);tick(lua)
 assert ackcount(lua)==0 and lua.globals().failures==1,failure
 setattr(lua.globals(),failure,False);tick(lua,1,6);tick(lua,12)
 assert ackcount(lua)==1,failure
 mark('file failure/retry: '+failure)
lua=scenario();lua.globals().mutateRow=22;tick(lua,23)
assert ackcount(lua)==1 and lua.globals().acks[1]['e']==2;mark('load/epoch change during row export discards stale batch')
lua=scenario();lua.globals().mutateClose=True;tick(lua)
assert ackcount(lua)==0 and lua.globals().renames==0;tick(lua,12)
assert ackcount(lua)==1 and lua.globals().acks[1]['e']==2;mark('epoch change during file write cannot acknowledge old save')
lua=scenario();lua.globals().sys.origin='invented_pre_history';tick(lua)
assert ackcount(lua)==0 and lua.globals().writes==0;mark('invalid origin rejected before file write')
lua=scenario();tick(lua,3);lua.globals().events.onShutdown();assert ackcount(lua)==0 and not stored(lua);mark('shutdown during export has no committed partial file')

changes=json.loads((O/'changes_01.json').read_text())
for change in changes:
 if not change['before']:continue
 a=(O/'before'/change['target']).read_text(encoding='utf-8-sig');b=(P/change['target']).read_text(encoding='utf-8-sig')
 fields=lambda s:re.findall(r'\b(?:private|public|protected)\s+persistent\s+let\s+(\w+)\s*:\s*([^;]+);',s)
 assert fields(a)==fields(b),change['target']
 methods=lambda s:set(re.findall(r'\bfunc\s+(\w+)\(',s))
 assert methods(a)<=methods(b),change['target']
mark('all 10 existing source files preserve saved fields and existing APIs')
catalogue=json.loads((O/'catalogue.json').read_text());rows=catalogue['rows']
data=(P/'r6/scripts/TowerContinued_HistorySnapshot_HS1/SnapshotDataHS1.reds').read_text()
assert len(rows)==158 and len({r['id'] for r in rows})==158
assert sum(r['u9'] for r in rows)==72
assert sum(not r['sources'] for r in rows)==18
for i,row in enumerate(rows):
 for method,expected in [('ID',row['id']),('Paths',[x[0] for x in row['journals']]),('Classes',[x[1] for x in row['journals']]),('Facts',row['facts'])]:
  assert cat.values(data,method,i)==expected,(method,i)
 assert row['journals'][0]==[row['root'],'gameJournalQuest']
 for p,h in catalogue['source_pins'].items():assert cat.sha(Path(p))==h,p
mark('158 selected identities; all generated paths/classes/facts equal pinned installed catalogues')
state=(H/'SnapshotStateHS1.reds').read_text()
snapshot=cat.block(state,r'public class SnapshotStateHS1 extends ScriptableSystem\s*\{')
assert not re.search(r'\.(?:SetFact|SetFactStr|ChangeEntryState|GiveItem|GiveReward|Teleport)\(',snapshot)
recovery=cat.block(state,r'public class SnapshotRecoveryHS1 extends ScriptableSystem\s*\{')
assert re.findall(r'SetOwned\(n"([^"]+)",(\d+)\)',recovery)==[('PTFRPA2_Fault','0'),('PTFRPA2_Finished','1')]
assert 'this.ExactFailedPreparation()' in cat.body(recovery,'Poll')
assert 'this.phase=1' in cat.body(recovery,'Poll') and 'this.originalFault=2' in cat.body(recovery,'Poll')
assert not re.search(r'\.(?:Teleport|Activate|GiveReward|ChangeEntryState|FullNerf|Start)\(',recovery)
mark('snapshot performs observation only; recovery writes exactly two owned acknowledgement facts')
assert 'this.rows[i].stable' in cat.body(snapshot,'Allows')
assert 'this.rows[i].states[0]==1 || this.rows[i].states[0]==2' in cat.body(snapshot,'Allows')
assert 'this.rows[i].states[indices[k]]!=1' in cat.body(snapshot,'FreshU9')
assert 'this.rows[i].facts[indices[k]]!=0' in cat.body(snapshot,'FreshU9')
assert 'this.faulted || this.frozen' in cat.body(snapshot,'Poll')
mark('accepted baseline preserves terminal/unknown/unstable rows and is not recaptured after restoration')
report={'status':'PASS_OFFLINE_NOT_LIVE','checks':results,'count':len(results),'lua_runtime':'Lua 5.1 via lupa; real exporter executed','limitations':['Native snapshot serialization and callbacks need live test','No claim of generic quest stage resume','Overlay and refund-speed work remain separate']}
output=O/sys.argv[1];assert not output.exists();output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'count':len(results)}))
