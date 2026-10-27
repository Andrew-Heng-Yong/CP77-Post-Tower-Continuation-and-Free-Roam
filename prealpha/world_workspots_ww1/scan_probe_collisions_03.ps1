Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'probe_03/manifest_01.json') -Raw | ConvertFrom-Json
if ($manifest.native_resource_count -ne 1 -or $manifest.addon_paths -ne 3) {throw 'Prototype manifest changed'}
$depot = [string]$manifest.original_depot
$key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot).ToString()
$mod = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc\mod'
$archives = @(Get-ChildItem -LiteralPath $mod -Filter '*.archive' -File)
$hs = [WolvenKit.Common.Services.HashService]::new();$hs.Load()
$hits = @()
foreach($f in $archives){
  $arc=$null
  if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($f.FullName,$hs,[ref]$arc).ToString() -cne 'NoError'){throw ('Unreadable installed archive '+$f.FullName)}
  foreach($e in $arc.Files.Values){if($e.Key.ToString() -ceq $key){$hits+=@{archive=$f.FullName;depot=$e.Name}}}
}
$result=[ordered]@{status='READ_ONLY_PROBE_COLLISION_SCAN';installed_archives=$archives.Count;depot=$depot;hash=$key;collisions=$hits}
$target=Join-Path $PSScriptRoot 'probe_03/collisions_01.json'
if(Test-Path -LiteralPath $target){throw 'Preserve collision evidence; use a successor'}
[IO.File]::WriteAllText($target,($result|ConvertTo-Json -Depth 10)+"`n",[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Depth 10
if($hits.Count){throw 'Prototype resource collides with installed archive'}
