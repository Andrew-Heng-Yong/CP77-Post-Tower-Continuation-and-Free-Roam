param()
$ErrorActionPreference='Stop'
$workspace='C:\Users\Ayong\Documents\cp77 modding\tower ws'
$planPath=Join-Path $workspace 'research\gig_restoration\native_gigs_u9\build_plan.json'
$plan=Get-Content -LiteralPath $planPath -Raw|ConvertFrom-Json -Depth 100
$installed='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\r6\scripts\PTFR_PreAlpha\PTFR_NativeGigsU9\NativeGigDataU9.generated.reds'
$text=Get-Content -LiteralPath $installed -Raw
$ids=@([regex]::Matches([regex]::Match($text,'public static func IDs\(\).*?return \[(.*?)\];').Groups[1].Value,'"(sts_\w+)"')|ForEach-Object{$_.Groups[1].Value})
if($ids.Count -ne 72){throw 'Unexpected whitelist size'}
$rows=[Collections.Generic.List[object]]::new()
$lines=[Collections.Generic.List[string]]::new()
$lines.Add('module PTFR.ActivityStateR3')
$lines.Add('// Generated read-only fact labels from the pinned U9 original-parent graph recipe.')
$lines.Add('public abstract class GigDiagnosticsDataPA5 {')
$lines.Add('  public static func ParentFacts(i: Int32) -> array<String> {')
for($i=0;$i -lt $ids.Count;$i++){
  $id=$ids[$i];$jobs=@($plan.jobs|Where-Object id -eq $id)
  if($jobs.Count -ne 1){throw 'Missing/duplicate source job: '+$id}
  $raw=@($jobs[0].parent.ancestors,$jobs[0].parent.nested)|ConvertTo-Json -Depth 100
  $names=@([regex]::Matches($raw,'"factName"\s*:\s*"([A-Za-z0-9_]+)"')|ForEach-Object{$_.Groups[1].Value}|Sort-Object -Unique)
  # Discovery facts come from actual per-gig map slices, not a region guess.
  $mapNames=@()
  foreach($file in Get-ChildItem -LiteralPath (Join-Path $workspace 'research\gig_restoration\native_gigs_u9') -Filter ($id+'_map*.json') -File){
    $mapRaw=Get-Content -LiteralPath $file.FullName -Raw
    $mapNames+=@([regex]::Matches($mapRaw,'"factName"\s*:\s*"([A-Za-z0-9_]+)"')|ForEach-Object{$_.Groups[1].Value}|Where-Object{$_ -notlike 'PTFR*'})
  }
  $names=@(@($names)+@($mapNames)|Sort-Object -Unique)
  if($jobs[0].shared_gate -eq 'ep1_tier3'){$names+=,'PTFRU9_EP1Tier3_Ready'}
  $quoted=@($names|ForEach-Object{'"'+$_+'"'}) -join ','
  $lines.Add('    if i=='+$i+' { return ['+$quoted+']; }')
  $rows.Add([ordered]@{index=$i;id=$id;facts=$names})
}
$lines.Add('    let empty: array<String>; return empty;')
$lines.Add('  }')
$lines.Add('}')
$output=Join-Path $PSScriptRoot 'GigDiagnosticsDataPA5.generated.reds'
if(Test-Path -LiteralPath $output){throw 'Generated diagnostic data already exists'}
[IO.File]::WriteAllText($output,($lines -join "`n")+"`n",[Text.UTF8Encoding]::new($false))
$report=Join-Path $workspace 'research\postending_pa5\gigs\data_manifest.json'
if(Test-Path -LiteralPath $report){throw 'Evidence report already exists'}
[void][IO.Directory]::CreateDirectory((Split-Path -Parent $report))
$data=[ordered]@{status='READ_ONLY_DIAGNOSTIC_DATA';whitelist_count=$ids.Count;source_plan_sha256=(Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash;installed_catalogue_sha256=(Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash;generated_sha256=(Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash;rows=$rows.ToArray();runtime_writes=0}
[IO.File]::WriteAllText($report,($data|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
'Generated diagnostic data for '+$ids.Count+' whitelisted gigs.'
