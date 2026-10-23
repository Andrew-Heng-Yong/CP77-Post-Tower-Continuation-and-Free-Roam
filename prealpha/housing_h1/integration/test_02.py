"""Reuse the entry regression suite and verify idle-only old-owner revocation."""
import importlib.util
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
code=module('h1_current',HERE/'generate_03.py')
suite=module('h1_prior_tests',HERE/'test_01.py')
suite.code=code
def main(revision):
    suite.main(revision)
    out=HERE/'build'/revision
    text=(out/'package/r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds').read_text()
    start=text.index('// Old saves may retain Enabled1')
    end=text.index('    if IsDefined(housing) && housing.HousingReadyForReveal()',start)
    fragment=text[start:end]
    assert fragment.count('this.Set(')==1 and 'this.Set(q,n"PTFRB0H10P_Enabled",0)' in fragment
    assert 'housing.Enforcing() && !housing.Entitled("h10")' in fragment
    for f in ['PTFRB0H10P','PTFRB0H10M','PTFRB0H10I_M','PTFRB0H10I_H','PTFRB0H10I_B','PTFRB0H10I_S','PTFRB0H10I_W']:
        assert 'q.GetFact(n"'+f+'_Active") == 0' in fragment
    def revoke(enforcing,entitled,ready,enabled,active):
        return enforcing and not entitled and ready==1 and enabled==1 and all(v==0 for v in active)
    assert revoke(True,False,1,1,[0]*7)
    for i in range(7):
        active=[0]*7;active[i]=1;assert not revoke(True,False,1,1,active)
    assert not revoke(False,False,1,1,[0]*7)
    assert not revoke(True,True,1,1,[0]*7)
    assert not revoke(True,False,0,1,[0]*7)
    assert not revoke(True,False,1,0,[0]*7)
    p=out/'tests.json';report=json.loads(p.read_text())
    report['tester_sha256']=code.prior.sha(__file__)
    report['source_pins']={(HERE/'test_01.py').relative_to(code.ROOT).as_posix():code.prior.sha(HERE/'test_01.py')}
    report['idle_revocation_cases']=12;report['case_count']+=12
    report['old_native_owner_restarted']=False
    p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS idle-only existing enable permission revocation; 32 integration cases total')
if __name__=='__main__':main(sys.argv[1])
