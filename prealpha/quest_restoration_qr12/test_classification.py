"""Synthetic prerequisite controls, not save/gameplay fixtures."""
from pathlib import Path
import copy,json
from classify import classify
H=Path(__file__).resolve().parent
def main():
    inv=json.loads((H/'inventory_verified.json').read_text());r=next(x for x in inv['rows']if x['kind']=='GAME_SAVE'and x['slot_directory']=='ManualSave-24')
    parsed={}
    for p in [H/'probe_01.json',*H.glob('batch_*.json')]:
        for x in json.loads(p.read_text())['results']:parsed[x['sha256']]=x
    p=parsed[r['sha256']];checks=[]
    def item(row,state,answer,id):return next(x for x in classify(row,state,answer)if x['scenario']==id)
    b='BRENDAN_unearned_fresh_containment'
    assert item(r,p,'Don’t remember',b)['status']=='BLOCKED_BY_HISTORY';checks.append('actual private admission blocks fresh negative fixture despite unknown human history')
    clean=copy.deepcopy(p)
    for marker in ['PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered']:clean['facts'].pop(marker,None)
    assert item(r,clean,'Don’t remember',b)['status']=='REQUIRES_MANUAL_PREREQUISITE';checks.append('synthetic no-admission state still requires known human history')
    assert item(r,clean,'Never started any Brendan job',b)['status']=='READY';checks.append('known hypothetical human prerequisite with no admission can qualify negative containment only')
    fake=copy.deepcopy(p);fake['facts']['mq037_brendan_introduced']=[{'value_u32':1}]
    assert item(r,fake,'Never started any Brendan job',b)['status']=='BLOCKED_BY_HISTORY';checks.append('contradictory positive history overrides proposed negative fixture')
    for marker in ['PTFRS23_MQ037_Issued','PTFRS23_MQ037_Entered']:
        fake=copy.deepcopy(clean);fake['facts'][marker]=[{'value_u32':1}]
        assert item(r,fake,'Never started any Brendan job',b)['status']=='BLOCKED_BY_HISTORY'
        assert item(r,fake,'Never started any Brendan job','BRENDAN_earned_descendant_preservation')['status']=='UNKNOWN'
        checks.append(marker+' prevents false fresh READY without inventing earned native history')
    row={**r,'kind':'OFFLINE_BACKUP'};assert item(row,p,'Never started any Brendan job',b)['status']=='NOT_TESTABLE';checks.append('offline copy cannot become immediate Load Game test')
    row={**r,'lineage':'NOT_INDEPENDENTLY_CONFIRMED'};assert item(row,p,'Never started any Brendan job',b)['status']!='READY';checks.append('same filename without hash-bound human lineage not READY')
    assert item(r,p,'Don’t remember','CVI02_fresh_specialized_calls')['status']=='BLOCKED_BY_HISTORY';checks.append('completed CVI cannot be replayed')
    assert item(r,p,'Don’t remember','SKIPPY_supported_return_1101')['status']=='UNKNOWN';checks.append('kill counts do not certify pre1101 stage')
    assert item(r,p,'Don’t remember','NITRO_existing_issued_preservation')['status']=='UNKNOWN';checks.append('Issued1 not exact executing-selector proof')
    fake=copy.deepcopy(p);fake['facts'].pop('q302_ronald_messages_enabled',None)
    assert item(r,fake,'Don’t remember','RONALD_prospective_news')['status']!='READY';checks.append('serialized absence does not invent subscription')
    dest=H/'classification_controls_02.json';assert not dest.exists();dest.write_text(json.dumps({'status':'PASS_PREREQUISITE_CONTROLS','checks':checks,'scope':'Synthetic answer branches, not human/save proof'},indent=2)+'\n',encoding='utf-8')
    print({'checks':len(checks),'status':'PASS_PREREQUISITE_CONTROLS'})
if __name__=='__main__':main()
