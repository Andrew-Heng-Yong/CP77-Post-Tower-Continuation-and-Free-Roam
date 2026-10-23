"""Exact scope/guard audit and Lua bridge tests; not REDengine execution."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.lua51 import LuaRuntime
from prepare_tower_journal import BASE, GUARDS, MUTABLE, SOURCE, find, inventory

CORE = ROOT/'redscript/PTFR_TowerJournal/TowerJournalCleanup.reds'
LUA = ROOT/'diagnostics/PTFR_TowerJournal/init.lua'
AUDIT = ROOT/'research/tower_journal_cleanup'

def scope():
    manifest = json.loads((AUDIT/'manifest.json').read_text())
    expected = inventory(find(json.loads(SOURCE.read_text(encoding='utf-8-sig')))[0], 'ep1/quests/main_quest')
    assert manifest['rows'] == expected
    assert len(expected) == 88 and sum(r['mutable'] for r in expected) == 23
    assert all(r['path'] == BASE or r['path'].startswith(BASE+'/') for r in expected)
    assert {r['className'] for r in expected if r['mutable']} == MUTABLE
    text = CORE.read_text()
    assert hashlib.sha256(CORE.read_bytes()).hexdigest() == manifest['redscript_sha256']
    actual = {name:int(value) for name,value in re.findall(r'if q.GetFact\(n"([^"]+)"\) != (\d+) \{ return false; \}',text)}
    assert actual == GUARDS
    assert re.findall(r'j\.(Change\w+|Untrack\w+|Track\w+)\(',text) == ['ChangeEntryState','UntrackEntry']
    assert not re.search(r'\.(SetFact|DeleteScriptedQuest|SetEntryVisited|TrackEntry|ChangeEntryStateByHash)\(',text)
    assert 'JournalNotifyOption.DoNotNotify' in text
    assert 'this.rows[i].mutable && Equals(j.GetEntryState(this.rows[i].entry),gameJournalEntryState.Active)' in text
    assert text.index('if this.TowerTracked(j) {') < text.index('j.UntrackEntry();')
    assert 'this.attempted = true;' in text and 'this.waiting = i;' in text
    assert text.index('this.waiting = i;') < text.index('j.ChangeEntryState(')
    assert 'PARTIAL_TIMEOUT_NO_RETRY' in text and 'INACTIVE_FAILED_OR_COMPLETE_STATE_CHANGED' in text
    assert 'this.player.GetGame()).DelayCallback' in text
    assert 'extends ScriptableSystem' not in text and '@wrapMethod' not in text
    assert not re.search(r':(?:ChangeEntryState|UntrackEntry|SetFact|ExecutePSAction|Teleport)\(',LUA.read_text())
    # The deny cases are derived from emitted guards, not claimed native tests.
    negatives=0
    for name,wanted in GUARDS.items():
        for wrong in (-1,0,1,2):
            if wrong == wanted: continue
            candidate=dict(GUARDS);candidate[name]=wrong
            assert not all(candidate[n]==v for n,v in actual.items())
            negatives+=1
    return negatives

SETUP = '''
events={};rows={};calls={};say={};writes={};failed_event=nil;last_event=nil
function print(s) say[#say+1]=s end
function IsDefined(x) return type(x)=="table" end
function registerForEvent(n,f) events[n]=f end
json={encode=function(row) rows[#rows+1]=row;last_event=row.event;return row.event end}
io={open=function(name,mode)
 if mode=="r" then return nil end
 return {write=function(self,line)
   if failed_event==last_event then return nil,"MOCK disk failure" end
   writes[#writes+1]=line;return self end,
   flush=function() return true end,close=function() return true end}
end}
player={}
Game={GetPlayer=function() return player end,GetQuestsSystem=function() return {GetFactStr=function() return 1 end} end}
function NewObject(name)
 assert(name=="PTFRTowerJournalCleanup")
 core={status="IDLE",events={},
   Read=function(self,p) return {"VALID|true","SAFE|true","TRACK|0|false"} end,
   ReadOtherQuests=function(self,p) return {"unrelated|2"} end,
   Prepare=function(self,p) calls[#calls+1]="Prepare";self.status=prepare_status or "PREPARED";return self.status end,
   Apply=function(self,p) calls[#calls+1]="Apply";assert(writes[#writes]:find("BEFORE_REQUEST",1,true));self.status="REQUESTED";return self.status end,
   GetStatus=function(self) return self.status end,
   DrainEvents=function(self) local e=self.events;self.events={};return e end,
   Cancel=function(self) calls[#calls+1]="Cancel" end}
 return core
end
'''

def fixture(extra=''):
    vm=LuaRuntime(unpack_returned_tuples=True);vm.execute(SETUP);vm.execute(extra)
    mod=vm.execute(LUA.read_text());return vm,mod

def bridge():
    vm,mod=fixture();mod.Repair();assert len(vm.globals().calls)==0
    mod.Start();assert vm.globals().calls[1]=='Prepare'
    assert [row['event'] for _,row in vm.globals().rows.items()] == ['BASELINE','PREPARED']
    mod.Repair();mod.Repair()
    assert [v for _,v in vm.globals().calls.items()].count('Apply')==1
    vm.execute('core.events={"REQUEST|exact","CONFIRMED|exact"};core.status="VERIFIED_JOURNAL_STATE";events.onUpdate(1)')
    mod.Check();mod.Stop()
    assert vm.globals().rows[len(vm.globals().rows)]['event']=='STOP'
    vm,mod=fixture('prepare_status="HIERARCHY_MISMATCH"');mod.Start();mod.Repair()
    assert 'Apply' not in [v for _,v in vm.globals().calls.items()]
    for event in ('BASELINE','PREPARED','BEFORE_REQUEST'):
        vm,mod=fixture('failed_event="'+event+'"');mod.Start();mod.Repair()
        assert 'Apply' not in [v for _,v in vm.globals().calls.items()]
    vm,mod=fixture();mod.Start();vm.execute('failed_event="STATUS";core.status="VERIFIED_JOURNAL_STATE";events.onUpdate(1)')
    assert vm.globals().calls[len(vm.globals().calls)]=='Cancel'
    vm,mod=fixture();mod.Start();vm.execute('events.onShutdown()')
    assert vm.globals().rows[len(vm.globals().rows)]['event']=='STOP'
    return 10

if __name__=='__main__':
    report=dict(status='OFFLINE_SCOPE_AND_BRIDGE_PASS_NOT_NATIVE_RUNTIME',rows=88,mutable_entries=23,
                negative_fact_cases=scope(),bridge_cases=bridge(),live_tested=False)
    (AUDIT/'offline_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
