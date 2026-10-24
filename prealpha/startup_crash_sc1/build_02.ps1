$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$W=Split-Path -Parent (Split-Path -Parent $PSScriptRoot);$C=Join-Path $PSScriptRoot 'candidate_01';$source=Join-Path $C 'native_source_02'
if(Test-Path $source){throw 'Use successor build'}
. (Join-Path $W 'tools/build_phase2a.ps1') -WorkspaceRoot $W -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$rel='archive/pc/mod/00000000_TowerContinued_Housing_H1.archive';$installed=Join-Path $game $rel
$expected='E8F4F535A9A24B8C080360D68C8993B19EDE12366118284E5A9CE683A0CA523E'
if((Get-FileHash -LiteralPath $installed).Hash -cne $expected){throw 'H1 baseline differs'}
$prepared=Get-Content -LiteralPath (Join-Path $C 'prepared_01.json') -Raw|ConvertFrom-Json -Depth 100
if($prepared.resources.Count -ne 9){throw 'Unexpected scene scope'}
function OpenArc($path){$a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Read failed'};return $a}
function Bytes($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);return ,$m.ToArray()}finally{$m.Dispose()}}
function HashBytes($b){[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($b))}
$arc=OpenArc $installed;if($arc.Files.Count -ne 17){throw 'Resource count differs'}
$before=@{};$names=@{}
foreach($e in $arc.Files.Values){
 $name=$e.Name;if([IO.Path]::IsPathRooted($name) -or $name.Contains(':') -or $name -match '(^|[/\\])\.\.([/\\]|$)'){throw 'Unsafe depot'}
 if([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($name) -ne $e.Key){throw 'Depot mismatch'}
 $p=[IO.Path]::GetFullPath((Join-Path $source $name));if(!$p.StartsWith([IO.Path]::GetFullPath($source)+'\')){throw 'Path escape'}
 New-Item -ItemType Directory -Force -Path (Split-Path $p -Parent)|Out-Null;$b=Bytes $e;[IO.File]::WriteAllBytes($p,$b);$before[$name]=HashBytes $b;$names[$e.Key]=$name
}
New-Item -ItemType Directory -Path (Join-Path $C 'readback_02')|Out-Null
$options=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new();$rows=@()
foreach($r in $prepared.resources){
 if((Get-FileHash -LiteralPath $r.prepared).Hash -cne $r.prepared_sha256 -or $before[$r.depot] -cne $r.raw_sha256){throw 'Source drift'}
 $dto=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Deserialize([WolvenKit.Common.Conversion.RedFileDto],(Get-Content -LiteralPath $r.prepared -Raw),$options)
 $p=Join-Path $source $r.depot;Write-Cr2wFile $dto.Data $p
 $read=Read-Cr2wFile $p;$json=Join-Path $C ('readback_02/'+[IO.Path]::GetFileName($p)+'.json');Export-Cr2wJson $read $json
 $rows+=@{depot=$r.depot;before=$r.raw_sha256;after=(Get-FileHash -LiteralPath $p).Hash;readback=$json;readback_sha256=(Get-FileHash -LiteralPath $json).Hash}
}
$dest=Join-Path $C ('package/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $dest -Parent)|Out-Null
$stream=[IO.File]::Create($dest);try{if(!([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new($source),$stream)){throw 'Packing failed'}}finally{$stream.Dispose()}
$packed=OpenArc $dest;if($packed.Files.Count -ne 17){throw 'Packed count mismatch'};$unchanged=0
foreach($e in $packed.Files.Values){$name=$names[$e.Key];if(!$name){throw 'Unexpected packed resource'};$actual=HashBytes (Bytes $e);if($actual -cne (Get-FileHash -LiteralPath (Join-Path $source $name)).Hash){throw 'Packed bytes mismatch'};if($name -notin $prepared.resources.depot){if($actual -cne $before[$name]){throw 'Unrelated owner changed'};$unchanged++}}
if($unchanged -ne 8){throw 'Owner preservation count'}
$bp=Join-Path $C ('before/'+$rel);New-Item -ItemType Directory -Force -Path (Split-Path $bp -Parent)|Out-Null;Copy-Item -LiteralPath $installed -Destination $bp
if((Get-FileHash -LiteralPath $installed).Hash -cne $expected -or (Get-FileHash -LiteralPath $bp).Hash -cne $expected){throw 'Baseline drift'}
$result=@{status='BUILT_SC1_NATIVE_NOT_LIVE';target=$rel;before=$expected;after=(Get-FileHash -LiteralPath $dest).Hash;resources=$rows;unchanged_resources=$unchanged;original_resource_hashes=$before;game_writes=0;builder_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash}
$result|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $C 'build_02.json') -Encoding utf8
$result|Select-Object status,before,after,unchanged_resources|ConvertTo-Json

