"""Standalone LuaJIT fixtures. Never imports/loads CET or the game process."""
from pathlib import Path
import sys,json,re,hashlib,argparse,copy
W=Path(__file__).resolve().parents[3];H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'tooling'))
from lupa.luajit21 import LuaRuntime
ADDON=H/'addon/bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def native(x):
 if hasattr(x,'items'):
  d={k:native(v)for k,v in x.items()}
  if d and set(d)==set(range(1,len(d)+1)):return[d[i]for i in range(1,len(d)+1)]
  return d
 return x
PRELUDE=r'''
clock=1000; files={}; callbacks={}; hooks={}; listeners={}; oldCallbacks={}; facts={}; unregs={}; calls={}; counter=0
pregame=true; missingPlayer=true; failListener=nil; failUnregister=false; failPhone=false; failOpen=false; failWrite=false; ident="playerA"
json={encode=encodeJSON,decode=function(text)return decodeJSON(text)end}
os={time=function()return clock end,date=function()return "20300101T000000Z"end}
function print(s) end
function registerForEvent(n,f)callbacks[n]=f end
function ObserveBefore(c,m,f)hooks[c.."."..m]=f end
function IsDefined(x)return type(x)=="table"end
CName={new=function(x)return x end}
TweakDBID={new=function(x)return x end}
function NewProxy(spec)return{Target=function()return spec end,Function=function()return "Callback"end}end
io={open=function(p,mode)
 if p=="watch.json"and mode=="rb"then return{read=function()return CONFIG end,close=function()return true end}end
 assert(p:match("^QR9_capture_[A-Za-z0-9_]+%.jsonl$")and mode=="a+","unexpected file operation")
 if failOpen then return nil,"fixture open failure"end
 files[p]=files[p]or""
 return{seek=function()return #files[p]end,write=function(self,s)if failWrite then return nil end;files[p]=files[p]..s;return self end,flush=function(self)return self end,close=function()return true end}
end}
player={IsAttached=function()return true end,GetEntityID=function()return{hash=ident}end}
q={GetFactStr=function(self,n)calls.fact=(calls.fact or0)+1;return facts[n]or0 end,
 RegisterListener=function(self,n,p,f)
  assert(f=="Callback"and p.args[1]=="Int32");if n==failListener then error("fixture listener failure")end
  local id=counter;counter=counter+1;listeners[n]={callback=p.callback,id=id};oldCallbacks[#oldCallbacks+1]=p.callback;return id
 end,
 UnregisterListener=function(self,n,id)
  if failUnregister then error("fixture unregister failure")end
  assert(listeners[n]and listeners[n].id==id,"wrong listener ID");listeners[n].callback(0);listeners[n]=nil;unregs[#unregs+1]={name=n,id=id}
 end}
Game={
 GetPlayer=function()calls.player=(calls.player or0)+1;if not missingPlayer then return player end end,
 GetSystemRequestsHandler=function()return{IsPreGame=function()return pregame end}end,
 GetQuestsSystem=function()calls.quests=(calls.quests or0)+1;return q end,
 GetJournalManager=function()return{GetEntryByString=function(self,p,c)return{path=p}end,GetEntryState=function()return"gameJournalEntryState.Active"end}end,
 GetPhoneManager=function()if failPhone then error("fixture phone getter unavailable")end;return{IsPhoneCallActive=function()return false end}end
 ,GetVehicleSystem=function()return{IsVehiclePlayerUnlocked=function(self,record)return record=="Vehicle.v_sportbike1_yaiba_kusanagi_player"end}end
}
setmetatable(Game,{__index=function(t,k)error("UNSUPPORTED_OR_MUTATING_GAME_API:"..k)end})
function loaded()missingPlayer=false;pregame=false end
function countListeners()local n=0;for _in pairs(listeners)do n=n+1 end;return n end
'''.replace('or0','or 0').replace('for _in','for _ in')
def runtime(source):
 l=LuaRuntime(unpack_returned_tuples=True);g=l.globals();g.encodeJSON=lambda x:json.dumps(native(x),sort_keys=True,separators=(',',':'));g.decodeJSON=lambda x:l.table_from(json.loads(x),recursive=True);l.execute(PRELUDE);g.CONFIG=(ADDON/'watch.json').read_text(encoding='utf-8');m=l.execute(source);g.module=m;g.callbacks['onInit']();return l,g,m
def logrows(g,p):return[json.loads(x)for x in g.files[p].splitlines()]
def fixtures(source):
 passed=[]
 def ck(n,v):assert v,n;passed.append(n)
 l,g,m=runtime(source)
 for _inrange in range(1000):g.callbacks['onUpdate'](.01)
 ck('inactive module performs zero game API reads',g.calls.player is None and g.calls.fact is None)
 p=m.start('S00');ck('main-menu start arms without quest-system calls',m.status()['state']=='ARMED_NO_PLAYER'and g.calls.quests is None)
 ck('normal waiting reason is explicit and deduplicated',m.status()['last_wait_reason'].startswith('Game.GetPlayer:')and sum(r['event']=='SESSION_WAIT'for r in logrows(g,p))==1)
 g.callbacks['onUpdate'](2);ck('steady main-menu waiting never floods',sum(r['event']=='SESSION_WAIT'for r in logrows(g,p))==1)
 g.loaded();g.callbacks['onUpdate'](2);ck('normal attached baseline registers exact17facts including listenerID0',m.status()['state']=='RECORDING'and g.countListeners()==17 and min(v.id for _,v in g.listeners.items())==0)
 baseline=logrows(g,p);ck('initial fact values labeled baseline not transitions',baseline[0]['event']=='CAPTURE_START'and next(x for x in baseline if x['event']=='ATTACHED_BASELINE')['data']['interpretation'].startswith('initial values'))
 n='q307_finished';g.facts[n]=2;g.listeners[n].callback(1);r=logrows(g,p)[-1];ck('callback delivery distinguished from later current DB value',r['data']['callback_value']==1 and r['data']['current_db']==2 and r['data']['previous_observed']==0 and r['data']['delivery_differs_from_current'])
 freads=g.calls.fact
 for _inrange in range(300):g.callbacks['onUpdate'](.02)
 ck('no per-frame fact polling fallback',g.calls.fact==freads)
 g.failPhone=True;g.callbacks['onUpdate'](2);count=len(logrows(g,p));g.callbacks['onUpdate'](2);ck('stable missing getter error logged once and remains unobserved',len(logrows(g,p))==count and logrows(g,p)[-1]['data']['phone_active']=='NOT_OBSERVED')
 m.mark('visible_call');ck('mark is user annotation only',any(r['event']=='USER_MARK'and'not an automatic'in r['data']['interpretation']for r in logrows(g,p)))
 stale=g.oldCallbacks[1];m.stop();ck('stop unsubscribes exact17IDs and ignores callbacks during cleanup',len(g.unregs)==17 and g.countListeners()==0 and m.status()['state']=='NOT_RUNNING')
 p2=m.start('S00');num=len(logrows(g,p2));stale(99);ck('old generation callback cannot contaminate new capture',p2!=p and len(logrows(g,p2))==num);m.stop()
 l,g,m=runtime(source);g.loaded();p=m.start('S01');g.hooks['PlayerPuppet.OnDetach'](g.player);ck('observed detach closes subscriptions',m.status()['state']=='NOT_RUNNING'and g.countListeners()==0 and any(r['event']=='STOP'and'PLAYER_DETACH'in r['data']['reason']for r in logrows(g,p)))
 l,g,m=runtime(source);g.loaded();p=m.start('S02');g.pregame=True;g.callbacks['onUpdate'](2);ck('observed load guard stops without automatic resume',m.status()['state']=='NOT_RUNNING'and g.countListeners()==0);g.loaded();g.callbacks['onUpdate'](2);ck('load never auto-rearms capture',g.countListeners()==0)
 l,g,m=runtime(source);g.loaded();p=m.start('S00',None,1);g.clock=1002;g.callbacks['onUpdate'](.1);ck('duration cap closes log and everylistener',m.status()['state']=='NOT_RUNNING'and g.countListeners()==0 and any(r['event']=='STOP'and r['data']['reason']=='DURATION_LIMIT'for r in logrows(g,p)))
 l,g,m=runtime(source);g.loaded();p=m.start('S00');cb=g.listeners['q307_finished'].callback
 for i in range(2300):cb(i)
 rs=logrows(g,p);ck('event storm bound2048rows and cleanup',len(rs)<=2048 and g.countListeners()==0 and m.status()['state']=='NOT_RUNNING');ck('sequential JSONL with one capture ID',all(r['seq']==i+1 and r['run_id']==p for i,r in enumerate(rs)))
 l,g,m=runtime(source);g.loaded();g.failListener='q307_finished';p=m.start('S00');ck('partial listener setup fails closed and cleans priorIDs',p is None and m.status()['state']=='NOT_RUNNING'and g.countListeners()==0 and any(r['event']=='LISTENER_CALL_FAILED'for r in logrows(g,m.status()['path'])))
 l,g,m=runtime(source);g.loaded();g.Game.GetSystemRequestsHandler=lambda:None;p=m.start('S00');ck('missing context getter yields actionable bounded waiting reason','IsPreGame:'in m.status()['last_wait_reason']and sum(r['event']=='SESSION_WAIT'for r in logrows(g,p))==1);m.stop()
 l,g,m=runtime(source);g.loaded();g.player.GetEntityID=lambda self:None;p=m.start('S00');ck('missing entity identity never attaches under NOT_OBSERVED placeholder',m.status()['state']=='ARMED_NO_PLAYER'and'GetEntityID:'in m.status()['last_wait_reason']and g.countListeners()==0);m.stop()
 l,g,m=runtime(source);g.loaded();p=m.start('S00');g.failUnregister=True;m.stop();ck('unsubscribe failure blocks subsequent start',m.status()['cleanup_failed']and m.start('S00')is None)
 l,g,m=runtime(source);g.loaded();p=m.start('S08');g.failUnregister=True;cb=g.listeners['q307_finished'].callback
 for i in range(2300):cb(i)
 ck('combined event storm and all unsubscribe failures stay bounded',len(logrows(g,p))<=2048 and m.status()['cleanup_failed']and m.status()['state']=='NOT_RUNNING')
 l,g,m=runtime(source);g.loaded();p=m.start('S03');rr=next(r for r in logrows(g,p)if r['event']=='ATTACHED_STATE');ck('four typed vehicles read separately from facts with no eligibility claim',len(rr['data']['vehicle_unlock'])==4 and rr['data']['vehicle_unlock']['Vehicle.v_sportbike1_yaiba_kusanagi_player']is True and rr['data']['actual_graph_activation']=='NOT_OBSERVED');m.stop()
 l,g,m=runtime(source);g.failOpen=True;ck('file open failure stays inactive',m.start('S00')is None and m.status()['state']=='NOT_RUNNING');g.failOpen=False;g.failWrite=True;ck('initial write failure closes without registering APIs',m.start('S00')is None and g.countListeners()==0)
 l,g,m=runtime(source);g.loaded();p=m.start('S00');g.callbacks['onShutdown']();ck('normal shutdown unsubscribes',m.status()['state']=='NOT_RUNNING'and g.countListeners()==0);oldfiles=dict(g.files.items());m2=l.execute(source);g.callbacks['onInit']();p2=m2.start('S00');ck('module reload never truncates existing capture',p2!=p and g.files[p]==oldfiles[p]);m2.stop()
 ck('invalid profile rejected',m.start('UNKNOWN')is None);ck('invalid duration rejected',m.start('S00',None,901)is None and m.start('S00',None,-1)is None)
 for profile in('S00','S01','S02','S03','S04','S05','S06','S07','S08'):
  l,g,m=runtime(source);g.loaded();p=m.start(profile);ck('profile-budget-and-start-stop:'+profile,m.status()['state']=='RECORDING'and 0<g.countListeners()<=96);m.stop()
 # Return a representative SYNTHETIC artifact, never labeled observed gameplay.
 return passed,rs
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);source=(ADDON/'init.lua').read_text(encoding='utf-8');checks,rows=fixtures(source)
 assert not re.search(r'\b(?:SetFact\w*|Override|ForceStart\w*|SaveGame|ChangeEntryState|SetEntryState|AddToInventory)\s*\(',source)
 mutations=[('setter-added',source.replace('quests:GetFactStr(captured)','quests:SetFactStr(captured,1)',1)),('old-callback-generation-guard-removed',source.replace(' or generation ~= gen','')),('cleanup-call-replaced',source.replace('quests:UnregisterListener(CName.new(r.name),r.id)','quests:GetFactStr(r.name)')),('duration-bound-increased',source.replace('seconds>900','seconds>90000')),('event-cap-removed',source.replace('rows >= MAX_ROWS-4 or ','',1))]
 controls=[]
 for n,s in mutations:
  try:
   if re.search(r'\bSetFact\w*\s*\(',s):raise AssertionError('forbidden setter')
   fixtures(s)
  except (AssertionError,Exception)as e:controls.append({'fault':n,'detected':True,'failure':str(e)[:240]})
  else:controls.append({'fault':n,'detected':False})
 assert all(c['detected']for c in controls)
 import lupa,importlib.metadata
 tooling={'version':importlib.metadata.version('lupa'),'path':lupa.__file__,'Lua':LuaRuntime().eval('_VERSION'),'LuaJIT':LuaRuntime().eval('jit.version'),'files':[{'path':str(p),'sha256':sha(p)}for p in sorted((H/'tooling/lupa').glob('*luajit21*.pyd'))],'origin':'Official PyPI lupa2.8 wheel installed to private target via uv; no global/game install.'}
 result={'status':'PASS_OFFLINE_LUAJIT_FIXTURES_NOT_RUNTIME_TESTED','assertions':checks,'assertion_count':len(checks),'actual_Lua_source_mutants':controls,'code_sha256':sha(ADDON/'init.lua'),'config_sha256':sha(ADDON/'watch.json'),'tooling':tooling,'no_real_Game_API_calls':True,'no_CET_DLL_loaded':True,'runtime_or_gameplay_execution':False,'limits':['API doubles prove logger logic, not actual game API exposure, callbacks or cleanup delivery.','Player entity hash is not a save identity. Stop before intentional load; only observed detach/pregame/identity changes can auto-stop.','No actual graph/native owner/ArchiveXL engine receipt/saved timer/phone queue observation is provided.']}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(out/'SYNTHETIC_events.jsonl').write_text(''.join(json.dumps(r)+'\n'for r in rows),encoding='utf-8');print(result['status'],len(checks),'assertions',len(controls),'source mutants')
if __name__=='__main__':main()
