-- No callbacks, polling, console spam or automatic mutations. Test() is an
-- explicit disposable-save fixture, not part of normal restoration.
local M = {}
local mq = 'quests/minor_quest/mq043_cyberpsychos'
local target = 'quests/minor_quest/ma_wat_kab_08'
local function fact(q, n) return q:GetFactStr(n) end
local function state(j, path, class)
  local e = j:GetEntryByString(path, class)
  if not e then return nil end
  return j:GetEntryState(e), e
end
function M.Status()
  local q = Game.GetQuestsSystem()
  if not q or not Game.GetPlayer() then return 'P1: load a save first.' end
  local names = {'PTFRP1_TestRequest','PTFRP1_Test_Issued','PTFRP1_TestResetDone','PTFRP1_TestCrateReady','PTFRP1_TestPreparing','PTFRP1_ma_wat_kab_08_Ready','PTFRP1_ma_wat_kab_08_Issued','PTFRP1_ma_wat_kab_08_Entered','PTFRP1_ma_wat_kab_08_Refused','PTFRP1_Report_Issued','PTFRP1_Reward_Issued','ma_kab_08_start','ma_kab_08_finished','ow_psychos_done','ow_psychos_killed','mq043_done','ow_psychos_reward_collected'}
  local rows = {}
  for _, n in ipairs(names) do rows[#rows+1] = n .. '=' .. tostring(fact(q,n)) end
  return table.concat(rows, ' | ')
end
function M.Test(token)
  if token ~= 'DISPOSABLE_SAVE' then return 'Refused: use Test("DISPOSABLE_SAVE") only on a separate manual test save. Discard this branch afterwards.' end
  local q,j,p = Game.GetQuestsSystem(),Game.GetJournalManager(),Game.GetPlayer()
  if not q or not j or not p then return 'Refused: load a save first.' end
  local required = {PostTowerFreeRoamActive=1,PTFRP0_DR13=1,PTFRPA2_Finished=1,PTFRPA2_Fault=0,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q307_ep1_killed=1,q307_active=0,q307_debug_reset=0,q115_point_of_no_return=0,q305_johnny_scene_active=0,PTFRU9_Support_Issued=1,PTFRU9_Support_Fault=0,PTFRN1_Support_Issued=1,PTFRP1_Test_Ready=1,PTFRP1_TestRequest=0,PTFRP1_Test_Issued=0,PTFRP1_TestPreparing=0,PTFRP1_Report_Issued=0,PTFRP1_Reward_Issued=0,PTFRP1_ma_wat_kab_08_Issued=0,ow_psychos_done=17,ow_psychos_reward_collected=1,mq043_done=1,holo_setup_active=0,holo_setup_started=0,holo_interrupt_call=0,holo_force_reset=0}
  for n,v in pairs(required) do if fact(q,n) ~= v then return 'Refused without changes: '..n..' must be '..v..'; actual '..tostring(fact(q,n))..'. Send Status(); do not force this guard.' end end
  if state(j,mq,'gameJournalQuest') ~= gameJournalEntryState.Succeeded or state(j,target,'gameJournalQuest') ~= gameJournalEntryState.Succeeded then return 'Refused without changes: both Psycho Killer and Lt. Mower must already be Succeeded.' end
  local _,obj=state(j,mq..'/mq043_cyberpsychos/01_help_regina','gameJournalQuestObjective')
  if not obj or j:GetObjectiveCurrentCounter(obj) ~= 17 then return 'Refused without changes: native help-Regina journal counter must be 17.' end
  -- Preflight EVERY referenced entry before the first mutation.
  local f=io.open('data.json','r');if not f then return 'Refused: test data missing.' end
  local ok,data=pcall(json.decode,f:read('*a'));f:close()
  if not ok or type(data)~='table' or data.key~='ma_wat_kab_08' or type(data.paths)~='table' then return 'Refused: invalid test data.' end
  local onscreens={}
  for _,v in ipairs(data.paths) do
    local _,entry=state(j,v.path,v.class)
    if not entry then return 'Refused without changes: journal entry missing '..v.path end
    if v.class=='gameJournalOnscreen' then onscreens[#onscreens+1]=entry end
  end
  -- First close normal admission. The native test graph rechecks completion,
  -- consumes its one-shot owner, resets this encounter and then releases it.
  q:SetFactStr('PTFRP1_TestPreparing',1)
  for _,entry in ipairs(onscreens) do j:SetEntryVisited(entry,false) end
  q:SetFactStr('PTFRP1_TestRequest',1)
  return 'Queued TEST ONLY: Lt. Mower replay, 16/17 reports with zero killed, and one native Regina-crate refill. Close CET; stay away from the encounter until TestResetDone=1. Do not keep this branch as your main save. NPC/device replay remains unverified.'
end
return M
