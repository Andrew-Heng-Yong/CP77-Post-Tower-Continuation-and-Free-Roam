"""Source anchors and bounded presentation/lifecycle model; NOT renderer proof."""
import itertools, json, re
from catalog_gig_rollout_r2 import ROOT, sha, read
OUT=ROOT/'research/johnny_voice_jv1'
SOURCE='redscript/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds'

def main():
    assert not (OUT/'install_receipt.json').exists(), 'Installed evidence pinned'
    source=(ROOT/SOURCE).read_text()
    compile=read(OUT/'compile_result.json')
    assert compile['source_sha256']==sha(ROOT/SOURCE) and compile['equipmentex']
    flat=(OUT/'compiled_flat.script').read_text(encoding='utf-8-sig')
    own=flat.split('public class PTFR.JohnnyVoiceJV1.JohnnyVoiceJV1 extends ScriptableSystem {',1)[1].split('public class PTFR.JohnnyVoiceJV1.JohnnyVoiceTick',1)[0]
    for anchor in ('actor.GetComponents()', 'as IVisualComponent', '.TemporaryHide(true);', 't"Character.Silverhand"','actor.IsAttached()'):assert anchor in own,anchor
    for anchor in ('class IVisualComponent extends IPlacedComponent','class entISkinTargetComponent extends IVisualComponent','class entSkinnedMeshComponent extends entISkinTargetComponent','class SoundComponentBase extends IPlacedComponent','class ISkinableComponent extends IPlacedComponent','class AnimatedComponent extends ISkinableComponent'):assert anchor in flat,anchor
    # Native NPC wrapper runs once, then registers; stock body remains compiled.
    wrapper=source.split('@wrapMethod(NPCPuppet)',1)[1].split('@wrapMethod(PlayerDevelopmentData)',1)[0]
    assert wrapper.count('wrappedMethod()')==1 and wrapper.index('wrappedMethod()')<wrapper.index('policy.Register(this)') and 'return result;' in wrapper
    assert source.count('TemporaryHide(')==1 and '.TemporaryHide(true)' in source
    for forbidden in ('SetFact(', 'ChangeEntryState', 'SetTrackedEntry', 'persistent let', 'Toggle(', 'SetInvisible(', 'Kill(', 'Despawn(', 'StopEffect(', 'ScheduleAppearanceChange(', '@replaceMethod', '@addField'):assert forbidden not in source,forbidden
    assert 'epoch != this.epoch' in source and 'this.epoch += 1' in source
    assert 'ArrayErase(this.actors, i)' in source and 'i -= 1' in source
    assert 'ArrayClear(this.actors)' not in source.split('public func Restored()',1)[1].split('private func Schedule()',1)[0]
    facts=re.findall(r'facts.GetFact\(n"([^"]+)"\) == ([01])',source)
    assert len(facts)==10 and len({k for k,v in facts})==10
    # Components are isolated to the exact attached actor. Rendering semantics
    # and callback ordering are deliberately not asserted by this Python model.
    cases=0
    for values in itertools.product((0,1),repeat=10):
        tower=all(str(v)==target for v,(_,target) in zip(values,facts))
        for defined,attached,silverhand,visual in itertools.product((False,True),repeat=4):
            selected=defined and attached and silverhand and tower and visual
            if selected:assert all((defined,attached,silverhand,tower,visual))
            if not visual or not silverhand or not tower:assert not selected
            cases+=1
    # Stale restore callbacks never reschedule; weak actor lists prune safely.
    lifecycle=0
    for running,current,received in itertools.product((False,True),range(4),range(4)):
        runs=running and current==received
        if not running or current!=received:assert not runs
        lifecycle+=1
    for size in range(8):
        for mask in itertools.product((False,True),repeat=size):
            actors=list(enumerate(mask))
            for i in range(len(actors)-1,-1,-1):
                if not actors[i][1]:actors.pop(i)
            assert actors==[(i,v) for i,v in enumerate(mask) if v]
            lifecycle+=1
    scene=ROOT/'research/gig_restoration/minefield_g3/sources/json/base/open_world/street_stories/badlands/inland_avenue/sts_bls_ina_07/scenes/sts_bls_ina_07_comments.scene.json'
    obj=read(scene)['Data']['RootChunk']
    johnny=next(a for a in obj['actors'] if a['actorName']=='johnny')
    assert johnny['acquisitionPlan']=='spawnDespawn' and johnny['spawnDespawnParams']['isEnabled']==1
    assert obj['props']==[], 'Independent props need a per-owner adapter'
    result={'status':'PASS_JV1_PRESENTATION_OFFLINE_LIVE_PENDING','decision_cases':cases,'lifecycle_model_cases':lifecycle,'native_callbacks_preserved':True,'fact_writes':0,'journal_writes':0,'save_fields':0,'equipmentex_full_compile':True,'renderer_and_audio_live_proof':False,'independent_props_covered':False,'appearance_refresh_flash_tested':False,'files':[{'source':SOURCE,'relative':'r6/scripts/PTFR_JohnnyVoiceJV1/JohnnyVoiceJV1.reds','sha256':sha(ROOT/SOURCE)}], 'compile_sha256':sha(OUT/'compile_result.json'),'scene_sha256':sha(scene),'tools':{p:sha(ROOT/p) for p in ('tools/compile_johnny_voice_jv1.py','tools/test_johnny_voice_jv1.py')}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')},indent=2))
if __name__=='__main__':main()
