"""Additional adversarial cases for actual QR10 Lua; synthetic world, not gameplay."""
from pathlib import Path
import importlib.util,json,sys
H=Path(__file__).resolve().parent
Q10=H.parent
spec=importlib.util.spec_from_file_location('qr10_controls',Q10/'test_diagnostics.py')
controls=importlib.util.module_from_spec(spec);spec.loader.exec_module(controls)

def main():
 source=(controls.NEW/'init.lua').read_text();passed=[]
 def ck(name,value):assert value,name;passed.append(name)
 config=json.loads((controls.NEW/'watch.json').read_text())
 config['profiles']['D00']['facts']=['fixture_'+str(i)for i in range(96)]
 l,g,m=controls.runtime(source,config=config);g.loaded();p=m.start('D00',None,900)
 ck('exact96-fact baseline bounded',g.calls.fact==96)
 controls.tick(g,200,False)
 ck('large update samples one pass without catchup',g.calls.fact==192 and m.status()['sample_rounds']==1)
 m.stop();n=len(controls.rows(g,p));m.stop()
 ck('repeat stop does not append or resubscribe',len(controls.rows(g,p))==n and g.registerCalls==0)
 config['profiles']['D00']['facts'].append('fixture_96')
 l,g,m=controls.runtime(source,config=config)
 ck('97-fact profile fails before any quest API',m.start('D00')is None and g.calls.quests is None)
 l,g,m=controls.runtime(source);g.loaded();p=m.start('S00')
 g.facts['q307_finished']=1;g.facts['q307_finished']=0;controls.tick(g)
 ck('reverted intermediate values are not fabricated',not controls.events(g,p,'FACT_SAMPLE_CHANGE'))
 g.badType=True;controls.tick(g);controls.tick(g)
 ck('invalid later Int32 produces one error per fact',len(controls.events(g,p,'FACT_SAMPLE_ERROR'))==17 and not controls.events(g,p,'FACT_SAMPLE_CHANGE'))
 g.badType=False;controls.tick(g)
 ck('same-value recovery is separate from transition',len(controls.events(g,p,'FACT_SAMPLE_RECOVERED'))==17 and not controls.events(g,p,'FACT_SAMPLE_CHANGE'))
 g.facts['q307_finished']=-2147483648;controls.tick(g)
 ev=controls.events(g,p,'FACT_SAMPLE_CHANGE')
 ck('negative native Int32 is retained',len(ev)==1 and ev[-1]['data']['current_sample']==-2147483648)
 g.facts['q307_finished']=2147483648;controls.tick(g)
 ck('overflow is error and retains last native value',len(controls.events(g,p,'FACT_SAMPLE_CHANGE'))==1)
 g.facts['q307_finished']=2147483647;controls.tick(g)
 ev=controls.events(g,p,'FACT_SAMPLE_CHANGE')[-1]
 ck('signed maximum after error retains provenance',ev['data']['current_sample']==2147483647 and ev['data']['previous_sample']==-2147483648 and ev['data']['gap_contained_read_error'])
 n=g.calls.fact;g.missingPlayer=True;controls.tick(g)
 ck('missing player stops before further fact getters',m.status()['state']=='NOT_RUNNING'and g.calls.fact==n)
 ck('no callback-shaped event labels',not any(r['event']in('FACT_DELIVERY','FACT_CALLBACK','LISTENER_CALLS_COMPLETED')for r in controls.rows(g,p)))
 ck('source has no rejected observer API calls',not any(k in source for k in('NewProxy(',':RegisterListener(',':UnregisterListener(',':SetFact',':ExecuteNode(')))
 l,g,m=controls.runtime(source);g.loaded();p=m.start('S00');config_calls=g.calls.fact
 ck('start while recording preserves capture',m.start('UNKNOWN')==p and g.calls.fact==config_calls)
 old=g.files[p];m.stop();p2=m.start('D00')
 ck('restart preserves old append-only log',p2!=p and g.files[p].startswith(old))
 m.stop()
 result={'status':'PASS_ADDITIONAL_OFFLINE_REVIEW','candidate_lua_sha256':controls.sha(controls.NEW/'init.lua'),
 'checks':passed,'native_delivery':'NOT_TESTED_UNSUPPORTED_RECEIVER','live_sampling':'NOT_TESTED',
 'limits':'Reuses the primary deterministic API double but adds independent boundary assertions; exact binary contract is separately proven by reviewer scripts. Not engine/gameplay proof.'}
 dest=H/'successor_controls_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({'status':result['status'],'checks':len(passed),'lua_sha256':result['candidate_lua_sha256']})

if __name__=='__main__':main()
