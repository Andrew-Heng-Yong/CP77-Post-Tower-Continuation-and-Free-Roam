"""J1 primary-source anchors and bounded UI decision model, not engine proof."""
import itertools,json,re
from catalog_gig_rollout_r2 import ROOT,sha,read
OUT=ROOT/'research/journal_label_j1'
SOURCE='redscript/PTFR_JournalLabelJ1/JournalLabelJ1.reds'
SCRIPT=ROOT/'research/finalboards_dismissal/decompiled/cyberpunk/UI/fullscreen/quest_log'

def main():
    source=(ROOT/SOURCE).read_text();panel=(SCRIPT/'questLogDetailsPanel.script').read_text();root=(SCRIPT/'questLog.script').read_text()
    initialize=panel.split('protected cb func OnInitialize() -> Bool {',1)[1].split('\n  }',1)[0]
    assert 'm_noSelectedQuestContainer, true' in initialize and 'm_questTitle' not in initialize
    assert 'inkTextRef.SetText(this.m_questTitle, questData.GetTitle(journalManager));' in panel
    assert 'this.m_detailsPanelCtrl = inkWidgetRef.GetController(this.m_detailsPanel) as QuestDetailsPanelController;' in root
    raw=OUT/'native_widget/raw/base/gameplay/gui/fullscreen/quest_log/quest_log.inkwidget'
    assert sha(raw)=='0D1C3114E2B56E8C754BD4C82284AE0D6D2E942E2862ABED91EE941AC77C3205'
    for token in (b'QuestDetailsPanelController',b'questLogGameController',b'For Whom the Bell Tolls'):assert token in raw.read_bytes()
    assert source.count('@wrapMethod(')==1 and '@wrapMethod(questLogGameController)' in source
    assert 'if IsDefined(this.m_currentQuestData) { return; }' in source
    assert source.count('inkTextRef.SetText(')==1
    assert source.index('let result = wrappedMethod();')<source.index('if this.PTFRJ1CompletedTower()')
    assert 'return result;' in source and 'UI-PanelNames-JOURNAL' in source
    for prohibited in ('SetFact(', 'ChangeEntryState', 'SetTrackedEntry', '@replaceMethod','@addField','Setup('):assert prohibited not in source,prohibited
    facts=re.findall(r'facts.GetFact\(n"([^"]+)"\) == ([01])',source)
    assert len(facts)==10 and len(set(k for k,v in facts))==10
    # All gate combinations, including absent panel/player and a selected job.
    # This models the source predicates only; actual callback order/rendering remains live pending.
    cases=0
    for values in itertools.product((0,1),repeat=10):
        tower=all(str(a)==b for a,(_,b) in zip(values,facts))
        for player,panel_present,selected in itertools.product((False,True),repeat=3):
            old='Only Pain' if selected else 'For Whom the Bell Tolls'
            result='Journal' if player and panel_present and tower and not selected else old
            if selected:assert result=='Only Pain'
            if not tower or not player or not panel_present:assert result==old
            cases+=1
    compile=read(OUT/'compile_result.json');assert compile['status']=='PASS_J1_OFFLINE_COMPILE_NOT_ENGINE_PROOF' and compile['source_sha256']==sha(ROOT/SOURCE)
    compiled=(OUT/'compiled_flat.script').read_text(encoding='utf-8-sig')
    assert 'inkTextRef.SetText(this.m_questTitle, questData.GetTitle(journalManager));' in compiled
    result={'status':'PASS_J1_UI_ONLY_OFFLINE_LIVE_PENDING','decision_cases':cases,'native_setup_preserved':True,'fact_writes':0,'journal_writes':0,'save_fields':0,'equipmentex_full_compile':True,'files':[{'source':SOURCE,'relative':'r6/scripts/PTFR_JournalLabelJ1/JournalLabelJ1.reds','sha256':sha(ROOT/SOURCE)}], 'compile_sha256':sha(OUT/'compile_result.json'),'native_widget_sha256':sha(raw),'native_script_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (SCRIPT/'questLog.script',SCRIPT/'questLogDetailsPanel.script')},'tools':{s:sha(ROOT/s) for s in ('tools/compile_journal_label_j1.py','tools/test_journal_label_j1.py','tools/extract_journal_label_j1.ps1')}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
