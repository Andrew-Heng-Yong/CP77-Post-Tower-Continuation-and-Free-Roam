param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
. (Join-Path $PSScriptRoot 'afterlife_faces_r5_deployment.ps1')
$audit=Join-Path $WorkspaceRoot 'research/gig_restoration/native_queue_u3';$out=Join-Path $WorkspaceRoot 'build/NativeQueueU3'
if(Test-Path (Join-Path $audit 'install_receipt.json')){throw 'Installed U3 evidence pinned'}
New-Item -ItemType Directory -Force $audit,$out|Out-Null
$oldU=Join-Path $WorkspaceRoot 'redscript/PTFR_NativeReuseU1/NativeReuseU1.reds'
$oldB=Join-Path $WorkspaceRoot 'build/NativeReuseU1/GigFamilyB7.reds'
R5Match $oldU 'F1EEAD97F5E3F24EB23C1103899AFCC2464DDF5F860A220F8AB7153E5678CC50'
R5Match $oldB '0FFCF6A347426018BBE0A6194DA58B912D31A5A64E142ADA64C4CBC14C3AD8AF'
$u=Get-Content $oldU -Raw;$b=Get-Content $oldB -Raw
$anchor='  private func OldUnused() -> Bool {'
$method=@'
  // U3: reserve Watson only when the original prelude can admit Shark.
  // This reads the native conditions; it never advances tiers or counters.
  private func NativeTierEligible() -> Bool {
    return this.Fact("sts_wat_kab_tier_1_4")>0 || (this.Fact("sts_wat_kab_tier_1")>0 && this.Fact("sts_wat_kab_tier_1_1")==0);
  }
'@
if([regex]::Matches($u,[regex]::Escape($anchor)).Count -ne 1){throw 'U1 anchor changed'}
$u=$u.Replace($anchor,$method+"`n"+$anchor)
$old='let permit=this.Tower() && this.Own("Fault")==0'
$new='let permit=this.Tower() && this.NativeTierEligible() && this.Own("Fault")==0'
if([regex]::Matches($u,[regex]::Escape($old)).Count -ne 1){throw 'Permit anchor changed'}
$u=$u.Replace($old,$new).Replace('Native reuse U1 Shark:','Native reuse U3 Shark:')
$u=$u.Replace(' | Original phases/calls/rewards; no custom payout acknowledgement or fixer-credit repair.',' | U3 tier-aware queue; waiting does not reserve Watson. Original phases/calls/rewards; fixer-credit repair still pending.')
$oldGuard='this.Fact("PTFRU1_Shark_Request")==1 && this.Fact("PTFRU1_Shark_OwnerFinished")!=1'
$newGuard='this.Fact("PTFRU1_Shark_Request")==1 && this.Fact("PTFRU1_Shark_OwnerFinished")!=1 && (this.Fact("PTFRU1_Shark_Permit")==1 || this.Fact("PTFRU1_Shark_Started")==1)'
if([regex]::Matches($b,[regex]::Escape($oldGuard)).Count -ne 1){throw 'B7 interlock changed'}
$b=$b.Replace($oldGuard,$newGuard)
$files=@(
 @{source='build/NativeQueueU3/NativeReuseU1.reds';relative='r6/scripts/PTFR_NativeReuseU1/NativeReuseU1.reds';predecessor=R5Hash $oldU},
 @{source='build/NativeQueueU3/GigFamilyB7.reds';relative='r6/scripts/PTFR_GigFamilyB7/GigFamilyB7.reds';predecessor=R5Hash $oldB}
)
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot $files[0].source),$u,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $WorkspaceRoot $files[1].source),$b,[Text.UTF8Encoding]::new($false))
foreach($f in $files){$f.sha256=R5Hash (Join-Path $WorkspaceRoot $f.source)}
R5Json (Join-Path $audit 'manifest.json') ([ordered]@{status='U3_QUEUE_REPAIR_BUILT';files=$files;native_graph_changes=0;native_fact_writes_added=0;persistent_schema_changes=0;note='At Watson count4 stock tier1_4 waits for11. Missing handler diagnosis was premature; repair only premature exclusive reservation, never force unlock.'})
'U3_QUEUE_REPAIR_BUILT'
