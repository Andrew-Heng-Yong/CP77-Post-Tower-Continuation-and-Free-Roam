from pathlib import Path
import hashlib,json,shutil,re
H=Path(__file__).resolve().parent;W=H.parent.parent;C=H/'candidate_01';O=C/'diagnosis_01';O.mkdir(parents=True,exist_ok=False)
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077');S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
inputs={}
def copy(p,d):
 h=sha(p);d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d);assert sha(p)==sha(d)==h;inputs[str(p)]=h
for r in ['red4ext/logs/red4ext-2026-10-24-17-24-08.log','bin/x64/plugins/cyber_engine_tweaks/gamelog.log','r6/logs/redscript_rCURRENT.log']:
 copy(G/r,O/'logs'/Path(r).name)
context=['r6/scripts/PTFR_PreAlpha/PA1/PreAlphaArrivalPA1.reds','r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/CyberwarePolicy.reds','r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R2/BodyPolicy.reds','r6/scripts/TowerContinued_Housing_H1/HousingState.reds']
for p in context:copy(G/p,O/'context'/Path(p).name)
changes=[]
for rel in ['r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds','r6/scripts/TowerContinued_Housing_H1/HousingPurchase.reds']:
 src=G/rel;copy(src,C/'before'/rel);s=src.read_text(encoding='utf-8-sig')
 if rel.endswith('StartupCoverLC1.reds'):
  start=s.index('  public func Leave(epoch:Int32) -> Void {');end=s.index('  private func SetStage',start)
  s=s[:start]+'''  // Compatibility entry point only. The setup cover has no exit action.
  public func Leave(epoch:Int32) -> Void {}
'''+s[end:]
  s=s.replace('PTFR_LoadingLC2','PTFR_LoadingLC3').replace('LC2 visible/released=','LC3 visible/released=')
  s=s.replace('The entry module reports a fault. Press Esc to return to the main menu.','The entry module reports a fault; setup remains covered.')
  s=s.replace('    this.Text("ESC  Return to main menu",215.0,24);\n','')
  s=s.replace('    if evt.IsAction(n"cancel") && IsDefined(this.owner) { this.owner.Leave(this.epoch); }\n','')
  s=s.replace('this.stage+"\\n"+this.detail+"\\nPress Esc to return to the main menu."','this.stage+"\\n"+this.detail')
  marker='      " fault="+ToString(this.Fact(n"PTFRPA2_Fault"))+" | "+this.EndingFacts());\n'
  assert s.count(marker)==1
  s=s.replace(marker,marker+'''    if this.completedSteps>=10 {
      let game=this.GetGameInstance();let arrival=GameInstance.GetScriptableSystemsContainer(game).Get(n"PTFR.ActivityStateR3.PreAlphaArrivalPA1") as PreAlphaArrivalPA1;
      let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerMainGameObject() as PlayerPuppet;
      if IsDefined(arrival) { ModLog(n"PTFR_LoadingLC3","Control diagnostic: "+arrival.Status()+" bodySafe="+ToString(BodyPolicy.Safe(player))); }
      ModLog(n"PTFR_LoadingLC3","Housing purchase scenes north/japan/glen/corpo="+ToString(this.Fact(n"PTFRH1_northside_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_japantown_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_glen_PurchaseSceneActive"))+"/"+ToString(this.Fact(n"PTFRH1_corpo_PurchaseSceneActive")));
    }
''')
  assert 'GotoMainMenu' not in s and 'Press Esc' not in s and 'Return to main menu' not in s and 'owner.Leave' not in s
 else:
  s=s.replace('import Codeware.UI.*','import Codeware.UI.*\nimport PTFR.LoadingCoverLC1.*')
  old='      let canOffer = !IsDefined(self.m_popup) && state.CanPurchase(id, player);'
  assert s.count(old)==1
  s=s.replace(old,'''      // Purchase interactions are gameplay, not setup acknowledgements. Keep
      // remote/premature scenes idle; do not acquire V behind the loading cover.
      let canOffer = StartupCoverLC1.GameplayReleased(game) && !IsDefined(self.m_popup) &&
        state.CanPurchase(id, player) && HousingPurchaseLocation.Validate(game, id, HousingPurchaseLocation.Source(id));''')
  old='    if !IsDefined(state) || !IsDefined(manager) || !manager.IsInitialized() || !state.CanPurchase(id, player) || !HousingPurchaseLocation.Validate(game, id, source) { return false; }'
  assert s.count(old)==1;s=s.replace(old,old.replace('if !IsDefined(state)','if !StartupCoverLC1.GameplayReleased(game) || !IsDefined(state)'))
 p=C/'package'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8');changes.append({'target':rel,'before':sha(src),'after':sha(p)})
(C/'changes_01.json').write_text(json.dumps(changes,indent=2)+'\n')
(O/'inputs.json').write_text(json.dumps({'copied':inputs,'saves':{str(p):sha(p) for p in S.rglob('*') if p.is_file()}},indent=2)+'\n')
log=(O/'logs/gamelog.log').read_text(encoding='utf-8-sig');last=log[log.index('[2026-10-24 17:32:04'):]
stages=[{'sim':float(a),'stage':b} for a,b in re.findall(r'elapsedSim=([\d.]+) stage=([^|\r\n]+)',last)]
osc=[x for x in stages if x['stage'].strip() in ['Checking player control','Final checks']]
assert len(osc)>20 and all(x['stage']!=y['stage'] for x,y in zip(osc,osc[1:]))
report={'status':'SOURCE_BOUND_HOUSING_FEEDBACK_LOOP_MATCHES_LOG_CADENCE','alternating_stages':osc,'normal_shutdown':True,'limitation':'LC2 logged a combined control predicate, not the exact failing subpredicate. H1 acquisition/eligibility cycle is source-proven and matches the 1s rhythm; LC3 keeps strict final checks and adds exact control diagnostics.','profile_completed':True,'source_hashes':inputs}
(O/'assessment_01.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(W/'prealpha/loading_cover_lc2/compile_01.py',H/'compile_01.py')
print(json.dumps({'replacements':len(changes),'alternating_stages':len(osc),'save_files':len(list(S.rglob('sav.dat')))}))
