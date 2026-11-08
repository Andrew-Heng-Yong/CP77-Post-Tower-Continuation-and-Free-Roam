param([Parameter(Mandatory=$true)][string]$Group,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$result=Get-Content -LiteralPath (Join-Path $workspace ('prealpha/quest_restoration_qr6/groups/'+$Group+'/results.json')) -Raw | ConvertFrom-Json
$pinfile=@($result.source_pin_paths|Where-Object {$_ -match '[\\/]source_pins.json$'})[0]
$rows=Get-Content -LiteralPath $pinfile -Raw | ConvertFrom-Json
$target=[IO.Path]::GetFullPath((Join-Path $workspace $Output))
if(-not $target.StartsWith((Join-Path $workspace 'prealpha/quest_restoration_qr6/groups/C01/reviews/'),[StringComparison]::OrdinalIgnoreCase)){throw 'Review output outside assigned directory'}
if(Test-Path -LiteralPath $target){throw 'Use a fresh review export directory'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
New-Item -ItemType Directory -Path $target | Out-Null
$out=@();$ix=0
foreach($r in $rows){
 $raw=[string]$r.raw
 if((Get-FileHash -LiteralPath $raw -Algorithm SHA256).Hash -cne $r.raw_sha256){throw ('Source changed '+$r.depot)}
 $json=Join-Path $target ('resource_'+$ix+'.json');$ix++
 try{Export-Cr2wJson (Read-Cr2wFile $raw) $json;$out+=@{depot=$r.depot;raw=$raw;raw_sha256=$r.raw_sha256;json=$json;json_sha256=(Get-FileHash -LiteralPath $json -Algorithm SHA256).Hash;status='EXPORTED';worker_json=$r.json;worker_json_sha256=$r.json_sha256}}
 catch{$out+=@{depot=$r.depot;raw=$raw;raw_sha256=$r.raw_sha256;status='OPAQUE';error=$_.Exception.Message}}
}
[IO.File]::WriteAllText((Join-Path $target 'manifest.json'),($out|ConvertTo-Json -Depth 100),[Text.UTF8Encoding]::new($false))
@{group=$Group;resources=$out.Count;opaque=@($out|Where-Object status -eq 'OPAQUE').Count;output=$target}|ConvertTo-Json -Compress
