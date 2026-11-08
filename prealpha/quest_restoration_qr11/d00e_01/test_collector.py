"""Synthetic schema2 cases only; no game, registry, saves or actual collection."""
from pathlib import Path
import json
from collect_d00e import analyze,FACT
H=Path(__file__).resolve().parent
def main():
    rows=[]
    def add(event,data):rows.append({'schema':2,'module':'PTFR_QR9_Diagnostics','profile':'D00E','run_id':'SYNTHETIC_QR11','seq':len(rows)+1,'event':event,'data':data})
    def run(r=None):return analyze(('\n'.join(json.dumps(x)for x in(r or rows))+'\n').encode())
    passed=[]
    add('CAPTURE_START',{'version':'QR10D01','watch_facts':[FACT]});add('ATTACHED_BASELINE',{'facts':{FACT:0}});add('NATIVE_CALLBACK_UNAVAILABLE',{})
    add('FACT_SAMPLE_CHANGE',{'fact':FACT,'previous_sample':0,'current_sample':1});add('STOP',{});add('CAPTURE_CLEANUP',{})
    assert run()['status']=='SAMPLED_CHANGE_RECORDED_AWAITING_HUMAN_CORRELATION';passed.append('positive sample does not auto-PASS gameplay/native callbacks')
    assert run()['native_callbacks']=='UNSUPPORTED_NOT_TESTED';passed.append('native callback capability stays explicit')
    clean=[r for r in rows if r['event']!='FACT_SAMPLE_CHANGE']
    for i,r in enumerate(clean):r={**r,'seq':i+1};clean[i]=r
    assert run(clean)['status']=='INCONCLUSIVE_NO_SAMPLED_CHANGE';passed.append('no samples is inconclusive')
    assert run(rows[:-2])['status']=='INCONCLUSIVE_INCOMPLETE_CAPTURE';passed.append('missing stop is inconclusive')
    bad=json.loads(json.dumps(rows));bad[3]['data']['current_sample']=0
    assert run(bad)['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('same-value alleged transition refused')
    bad=json.loads(json.dumps(rows));bad[3]['data']['previous_sample']=99
    assert run(bad)['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('inconsistent previous sample refused')
    bad=json.loads(json.dumps(rows));bad[3]['event']='FACT_DELIVERY'
    assert run(bad)['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('native-event mislabelling refused')
    bad=json.loads(json.dumps(rows));bad[3]['event']='FACT_SAMPLE_ERROR'
    assert run(bad)['status']=='FAIL_DIAGNOSTIC_GETTER';passed.append('getter error distinct from gameplay failure')
    assert analyze(b'bad json')['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('malformed JSON refused')
    bad=json.loads(json.dumps(rows));bad[0]['data']['version']='QR9B04'
    assert run(bad)['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('wrong observer version refused')
    for b in (b'[]\n',b'{"data":[]}\n',b'"text"\n'):
        assert analyze(b)['status']=='FAIL_CAPTURE_INTEGRITY';passed.append('malformed row shape refused:'+str(b))
    out=H/'collector_controls_02.json';assert not out.exists();out.write_text(json.dumps({'status':'PASS_OFFLINE_COLLECTOR','checks':passed,'scope':'Synthetic rows; no live run or native callbacks tested.'},indent=2)+'\n',encoding='utf-8')
    print({'status':'PASS_OFFLINE_COLLECTOR','checks':len(passed)})

if __name__=='__main__':main()
