param([ValidatePattern('^built_[0-9]{2}$')][string]$BuildName = 'built_04')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$native = Join-Path $PSScriptRoot 'native_01'
$built = Join-Path $PSScriptRoot $BuildName
$sources = Join-Path $built 'source'
$output = Join-Path $built 'world_verification.json'
if (Test-Path -LiteralPath $output) { throw 'Preserve previous verification' }
$planFile = Join-Path $PSScriptRoot 'plan.json'
$plan = Get-Content -LiteralPath $planFile -Raw | ConvertFrom-Json -AsHashtable
$build = Get-Content -LiteralPath (Join-Path $built 'build.json') -Raw | ConvertFrom-Json -AsHashtable
if ((Get-FileHash -LiteralPath $planFile).Hash -cne $build.plan_sha256) { throw 'Plan drift' }

function Read-World([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    try {
        $r = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $r.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{ param($e) return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs] })
        $f = $null
        if ($r.ReadFile([ref]$f,$true).ToString() -cne 'NoError') { throw "Read failed: $path" }
        return $f.RootChunk
    } finally { $stream.Dispose() }
}
function Json($object) {
    return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($object,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
}
function Digest([byte[]]$bytes) { return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
function Check([bool]$success, [string]$label) {
    if (!$success) { throw "Verification failed: $label" }
    $checks.Add($label)
}
$checks = [Collections.Generic.List[string]]::new()
foreach ($resource in $build.resources) {
    Check ((Get-FileHash -LiteralPath (Join-Path $sources $resource.depot)).Hash -ceq $resource.sha256) "Typed resource hash $($resource.depot)"
}
$originalBlock = Read-World (Join-Path $native 'block.streamingblock')
$privateBlock = Read-World (Join-Path $sources $plan.block)
Check ($privateBlock.Descriptors.Count -eq 2) 'Exactly two private descriptors'

$rows = foreach ($spec in $plan.sectors) {
    $row = @($build.sectors | Where-Object name -ceq $spec.name)[0]
    $key = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($spec.private_ref)
    Check ($row.depot.EndsWith('\quest_'+$key.ToString('x16')+'.streamingsector')) "Engine depot hash $($spec.name)"
    $donorPath = Join-Path $native ($spec.name+'.streamingsector')
    Check ((Get-FileHash -LiteralPath $donorPath).Hash -ceq $spec.sha256) "Original donor $($spec.name)"
    $a = Read-World $donorPath
    $b = Read-World (Join-Path $sources $row.depot)
    Check ($b.Nodes.Count -eq $spec.keep.Count -and $b.VariantIndices.Count -eq 1 -and $b.VariantIndices[0].ToString() -ceq '0' -and $b.VariantNodes.Count -eq 0) "Single base range $($spec.name)"
    Check ($b.PersistentNodes.Count -eq 0 -and $b.Version.ToString() -ceq '68') "Supported sector layout $($spec.name)"
    $map = @{}
    for ($i=0; $i -lt $spec.keep.Count; $i++) {
        $old = $spec.keep[$i]
        Check ($b.Nodes[$i].Chunk.GetType().Name -ceq 'worldAISpotNode') "Passive workspot only $($spec.name)/$i"
        Check ((Json $a.Nodes[$old].Chunk) -ceq (Json $b.Nodes[$i].Chunk)) "Byte donor definition semantics $($spec.name)/$i"
        $map.Add([int]$old,$i)
    }
    $nativeBytes = $a.NodeData.Buffer.GetBytes()
    $privateBytes = $b.NodeData.Buffer.GetBytes()
    $targetIndex = 0
    for ($offset=0; $offset -lt $nativeBytes.Length; $offset+=144) {
        $old = [int]([BitConverter]::ToUInt64($nativeBytes,$offset+112) -band 0x7FFFF)
        if (!$map.ContainsKey($old)) { continue }
        $targetOffset = $targetIndex*144
        $bits = [BitConverter]::ToUInt64($privateBytes,$targetOffset+112)
        Check (($bits -band 0x7FFFF) -eq $map[$old]) "Placement remap $($spec.name)/$targetIndex"
        $actual = [byte[]]$privateBytes[$targetOffset..($targetOffset+143)]
        $expected = [byte[]]$nativeBytes[$offset..($offset+143)]
        $restoredIndex = ($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$old
        [Array]::Copy([BitConverter]::GetBytes($restoredIndex),0,$actual,112,8)
        Check ((Digest $actual) -ceq (Digest $expected)) "Exact native workspot placement $($spec.name)/$targetIndex"
        $targetIndex++
    }
    Check ($targetIndex -eq $b.NodeData.Data.Count -and $privateBytes.Length -eq $targetIndex*144) "No additional placements $($spec.name)"
    $aMeta = Json $a | ConvertFrom-Json -AsHashtable -Depth 100
    $bMeta = Json $b | ConvertFrom-Json -AsHashtable -Depth 100
    foreach ($field in @('nodes','nodeData','variantIndices','variantNodes')) {
        $aMeta.Remove($field)
        $bMeta.Remove($field)
    }
    Check (($aMeta | ConvertTo-Json -Compress -Depth 100) -ceq ($bMeta | ConvertTo-Json -Compress -Depth 100)) "Preserve sector metadata and NodeRefs $($spec.name)"

    $oldDescriptor = @($originalBlock.Descriptors | Where-Object { $_.Data.DepotPath.ToString() -ceq $spec.donor })[0]
    $newDescriptor = @($privateBlock.Descriptors | Where-Object { $_.QuestPrefabNodeRef.ToString() -ceq $spec.private_ref })[0]
    Check ($newDescriptor.Data.DepotPath.ToString() -ceq $row.depot -and $newDescriptor.NumNodeRanges.ToString() -ceq '1' -and $newDescriptor.Variants.Count -eq 0) "Descriptor points to exact base sector $($spec.name)"
    $restore = $newDescriptor.DeepCopy()
    $restore.Data = $oldDescriptor.Data
    $restore.QuestPrefabNodeRef = $oldDescriptor.QuestPrefabNodeRef
    $restore.NumNodeRanges = $oldDescriptor.NumNodeRanges
    foreach ($variant in $oldDescriptor.Variants) { $restore.Variants.Add($variant) }
    Check ((Json $restore) -ceq (Json $oldDescriptor)) "Descriptor metadata preserved $($spec.name)"
    @{ name=$spec.name; workspots=$b.Nodes.Count; placements=$targetIndex; donor=$spec.donor; depot=$row.depot }
}
$originalBlock.Descriptors.Clear()
$privateBlock.Descriptors.Clear()
Check ((Json $originalBlock) -ceq (Json $privateBlock)) 'All block metadata preserved'

# Verify the separate resource-depot namespace and the exact workspot assets.
$game = 'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$service = [WolvenKit.Common.Services.HashService]::new()
$service.Load()
$reader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$assets = @($plan.sectors | ForEach-Object { $_.workspots } | Sort-Object -Unique)
$keys = @{}
$expected = @{}
foreach ($asset in $assets) {
    $key = [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($asset)
    $keys.Add($key,$asset)
    $expected[$key] = @()
}
foreach ($resource in $build.resources) {
    $keys.Add([WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($resource.depot),$resource.depot)
}
$archives = @(Get-ChildItem -LiteralPath $game -Filter '*.archive' -Recurse -File)
foreach ($file in $archives) {
    $archive = $null
    if ($reader.ReadArchive($file.FullName,$service,[ref]$archive).ToString() -cne 'NoError') { throw "Unreadable archive: $file" }
    foreach ($key in $keys.Keys) {
        if (!$archive.Files.ContainsKey([uint64]$key)) { continue }
        if (!$expected.ContainsKey($key)) { throw "Private depot collision: $($keys[$key]) in $file" }
        $m = [IO.MemoryStream]::new()
        try {
            $archive.Files[[uint64]$key].Extract($m)
            $expected[$key] += @{ archive=$file.Name; sha256=Digest $m.ToArray() }
        } finally { $m.Dispose() }
    }
}
$assetRows = foreach ($key in $expected.Keys) {
    $official = @($expected[$key] | Where-Object archive -match '^(basegame_|ep1_)')
    Check ($official.Count -gt 0) "Workspot asset provider $($keys[$key])"
    @{ depot=$keys[$key]; providers=$expected[$key] }
}
@{ status='PASS_TYPED_FILTERED_WORKSPOTS'; sectors=@($rows); checks=$checks.ToArray(); assets=@($assetRows); archives_scanned=$archives.Count } |
    ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
Write-Output "Verified $($rows.workspots -join '+') workspots, $($assets.Count) native assets, and four new depot keys"
