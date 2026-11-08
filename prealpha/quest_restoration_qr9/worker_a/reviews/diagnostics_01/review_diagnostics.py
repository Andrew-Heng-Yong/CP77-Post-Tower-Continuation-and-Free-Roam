"""Independent source review and Lua API doubles. Does not load CET or game DLLs."""
from pathlib import Path
import sys,json,hashlib,re
H=Path(__file__).resolve().parent
W=H.parents[2]
B=W/'worker_b'
sys.path.insert(0,str(B/'tooling'))
from lupa.luajit21 import LuaRuntime
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def value(x):
    if hasattr(x,'items'):
        d={k:value(v) for k,v in x.items()}
        return [d[i] for i in range(1,len(d)+1)] if d and set(d)==set(range(1,len(d)+1)) else d
    return x
addon=B/'addon/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics'
src=(addon/'init.lua').read_text()
cfg=json.loads((addon/'watch.json').read_text())
checks=[]
def ck(name,ok):
    assert ok,name
    checks.append(name)
ck('frozen manifest identity',sha(B/'addon_manifest_04.json')=='59B3CE96220B807D87AF67B66A47ED02549D66B59A5BEA8F620C2910D55C0580')
ck('frozen code identity',sha(addon/'init.lua')=='ACCE8B7E4E1E355BBC6D6F4752FDBCC7BB3034F594B13AB055EC35742D333718')
ck('frozen configuration identity',sha(addon/'watch.json')=='AEC4D4921AC64B0C37006E7839DD3F9466457B44A735DFFD4637C4261D5EAED2')
ck('no mutating engine API vocabulary',not re.search(r'\b(?:SetFact\w*|ForceStart\w*|Override|SaveGame|ChangeEntryState|SetEntryState|AddToInventory|ResetKillCount)\s*\(',src))
ck('exact nine profiles and bounded valid fact names',set(cfg['profiles'])=={f'S{i:02}' for i in range(9)} and all(1<=len(p['facts'])<=96 and all(re.fullmatch('[A-Za-z0-9_]{1,128}',n)for n in p['facts'])for p in cfg['profiles'].values()))
PRE=r'''
now=1000; ready=true; apiReads=0; factReads=0; nextId=0; callbacks={}; hooks={}; subscriptions={}; removed={}; files={}; delivered={}; knownFacts={}
json={encode=encodeJson,decode=decodeJson}; os={time=function()return now end,date=function()return '20300101T000000Z'end}
function print()end
function IsDefined(x)return type(x)=='table'end
function registerForEvent(n,f)callbacks[n]=f end
function ObserveBefore(c,n,f)assert(c=='PlayerPuppet' and n=='OnDetach');hooks.detach=f end
CName={new=function(x)return x end};TweakDBID={new=function(x)return x end}
function NewProxy(s)return{Target=function()return s end,Function=function()return 'callback'end}end
io={open=function(p,mode)
 if p=='watch.json' then assert(mode=='rb');return{read=function()return configText end,close=function()return true end}end
 assert(mode=='a+' and p:match('^QR9_capture_[A-Za-z0-9_]+%.jsonl$'),'unexpected file access')
 files[p]=files[p]or''
 return{seek=function()return #files[p]end,write=function(self,s)files[p]=files[p]..s;return self end,flush=function(self)return self end,close=function()return true end}
end}
player={IsAttached=function()return true end,GetEntityID=function()return{hash='independent_player'}end}
quest={GetFactStr=function(self,n)factReads=factReads+1;return knownFacts[n]or 0 end,
 RegisterListener=function(self,n,proxy,method)assert(method=='callback'and proxy.args[1]=='Int32');local id=nextId;nextId=nextId+1;subscriptions[id]={name=n,callback=proxy.callback};return id end,
 UnregisterListener=function(self,n,id)assert(subscriptions[id]and subscriptions[id].name==n);removed[#removed+1]=id;subscriptions[id].callback(999);subscriptions[id]=nil end}
Game={GetPlayer=function()apiReads=apiReads+1;if ready then return player end end,
 GetSystemRequestsHandler=function()return{IsPreGame=function()return not ready end}end,
 GetQuestsSystem=function()return quest end,
 GetJournalManager=function()return{GetEntryByString=function(self,p,c)return{}end,GetEntryState=function()return 'Active'end}end,
 GetPhoneManager=function()return{IsPhoneCallActive=function()return false end}end,
 GetVehicleSystem=function()return{IsVehiclePlayerUnlocked=function()return false end}end}
setmetatable(Game,{__index=function(t,k)error('unexpected game API:'..k)end})
function listenerCount()local n=0;for _,s in pairs(subscriptions)do n=n+1 end;return n end
'''
def runtime():
    l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
    g.encodeJson=lambda x:json.dumps(value(x),sort_keys=True,separators=(',',':'))
    g.decodeJson=lambda s:l.table_from(json.loads(s),recursive=True)
    l.execute(PRE);g.configText=json.dumps(cfg);m=l.execute(src);return l,g,m
def rows(g,p):return [json.loads(x)for x in g.files[p].splitlines()]
l,g,m=runtime()
g.callbacks.onInit()
for _ in range(100):g.callbacks.onUpdate(1)
ck('inactive module never reads game state',g.apiReads==0 and g.factReads==0)
g.files['QR9_capture_20300101T000000Z_0001.jsonl']='EXISTING_USER_LOG\n'
p=m.start('S00','independent',20)
ck('existing log is never truncated or reused',p.endswith('0002.jsonl') and g.files['QR9_capture_20300101T000000Z_0001.jsonl']=='EXISTING_USER_LOG\n')
ck('exact listener IDs including zero retained',g.listenerCount()==len(cfg['profiles']['S00']['facts']) and g.subscriptions[0] is not None)
initial=rows(g,p)[0]['data']
ck('source signals never become execution or installed hash claims',all(initial[k]=='NOT_OBSERVED'for k in ['actual_graph_activation','native_owner','ArchiveXL_engine_receipt','save_identity','actual_installed_core_hashes','startup_before_command']))
reads=g.factReads
for _ in range(8):g.callbacks.onUpdate(2)
ck('fact reads are not a polling fallback',g.factReads==reads)
saved=g.subscriptions[0].callback
m.stop('independent stop')
ck('cleanup removes exact IDs and callback reentry is ignored',g.listenerCount()==0 and len(g.removed)==len(cfg['profiles']['S00']['facts']) and not any(r['event']=='FACT_DELIVERY'for r in rows(g,p)))
p2=m.start('S00','second',20);n=len(rows(g,p2));saved(321)
ck('stale callback cannot reach successor log',len(rows(g,p2))==n)
g.now=1030;g.callbacks.onUpdate(2)
ck('deadline stops and releases all transient registrations',m.status()['state']=='NOT_RUNNING' and g.listenerCount()==0)
l,g,m=runtime();g.ready=False;p=m.start('S00')
ck('main-menu command remains armed without reading quest facts',m.status()['state']=='ARMED_NO_PLAYER' and g.factReads==0)
g.ready=True;g.callbacks.onUpdate(2);g.ready=False;g.callbacks.onUpdate(2)
ck('observed session loss stops without automatic resume',m.status()['state']=='NOT_RUNNING' and g.listenerCount()==0)
g.ready=True;g.callbacks.onUpdate(2)
ck('later attach does not automatically restart capture',m.status()['state']=='NOT_RUNNING' and g.listenerCount()==0)
out=H/'result.json';assert not out.exists()
result=dict(status='PASS_INDEPENDENT_SOURCE_AND_LUA_DOUBLES_NOT_GAMEPLAY',checks=checks,assertions=len(checks),source_sha256=sha(addon/'init.lua'),config_sha256=sha(addon/'watch.json'),reviewer='A independent of B implementation',real_game_calls=0,CET_loaded=False,limits=['API double results do not prove current CET binding or runtime listener delivery.','Player entity ID is not save identity; deliberate load requires manual stop.','No native owner, graph activation, ArchiveXL receipt, saved timer or pending phone queue is observed.'])
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],assertions=len(checks),sha256=sha(out))))
