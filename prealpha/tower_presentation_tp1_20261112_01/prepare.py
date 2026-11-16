"""Stage a native FPP handback candidate and bounded presentation observer."""
from pathlib import Path
import shutil,difflib
from capture import HERE,BASELINE,BASELINE_SHA,sha,read,write,plain

COVER='r6/scripts/PTFR_Consolidated/PTFR_LoadingCoverLC1.reds'
R1='r6/scripts/PTFR_Consolidated/PTFR_RestrictionsR1.reds'
def one(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)

def main():
    target=HERE/'candidate_02';assert not target.exists()
    assert sha(BASELINE)==BASELINE_SHA
    manifest=read(BASELINE);game=Path(manifest['game_root']);base=HERE/'base_02/package'
    for row in manifest['core_files']+manifest['required_files']:
        plain(game/row['path']);assert sha(game/row['path'])==row['sha256']
    for row in manifest['core_files']:assert sha(base/row['path'])==row['sha256']
    source=(base/COVER).read_text(encoding='utf-8-sig')
    changed=one(source,'  private let travelSampleAt: Float;', '  private let travelSampleAt: Float;\n  private let presentationAt:Float;\n  private let presentationTrips:Int32;\n  private let presentationCaptures:Int32;')
    changed=one(changed,'\n    this.travelSampleAt=0.0;','\n    this.travelSampleAt=0.0;\n    this.presentationAt=0.0;this.presentationTrips=0;this.presentationCaptures=0;')
    changed=one(changed,'    if this.leaving || this.released { return; }','''    if this.presentationAt>0.0 && this.EngineNow()>=this.presentationAt {
      this.presentationAt=0.0;
      if this.Required() && this.Fact(n"PTFRPA2_Finished")==1 {
        this.TracePresentation(n"ready-plus-3s");
      }
    }
    if this.leaving || this.released { return; }''')
    changed=one(changed,'    this.released=true;this.Drop();','    this.released=true;this.Drop();\n    this.presentationAt=this.EngineNow()+3.0;')
    changed=one(changed,'    if Equals(stage,n"native-start") { this.travelSampleAt=this.EngineNow()+5.0; }','''    if Equals(stage,n"native-start") {
      this.travelSampleAt=this.EngineNow()+5.0;
      this.presentationTrips+=1;
    }
    if this.presentationTrips>0 && this.presentationTrips<=3 &&
      (Equals(stage,n"native-start") || Equals(stage,n"follow-up") || Equals(stage,n"native-finished")) {
      this.TracePresentation(stage);
    }''')
    changed=one(changed,'  public func TraceFastTravel(stage: CName) -> Void {','''  private func TracePresentation(reason: CName) -> Void {
    if this.presentationCaptures>=10 { return; }
    this.presentationCaptures+=1;
    PresentationTraceTP1.Capture(this.GetGameInstance(),reason);
  }
  public func TraceFastTravel(stage: CName) -> Void {''')
    changed+='\n'+(HERE/'presentation.reds').read_text(encoding='utf-8')
    r1old=(base/R1).read_text(encoding='utf-8-sig')
    r1new=one(r1old,'  private let handRefreshRequested: Bool;','  private let handRefreshRequested: Bool;\n  private let representationReturnQueued: Bool;')
    r1new=one(r1new,'        this.handRefreshRequested = false;','        this.handRefreshRequested = false;\n        this.representationReturnQueued = false;')
    r1new=one(r1new,'    this.handRefreshAttempts -= 1;','''    // Native camera takeover uses this event when handing V back to FPP.
    // Run once only at the existing fresh-treatment handoff, after genuine
    // arrival and Safe() has excluded scenes, workspots, vehicles and menus.
    // Do not activate TPP, move the camera or change any equipment here.
    if !this.representationReturnQueued {
      this.representationReturnQueued = true;
      player.QueueEvent(new DeactivateTPPRepresentationEvent());
      ModLog(n"PTFR_Restrictions_R1", "Post-Tower native first-person representation handback queued; visual verification pending.");
      return;
    }
    this.handRefreshAttempts -= 1;''')
    shutil.copytree(base,target/'package')
    (target/'package'/COVER).write_bytes(changed.replace('\n','\r\n').encode('utf-8'))
    (target/'package'/R1).write_bytes(r1new.replace('\n','\r\n').encode('utf-8'))
    rows=[]
    for row in manifest['core_files']:
        pin=sha(target/'package'/row['path']);assert pin==row['sha256'] or row['path'] in {COVER,R1}
        rows.append({'path':row['path'],'sha256':pin})
    (target/'source.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),changed.splitlines(True),fromfile='RD1/'+COVER,tofile='TP1/'+COVER)),encoding='utf-8')
    (target/'hands.patch').write_text(''.join(difflib.unified_diff(r1old.splitlines(True),r1new.splitlines(True),fromfile='RD1/'+R1,tofile='TP1/'+R1)),encoding='utf-8')
    write(target/'manifest.json',{'status':'FPP_HANDBACK_CANDIDATE_WITH_BLACKOUT_DIAGNOSTIC_UNVERIFIED_LIVE','baseline_manifest_sha256':BASELINE_SHA,'changed_paths':[COVER,R1],'files':rows,'game_writes':0,'save_writes':0})
    print('Staged candidate_02: native first-person handback plus bounded observer; all other 49 Core paths unchanged.')

if __name__=='__main__':main()
