"""Assemble tested housing components without touching the installed game."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
GAME=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v): Path(p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')


def main(args):
    assert re.fullmatch(r'h1_\d{2}',args.revision)
    out=HERE/'build'/args.revision
    out.mkdir(parents=True,exist_ok=False)
    pins={}
    def pin(path,digest=None):
        path=Path(path).resolve()
        assert path.is_relative_to(ROOT),path
        rel=path.relative_to(ROOT).as_posix()
        actual=sha(path)
        assert digest is None or actual==digest,(rel,'source changed')
        assert rel not in pins or pins[rel]==actual
        pins[rel]=actual
        return rel
    def source_pins(manifest):
        assert manifest.get('source_pins')
        for p,h in manifest['source_pins'].items():pin(ROOT/p,h)
    def bind_tester(proof,manifest=None):
        digest=proof.get('tester_sha256')
        if digest is None:
            # The frozen runtime receipt predates the explicit tester field.
            # Its component pins the exact executable test source instead.
            assert manifest and manifest.get('status')=='BUILT_H1_RUNTIME_NOT_LIVE'
            keys=[p for p in manifest['source_pins'] if re.fullmatch(r'prealpha/housing_h1/runtime/test_0[23]\.py',p)]
            assert len(keys)==1,'Exact runtime tester binding required'
            key=keys[0]
            digest=manifest['source_pins'][key]
            assert 'source pin '+key in proof['check_names']
            pin(ROOT/key,digest)
        assert digest,'Test receipt must identify its executable source'
        matches=[p for p in HERE.rglob('*.py') if sha(p)==digest]
        assert len(matches)==1,('Ambiguous tester',digest,len(matches))
        pin(matches[0],digest)
    files=[];components=[]
    def copy(relative,source,digest,before=''):
        assert not Path(relative).is_absolute() and '..' not in Path(relative).parts
        assert relative not in [f['relative'] for f in files]
        assert sha(source)==digest
        if before:assert sha(GAME/relative)==before
        else:assert not (GAME/relative).exists()
        target=out/'package'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        files.append(dict(relative=relative,sha256=digest,before_sha256=before,action='replace' if before else 'add'))
    packpath=Path(args.pack).resolve();pack=read(packpath)
    assert pack['status']=='PASS_H1_PACK_AND_RESOURCE_SCOPE_NOT_LIVE' and pack['packed_readback'] is True
    pin(packpath);source_pins(pack)
    nativepath=Path(pack['component']);native=read(nativepath)
    pin(nativepath,pack['component_sha256']);source_pins(native)
    ntests=nativepath.parent/'tests.json';nt=read(ntests)
    assert nt['status'].startswith('PASS')
    bound=nt.get('component_sha256',nt.get('build_sha256'))
    assert bound==sha(nativepath), 'Native component test binding'
    pin(ntests)
    bind_tester(nt)
    if nt.get('source_pins'):source_pins(nt)
    components.append(dict(kind='native',manifest=nativepath.relative_to(ROOT).as_posix(),sha256=sha(nativepath),
                           tests=ntests.relative_to(ROOT).as_posix(),tests_sha256=sha(ntests)))
    reviewpath=ROOT/'research/housing_h1/purchase/native_review_01.json';review=read(reviewpath)
    assert review['status'].startswith('PASS') and review['component_sha256']==sha(nativepath)
    pin(reviewpath);source_pins(review)
    pin(HERE/'purchase/review_native_01.py',review['reviewer_sha256'])
    for row in pack['files']:copy(row['relative'],packpath.parent/'package'/row['relative'],row['sha256'])
    for filename in args.components:
        path=Path(filename).resolve();m=read(path)
        pin(path);source_pins(m)
        tests=path.parent/'tests.json';t=read(tests)
        assert t['status'].startswith('PASS')
        assert t.get('component_sha256',t.get('manifest_sha256',t.get('build_sha256')))==sha(path),'Script component test binding'
        pin(tests)
        bind_tester(t,m)
        if t.get('source_pins'):source_pins(t)
        for row in m['files']:
            copy(row['relative'],path.parent/'package'/row['relative'],row['sha256'],row.get('before_sha256',''))
        components.append(dict(kind='script',manifest=path.relative_to(ROOT).as_posix(),sha256=sha(path),
                               tests=tests.relative_to(ROOT).as_posix(),tests_sha256=sha(tests)))
    for tool in ['assemble_01.py','compile_01.py','deploy_01.ps1','test_deploy_01.py','pack_02.ps1']:
        pin(HERE/tool)
    pin(HERE/'runtime/check_compatibility_02.py')
    contract=Path(args.contract).resolve();pin(contract)
    assert len(files)==7 and sum(f['action']=='replace' for f in files)==2,'Exact H1 package scope'
    m=dict(status='BUILT_H1_LIVE_PENDING',files=files,components=components,
           native_pack=packpath.relative_to(ROOT).as_posix(),resources=pack['resources'],boots=pack['boots'],
           injections=pack['injections'],official_overrides=[],mod_overrides=pack['mod_overrides'],
           source_pins=pins,installer_sha256=sha(HERE/'deploy_01.ps1'),
           persistence_contract=contract.relative_to(ROOT).as_posix(),persistence_contract_sha256=sha(contract),
           scope='One-time ordinary home entitlement loss; paid native-price reacquisition; earned Kerry exception; no quest reset.',
           public_beta_released=False,live_verified=False)
    write(out/'build.json',m)
    digest=sha(out/'build.json')
    write(out/'tests.json',dict(status='PASS_H1_BOUND_COMPONENT_TESTS_NOT_LIVE',build_sha256=digest,
          assembler_sha256=sha(__file__),component_tests=components,source_pins_verified=len(pins),files_verified=len(files)))
    resource=pack.copy();resource['build_sha256']=digest
    write(out/'resource_check.json',resource)
    print(json.dumps(dict(status=m['status'],build=str(out),files=len(files),resources=len(pack['resources']),
                         manifest_sha256=digest),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('revision');parser.add_argument('--pack',required=True)
    parser.add_argument('--components',nargs='+',required=True);parser.add_argument('--contract',required=True)
    main(parser.parse_args())
