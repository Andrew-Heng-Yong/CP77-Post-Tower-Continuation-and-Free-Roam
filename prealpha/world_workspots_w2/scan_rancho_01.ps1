Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_04/package_proof_01.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'W3_51_PATH_CANDIDATE_PACKED_NOT_INSTALLED'){throw 'Candidate proof changed'}
$key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$proof.new_resource).ToString()
$mod='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
$archives=@(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File|Sort-Object Name)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$hits=[Collections.Generic.List[object]]::new()
foreach($file in $archives){
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw "Unreadable archive $($file.Name)"}
 foreach($entry in $arc.Files.Values){if($entry.Key.ToString() -ceq $key){$hits.Add([ordered]@{archive=$file.Name;depot=$entry.Name})}}
}
$out=Join-Path $PSScriptRoot 'candidate_04/collisions_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve collision evidence'}
$result=[ordered]@{status=if($hits.Count){'COLLISION_REVIEW_REQUIRED'}else{'PASS_ZERO_COLLISIONS'};archive_count=$archives.Count;resource=$proof.new_resource;hash=$key;hits=@($hits);game_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;archives=$result.archive_count;hits=$hits.Count}|ConvertTo-Json
if($hits.Count){throw 'Rancho resource collision'}
