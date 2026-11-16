"""Pin observed findings and qualify the bounded read-only observer."""
import re
from capture import HERE,BASELINE,BASELINE_SHA,sha,read,write
from prepare import COVER,R1

def main():
    out=HERE/'assessment_02.json';assert not out.exists()
    baseline=read(BASELINE);candidate=read(HERE/'candidate_02/manifest.json');compiled=read(HERE/'compile_02/result.json')
    assert sha(BASELINE)==BASELINE_SHA and compiled['status']=='PASS' and compiled['source_count']==148
    before={r['path']:r['sha256'] for r in baseline['core_files']}
    after={r['path']:r['sha256'] for r in candidate['files']}
    assert set(before)==set(after) and {p for p in before if before[p]!=after[p]}=={COVER,R1}
    for p,h in after.items():assert sha(HERE/'candidate_02/package'/p)==h
    assert compiled['staged_hashes'][COVER]==after[COVER]
    old=(HERE/'base_02/package'/COVER).read_text(encoding='utf-8')
    new=(HERE/'candidate_02/package'/COVER).read_text(encoding='utf-8')
    assert re.findall(r'^.*persistent let.*$',old,re.M)==re.findall(r'^.*persistent let.*$',new,re.M)
    extra=(HERE/'presentation.reds').read_text(encoding='utf-8')
    calls=set(re.findall(r'\.([A-Za-z_]\w*)\(',extra))
    assert all(c.startswith(('Get','Is')) or c in {'Capture','Meshes','Layer','Widget','ToStringDEBUG','FindComponentByType'} for c in calls),calls
    # Keep every original gameplay write exactly: no new setter/removal/queue
    # or replacement hook was introduced in the observer's host script.
    writes=r'^.*(?:SetFact|SetVisible|SetOpacity|QueueRequest|RemoveItem|AddItem|GiveItem|wrappedMethod|@replaceMethod).*$'
    assert re.findall(writes,old,re.M)==re.findall(writes,new,re.M)
    r1old=(HERE/'base_02/package'/R1).read_text(encoding='utf-8')
    r1new=(HERE/'candidate_02/package'/R1).read_text(encoding='utf-8')
    assert re.findall(r'^.*persistent let.*$',r1old,re.M)==re.findall(r'^.*persistent let.*$',r1new,re.M)
    assert r1old.split('public final func PTFRRefreshPostTowerHands(',1)[1]==r1new.split('public final func PTFRRefreshPostTowerHands(',1)[1]
    native_writes=r'^.*(?:SetFact|RemoveItem|AddItem|GiveItem|QueueEvent).*$'
    assert re.findall(native_writes,r1new,re.M)==re.findall(native_writes,r1old.replace('    this.handRefreshAttempts -= 1;','      player.QueueEvent(new DeactivateTPPRepresentationEvent());\n    this.handRefreshAttempts -= 1;'),re.M)
    handoff=r1new.split('private func RefreshPostTowerHands(',1)[1].split('private func ReportRefundReadiness(',1)[0]
    assert handoff.index('this.handRefreshAttempts == 0')<handoff.index('!CyberwarePolicy.Safe(player)')<handoff.index('if !this.representationReturnQueued')<handoff.index('QueueEvent')
    assert handoff.index('this.representationReturnQueued = true')<handoff.index('QueueEvent')<handoff.index('this.handRefreshAttempts -= 1')
    logs=HERE/'evidence_02/logs/bin/x64/plugins/cyber_engine_tweaks'
    lines=[]
    for name in ('gamelog.log','scripting.log','cyber_engine_tweaks.log'):
        for n,line in enumerate((logs/name).read_text(encoding='utf-8',errors='replace').splitlines(),1):
            if re.search(r'2026-11-12 17:(?:4[2-9]|5[0-4]):',line) and re.search(r'PTFR_FastTravel|stock hands|mq007_done|resume|shut.*down|shutdown',line,re.I):
                lines.append({'log':name,'line':n,'text':line})
    assert any('mq007_done' in r['text'] and '1' in r['text'] for r in lines)
    assert any('native-start' in r['text'] for r in lines) and any('follow-up' in r['text'] for r in lines)
    assert not any('native-finished' in r['text'] for r in lines)
    write(HERE/'evidence_03/session_excerpt.json',lines)
    write(out,{'status':'PASS_BOUNDED_STATIC_QUALIFICATION_LIVE_FIX_UNVERIFIED','baseline_manifest_sha256':BASELINE_SHA,
        'candidate_manifest_sha256':sha(HERE/'candidate_02/manifest.json'),'compile_sha256':sha(HERE/'compile_02/result.json'),
        'compile_sources':148,'core_paths':51,'unchanged_paths':49,'archive_and_xl':'EXACT_RD1_BYTES',
        'new_observer_calls':sorted(calls),'persistent_fields':'UNCHANGED','existing_gameplay_writes':'UNCHANGED',
        'capture_limits':'At most 10 captures per attached session, one after Ready and start/five-second follow-up/finish for at most three trips. Up to 32 meshes per entity and 32 UI rows per layer; depth 2.',
        'hands_candidate':'One native DeactivateTPPRepresentationEvent, only within the existing first treatment, after genuine arrival and normal-player/safe-gameplay guards. No forced TPP activation or camera switch. Attachment and conservation logic unchanged.',
        'source_pins':{n:sha(HERE/n) for n in ('capture.py','prepare.py','presentation.reds','compile.py','assess.py','native.py')},
        'observed':{'machine_gun':'USER_REPORTED_WORKING_AND_NATIVE_MQ007_DONE_TRANSITION','arms':'USER_REPORTED_MISSING_DESPITE_LOGICAL_ATTACHMENT_CONFIRMATION',
          'fast_travel':'USER_REPORTED_ALL_SCREEN_BLACK; TELEPORT_POSITION_CHANGED; NO_FINISH_CALLBACK_LOGGED; OWN_POPUP_ABSENT'},
        'unknown':['Active native loading/fade layer during blackout','Actual arm mesh visibility during failure','Root cause and repair','Moving Heat gameplay','Machine Gun reward counts and reload'],
        'game_writes':0,'save_writes':0})
    print('PASS: exact two-script delta, 148-source compile, unchanged persisted fields/item logic; native handback candidate and blackout diagnosis require gameplay.')

if __name__=='__main__':main()
