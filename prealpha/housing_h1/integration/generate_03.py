"""H1 integration also revokes the old H10 owner's reusable enable permission."""
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('h1_prior_integration',HERE/'generate_02.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
prior=base.prior


def transform(relative,original):
    text=base.transform(relative,original)
    if relative.endswith('/RestorationBaseline.reds'):
        text=base.swap(text,
          '    let housing = HousingState.Get(game);\n'
          '    if IsDefined(housing) && housing.HousingReadyForReveal() && housing.Entitled("h10") && h10Actions &&',
          '    let housing = HousingState.Get(game);\n'
          '    // Old saves may retain Enabled1 in an already-registered native wait.\n'
          '    // Revoke only its reusable permission after all action owners are idle;\n'
          '    // never reset/restart the owner or interrupt a scene in progress.\n'
          '    if IsDefined(housing) && housing.Enforcing() && !housing.Entitled("h10") &&\n'
          '       q.GetFact(n"PTFRH1_Ready") == 1 && q.GetFact(n"PTFRB0H10P_Enabled") == 1 &&\n'
          '       q.GetFact(n"PTFRB0H10P_Active") == 0 && q.GetFact(n"PTFRB0H10M_Active") == 0 &&\n'
          '       q.GetFact(n"PTFRB0H10I_M_Active") == 0 && q.GetFact(n"PTFRB0H10I_H_Active") == 0 &&\n'
          '       q.GetFact(n"PTFRB0H10I_B_Active") == 0 && q.GetFact(n"PTFRB0H10I_S_Active") == 0 &&\n'
          '       q.GetFact(n"PTFRB0H10I_W_Active") == 0 {\n'
          '      this.Set(q,n"PTFRB0H10P_Enabled",0);\n'
          '    }\n'
          '    if IsDefined(housing) && housing.HousingReadyForReveal() && housing.Entitled("h10") && h10Actions &&')
    return text


def main(revision):
    assert re.fullmatch(r'integration_\d{2}',revision)
    out=HERE/'build'/revision;out.mkdir(parents=True,exist_ok=False)
    files=[]
    for relative,digest in prior.INPUTS.items():
        src=prior.GAME/relative;assert prior.sha(src)==digest
        original=src.read_text(encoding='utf-8-sig');result=transform(relative,original)
        assert prior.fields(result)==prior.fields(original)
        p=out/'package'/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(result,encoding='utf-8',newline='\n')
        files.append(dict(relative=relative,before_sha256=digest,sha256=prior.sha(p),persistent_fields=prior.fields(result)))
    sources=[HERE/'generate_01.py',HERE/'generate_02.py',Path(__file__)]
    report=dict(status='BUILT_H1_INTEGRATION_NOT_LIVE',files=files,
                source_pins={p.relative_to(ROOT).as_posix():prior.sha(p) for p in sources},
                late_fixture_disabled=True,saved_fields_retained=True,arrival_camera_modified=False,
                old_h10_permission_revoked_only_when_idle=True,owner_restart=False,
                established_handoff_grants_quest_certificate=False,property_ready_required_before_reveal=True)
    (out/'component.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],output=str(out)),indent=2))


if __name__=='__main__':main(sys.argv[1])
