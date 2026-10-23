"""Exercise scoped H1 replacement/addition and rollback in isolated fixtures.

Synthetic fixtures test deployment mechanics only and are rejected by live mode.
Pass an aggregate build to exercise the same mechanism with real package bytes.
"""
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GAME = Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
REPLACE = ['r6/scripts/PTFR_PreAlpha/PA1/PreAlphaEntry.reds',
           'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds']
ADD = ['archive/pc/mod/00000000_TowerContinued_Housing_H1.archive',
       'archive/pc/mod/00000000_TowerContinued_Housing_H1.archive.xl',
       'r6/scripts/TowerContinued_Housing_H1/HousingState.reds']


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p, obj): Path(p).write_text(json.dumps(obj, indent=2)+'\n', encoding='utf-8')
def quote(v): return "'"+str(v).replace("'", "''")+"'"


def main(source=None):
    suite = HERE/'fixtures'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    suite.mkdir(parents=True, exist_ok=False)
    cases = []

    def fixture(name):
        root = suite/name
        game, saves, build, recovery = (root/n for n in ['game','saves','build','recovery'])
        for folder in [game/'archive/pc/mod',game/'r6/scripts',game/'r6/cache',saves,build]:
            folder.mkdir(parents=True,exist_ok=True)
        for rel in REPLACE:
            p=game/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/rel,p)
        if source:
            manifest = read(source/'build.json')
            shutil.copytree(source/'package',build/'package')
        else:
            files=[]
            for rel in REPLACE+ADD:
                p=build/'package'/rel;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(('Synthetic replacement/addition '+rel).encode())
                files.append(dict(relative=rel,sha256=sha(p),action='replace' if rel in REPLACE else 'add',
                                  before_sha256=sha(game/rel) if rel in REPLACE else ''))
            manifest=dict(status='BUILT_H1_LIVE_PENDING',files=files,
                          source_pins={'prealpha/housing_h1/deploy_01.ps1':sha(HERE/'deploy_01.ps1')},
                          installer_sha256=sha(HERE/'deploy_01.ps1'))
        manifest['synthetic_fixture']=True
        write(build/'build.json',manifest)
        sentinels={game/'r6/cache/final.redscripts':b'untouched cache',saves/'ManualSave-1/sav.dat':b'untouched save',
                   game/'r6/scripts/other.reds':b'untouched other script',game/'archive/pc/mod/existing.archive':b'untouched archive',
                   game/'archive/pc/mod/existing.archive.xl':b'untouched XL',game/'archive/pc/content/native.archive':b'untouched native'}
        for p,data in sentinels.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        deps={str(p):sha(p) for p in (game/'r6/scripts').rglob('*.reds')}
        tool=build/'compiler.bin';tool.write_bytes(b'fixture only compiler identity')
        common=dict(status='PASS_FIXTURE_REBOUND_NOT_COMPILER_PROOF',build_sha256=sha(build/'build.json'))
        write(build/'compile_result.json',common|dict(full_scc=True,live_files_unchanged=True,
              dependencies=deps,protected={str(game/'r6/cache/final.redscripts'):sha(game/'r6/cache/final.redscripts')},
              compiler_inputs={str(tool):sha(tool)},script_roots=[str(game/'r6/scripts')],
              overlay_pins={str(build/'package'/row['relative']):row['sha256'] for row in manifest['files'] if row['relative'].endswith('.reds')}))
        write(build/'resource_check.json',common|dict(archive_pins={str(game/'archive/pc/mod/existing.archive'):sha(game/'archive/pc/mod/existing.archive')},
              xl_pins={str(game/'archive/pc/mod/existing.archive.xl'):sha(game/'archive/pc/mod/existing.archive.xl')},
              official_archive_pins={str(game/'archive/pc/content/native.archive'):sha(game/'archive/pc/content/native.archive')}))
        write(build/'tests.json',common);write(build/'compatibility_check.json',common);write(build/'deployment_tests.json',common)
        return dict(root=root,game=game,saves=saves,build=build,recovery=recovery,sentinels={str(p):sha(p) for p in sentinels},files=manifest['files'])

    def invoke(f,mode='Validate',ok=True,extra='',busy=False):
        command='function Get-Process { param([string]$Name) '+('[pscustomobject]@{Id=123;ProcessName="Cyberpunk2077"}' if busy else 'return')+' }; '
        command+='& '+quote(HERE/'deploy_01.ps1')+' -Fixture -Mode '+quote(mode)
        for name,key in [('GameRoot','game'),('SaveRoot','saves'),('Build','build'),('RecoveryRoot','recovery')]:command+=' -'+name+' '+quote(f[key])
        result=subprocess.run(['pwsh','-NoProfile','-Command',command+' '+extra],capture_output=True,text=True,timeout=90)
        (f['root']/(mode+'_'+str(len(list(f['root'].glob('*.log'))))+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
        assert (result.returncode==0)==ok,(f['root'].name,mode,result.stdout,result.stderr)
        for p,h in f['sentinels'].items():assert sha(p)==h,p
        return result

    def pristine(f):
        for row in f['files']:
            p=f['game']/row['relative']
            if row['action']=='replace':assert sha(p)==row['before_sha256']
            else:assert not p.exists()

    normal=fixture('normal');invoke(normal);pristine(normal)
    invoke(normal,'Install')
    for row in normal['files']:assert sha(normal['game']/row['relative'])==row['sha256']
    invoke(normal,'ValidateRollback');invoke(normal,'Rollback');pristine(normal)
    invoke(normal,'Rollback',ok=False);cases.append('install_exact_backup_rollback_no_repeat')
    for count in [1,2,len(normal['files'])]:
        f=fixture('interrupted_'+str(count));invoke(f,'Install',ok=False,extra='-FailAfterWrite '+str(count))
        invoke(f,'ValidateRollback');invoke(f,'Rollback');pristine(f);cases.append('rollback_interrupted_'+str(count))
    f=fixture('running');invoke(f,'Install',ok=False,busy=True);pristine(f);cases.append('running_game_refused')
    for name,mutate in [
        ('path_escape',lambda m:m['files'][0].update(relative='../escape')),
        ('wrong_old_hash',lambda m:m['files'][0].update(before_sha256='0'*64)),
        ('wrong_new_hash',lambda m:m['files'][0].update(sha256='0'*64)),
        ('duplicate_path',lambda m:m['files'].append(m['files'][0])),
        ('unscoped_file',lambda m:m['files'][-1].update(relative='r6/scripts/other.reds')),
        ('wrong_action',lambda m:m['files'][0].update(action='add')),
        ('wrong_installer',lambda m:m.update(installer_sha256='0'*64)),
    ]:
        f=fixture(name);m=read(f['build']/'build.json');mutate(m);write(f['build']/'build.json',m)
        invoke(f,'Install',ok=False);pristine(f);cases.append(name)
    f=fixture('changed_source');(f['build']/'package'/f['files'][0]['relative']).write_bytes(b'drift')
    invoke(f,'Install',ok=False);pristine(f);cases.append('changed_payload')
    f=fixture('existing_addition');q=f['game']/ADD[-1];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b'userfile')
    invoke(f,'Install',ok=False);assert q.read_bytes()==b'userfile';cases.append('existing_addition_preserved')
    f=fixture('rollback_drift');invoke(f,'Install');p=f['game']/f['files'][0]['relative'];p.write_bytes(b'futureversion')
    invoke(f,'Rollback',ok=False);assert p.read_bytes()==b'futureversion';cases.append('future_target_prevents_rollback')
    for filename in ['tests.json','compile_result.json','resource_check.json','compatibility_check.json','deployment_tests.json']:
        f=fixture('bad_'+filename);p=f['build']/filename;v=read(p);v['build_sha256']='0'*64;write(p,v)
        invoke(f,'Install',ok=False);pristine(f);cases.append('stale_'+filename)
    report=dict(status='PASS_DEPLOYMENT_FIXTURES_NOT_LIVE',synthetic=not bool(source),
                source=str(source) if source else None,build_sha256=sha(source/'build.json') if source else None,case_count=len(cases),cases=cases,
                installer_sha256=sha(HERE/'deploy_01.ps1'),tester_sha256=sha(__file__),
                suite=str(suite),game_save_cache_writes=False)
    write(suite/'tests.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':main(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None)
