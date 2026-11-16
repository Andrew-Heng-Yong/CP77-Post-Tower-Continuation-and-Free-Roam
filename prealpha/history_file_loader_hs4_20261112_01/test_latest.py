"""Execute the actual Lua loader against the captured real exports and queued doubles."""
import argparse
import ast
from copy import deepcopy
import json
import sys
from pathlib import Path
from build import HERE, BASE, LUA, RED, read, sha, write

ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'prealpha/quest_restoration_qr9/worker_b/tooling'))
from lupa.luajit21 import LuaRuntime


def fixture_function():
    path=BASE/'test_export.py'
    assert sha(path)==read(BASE/'checkpoint.json')['sources']['test_export.py']
    tree=ast.parse(path.read_text())
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixture']
    env={'LuaRuntime':LuaRuntime,'json':json}
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),env)
    return env['fixture']


ENGINE=r'''
queue={};begins=0;finishes=0;packetCalls=0
dir=function()
  local a={};for name in pairs(files) do a[#a+1]={name=name,type="file"} end;return a
end
local function add(fn) queue[#queue+1]=fn end
drain=function()
  local work=queue;queue={};for _,fn in ipairs(work) do fn() end
  local s=systems[3]
  if s.pending and s.exported and systems[1].exported then s.pending=false end
end
function installReceiver()
  local s=systems[3]
  s.client="";s.loaded=false;s.required=false;s.pending=false;s.may=true;s.transaction="";s.fault=false
  s.cursors={[1]=0,[3]=0};s.packets={[1]={},[3]={}}
  s.MayLoadLatestHS4=function(self) return self.may and not self.pending end
  s.NativeExportPendingHS4=function(self) return self.pending end
  s.ClientLeaseHS4=function(self) return self.client end
  s.OpenClientHS4=function(self,lease) self.client=lease;return true end
  s.RequireLatestHS4=function(self,e,l) assert(e==self.epoch and l==self.client);self.required=true end
  s.GlobalFileReadyHS4=function(self) return self.loaded end
  s.DefinitionHS4=function(self,c,i) return c==1 and defs1[i+1] or defs3[i+1] end
  s.ImportTransactionHS4=function(self) return self.transaction end
  s.ImportCursorHS4=function(self,c) return self.cursors[c] end
  s.ImportFaultHS4=function(self) return self.fault end
  local function current(self,e,l,t)
    return systems[3]==self and self.epoch==e and self.client==l and self:MayLoadLatestHS4() and (not t or self.transaction==t)
  end
  s.BeginFileHS4=function(self,e,l,t,ticket,route,rev,legacyRev,token1,token3)
    add(function()
      if not current(self,e,l) then return end
      begins=begins+1;self.transaction=t;self.cursors={[1]=0,[3]=0};self.packets={[1]={},[3]={}};self.loaded=false
      self.selected={ticket=ticket,route=route,revision=rev,legacyRevision=legacyRev,token1=token1,token3=token3}
    end)
  end
  s.SendPacketHS4=function(self,e,l,t,c,start,n,data)
    packetCalls=packetCalls+1
    add(function()
      if not current(self,e,l,t) or self.cursors[c]~=start then return end
      self.packets[c][#self.packets[c]+1]={start=start,count=n,data=data};self.cursors[c]=start+n
    end)
  end
  s.FinishFileHS4=function(self,e,l,t)
    add(function()
      if not current(self,e,l,t) then return end
      assert(self.cursors[1]==158 and self.cursors[3]==hs3count)
      finishes=finishes+1;self.loaded=true;self.exported=true;systems[1].exported=true
    end)
  end
end
installReceiver()
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=int,default=1);ap.add_argument('--attempt',type=int,default=1);a=ap.parse_args()
    out=HERE/f'verification_{a.attempt:02}';assert not out.exists();out.mkdir()
    source_path=HERE/f'candidate_{a.candidate:02}/package'/LUA
    source=source_path.read_text(encoding='utf-8')
    game=Path(read(BASE/'deployment_01/installed_manifest_01.json')['game_root'])
    export=(game/LUA).parent
    names={1:'snapshot_hs1_20261112T193921Z_151_2.json',3:'snapshot_hs3_20261112T193931Z_1_3.json'}
    raw={c:(export/n).read_text(encoding='utf-8') for c,n in names.items()}
    docs={c:json.loads(v) for c,v in raw.items()}
    assert sha(export/names[3])=='C27598B50A97F3B7D3DD4905CEF1EB8C0F8FB67DF2865933E022B58D5D13D8F0'
    fixture=fixture_function();checks=[]
    def setup(extra=None,empty=False):
        lua,g=fixture(source,len(docs[3]['rows']))
        g.defs1=lua.table_from([json.dumps(r['definition'],separators=(',',':')) for r in docs[1]['rows']])
        g.defs3=lua.table_from([json.dumps(r['definition'],separators=(',',':')) for r in docs[3]['rows']])
        lua.execute(ENGINE)
        for c in (1,3):
            g.systems[c].ready=False
            if not empty:g.files[names[c]]=raw[c]
        if extra:
            for k,v in extra.items():g.files[k]=v if isinstance(v,str) else json.dumps(v,separators=(',',':'))
        return lua,g
    def drive(g,n=650,drain=True):
        for _ in range(n):
            if drain:g.drain()
            g.events['onUpdate'](0.1)
        if drain:g.drain()
    def loaded(g):
        assert g.systems[3].loaded, [g.messages[i] for i in range(1,len(g.messages)+1)][-3:]
        assert g.finishes==1
    def check(name):checks.append(name)
    lua,g=setup();drive(g);loaded(g)
    assert g.systems[3].selected.token3==names[3][13:-5]  # snapshot_hs3_ prefix
    # Reassemble every transferred primitive to prove complete real data, not
    # merely the selected filename or a mock completion flag.
    for channel in (1,3):
        actual=[]
        for i in range(1,len(g.systems[3].packets[channel])+1):
            packet=g.systems[3].packets[channel][i]
            actual.extend(packet.data[j] for j in range(1,len(packet.data)+1))
        expected=[]
        for r in docs[channel]['rows']:
            if channel==1:
                expected.extend((int(r['stable']),int(r['legacy_pre_ending_certificate'])))
                for key in ('states','counters','optional','tracked','facts'):expected.extend(r[key])
            else:
                expected.extend([r[k] for k in ('state','counter','optional','tracked')] if r['definition']['kind']=='journal' else [r['value']])
                expected.append(int(r['stable']))
        assert actual==expected
    check('Actual captured exports selected; every transferred primitive matches all original rows and flags')
    assert g.systems[1].acks==g.systems[3].acks==0
    assert set(g.files.keys())==set(names.values());check('Loading does not rewrite existing exports or recapture current state')
    # Saved ready/frozen data are deliberately unavailable in the fixture.
    assert not g.systems[1].ready and not g.systems[3].ready
    check('File loading succeeds independently of saved ready/frozen flags and cached-array export readiness')
    newest='snapshot_hs3_20261112T200001Z_2_9.json'
    for kind in ('truncated','catalogue','definition','type','short_rows'):
        bad=deepcopy(docs[3]);bad['revision']=2
        if kind=='truncated':bad='{"schema":3'
        elif kind=='catalogue':bad['catalogue']='other'
        elif kind=='definition':bad['rows'][100]['definition']['path']='other/path'
        elif kind=='type':bad['rows'][5000]['value']='not an integer'
        else:bad['rows'].pop()
        lua,g=setup({newest:bad});drive(g,1000);loaded(g)
        assert g.systems[3].selected.token3==names[3][13:-5]
        check('Newest '+kind+' file rejected; previous complete valid capture selected')
    newer1='snapshot_hs1_20261112T193930Z_152_8.json'
    for kind in ('fallback','different_progress'):
        bad=deepcopy(docs[1]);bad['revision']=152
        if kind=='fallback':bad['origin']='post_ending_fallback'
        else:bad['rows'][0]['states'][0]=3 if bad['rows'][0]['states'][0]!=3 else 2
        lua,g=setup({newer1:bad});drive(g,750);loaded(g)
        assert g.systems[3].selected.token1==names[1][13:-5]
        check('Legacy '+kind+' file cannot be paired with the extended capture')
    new1,new3=deepcopy(docs[1]),deepcopy(docs[3]);new1['revision']=152;new3['revision']=2
    lua,g=setup({'snapshot_hs1_20261112T200000Z_152_8.json':new1,newest:new3});drive(g);loaded(g)
    assert g.systems[3].selected.revision==2 and g.systems[3].selected.legacyRevision==152
    check('Global newer complete capture wins without a character/save/run identity filter')
    lua,g=setup();g.files[names[1]]=None;drive(g,1000)
    assert not g.systems[3].loaded and g.begins==0 and g.systems[3].required
    check('No compatible legacy companion blocks publication and preserves the existing files')
    lua,g=setup();drive(g,300)
    assert g.begins==1 and g.finishes==0
    g.files[names[3]]=raw[3]+' '
    drive(g,320)
    assert g.finishes==0
    check('File bytes changing during transfer cannot publish the staged rows')
    for moment in (50,300):
        lua,g=setup();drive(g,moment)
        lua.execute('systems[3]=makeSystem(3,hs3count,"new loaded save");systems[3].ready=false;installReceiver()')
        drive(g,650);loaded(g)
        assert g.systems[3].selected.token3==names[3][13:-5]
        check(f'Same-epoch save switch after {moment} frames restarts validation/transfer with a new lease')
    lua,g=setup();drive(g,230)
    before=g.packetCalls;drive(g,100,drain=False)
    assert len(g.queue)<=1 and g.packetCalls<=before+1
    drive(g,650);loaded(g)
    check('A stalled simulation queue cannot accumulate repeated packet requests')
    lua,g=setup();g.systems[3].pending=True;drive(g,300)
    assert g.begins==0 and not g.systems[3].loaded
    g.systems[3].pending=False;drive(g);loaded(g)
    check('Unexported native capture blocks importing an older global snapshot')
    lua,g=setup();g.attached=False;drive(g,100);assert g.begins==0
    g.attached=True;g.pregame=True;drive(g,100);assert g.begins==0
    g.pregame=False;drive(g);loaded(g);check('Loading screen and pregame cannot access or publish the history')
    def cached_real(lua,g):
        for channel in (1,3):
            d=docs[channel];s=g.systems[channel];s.ready=True;s.revision=d['revision']
            header=json.dumps({k:v for k,v in d.items() if k!='rows'},separators=(',',':'))[:-1]+',"rows":['
            rows=[json.dumps(r,separators=(',',':')) for r in d['rows']]
            s.HeaderJSON=lambda self,header=header:header
            s.RowJSON=lambda self,i,rows=rows:rows[int(i)]
        lua.execute('os.date=function() return "20261112T200000Z" end')
    lua,g=setup(empty=True);cached_real(lua,g);drive(g,1150);loaded(g)
    assert g.systems[1].acks==g.systems[3].acks==1
    check('Missing files regenerate from intact saved data, then the generated latest capture is read back through the loader')
    lua,g=setup();cached_real(lua,g);g.systems[3].pending=True
    lua.execute('oldOpen=io.open;blockLegacy=true;io.open=function(name,mode) if blockLegacy and mode=="wb" and name:match("^snapshot_hs1_") then return nil end;return oldOpen(name,mode) end')
    drive(g,450)
    assert g.systems[3].acks==1 and g.systems[1].acks==0 and g.systems[3].pending and g.begins==0
    g.blockLegacy=False;drive(g,750);loaded(g)
    assert g.systems[1].acks==1 and not g.systems[3].pending
    check('Completed HS3 export cannot release the native-capture hold while the HS1 write still fails')
    write(out/'latest_fixtures.json',{'status':'PASS_ACTUAL_LUA_GLOBAL_LATEST_FIXTURES','count':len(checks),'checks':checks,
        'candidate_sha256':sha(source_path),'tool_sha256':sha(__file__),
        'source_exports':{name:sha(export/name) for name in names.values()},
        'limits':'Actual Lua and full real snapshot values; in-memory filesystem and queued engine doubles. No live REDscript execution or deployment claim.'})
    print(json.dumps({'status':'PASS_ACTUAL_LUA_GLOBAL_LATEST_FIXTURES','checks':len(checks)}))

if __name__=='__main__':main()
