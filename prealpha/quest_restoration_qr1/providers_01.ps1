Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$C=Join-Path $PSScriptRoot 'candidate_01'
if(Test-Path -LiteralPath (Join-Path $C 'providers_01.json')){throw 'Preserve provider evidence'}
$b=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'baseline.json') -Raw|ConvertFrom-Json -Depth 100
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$lookup=@{};$archives=@();$providers=@();$unexpected=@()
foreach($p in $b.private_resources.PSObject.Properties){$key=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name);$lookup[$key]=@{depot=$p.Name;sha256=$p.Value}}
$parent='ep1\quest\ep1.quest';$pk=[uint64][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($parent)
$parentPins=@(Get-Content -LiteralPath (Join-Path $W 'diagnostics/vanilla_parity_20261029_01/parents.json') -Raw|ConvertFrom-Json -Depth 30)
$own=[IO.Path]::GetFullPath((Join-Path $b.game 'archive/pc/mod/zzzz_PTFR_Combined.archive'))
function ExtractHash($entry){$mem=[IO.MemoryStream]::new();try{$entry.Extract($mem);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($mem.ToArray()))}finally{$mem.Dispose()}}
foreach($f in Get-ChildItem -LiteralPath (Join-Path $b.game 'archive/pc') -File -Recurse -Filter '*.archive'){
 $a=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Unreadable archive'}
 $stock=$f.DirectoryName -notlike '*\mod*';$archives+=,@{path=$f.FullName;bytes=$f.Length;mtime_utc=$f.LastWriteTimeUtc.ToString('o');members=$a.Files.Count}
 foreach($key in $lookup.Keys){
  if(-not $a.Files.ContainsKey([uint64]$key)){continue}
  $ref=$lookup[$key];$hash=ExtractHash $a.Files[[uint64]$key];$isOwn=$f.FullName -ceq $own
  if($isOwn -and $hash -cne $ref.sha256){throw 'Installed PH3 changed'}
  $role=if($isOwn){'PINNED_INSTALLED_PH3'}elseif($stock -and $ref.depot -notlike 'towercontinued\*'){'NATIVE_COUNTERPART_OF_RECORDED_OVERRIDE'}else{'UNEXPECTED_ADDITIONAL_PROVIDER'}
  $row=@{depot=$ref.depot;archive=$f.FullName;sha256=$hash;role=$role;stock=$stock};$providers+=,$row
  if($role -ceq 'UNEXPECTED_ADDITIONAL_PROVIDER'){$unexpected+=,$row}
 }
 if($a.Files.ContainsKey($pk)){
  $h=ExtractHash $a.Files[$pk];if($parentPins.sha256 -cnotcontains $h){throw 'Native XL parent changed'}
 }
}
@{status=if($unexpected.Count){'UNRESOLVED_ADDITIONAL_PROVIDERS'}else{'PASS_CURRENT_PTFR_NAMESPACE_PROVIDER_CENSUS'};archives=$archives;providers=$providers;unexpected=$unexpected;new_depots=0;new_collision_risk='None introduced: source depots and XL bytes unchanged';scope='Fresh provider lookup for every staged PTFR payload and native XL parent. Presence-only dependencies outside these keys retain prior audit limitations.';game_writes=0;save_writes=0}|ConvertTo-Json -Depth 40|Set-Content -LiteralPath (Join-Path $C 'providers_01.json') -Encoding utf8NoBOM
@{archives=$archives.Count;providers=$providers.Count;unexpected=$unexpected.Count}|ConvertTo-Json
