param([string]$OutputName='bar_provider_01')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path
$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b'
$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_1_nightcity.archive'
$depot='base\worlds\03_night_city\_compiled\default\ep1\quest_7abca2b8d18f8562.streamingsector'
$before=(Get-FileHash -LiteralPath $archive).Hash
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc)
$entries=@($arc.Files.Values | Where-Object {$_.Name -ceq $depot})
if($entries.Count -ne 1){throw ('Exact provider entries: '+$entries.Count)}
$raw=Join-Path $out 'q302_bar.streamingsector'
$m=[IO.MemoryStream]::new()
try{$entries[0].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
if((Get-FileHash -LiteralPath $raw).Hash -cne '27D58B701489CF8AF978C8EF44B27C8D1115452BDC818490D2F637A4AA26D3DF'){throw 'Pinned historical bar provider hash differs'}
$status='EXPORTED';$errorText=$null;$json=Join-Path $out 'q302_bar.streamingsector.json'
try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}catch{$status='OPAQUE';$errorText=$_.Exception.Message}
$after=(Get-FileHash -LiteralPath $archive).Hash
if($before -cne $after){throw 'Read-only source archive changed'}
@{archive=$archive;archive_sha256=$before;depot=$depot;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;status=$status;json=$json;json_sha256=$(if(Test-Path -LiteralPath $json){(Get-FileHash -LiteralPath $json).Hash}else{$null});error=$errorText;archive_unchanged=$true}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Pinned bar provider '+$status)
