"""Qualify exact inputs, native evidence and the bounded source delta."""
import re
from capture import HERE, ROOT, BASELINE, BASELINE_SHA, sha, read, write
from prepare import COVER, R1

def method(source, signature):
    start=source.index(signature); brace=source.index('{',start); depth=1; i=brace+1
    while depth:
        depth+=(source[i]=='{')-(source[i]=='}'); i+=1
    return source[start:i]

def main():
    target=HERE/'assessment_03.json';assert not target.exists()
    assert sha(BASELINE)==BASELINE_SHA
    baseline=read(BASELINE); candidate=read(HERE/'candidate_03/manifest.json'); compiled=read(HERE/'compile_03/result.json')
    assert compiled['status']=='PASS' and compiled['source_count']==148
    before={r['path']:r['sha256'] for r in baseline['core_files']};after={r['path']:r['sha256'] for r in candidate['files']}
    assert len(after)==51 and before.keys()==after.keys()
    assert {p for p in before if before[p]!=after[p]}=={COVER,R1}
    for p,h in after.items():assert sha(HERE/'candidate_03/package'/p)==h
    old={p:(HERE/'base_01/package'/p).read_text(encoding='utf-8') for p in (COVER,R1)}
    new={p:(HERE/'candidate_03/package'/p).read_text(encoding='utf-8') for p in (COVER,R1)}
    for p in (COVER,R1):
        assert compiled['staged_hashes'][p]==after[p]
        assert re.findall(r'^.*persistent let.*$',old[p],re.M)==re.findall(r'^.*persistent let.*$',new[p],re.M)
        # All pre-existing quest/item/equipment mutations are retained exactly.
        writes=r'^.*(?:SetFact\(|RemoveItem\(|AddItem\(|GiveItem\(|SetItem\(|SetStat\().*$'
        assert re.findall(writes,old[p],re.M)==re.findall(writes,new[p],re.M)
        raw=(HERE/'candidate_03/package'/p).read_bytes();assert b'\n' not in raw.replace(b'\r\n',b'')
    for signature in ('private final func SetFastTravelStarted()', 'protected cb func OnLoadingScreenFinished(value: Bool)'):
        assert method(old[COVER],signature)==method(new[COVER],signature)
    assert old[R1].split('public class CyberwareTreatmentRestore',1)[1]==new[R1].split('public class CyberwareTreatmentRestore',1)[1]
    handoff=method(new[COVER],'private func FinishPresentationTP2()')
    assert 'this.continuation || this.presentationRepairState >= 4' in handoff
    assert handoff.index('this.Accepts(this.epoch)')<handoff.index('QueueBroadcastEvent')
    for guard in ('CyberwarePolicy.Safe(player)','IsEntityInScene','IsPhoneCallActive','IsInFreeCamera','PTFRTP2HandsSettled',
                  'FastTravelStarted','FastTravelLoadingScreenStarted','ArraySize(layer.GetGameControllers()) != 0'):
        assert handoff.index(guard)<handoff.index('QueueBroadcastEvent'),guard
    assert handoff.count('new ActivateTPPRepresentationEvent()')==handoff.count('new DeactivateTPPRepresentationEvent()')==1
    assert handoff.index('this.presentationRepairState=2')<handoff.index('new ActivateTPPRepresentationEvent()')
    assert handoff.index('this.presentationRepairState=3')<handoff.index('new DeactivateTPPRepresentationEvent()')
    assert 'new Finalize' not in handoff and 'SetBool(' not in handoff and 'SetFact(' not in handoff
    assert 'GetFPPCameraComponent' not in handoff and 'inkEndGameLoadingState' in handoff
    poll=method(new[COVER],'public func Poll(epoch:Int32)')
    assert poll.index('!this.Check()')<poll.index('!this.FinishPresentationTP2()')<poll.index('this.released=true')
    assert 'presentationRepairState=0' in method(new[COVER],'public func Restored()')
    assert 'presentationStateCaptures>=24' in new[COVER] and 'as entSkinnedMeshComponent' in new[COVER]
    # Executing native handler evidence: no-op deactivation in states 1/5,
    # full activation accepts FPP, deactivation accepts activation in flight.
    deact=read(ROOT/'prealpha/tower_presentation_tp1_20261112_01/native_12/readback.json')['functions'][0]
    deact_text='\n'.join(i['mnemonic']+' '+i['operands'] for i in deact['instructions'])
    assert 'lea eax, [rsi - 1]' in deact_text and 'test eax, 0xfffffffb' in deact_text
    native=read(HERE/'events_01/readback.json')
    funcs={f['begin_rva']:f for f in native['functions']}
    assert '0xaad830' in funcs and '0x2aa79e0' in funcs and '0x2aa7a6c' in funcs and '0x7d71bc' in funcs
    hide='\n'.join(i['mnemonic']+' '+i['operands'] for i in funcs['0x7d71bc']['instructions'])
    assert 'mov edx, 4' in hide and 'call 0x1407d7340' in hide and 'and dword ptr [rbx + 0x1fc], 0' in hide
    evidence=['events_01/readback.json','events_03/readback.json','native_20/readback.json','native_23/readback.json',
              'native_31/readback.json','graphs_01/final_boards.questphase.json','graphs_01/q307_ending_board.questphase.json']
    source_pins={n:sha(HERE/n) for n in ('capture.py','prepare.py','handoff.reds','compile.py','assess.py')}
    write(target,{'status':'PASS_BOUNDED_STATIC_QUALIFICATION_LIVE_FIX_UNVERIFIED',
        'baseline_manifest_sha256':BASELINE_SHA,'candidate_manifest_sha256':sha(HERE/'candidate_03/manifest.json'),
        'compile_sha256':sha(HERE/'compile_03/result.json'),'compile_sources':148,'core_paths':51,'unchanged_paths':49,
        'archive_and_xl':'EXACT_TP1_RD1_BYTES; NO_NEW_DEPOT_OR_PHASE_REGISTRATION',
        'persistent_fields':'UNCHANGED','quest_item_reward_mutations':'EXACT_BASELINE; NO_NEW_WRITES',
        'fast_travel_implementation':'EXACT_BASELINE; NO_FAKE_COMPLETION_OR_WATCHDOG',
        'source_pins':source_pins,'evidence_pins':{n:sha(HERE/n) for n in evidence},
        'qualification':['Same-session fresh completed Tower only; restored completed saves bypass',
          'Input-covered native TPP/FPP event pair after attachment work; engine retains finalization',
          'Loading presentation cleanup only with no controller and no active/loading travel flags',
          'Source-reviewed one-shot stages, actor identity, session reset and guard ordering',
          'Native handler evidence and exact full registered-source compilation; no native code executed in fixtures'],
        'limitations':['Blackout root cause remains a hypothesis: residual loading-layer/ending visual state',
          'Dispatch and visual effect of loading cleanup not yet observed in game',
          'Body cycle has settling intervals, not a native completion or mesh-render acknowledgement',
          'No gameplay trial or interrupted-save compatibility certification performed'],
        'game_writes':0,'save_writes':0})
    print('PASS: exact two-script scope, preserved persistent fields and mutations, native evidence, bounded guards, 148-source compile; gameplay unverified.')

if __name__=='__main__':main()
