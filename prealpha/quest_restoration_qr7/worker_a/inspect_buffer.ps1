param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output | Out-Null
$p=Join-Path $w 'prealpha/quest_restoration_qr7/shared/marker_providers_01/provider_2.streamingsector'
if((Get-FileHash -LiteralPath $p).Hash -ne '3639FA7E15D376613D1413409A5E6A9F5E467FAA0A3F00B38BCB1966B38031E1'){throw 'Source drift'}
$f=Read-Cr2wFile $p
$d=$f.RootChunk.NodeData
$props=@($d.GetType().GetProperties()|ForEach-Object {[ordered]@{name=$_.Name;type=$_.PropertyType.FullName}})
$out=[ordered]@{data_type=$d.GetType().FullName;properties=$props;file_buffers=@($f.GetBuffers() | ForEach-Object {[ordered]@{type=$_.GetType().FullName;methods=@($_.GetType().GetMethods()|ForEach-Object {$_.ToString()});properties=@($_.GetType().GetProperties()|ForEach-Object {[ordered]@{name=$_.Name;type=$_.PropertyType.FullName}})}})}
[IO.File]::WriteAllText((Join-Path $Output 'reflection.json'),($out|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
$out|ConvertTo-Json -Depth 7
