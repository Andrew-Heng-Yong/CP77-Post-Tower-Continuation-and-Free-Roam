"""Offline LuaJIT controls, with independent installed receiver-class contract.
No game module loading, game API execution, real output log or save access.
"""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preflight import fresh_output
H=Path(__file__).resolve().parent
W=H.parents[1]
Q9=W/'prealpha/quest_restoration_qr9/worker_b'
sys.path.insert(0,str(Q9/'tooling'))
from lupa.luajit21 import LuaRuntime
REL=Path('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics')
NEW=H/'candidate_02'/REL
OLD=Q9/'addon'/REL

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def native(x):
    if hasattr(x,'items'):
        d={k:native(v)for k,v in x.items()}
        if d and set(d)==set(range(1,len(d)+1)):return[d[i]for i in range(1,len(d)+1)]
        return d
    return x

# Read only the old deterministic world stub expression, not its self-agreeing tests.
tree=ast.parse((Q9/'test_offline.py').read_text())
expr=next(x.value for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PRELUDE'for t in x.targets))
base=eval(compile(ast.Expression(expr),'<pinned fixture literals>','eval'),{'__builtins__':{}})
base=base.replace('^QR9_capture_','^QR[0-9]+_capture_')
CONTRACT=r'''
-- Contract constants are independently decoded from installed binaries, reviewed separately.
proxyClassFlags=2; registrationRequiresFlag=4; rejectedRegistrations=0; registerCalls=0; failFact=nil; badType=false
function NewProxy(spec)
 calls.proxy=(calls.proxy or 0)+1
 assert(type(spec.callback)=="function" and spec.args[1]=="Int32")
 return{Target=function()return{flags=proxyClassFlags,spec=spec}end,Function=function()return"Callback;Int32"end}
end
q.RegisterListener=function(self,n,p,f)
 registerCalls=registerCalls+1
 if math.floor(p.flags/registrationRequiresFlag)%2==0 then
  rejectedRegistrations=rejectedRegistrations+1;return 0
 end
 error("fixture cannot certify live callback dispatch")
end
q.UnregisterListener=function(self,n,id)unregs[#unregs+1]={name=n,id=id}end
q.GetFactStr=function(self,n)
 calls.fact=(calls.fact or 0)+1
 if failFact==n then error("fixture getter failure")end
 if badType then return "not an Int32"end
 return facts[n]or 0
end
setmetatable(q,{__index=function(t,k)error("UNSUPPORTED_OR_MUTATING_QUEST_API:"..k)end})
'''
def runtime(source,old=False,config=None):
    l=LuaRuntime(unpack_returned_tuples=True);g=l.globals()
    g.encodeJSON=lambda x:json.dumps(native(x),sort_keys=True,separators=(',',':'))
    g.decodeJSON=lambda x:l.table_from(json.loads(x),recursive=True)
    l.execute(base+CONTRACT)
    g.CONFIG=json.dumps(config)if config else ((OLD if old else NEW)/'watch.json').read_text()
    m=l.execute(source);g.callbacks['onInit']();return l,g,m
def rows(g,p):return [json.loads(x)for x in g.files[p].splitlines()]
def events(g,p,event):return[x for x in rows(g,p)if x['event']==event]
def tick(g,dt=2,wall=True):
    if wall:g.clock+=dt
    g.callbacks['onUpdate'](dt)

def checks(source):
    passed=[]
    def ck(name,value):assert value,name;passed.append(name)
    l,g,m=runtime(source)
    for _ in range(200):tick(g,.01)
    ck('inactive observer performs no game reads',g.calls.player is None and g.calls.fact is None)
    p=m.start('S00',None,120);tick(g)
    ck('main menu remains armed without quest reads',m.status()['state']=='ARMED_NO_PLAYER'and g.calls.quests is None)
    ck('waiting state deduplicated',len(events(g,p,'SESSION_WAIT'))==1)
    g.loaded();tick(g)
    ck('native-incompatible path never called',g.registerCalls==0 and g.calls.proxy is None)
    ck('unsupported capability explicit',len(events(g,p,'NATIVE_CALLBACK_UNAVAILABLE'))==1 and m.status()['native_callback_delivery']=='UNSUPPORTED_NATIVE_PROXY_RECEIVER')
    ck('baseline is not a transition',len(events(g,p,'FACT_SAMPLE_CHANGE'))==0 and events(g,p,'ATTACHED_BASELINE')[0]['data']['facts']['q307_finished']==0)
    g.facts['q307_finished']=1
    before=g.calls.fact;tick(g,1)
    ck('no per-frame fact polling',g.calls.fact==before)
    tick(g,1);ev=events(g,p,'FACT_SAMPLE_CHANGE')
    ck('external fact write sampled without callback',len(ev)==1 and ev[0]['data']['previous_sample']==0 and ev[0]['data']['current_sample']==1)
    ck('sample is not native event/order',not events(g,p,'FACT_DELIVERY')and 'not a native callback'in ev[0]['data']['evidence']and ev[0]['data']['detected_elapsed_s']>=ev[0]['data']['previous_success_elapsed_s'])
    tick(g);ck('stable fact emits no duplicate transition',len(events(g,p,'FACT_SAMPLE_CHANGE'))==1)
    g.facts['q307_finished']=2;g.facts['q307_finished']=3;tick(g)
    ck('intermediate writes not invented',events(g,p,'FACT_SAMPLE_CHANGE')[-1]['data']['current_sample']==3 and len(events(g,p,'FACT_SAMPLE_CHANGE'))==2)
    g.failFact='q307_finished';tick(g);tick(g)
    ck('getter errors bounded and no fabricated value',len(events(g,p,'FACT_SAMPLE_ERROR'))==1 and len(events(g,p,'FACT_SAMPLE_CHANGE'))==2)
    g.failFact=None;g.facts['q307_finished']=4;tick(g)
    ck('recovery preserves last successful value/gap',events(g,p,'FACT_SAMPLE_CHANGE')[-1]['data']['previous_sample']==3 and events(g,p,'FACT_SAMPLE_CHANGE')[-1]['data']['gap_contained_read_error']and len(events(g,p,'FACT_SAMPLE_RECOVERED'))==1)
    m.mark('synthetic_annotation');ck('manual annotation explicitly user evidence',len(events(g,p,'USER_MARK'))==1 and'not an automatic'in events(g,p,'USER_MARK')[0]['data']['interpretation'])
    m.stop();n=g.calls.fact
    for _ in range(10):tick(g)
    ck('stop clears sampling and needs no unsubscribe',g.calls.fact==n and len(g.unregs)==0 and m.status()['state']=='NOT_RUNNING')
    ck('stop accounts getter/sample budget',events(g,p,'STOP')[0]['data']['fact_getter_calls']==n and events(g,p,'CAPTURE_CLEANUP')[0]['data']['native_subscriptions_created']==0)
    p2=m.start('S00',None,120);ck('new capture has fresh baseline/path',p2!=p and len(events(g,p2,'FACT_SAMPLE_CHANGE'))==0 and m.status()['sample_rounds']==0);m.stop()
    for reason in ('detach','pregame','identity','shutdown'):
        l,g,m=runtime(source);g.loaded();p=m.start('S00')
        if reason=='detach':g.hooks['PlayerPuppet.OnDetach'](g.player)
        elif reason=='pregame':g.pregame=True;tick(g)
        elif reason=='identity':g.ident='otherPlayer';tick(g)
        else:g.callbacks['onShutdown']()
        ck('lifecycle stops:'+reason,m.status()['state']=='NOT_RUNNING'and len(events(g,p,'STOP'))==1)
        n=g.calls.fact;g.loaded();tick(g);ck('no auto resume:'+reason,g.calls.fact==n and m.status()['state']=='NOT_RUNNING')
    l,g,m=runtime(source);g.loaded();p=m.start('S00',None,1);tick(g)
    ck('wall duration cap',m.status()['state']=='NOT_RUNNING'and events(g,p,'STOP')[0]['data']['reason']=='DURATION_LIMIT')
    l,g,m=runtime(source);g.loaded();p=m.start('S00',None,900)
    for _ in range(451):tick(g,2,False)
    ck('sample-round cap independent of frozen wall clock',m.status()['state']=='NOT_RUNNING'and g.calls.fact<=17*451 and events(g,p,'STOP')[0]['data']['reason']=='SAMPLE_ROUND_LIMIT')
    l,g,m=runtime(source);g.loaded();p=m.start('S00',None,900)
    for i in range(2500):
        for n in json.loads((NEW/'watch.json').read_text())['profiles']['S00']['facts']:g.facts[n]=i
        tick(g,2,False)
    rr=rows(g,p)
    ck('event storm bounded and closes sampling',len(rr)<=2048 and m.status()['state']=='NOT_RUNNING'and sum(len(x)+1 for x in g.files[p].splitlines())<=8388608)
    ck('JSONL sequenced per capture',all(x['seq']==i+1 and x['run_id']==p for i,x in enumerate(rr)))
    l,g,m=runtime(source);g.loaded();p=m.start('S00');n=g.calls.fact
    for dt in (-1,float('nan'),float('inf')):tick(g,dt,False)
    ck('invalid update deltas do not sample',g.calls.fact==n)
    l,g,m=runtime(source);g.loaded();g.badType=True
    ck('invalid baseline getter fails closed',m.start('S00')is None and m.status()['state']=='NOT_RUNNING')
    l,g,m=runtime(source);g.failOpen=True;ck('log-open failure never attaches',m.start('S00')is None and g.calls.quests is None)
    l,g,m=runtime(source);g.loaded();g.failWrite=True;ck('log-write failure never attaches',m.start('S00')is None and g.calls.quests is None)
    config=json.loads((NEW/'watch.json').read_text());config['profiles']['S00']['facts'].append('q307_finished')
    l,g,m=runtime(source,config=config);ck('duplicate watch names rejected',m.start('S00')is None)
    for p in json.loads((NEW/'watch.json').read_text())['profiles']:
        l,g,m=runtime(source);g.loaded();path=m.start(p);ck('profile lifecycle:'+p,m.status()['state']=='RECORDING'and 1<=g.calls.fact<=96);m.stop()
    return passed

def main():
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=fresh_output(a.out);out.mkdir()
    before=(OLD/'init.lua').read_text();after=(NEW/'init.lua').read_text()
    l,g,m=runtime(before,True);g.loaded();p=m.start('S00');g.facts['q307_finished']=1;tick(g)
    before_control={'source_sha256':sha(OLD/'init.lua'),'rejected_native_proxy_registrations':g.rejectedRegistrations,
        'reported_registration_count':events(g,p,'LISTENER_CALLS_COMPLETED')[0]['data']['returned_ids'],
        'FACT_DELIVERY_count':len(events(g,p,'FACT_DELIVERY')),'fact_now':g.facts['q307_finished'],
        'silent_coverage_gap_reproduced':len(events(g,p,'FACT_DELIVERY'))==0 and g.rejectedRegistrations==17}
    assert before_control['silent_coverage_gap_reproduced'];m.stop()
    passed=checks(after)
    mutations=[('sampling removed','  sampleFacts()','  -- sampleFacts()'),
        ('wrong diff condition','if sampled[name]~=value then','if sampled[name]==value then'),
        ('native mislabelling','emit("FACT_SAMPLE_CHANGE"','emit("FACT_DELIVERY"'),
        ('round cap removed','sampleRounds >= MAX_SAMPLE_ROUNDS','sampleRounds >= 999999'),
        ('auto resume after session loss','M.stop("SESSION_GUARD_CHANGED_NO_AUTO_RESUME"); return','return'),
        ('duplicate validation removed',' or seen[n]','')]
    detected=[]
    for label,old,new in mutations:
        assert after.count(old)==1,label
        try:checks(after.replace(old,new))
        except AssertionError as e:detected.append({'mutant':label,'detected_by':str(e)})
        else:raise AssertionError('undetected mutant:'+label)
    report={'status':'PASS_OFFLINE_ONLY','before_control':before_control,'after_source_sha256':sha(NEW/'init.lua'),
        'passed_checks':passed,'mutations_detected':detected,
        'native_delivery':'UNSUPPORTED_RECEIVER_NOT_VERIFIED','live_sampling':'NOT_TESTED',
        'limits':'Synthetic Lua world; independent class-flag contract from exact installed binary review. No engine dispatch, frame scheduling, real getter latency or gameplay proof.'}
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print({'status':report['status'],'checks':len(passed),'mutations':len(detected),'before_rejected':before_control['rejected_native_proxy_registrations']})

if __name__=='__main__':main()
