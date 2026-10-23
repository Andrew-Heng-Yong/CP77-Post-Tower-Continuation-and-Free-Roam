param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
# Explicitly authorized read-only save. Reports stay in workspace; no save writer.
$ErrorActionPreference='Stop'
$out=Join-Path $WorkspaceRoot 'research/gig_restoration/manual20_u4'
New-Item -ItemType Directory -Force $out|Out-Null
$report=Join-Path $out 'facts.json';$cat=Join-Path $out 'catalogue.json'
if((Test-Path $report) -or (Test-Path $cat)){throw 'Existing audit pinned'}
$planPath=Join-Path $WorkspaceRoot 'research/gig_restoration/family_b7/build_plan.json'
$raw=Get-Content $planPath -Raw;$plan=$raw|ConvertFrom-Json -Depth 100
$names=@('q307_done','q307_finished','wat_sts_counter','wat_achievement','kab_06_prestate_triggered','kana_yakin_default_on')
$names+=@([regex]::Matches($raw,'"factName"\s*:\s*"([A-Za-z0-9_]+)"')|ForEach-Object {$_.Groups[1].Value})
foreach($job in $plan.jobs){$names+=@($job.facts);foreach($suffix in @('Queued','Request','Permit','Started','OwnerFinished','Fault','CounterClaim','CounterAck','CountBase')){$names+=$job.tag+'_'+$suffix}}
foreach($prefix in @('PTFRU1_Shark','PTFRG1','PTFRG2')){foreach($suffix in @('Ready','Request','Permit','Started','OwnerFinished','Fault')){$names+=$prefix+'_'+$suffix}}
[IO.File]::WriteAllText($cat,(@{fact_names=@($names|Sort-Object -Unique);source=$planPath;source_sha256=(Get-FileHash $planPath -Algorithm SHA256).Hash}|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
& (Join-Path $PSScriptRoot 'inspect_gig_save.ps1') -SavePaths 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077/ManualSave-20/sav.dat' -CataloguePath 'research/gig_restoration/manual20_u4/catalogue.json' -OutputPath 'research/gig_restoration/manual20_u4/facts.json'
