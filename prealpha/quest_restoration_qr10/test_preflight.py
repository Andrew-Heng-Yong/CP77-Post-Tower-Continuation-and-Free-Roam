"""Workspace-only preflight negative controls; no installation implementation."""
from pathlib import Path
import argparse, copy, json, tempfile
import preflight as p
H=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=p.fresh_output(a.out);out.mkdir()
    manifest=p.read(H/'manifest_02.json');game=out/'game';game.mkdir();passed=[]
    for row in manifest['files']:
        q=game/row['path'];q.parent.mkdir(parents=True,exist_ok=True)
        q.write_bytes((p.W/'prealpha/quest_restoration_qr9/worker_b/addon'/row['path']).read_bytes())
    extra=game/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/unknown_capture.jsonl';extra.write_bytes(b'preserve me')
    p.validate(manifest,game,'before');passed.append('exact B04 before fixture accepted')
    def rejects(label,fn):
        try:fn()
        except AssertionError:passed.append(label)
        else:raise AssertionError('accepted unsafe fixture:'+label)
    rejects('running game refused',lambda:p.validate(manifest,game,'before',['Cyberpunk2077']))
    rejects('running launcher refused',lambda:p.validate(manifest,game,'before',['REDlauncher']))
    bad=copy.deepcopy(manifest);bad['files'][0]['path']='r6/scripts/anything.reds'
    rejects('non-diagnostic leaf refused',lambda:p.validate(bad,game))
    q=game/manifest['files'][0]['path'];original=q.read_bytes();q.write_bytes(b'unknown')
    rejects('unknown installed bytes refused',lambda:p.validate(manifest,game));q.write_bytes(original)
    for row in manifest['files']:(game/row['path']).write_bytes(Path(row['source']).read_bytes())
    p.validate(manifest,game,'after');passed.append('exact successor fixture accepted for verify/rollback preflight')
    rejects('after bytes rejected by before-only preflight',lambda:p.validate(manifest,game,'before'))
    assert extra.read_bytes()==b'preserve me';passed.append('unknown log untouched')
    rejects('containment escape refused',lambda:p.contained(game,H/'manifest_02.json'))
    for name in ('../qr10_scope_escape.json',str(H.parent/'scope_escape.json'),'dir/nested.json','dir\\nested.json','result:stream','..','COM1.json','NUL'):
        rejects('output path refused:'+name,lambda name=name:p.fresh_output(name))
    rejects('occupied output refused',lambda:p.fresh_output(a.out))
    # Symbolic link is fixture-only and optional on Windows if link privilege is unavailable.
    link=game/'escape'
    try:link.symlink_to(H,target_is_directory=True)
    except OSError:link_test='NOT_RUN_WINDOWS_LINK_PRIVILEGE; lstat reparse guard inspected'
    else:
        rejects('link refused',lambda:p.contained(game,link/'manifest_02.json'));link_test='PASS'
    result={'status':'PASS_READ_ONLY_PREFLIGHT_FIXTURES','checks':passed,'symlink_control':link_test,
        'not_tested':'No installer, atomic two-leaf transaction, crash recovery or actual rollback was executed.'}
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'checks':len(passed),'symlink':link_test})

if __name__=='__main__':main()
