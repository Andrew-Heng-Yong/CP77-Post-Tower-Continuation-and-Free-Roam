"""Prepare the bounded post-credits presentation repair; never deploy."""
from pathlib import Path
import difflib, shutil
from capture import HERE, BASELINE, BASELINE_SHA, sha, read, write, plain

COVER='r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
R1='r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds'

def one(text, old, new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)

def main():
    target=HERE/'candidate_03'; assert not target.exists()
    assert sha(BASELINE)==BASELINE_SHA
    baseline=read(BASELINE); game=Path(baseline['game_root']); base=HERE/'base_01/package'
    for row in baseline['core_files']+baseline['required_files']:
        plain(game/row['path']); assert sha(game/row['path'])==row['sha256']
    for row in baseline['core_files']:assert sha(base/row['path'])==row['sha256']
    old={p:(base/p).read_text(encoding='utf-8-sig') for p in (COVER,R1)}
    cover=one(old[COVER],'  private let presentationCaptures:Int32;', '''  private let presentationCaptures:Int32;
  private let presentationRepairState:Int32;
  private let presentationRepairAt:Float;
  private let presentationRepairActor:wref<PlayerPuppet>;
  private let presentationStateCaptures:Int32;''')
    cover=one(cover,'    this.presentationAt=0.0;this.presentationTrips=0;this.presentationCaptures=0;', '''    this.presentationAt=0.0;this.presentationTrips=0;this.presentationCaptures=0;
    this.presentationRepairState=0;this.presentationRepairAt=0.0;
    this.presentationRepairActor=null;this.presentationStateCaptures=0;''')
    cover=one(cover,'    if this.stableSince<0.0 { this.stableSince=this.Now(); }', '''    if !this.FinishPresentationTP2() { this.stableSince=-1.0;this.Heartbeat();return; }
    if this.stableSince<0.0 { this.stableSince=this.Now(); }''')
    cover=one(cover,'      i+=1;\n    }\n    ModLog(n"PTFR_PresentationTP1", NameToString(label)+" components=', '''      let skin=components[i] as entSkinnedMeshComponent;
      if IsDefined(skin) && count<32 {
        ModLog(n"PTFR_PresentationTP1", NameToString(label)+" skinnedMesh="+NameToString(skin.GetName())+
          " type="+NameToString(skin.GetClassName())+" enabled="+ToString(skin.IsEnabled())+
          " renderEnabled="+ToString(skin.isEnabled)+" appearance="+NameToString(skin.meshAppearance)+
          " mask="+ToString(skin.chunkMask)+" visibilityParam="+NameToString(skin.visibilityAnimationParam)+
          " renderingPlaneParam="+NameToString(skin.renderingPlaneAnimationParam));
        count+=1;
      }
      i+=1;
    }
    ModLog(n"PTFR_PresentationTP1", NameToString(label)+" components=''')
    handoff=(HERE/'handoff.reds').read_text(encoding='utf-8')
    repair,rest=handoff.split('// Observe the real ink state transitions;',1)
    wrapper,trace=rest.split('@addMethod(StartupCoverLC1)\n',1)
    methods=repair.replace('@addMethod(StartupCoverLC1)\n','')+'\n'+trace
    methods='\n'.join('  '+line if line else '' for line in methods.splitlines())+'\n'
    cover=one(cover,'  public func Status() -> String { return "LC3 visible/released=',methods+'  public func Status() -> String { return "LC3 visible/released=')
    cover+='\n// Observe the real ink state transitions;'+wrapper
    r1=old[R1]
    start=r1.index('    // Native camera takeover uses this event when handing V back to FPP.')
    end=r1.index('    this.handRefreshAttempts -= 1;',start)
    r1=r1[:start]+'''    // TP2 performs the full representation cycle under the setup cover after
    // this attachment pass settles; do not race it with a standalone return.
'''+r1[end:]
    r1=one(r1,'  private func ReportRefundReadiness() -> Void {', '''  // Transient attachment work only; does not infer visual success from an item.
  public func PTFRTP2HandsSettled() -> Bool { return this.handRefreshAttempts == 0; }
  private func ReportRefundReadiness() -> Void {''')
    shutil.copytree(base,target/'package')
    for p,new in ((COVER,cover),(R1,r1)):
        (target/'package'/p).write_bytes(new.replace('\n','\r\n').encode('utf-8'))
        (target/(Path(p).stem+'.patch')).write_text(''.join(difflib.unified_diff(old[p].splitlines(True),new.splitlines(True),fromfile='TP1/'+p,tofile='TP2/'+p)),encoding='utf-8')
    rows=[]
    for row in baseline['core_files']:
        h=sha(target/'package'/row['path']); assert h==row['sha256'] or row['path'] in (COVER,R1)
        rows.append({'path':row['path'],'sha256':h})
    write(target/'manifest.json',{'status':'CANDIDATE_RETAINED_HANDOFF_PRESENTATION_REPAIR_LIVE_UNVERIFIED',
        'baseline_manifest_sha256':BASELINE_SHA,'changed_paths':[COVER,R1],'files':rows,'game_writes':0,'save_writes':0})
    print('Prepared TP2 candidate_03: two script changes, 49 exact baseline paths, no deployment.')

if __name__=='__main__':main()
