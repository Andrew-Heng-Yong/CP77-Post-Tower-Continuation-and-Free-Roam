-- Offline API double. Deliberately no gameplay setters.
callbacks, hooks, facts, listeners, credits, restrictions = {}, {}, {}, {}, {}, {}
function registerForEvent(name,fn) callbacks[name]=fn end
function ObserveBefore(c,m,fn) hooks[c.."."..m]=fn end
function ObserveAfter(c,m,fn) hooks[c.."."..m]=fn end
function ModArchiveExists() return true end
function IsDefined(x) return type(x)=="table" end
function CNameMock(x) return x end
CName={new=CNameMock};TweakDBID={new=CNameMock}
function NewProxy(spec) return {Target=function(self)return spec end,Function=function(self)return "Callback" end} end
json={encode=pyEncode,decode=pyDecode}
io={open=function(path,mode)
  if path=="events.json" then return {read=function()return eventJSON end,close=function()end} end
  assert(path=="ptfr_runtime.jsonl" and mode=="a")
  return {write=function(self,line)capture(line)end,flush=function()end,close=function()end}
end}
local defs={UI_CreditsScreen={},PlayerStateMachine={HighLevel="HighLevel",IsMovingHorizontally="IsMovingHorizontally"}}
for _,k in ipairs({"FinalBoardsOpened","CredditsScrolling","FinalBoardsVideosFinished","LoadPonRSave","ForceStopCredits","SkippingCreditsDisabled"}) do defs.UI_CreditsScreen[k]=k;credits[k]=false end
credits.LoadPonRSave=true
for _,k in ipairs({"q307_active","q307_done","q307_finished","q307_2079","q307_main_game_killed","PostTowerFreeRoamActive"}) do facts[k]=0 end
facts.q307_active=1;facts.q307_2079=1
for _,k in ipairs({"NoMovement","BlockDeviceInteractions","NoPhotoMode","NoRadialMenus","NoTimeSkip","NoWorldInteractions"}) do restrictions["GameplayRestriction."..k]=true end
tier,visible,blocked=5,false,true
local psm={GetInt=function(self,k) assert(k=="HighLevel");return tier end,GetBool=function(self,k) assert(k=="IsMovingHorizontally");return false end}
local player={GetEntityID=function()return {hash="mock-player"}end,GetPlayerStateMachineBlackboard=function()return psm end,
 IsInvisible=function()return not visible end,GetWorldPosition=function()return{x=1,y=2,z=3}end}
local quests={GetFactStr=function(self,n)return facts[n] or 0 end,
 RegisterListener=function(self,n,p,f)assert(f=="Callback" and p.args[1]=="Int32");listeners[n]=p.callback;return 1 end,
 UnregisterListener=function()end}
local board={GetBool=function(self,k)assert(k);return credits[k]end,RegisterListenerBool=function(self,n,p,f)assert(p.args[1]=="Bool");return {}end,UnregisterListenerBool=function()end}
boardAvailable=false
boardDefExposed=false
Game={GetPlayer=function()return player end,GetQuestsSystem=function()return quests end,
 GetBlackboardSystem=function()return {Get=function()return boardAvailable and board or nil end}end,
 GetStatusEffectSystem=function()return {HasStatusEffect=function(self,id,r)return restrictions[r] end}end,
 GetQuestsContentSystem=function()return {IsTokensActivationBlocked=function()return blocked end,IsTokensActivationBlockedBySource=function(self,s)assert(s=="finalboards");return blocked end}end,
 IsSavingLocked=function()return true end,GetVehicleSystem=function()return {}end,
 GetPhoneManager=function()return {IsPhoneCallActive=function()return false end}end}
function GetAllBlackboardDefs()
  if boardDefExposed then return defs end
  return {PlayerStateMachine=defs.PlayerStateMachine}
end
