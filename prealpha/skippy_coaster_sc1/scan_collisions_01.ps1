Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$proof=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_07/package_proof_01.json') -Raw|ConvertFrom-Json
if($proof.status -cne 'SC1_51_PATH_CANDIDATE_PACKED_NOT_INSTALLED'){throw 'Candidate proof changed'}
$resources=@($proof.new_resource,$proof.changed_resource)
$keys=@{};foreach($resource in $resources){$keys[[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString([string]$resource).ToString()]=$resource}
$mod='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
$archives=@(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File|Sort-Object Name)
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$hits=[Collections.Generic.List[object]]::new()
foreach($file in $archives){
 $arc=$null
 if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw "Unreadable archive $($file.Name)"}
 foreach($entry in $arc.Files.Values){$key=$entry.Key.ToString();if($keys.ContainsKey($key)){$hits.Add([ordered]@{archive=$file.Name;depot=$entry.Name;resource=$keys[$key]})}}
}
$expected=@($hits|Where-Object {$_.archive -ceq 'zzzz_PTFR_Combined.archive' -and $_.resource -ceq $proof.changed_resource})
$bad=@($hits|Where-Object {$_.archive -cne 'zzzz_PTFR_Combined.archive' -or $_.resource -cne $proof.changed_resource})
if($expected.Count -ne 1 -or $bad.Count){throw 'Unexpected resource winner collision'}
$out=Join-Path $PSScriptRoot 'candidate_07/collisions_01.json'
if(Test-Path -LiteralPath $out){throw 'Preserve collision evidence'}
$result=[ordered]@{status='PASS_EXPECTED_SCENE_WINNER_ONLY';archive_count=$archives.Count;resources=$resources;hits=@($hits);game_writes=0}
[IO.File]::WriteAllText($out,($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
@{status=$result.status;archives=$result.archive_count;hits=$hits.Count}|ConvertTo-Json
