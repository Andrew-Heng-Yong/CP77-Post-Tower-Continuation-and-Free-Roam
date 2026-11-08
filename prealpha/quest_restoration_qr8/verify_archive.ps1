param([string]$Output='verification/archive_baseline_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot $Output))
if(-not $out.StartsWith([IO.Path]::GetFullPath($PSScriptRoot)+[IO.Path]::DirectorySeparatorChar)){throw 'Fresh QR8 output containment required'}
if(Test-Path -LiteralPath $out){throw 'Preserve previous verification output'}
$ep=Join-Path $PSScriptRoot 'source_epoch_00.json';$epoch=Get-Content -LiteralPath $ep -Raw|ConvertFrom-Json -Depth 100
$archive=Join-Path $epoch.candidate 'package/archive/pc/mod/zzzz_PTFR_Combined.archive'
if((Get-FileHash -LiteralPath $archive).Hash -cne $epoch.archive_sha256){throw 'Archive pin mismatch'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$packed=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError'){throw 'Archive read failed'}
$expected=@{};foreach($x in $epoch.source_resources.PSObject.Properties){$expected[$x.Name]=$x.Value}
if($packed.Files.Count -ne $expected.Count){throw 'Archive count differs'}
$rows=@();$keys=@{}
foreach($dep in($expected.Keys|Sort-Object)){
 $key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)
 if($keys.ContainsKey($key.ToString())){throw 'Depot FNV collision'};$keys[$key.ToString()]=$dep
 if(-not $packed.Files.ContainsKey($key)){throw "Missing member $dep"}
 $mem=[IO.MemoryStream]::new();try{$packed.Files[$key].Extract($mem);$h=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}
 if($h -cne $expected[$dep]){throw "Member mismatch $dep"};$rows+=,@{depot=$dep;key=$key.ToString();sha256=$h}
}
New-Item -ItemType Directory -Path $out|Out-Null
@{status='PASS_FRESH_ALL_ARCHIVE_PAYLOADS_READ_BACK_NO_REBUILD';source_epoch='QR8:00';source_epoch_sha256=(Get-FileHash -LiteralPath $ep).Hash;archive=$archive;archive_sha256=$epoch.archive_sha256;payloads=$rows.Count;rows=$rows;game_writes=0;save_writes=0}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $out 'result.json') -Encoding utf8NoBOM
'PASS_FRESH_ALL_ARCHIVE_PAYLOADS_READ_BACK_NO_REBUILD'
