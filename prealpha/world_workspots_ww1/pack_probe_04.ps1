Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base = Join-Path $PSScriptRoot 'probe_04'
$source = Join-Path $base 'source'
$package = Join-Path $base 'package'
$proof = Get-Content -LiteralPath (Join-Path $base 'compile_01/result.json') -Raw | ConvertFrom-Json
$ownerProof = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'candidate_02/owner_validation_01.json') -Raw | ConvertFrom-Json
if ($proof.status -cne 'PASS' -or $proof.source_count -ne 65 -or $ownerProof.native_guards -ne 16) { throw 'Script or owner proof missing' }
$relative = 'towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase'
$resource = Join-Path $source $relative
$resourceDigest = (Get-FileHash -LiteralPath $resource -Algorithm SHA256).Hash
$nativeDigest = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'candidate_02/source' $relative) -Algorithm SHA256).Hash
if ($resourceDigest -cne $nativeDigest) { throw 'Private owner drift' }
$file = Read-Cr2wFile $resource
$graph = $file.RootChunk.Graph.Chunk
$node = Get-QuestNode $graph 6
$expectedRef = '$/03_night_city/c_pacifica/coastview/cvi_ce_prefabMZQN2IY/#ce_pac_cvi_116'
if ($graph.Nodes.Count -ne 7 -or $node.PhaseInstancePrefabs.Count -ne 1 -or $node.PhaseInstancePrefabs[0].PrefabNodeRef.ToString() -cne $expectedRef) { throw 'Owner scope changed' }
if (@(Get-ChildItem -LiteralPath $source -Recurse -File).Count -ne 1) { throw 'Additional resource in additive archive' }
$arcRel = 'archive/pc/mod/zzzz_PTFR_WW1_Prototype.archive'
$xlRel = $arcRel + '.xl'
$scriptRel = 'r6/scripts/PTFR_WW1_Prototype/WW1Probe.reds'
$archive = Join-Path $package $arcRel
$xl = Join-Path $package $xlRel
if ((Test-Path -LiteralPath $archive) -or (Test-Path -LiteralPath $xl)) { throw 'Probe package already exists; use successor name' }
New-Item -ItemType Directory -Force -Path (Split-Path $archive -Parent) | Out-Null
$hs = [WolvenKit.Common.Services.HashService]::new(); $hs.Load()
$stream = [IO.File]::Create($archive)
try {
  $writer = [WolvenKit.RED4.Archive.IO.ArchiveWriter]::new($hs,[WolvenKit.SerilogWrapper]::new())
  if (-not $writer.WriteArchive([IO.DirectoryInfo]::new($source),$stream)) { throw 'Archive write failed' }
} finally { $stream.Dispose() }
$packed = $null
if (([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($archive,$hs,[ref]$packed).ToString() -cne 'NoError') { throw 'Archive readback failed' }
if ($packed.Files.Count -ne 1) { throw 'Packed archive contains extra resources' }
$entry = @($packed.Files.Values)[0]
if ($entry.Name -cne $relative) { throw ('Packed depot mismatch '+$entry.Name) }
$memory = [IO.MemoryStream]::new()
try { $entry.Extract($memory); $packedHash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray())) } finally { $memory.Dispose() }
if ($packedHash -cne $resourceDigest) { throw 'Packed owner differs from verified resource' }
$xlText = @"
quest:
  phases:
    - path: towercontinued\world_workspots_ww1\ce_pac_cvi_116_owner.questphase
      parent: ep1\quest\ep1.quest
      input:
        node: [1]
        socket: Out
"@
[IO.File]::WriteAllText($xl,$xlText+"`n",[Text.UTF8Encoding]::new($false))
$script = Join-Path $package $scriptRel
if ((Get-FileHash -LiteralPath $script -Algorithm SHA256).Hash -cne $proof.candidate_script_sha256) { throw 'Script changed after compiler proof' }
$paths = @($arcRel,$xlRel,$scriptRel)
$actual = @(Get-ChildItem -LiteralPath $package -Recurse -File | ForEach-Object { [IO.Path]::GetRelativePath($package,$_.FullName).Replace('\','/') } | Sort-Object)
if (@(Compare-Object ($paths|Sort-Object) $actual).Count) { throw 'Package path census mismatch' }
$files = foreach($p in $paths) { [ordered]@{path=$p; sha256=(Get-FileHash -LiteralPath (Join-Path $package $p) -Algorithm SHA256).Hash} }
$manifest = [ordered]@{
  status='ADDITIVE_CVI116_PROBE_WITH_STARTUP_STAGED_NOT_INSTALLED';
  mode='Temporary prototype only; remove all three probe paths before full production successor';
  addon_paths=3;existing_ptfr_paths_replaced=0;native_resource_count=1;
  original_depot=$relative;original_prefab=$expectedRef;
  packed_resource_sha256=$packedHash;
  compiled_script_sha256=$proof.compiled_sha256;
  files=$files;
  live_effect='UNPROVEN';
  game_writes=0;save_writes=0
}
$manifestPath = Join-Path $base 'manifest_01.json'
if (Test-Path -LiteralPath $manifestPath) { throw 'Manifest exists; preserve evidence' }
[IO.File]::WriteAllText($manifestPath,($manifest|ConvertTo-Json -Depth 12)+"`n",[Text.UTF8Encoding]::new($false))
$manifest|ConvertTo-Json -Depth 8
