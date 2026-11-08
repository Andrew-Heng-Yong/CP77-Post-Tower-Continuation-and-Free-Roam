Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$B=Join-Path $W 'prealpha/phone_support_ph1/candidate_03';$C=Join-Path $PSScriptRoot 'candidate_01';if(Test-Path $C){throw 'Fresh candidate required'}
$id=Get-Content (Join-Path $PSScriptRoot 'id_proof_01.json') -Raw|ConvertFrom-Json -Depth 40
$G='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
foreach($f in Get-ChildItem (Join-Path $B 'package') -Recurse -File){$r=[IO.Path]::GetRelativePath((Join-Path $B 'package'),$f.FullName);if((Get-FileHash $f.FullName).Hash -cne (Get-FileHash (Join-Path $G $r)).Hash){throw 'Baseline drift'}}
New-Item -ItemType Directory $C|Out-Null
Copy-Item (Join-Path $B 'archive_source') (Join-Path $C 'archive_source') -Recurse;Copy-Item (Join-Path $B 'package') (Join-Path $C 'package') -Recurse
$old=Join-Path (Join-Path $C 'archive_source') $id.old_path;$alias=Join-Path (Join-Path $C 'archive_source') $id.new_path
New-Item -ItemType Directory (Split-Path $alias -Parent)|Out-Null;Copy-Item -LiteralPath $old -Destination $alias
$xl=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';$x=[IO.File]::ReadAllText($xl);if($x.Split($id.old_path).Count -ne 2){throw 'Registration changed'}
[IO.File]::WriteAllText($xl,$x.Replace($id.old_path,$id.new_path),[Text.UTF8Encoding]::new($false))
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$a=Join-Path $C 'package/archive/pc/mod/zzzz_PTFR_Combined.archive';$s=[IO.File]::Create($a)
try{if(-not ([WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())).WriteArchive([IO.DirectoryInfo]::new((Join-Path $C 'archive_source')),$s)){throw 'Pack failed'}}finally{$s.Dispose()}
function Arc($p){$a=$null;[void]([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($p,$hs,[ref]$a);return $a}
function EH($e){$m=[IO.MemoryStream]::new();try{$e.Extract($m);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($m.ToArray()))}finally{$m.Dispose()}}
$before=Arc (Join-Path $G 'archive/pc/mod/zzzz_PTFR_Combined.archive');$after=Arc $a
if($before.Files.Count -ne 1572 -or $after.Files.Count -ne 1573){throw 'Member count'}
foreach($e in $before.Files.Values){if(-not $after.Files.ContainsKey($e.Key) -or (EH $e) -cne (EH $after.Files[$e.Key])){throw 'Changed old resource'}}
$key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($id.new_path)
if((EH $after.Files[$key]) -cne (Get-FileHash $old).Hash){throw 'Alias differs'}
$count=0;foreach($f in Get-ChildItem (Join-Path $G 'archive/pc') -Recurse -Filter '*.archive' -File){$p=Arc $f.FullName;$count++;if($p.Files.ContainsKey($key)){throw 'Alias depot collision'}}
@{status='PASS_FULL_ARCHIVE_READBACK_NO_COLLISION';baseline_members=1572;candidate_members=1573;unchanged_members=1572;archives_scanned=$count;external_lizzies_archive_sha256=(Get-FileHash (Join-Path $G 'archive/pc/mod/LizziesBDs.archive')).Hash}|ConvertTo-Json|Set-Content (Join-Path $C 'verification_01.json') -Encoding utf8NoBOM
@{status='PASS_NATIVE_BINDINGS_AND_SERIALIZED_OWNER';change='Only one XL path substitution plus byte-identical alias; all existing resource payloads preserved';alias_sha256=(Get-FileHash $alias).Hash;old_path=$id.old_path;new_path=$id.new_path;old_id=$id.old_id;new_id=$id.new_id;id_proof_sha256=(Get-FileHash (Join-Path $PSScriptRoot 'id_proof_01.json')).Hash}|ConvertTo-Json|Set-Content (Join-Path $C 'semantic_verification_01.json') -Encoding utf8NoBOM
'PH2_BUILT_VERIFIED_NOT_INSTALLED'
