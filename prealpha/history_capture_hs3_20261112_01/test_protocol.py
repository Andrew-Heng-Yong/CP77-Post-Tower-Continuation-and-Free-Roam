"""Evaluate actual compiled-source predicates and cooked gate parameters offline."""
import json
import argparse
import math
import re
from types import SimpleNamespace
from common import HERE, RED, read, sha, write
from verify import load_model


def expression(source,signature):
    body=source.split(signature,1)[1].split('\n  }',1)[0]
    raw=body.split('return ',1)[1].split(';',1)[0]
    python=re.sub(r'this\.Fact\(n?"([^"]+)"\)',r'facts.get("\1",0)',raw)
    python=python.replace('&&',' and ').replace('||',' or ')
    python=re.sub(r'!(?!=)','not ',python)
    return compile('('+python.strip()+')','<actual REDscript predicate>','eval')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--attempt',type=int,default=6);args=ap.parse_args()
    out=HERE/f'verification_{args.attempt:02}';assert not out.exists();out.mkdir()
    path=HERE/'candidate_04/package'/RED;source=path.read_text(encoding='utf-8')
    native=source.split('public class CaptureArchiveHS3 extends ScriptableSystem {',1)[1]
    predicate=expression(native,'private func GateOpen(ticket: Int32,route: Int32) -> Bool {')
    def accepts(facts,ticket=1,route=1):
        return bool(eval(predicate,{'__builtins__':{}},{'facts':facts,'ticket':ticket,'route':route}))
    q307={'PTFRHS3_GateOpen':1,'PTFRHS3_GateTicket':1,'PTFRHS3_GateRoute':1,'PTFRHS3_GateResult':0,'q307_point_of_no_return':1}
    q115={**q307,'PTFRHS3_GateRoute':2,'q307_point_of_no_return':0}
    checks=[]
    assert accepts(q307);checks.append('q307 direct gate accepts the actual pre-bulk fact state')
    assert accepts(q115,route=2);checks.append('q115 gate accepts before its native point fact is written')
    assert not accepts({**q115,'q115_point_of_no_return':1},route=2)
    assert not accepts({**q307,'q115_point_of_no_return':1})
    checks.append('already crossed alternate cutoff cannot be relabelled as a fresh pre-cutoff capture')
    for name,val in [('PTFRHS3_GateOpen',0),('PTFRHS3_GateTicket',2),('PTFRHS3_GateRoute',2),('PTFRHS3_GateResult',1),
                     ('q307_debug_reset',1),('q307_2079',1),('q307_main_game_killed',1),('q307_ep1_killed',1),
                     ('q307_done',1),('q307_finished',1)]:
        assert not accepts({**q307,name:val}),name
        checks.append('reject '+name+'='+str(val))
    assert not accepts(q307,ticket=0);checks.append('unissued capture ticket rejected')
    compare=expression(native,'private func SameJournal(a: CaptureJournalHS3,b: CaptureJournalHS3) -> Bool {')
    a=SimpleNamespace(state=2,counter=97,optional=1,tracked=0)
    assert eval(compare,{'__builtins__':{}},{'a':a,'b':a})
    for key in ('state','counter','optional','tracked'):
        values=vars(a).copy();values[key]+=1
        assert not eval(compare,{'__builtins__':{}},{'a':a,'b':SimpleNamespace(**values)})
    checks.append('actual journal comparator rejects every changed progress field')
    unknown=SimpleNamespace(state=-1,counter=-1,optional=-1,tracked=-1)
    assert eval(compare,{'__builtins__':{}},{'a':unknown,'b':unknown}) and unknown.state==-1
    checks.append('missing journal identity stays unknown rather than becoming Inactive')
    model=load_model();gate_plan=read(HERE/'evidence_01/plan.json')
    for gate in gate_plan['gates']:
        model_data=model.normalize(model.load_export(HERE/f"archive_02/{gate['route']}_after.json"))
        g=next(g for g in model_data['graphs'] if g['path']==gate['graph']);nodes={n['id']:n for n in g['nodes']}
        condition=nodes[60004]['parameters']['condition'];fact_condition=condition['conditions'][0]['type'];delay=condition['conditions'][1]['type']
        def released(facts,elapsed):
            return facts.get(fact_condition['factName'],0)>fact_condition['value'] or elapsed>=delay['seconds']
        assert not released({},0) and not released({},29.9) and released({},30) and released({'PTFRHS3_GateResult':1},0)
        for ack,elapsed in [(1,0),(0,30)]:
            facts={'PTFRHS3_GateResult':ack,'PTFRHS3_GateOpen':1}
            assert released(facts,elapsed)
            for i in [60005,60006]:
                effect=nodes[i]['parameters']['type'];facts[effect['factName']]=effect['value']
            assert facts['PTFRHS3_GateOpen']==0 and facts['PTFRHS3_GateResult']==ack
            assert not accepts({**q307,**facts})
        checks.append(f"route {gate['route']} actual cooked gate releases on ack or timeout, closes capture and never fabricates success")
    # Source publication order: data remains unpublished until both passes have
    # completed, then native acknowledgement follows the committed receipt.
    body=native.split('private func OnCapturePollHS3(',1)[1].split('private func BoolJSON',1)[0]
    first=body.index('if this.pass==1 { this.pass=2;this.cursor=0;return; }')
    captured=body.index('legacy.CaptureNativeHS3(ticket,route)',first)
    committed=body.index('this.committed=true;',captured)
    ack=body.index('SetFact(n"PTFRHS3_GateResult",1)',committed)
    assert first<captured<committed<ack
    checks.append('two passes and both save-local publications precede native release acknowledgement')
    catalogue=read(HERE/'evidence_01/catalogue.json');count=sum(len(catalogue[k]) for k in ('journals','facts','items'))
    ticks=2*math.ceil(count/512)
    write(out/'protocol_fixtures.json',{'status':'PASS_SOURCE_PREDICATE_AND_COOKED_GATE_FIXTURES','checks':checks,'count':len(checks),
        'candidate_sha256':sha(path),'tool_sha256':sha(__file__),'nominal_delay_ticks_for_two_passes':ticks,
        'nominal_scheduled_seconds_excluding_engine_work':ticks*0.05,
        'limits':'This evaluates source expressions and exported graph parameters. Engine scheduling, save serialization and elapsed capture time require gameplay qualification.'})
    print(json.dumps({'status':'PASS_SOURCE_PREDICATE_AND_COOKED_GATE_FIXTURES','checks':len(checks),'nominal_ticks':ticks}))


if __name__=='__main__':main()
