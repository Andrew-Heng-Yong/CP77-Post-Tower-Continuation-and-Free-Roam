module PTFR.JournalLabelJ1

// Empty details retain the stock widget's authored sample quest title.
// UI-only: no journal state, tracking, progression or quest-fact writes.
@addMethod(QuestDetailsPanelController)
public final func PTFRJ1RestoreEmptyTitle() -> Void {
  if IsDefined(this.m_currentQuestData) { return; }
  inkTextRef.SetText(this.m_questTitle, GetLocalizedText("UI-PanelNames-JOURNAL"));
}

@addMethod(questLogGameController)
private final func PTFRJ1CompletedTower() -> Bool {
  let player = this.GetPlayerControlledObject();
  if !IsDefined(player) { return false; }
  let facts = GameInstance.GetQuestsSystem(player.GetGame());
  if !IsDefined(facts) { return false; }
  return facts.GetFact(n"PostTowerFreeRoamActive") == 1 && facts.GetFact(n"PTFRP0_DR13") == 1 &&
    facts.GetFact(n"q307_done") == 1 && facts.GetFact(n"q307_finished") == 1 && facts.GetFact(n"q307_2079") == 1 &&
    facts.GetFact(n"q307_main_game_killed") == 1 && facts.GetFact(n"q307_ep1_killed") == 1 &&
    facts.GetFact(n"q307_active") == 0 && facts.GetFact(n"q115_point_of_no_return") == 0 && facts.GetFact(n"q305_johnny_scene_active") == 0;
}

@wrapMethod(questLogGameController)
protected cb func OnInitialize() -> Bool {
  let result = wrappedMethod();
  if this.PTFRJ1CompletedTower() && IsDefined(this.m_detailsPanelCtrl) {
    this.m_detailsPanelCtrl.PTFRJ1RestoreEmptyTitle();
  }
  return result;
}
