param([Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
if(Test-Path -LiteralPath $Output){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $Output|Out-Null
$pins=@(@{name='current';path='prealpha/quest_restoration_qr7/shared/marker_providers_01/provider_2.streamingsector';sha='3639FA7E15D376613D1413409A5E6A9F5E467FAA0A3F00B38BCB1966B38031E1'},@{name='historical';path='research/phase2b_p4/staging_scan/ep1_1_nightcity/raw/base/worlds/03_night_city/_compiled/default/ep1/always_loaded_0.streamingsector';sha='E677EC8D8EB189AC4E6FD98D890FD5D108281ADA839D86D2EFD6E9FA902BB9A3'})
$records=@()
foreach($pin in $pins){
 $p=Join-Path $w $pin.path
 if((Get-FileHash -LiteralPath $p).Hash -ne $pin.sha){throw 'Input drift'}
 $f=Read-Cr2wFile $p
 $bytes=$f.RootChunk.NodeData.Buffer.GetBytes()
 $target=Join-Path $Output ($pin.name+'.buffer')
 [IO.File]::WriteAllBytes($target,$bytes)
 $records+=@{name=$pin.name;source=$p;source_sha256=$pin.sha;buffer=$target;buffer_sha256=(Get-FileHash -LiteralPath $target).Hash;bytes=$bytes.Length;mem_size=$f.RootChunk.NodeData.Buffer.MemSize;exported_entries=$f.RootChunk.NodeData.Data.Count}
}
[IO.File]::WriteAllText((Join-Path $Output 'manifest.json'),(@{scope='Read-only decoded raw buffer extraction, no source serialization';records=$records;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$records|ConvertTo-Json -Depth 8
