param([string]$OutputName='producer_readback_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out|Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_2_gamedata.archive'
$before=(Get-FileHash -LiteralPath $archive).Hash
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc)
$targets=Get-Content -Raw -LiteralPath (Join-Path $homeDir 'producer_targets_01.json')|ConvertFrom-Json
$rows=@();$i=0
foreach($t in $targets){
 $entries=@($arc.Files.Values|Where-Object {$_.Name -ceq $t.depot});if($entries.Count -ne 1){throw ('Exact producer count '+$entries.Count)}
 $raw=Join-Path $out ('producer_'+$i+'.questphase');$json=$raw+'.json';$m=[IO.MemoryStream]::new()
 try{$entries[0].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 Export-Cr2wJson (Read-Cr2wFile $raw) $json
 $rows+=@{depot=$t.depot;quest_id=$t.quest_id;graph=$t.graph;node=$t.node;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;json=$json;json_sha256=(Get-FileHash -LiteralPath $json).Hash;archive=$archive;archive_sha256=$before;pinned_old_raw=$t.pinned_old_raw;pinned_old_raw_sha256=$t.raw_sha256;current_matches_pinned=((Get-FileHash -LiteralPath $raw).Hash -ceq $t.raw_sha256)};$i++
}
if($before -cne (Get-FileHash -LiteralPath $archive).Hash){throw 'Read-only stock source archive changed'}
@{archive_unchanged=$true;producers=$rows}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Current native gig producer readbacks '+$rows.Count)
