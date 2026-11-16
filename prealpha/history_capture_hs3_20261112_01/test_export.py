"""Execute the actual candidate Lua with isolated in-memory filesystem/save fixtures."""
import json
import sys
from common import HERE, ROOT, LUA, read, sha, write

sys.path.insert(0, str(ROOT / 'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime


def fixture(source, hs3_count):
    lua=LuaRuntime(unpack_returned_tuples=True);g=lua.globals()
    g.decode=lambda text:lua.table_from(json.loads(text),recursive=True)
    g.hs3count=hs3_count
    lua.execute('''
events,files,messages,systems={},{},{},{}
attached,pregame=true,false
failWrite,failFlush,failClose,failRename,corruptReadback=false,false,false,false,false
switchOnRename=false
registerForEvent=function(name,fn) events[name]=fn end
print=function(message) messages[#messages+1]=message end
json={decode=decode}
os.date=function() return "20261112T190000Z" end
io.open=function(name,mode)
  if mode=="wb" then
    if failWrite then return nil end
    return {write=function(_,text) files[name]=text;return true end,
      flush=function() return not failFlush end,close=function() return not failClose end}
  end
  if files[name]==nil then return nil end
  return {read=function() if corruptReadback and name:sub(-4)==".tmp" then return "corrupt" end return files[name] end,
    close=function() return true end}
end
os.rename=function(a,b)
  if failRename then return false end
  assert(files[b]==nil);files[b],files[a]=files[a],nil
  if switchOnRename then systems[3].lease="" end
  return true
end
makeSystem=function(schema,count,label)
  local s={schema=schema,count=count,label=label,epoch=4,revision=1,lease="",token="",exported=false,ready=true,acks=0,failures=0}
  s.Epoch=function(self) return self.epoch end
  s.Revision=function(self) return self.revision end
  s.Count=function(self) return self.count end
  s.CanExport=function(self) return self.ready end
  s.Exported=function(self) return self.exported end
  s.LeaseHS3=function(self) return self.lease end
  s.BeginExportHS3=function(self,e,r,lease) assert(e==self.epoch and r==self.revision);self.lease=lease;return true end
  s.HeaderJSON=function(self)
    return '{"schema":'..self.schema..',"catalogue":"fixture","origin":"'..
      (self.schema==1 and "pre_ending" or "pre_native_cleanup")..'","route":1,"ticket":1,"revision":'..self.revision..',"rows":['
  end
  s.RowJSON=function(self,i) return '{"fixture":"'..self.label..'","index":'..i..'}' end
  s.FileToken=function(self) return self.token end
  s.AckFileLeaseHS3=function(self,e,r,token,lease)
    if e~=self.epoch or r~=self.revision or lease~=self.lease or lease=="" then return false end
    self.acks=self.acks+1;self.token=token;self.exported=true;return true
  end
  s.ReportIOFailure=function(self) self.failures=self.failures+1 end
  s.Status=function(self) return self.label end
  return s
end
systems[1]=makeSystem(1,158,"legacy")
systems[3]=makeSystem(3,hs3count,"first")
Game={GetPlayer=function() return {IsAttached=function() return attached end} end,
  GetSystemRequestsHandler=function() return {IsPreGame=function() return pregame end} end,
  GetScriptableSystemsContainer=function() return {Get=function(_,name)
    if name=="PTFR.HistorySnapshotHS1.SnapshotStateHS1" then return systems[1] end
    if name=="PTFR.HistorySnapshotHS1.CaptureArchiveHS3" then return systems[3] end
  end} end}
''')
    lua.execute(source)
    return lua,g


def drive(g,n):
    for _ in range(n): g.events['onUpdate'](0.1)


def main():
    out=HERE/'verification_01';assert not out.exists();out.mkdir()
    source=(HERE/'candidate_02/package'/LUA).read_text(encoding='utf-8')
    data=read(HERE/'evidence_01/catalogue.json');count=sum(len(data[k]) for k in ('journals','facts','items'))
    ticks=(count+63)//64+3;checks=[]
    lua,g=fixture(source,count);drive(g,ticks)
    assert g.systems[1].acks==1 and g.systems[3].acks==1
    path='snapshot_hs3_'+g.systems[3].token+'.json';saved=g.files[path]
    document=json.loads(saved);assert len(document['rows'])==count and document['rows'][-1]['index']==count-1
    checks.append('both actual exporters write and verify complete documents')
    g.systems[3].exported=False;g.systems[3].lease='';drive(g,ticks)
    assert g.systems[3].acks==2 and g.files[path]==saved
    checks.append('reload reuses byte-identical save-bound export')
    g.files[path]=None;g.systems[3].exported=False;g.systems[3].lease='';drive(g,ticks)
    assert g.systems[3].acks==3 and g.files['snapshot_hs3_'+g.systems[3].token+'.json']==saved
    checks.append('missing export is regenerated from save-local payload')
    lua,g=fixture(source,count);g.files['snapshot_hs3_existing.json']='different branch';g.systems[3].token='existing';drive(g,ticks)
    assert g.files['snapshot_hs3_existing.json']=='different branch' and g.systems[3].acks==1 and g.systems[3].token!='existing'
    checks.append('differing existing export is preserved')
    for failure in ('failWrite','failFlush','failClose','failRename','corruptReadback'):
        lua,g=fixture(source,count);g[failure]=True;drive(g,ticks)
        assert g.systems[3].acks==0 and not g.systems[3].exported
        g[failure]=False;drive(g,ticks+55);assert g.systems[3].acks==1
        checks.append(failure+' cannot acknowledge and can recover')
    lua,g=fixture(source,count);drive(g,20)
    # Same numbers are deliberately retained across the save switch. Only the
    # transient per-export lease distinguishes the new loaded system.
    lua.execute('systems[3]=makeSystem(3,hs3count,"second")')
    drive(g,ticks)
    doc=json.loads(g.files['snapshot_hs3_'+g.systems[3].token+'.json'])
    assert g.systems[3].acks==1 and all(r['fixture']=='second' for r in doc['rows'])
    checks.append('same-epoch same-revision save switch discards partial old payload')
    lua,g=fixture(source,count);g.switchOnRename=True;drive(g,ticks)
    assert g.systems[3].acks==0
    g.switchOnRename=False;drive(g,ticks);assert g.systems[3].acks==1
    checks.append('restore between rename and acknowledgement invalidates lease')
    lua,g=fixture(source,count);drive(g,20);g.systems[3].revision=2;g.systems[3].lease='';drive(g,ticks)
    assert g.systems[3].acks==1 and json.loads(g.files['snapshot_hs3_'+g.systems[3].token+'.json'])['revision']==2
    checks.append('new capture revision invalidates unfinished export')
    lua,g=fixture(source,count);g.attached=False;drive(g,ticks);assert g.systems[3].acks==0
    g.attached=True;g.pregame=True;drive(g,ticks);assert g.systems[3].acks==0
    g.pregame=False;drive(g,ticks);assert g.systems[3].acks==1
    checks.append('load and pregame cannot enter snapshot systems')
    lua,g=fixture(source,count);g.systems[3].count=count-1;drive(g,2);assert g.systems[3].acks==0
    checks.append('wrong catalogue count is rejected')
    assert 'retainedTestToken' not in source and 'retainedComparison' not in source and 'json.decode' in source
    result={'status':'PASS_ACTUAL_LUA_FIXTURES','checks':checks,'count':len(checks),'candidate_sha256':sha(HERE/'candidate_02/package'/LUA),
            'tool_sha256':sha(__file__),'limits':'In-memory filesystem and script-system doubles; no live game or engine persistence claim.'}
    write(out/'export_fixtures.json',result);print(json.dumps(result))


if __name__=='__main__':main()
