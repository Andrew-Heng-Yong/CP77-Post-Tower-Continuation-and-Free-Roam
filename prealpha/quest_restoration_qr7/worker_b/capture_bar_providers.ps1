param([string]$OutputName='bar_provider_02')
$ErrorActionPreference='Stop'
$ws=(Get-Location).Path;$homeDir=Join-Path $ws 'prealpha/quest_restoration_qr7/worker_b';$out=Join-Path $homeDir $OutputName
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$archive='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\ep1\ep1_1_nightcity.archive'
$before=(Get-FileHash -LiteralPath $archive).Hash
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$arc=$null
[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$arc)
$rows=@();$i=0
foreach($depot in @('base\worlds\03_night_city\_compiled\default\ep1\quest_7abca2b8d18f8562.streamingsector','base\worlds\03_night_city\_compiled\default\quest_7abca2b8d18f8562.streamingsector')){
 $entries=@($arc.Files.Values | Where-Object {$_.Name -ceq $depot})
 if($entries.Count -ne 1){throw ('Exact provider entries: '+$entries.Count+' '+$depot)}
 $raw=Join-Path $out ('provider_'+$i+'.streamingsector');$json=$raw+'.json';$m=[IO.MemoryStream]::new()
 try{$entries[0].Extract($m);[IO.File]::WriteAllBytes($raw,$m.ToArray())}finally{$m.Dispose()}
 $status='EXPORTED';$errorText=$null
 try{Export-Cr2wJson (Read-Cr2wFile $raw) $json}catch{$status='OPAQUE';$errorText=$_.Exception.Message}
 $rows+=@{archive=$archive;archive_sha256=$before;depot=$depot;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;status=$status;json=$json;json_sha256=$(if(Test-Path -LiteralPath $json){(Get-FileHash -LiteralPath $json).Hash}else{$null});error=$errorText};$i++
}
if($before -cne (Get-FileHash -LiteralPath $archive).Hash){throw 'Read-only source archive changed'}
@{archive_unchanged=$true;providers=$rows;historical_expected='27D58B701489CF8AF978C8EF44B27C8D1115452BDC818490D2F637A4AA26D3DF'}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8
Write-Output ('Exact bar provider probes: '+$rows.Count)
