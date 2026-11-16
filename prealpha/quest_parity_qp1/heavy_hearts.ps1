Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')

$out = Join-Path $PSScriptRoot 'candidate_01'
$source = Join-Path $out 'archive_source'
$proofDir = Join-Path $out 'heavy_hearts'
if (Test-Path -LiteralPath $proofDir) { throw 'Preserve existing Heavy Hearts proof' }
$before = Get-Content -LiteralPath (Join-Path $ws 'prealpha/johnny_batch4_jb3/candidate_01/package_manifest.json') -Raw | ConvertFrom-Json -AsHashtable
$auditDir = Join-Path $ws 'diagnostics/quest_animation_parity_20261110_01/encounter_audit/capture_01'
$capture = Get-Content -LiteralPath (Join-Path $auditDir 'providers.json') -Raw | ConvertFrom-Json
$hh1 = Join-Path $ws 'prealpha/heavy_hearts_hh1'
$native = Join-Path $hh1 'native_01'
$markerProof = Join-Path $ws 'prealpha/quest_restoration_qr7/shared/marker_providers_01'
$markers = Get-Content -LiteralPath (Join-Path $markerProof 'manifest.json') -Raw | ConvertFrom-Json
$marker = @($markers.providers | Where-Object depot -ceq 'base\worlds\03_night_city\_compiled\default\ep1\always_loaded_0.streamingsector')
if ($marker.Count -ne 1) { throw 'Expected one AlwaysLoaded EP1 marker provider' }
$marker = $marker[0]
$hh1Plan = Get-Content -LiteralPath (Join-Path $hh1 'plan.json') -Raw | ConvertFrom-Json -AsHashtable
$blockDepot = $hh1Plan.block
$entryDepot = 'towercontinued\native_gigs_u9\sts_ep1_06_entry.questphase'
$ambientDepot = 'towercontinued\quest_parity_qp1\heavy_hearts_ambient.questphase'
$areaSets = @(
    @{ name='gig'; ref='$/03_night_city/towercontinued/quest_parity_qp1/heavy_hearts_gig_areas'; keep=@(117,120,131,142,149,161) },
    @{ name='ambient'; ref='$/03_night_city/towercontinued/quest_parity_qp1/heavy_hearts_ambient_areas'; keep=@(152,159) }
)
$nativeStreetDepot = $hh1Plan.sectors[0].donor
$street = Join-Path $native 'street.streamingsector'
$nativeBlock = Join-Path $native 'block.streamingblock'
$pins = @{}
foreach ($p in $capture.providers) {
    if ($p.tag -like 'sts_ep1_06_*' -or $p.tag -like 'hh_private_*' -or
        $p.tag -in @('heavy_hearts','hh_native_street','hh_native_guard','hh_native_root')) {
        if ($pins.ContainsKey($p.depot)) { throw "Ambiguous current provider $($p.depot)" }
        $pins.Add($p.depot, @{archive=$p.archive;sha256=$p.sha256})
    }
}
$pins.Add($marker.depot, @{archive=$marker.provider;sha256=$marker.raw_sha256})
$nativeBlockDepot = 'base\worlds\03_night_city\_compiled\default\ep1\blocks\all.streamingblock'
$nativeBlockProvider = @($capture.providers | Where-Object { $_.depot -ceq $nativeBlockDepot -and $_.archive.EndsWith('\ep1_1_nightcity.archive') })
if ($nativeBlockProvider.Count -ne 1) { throw 'Ambiguous native EP1 block' }
$pins[$nativeBlockDepot] = @{archive=$nativeBlockProvider[0].archive;sha256=$nativeBlockProvider[0].sha256;allow_base_block=$true}

function HashBytes([byte[]]$bytes) {
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}
function DepotKey([string]$depot) {
    return [WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
}
function CheckHash([string]$path, [string]$expected) {
    if ((Get-FileHash -LiteralPath $path).Hash -cne $expected) { throw "Changed input: $path" }
}
function ReadWorld([string]$path) {
    $stream = [IO.File]::OpenRead($path)
    try {
        $reader = [WolvenKit.RED4.Archive.IO.CR2WReader]::new($stream)
        $reader.add_ParsingError([WolvenKit.RED4.Types.ParsingErrorEventHandler]{
            param($e) return $e -is [WolvenKit.RED4.Types.InvalidDefaultValueEventArgs]
        })
        $file = $null
        if ($reader.ReadFile([ref]$file, $true).ToString() -cne 'NoError') { throw "Cannot decode $path" }
        return $file
    } finally { $stream.Dispose() }
}
function TypedJson($obj) {
    return [WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($obj, [WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())
}

foreach ($spec in $areaSets) {
    $hash = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($spec.ref)
    $spec.depot = 'base\worlds\03_night_city\_compiled\default\ep1\quest_' + $hash.ToString('x16') + '.streamingsector'
}
$newDepots = @($areaSets | ForEach-Object { $_.depot }) + @($ambientDepot)
$game = (Get-Content -LiteralPath (Join-Path $ws 'prealpha/johnny_batch4_jb3/deployment_01/installed_manifest_01.json') -Raw | ConvertFrom-Json).game_root
$hashService = [WolvenKit.Common.Services.HashService]::new()
$hashService.Load()
$archiveReader = [WolvenKit.RED4.Archive.IO.ArchiveReader]::new()
$archiveFiles = @(Get-ChildItem -LiteralPath (Join-Path $game 'archive/pc') -File -Recurse -Filter '*.archive')
$observed = @{}
foreach ($archiveFile in $archiveFiles) {
    $archive = $null
    if ($archiveReader.ReadArchive($archiveFile.FullName,$hashService,[ref]$archive).ToString() -cne 'NoError') { throw "Cannot index $archiveFile" }
    foreach ($depot in $newDepots) {
        if ($archive.Files.ContainsKey((DepotKey $depot))) { throw "New Heavy Hearts depot collides: $depot" }
    }
    foreach ($depot in $pins.Keys) {
        $key = DepotKey $depot
        if (!$archive.Files.ContainsKey($key)) { continue }
        $pin = $pins[$depot]
        if ($pin.ContainsKey('allow_base_block') -and $archiveFile.Name -ceq 'basegame_3_nightcity.archive') { continue }
        if ($archiveFile.FullName -cne $pin.archive -or $observed.ContainsKey($depot)) { throw "Unexpected provider: $depot in $archiveFile" }
        $stream = [IO.MemoryStream]::new()
        try {
            $archive.Files[$key].Extract($stream)
            $digest = HashBytes $stream.ToArray()
        } finally { $stream.Dispose() }
        if ($digest -cne $pin.sha256) { throw "Changed provider payload $depot" }
        $observed.Add($depot, @{archive=$archiveFile.FullName;sha256=$digest;key=$key.ToString()})
    }
}
if ($observed.Count -ne $pins.Count) { throw 'Missing Heavy Hearts providers' }
CheckHash $street $pins[$nativeStreetDepot].sha256
CheckHash $nativeBlock $pins[$nativeBlockDepot].sha256
CheckHash $marker.raw $marker.raw_sha256
$always = (ReadWorld $marker.raw).RootChunk
$markerBytes = $always.NodeData.Buffer.GetBytes()
if ($markerBytes.Length -ne 144*$always.NodeData.Data.Count) { throw 'Marker stride changed' }
$markerNames = @('#sts_sm_ep1_06_bouncer','#sts_sm_ep1_06_client','#sts_sm_ep1_06_chats','#sts_sm_ep1_06_drug_dealer')
$markerRows = @{}
for ($i=0; $i -lt $always.NodeData.Data.Count; $i++) {
    $pos = $always.NodeData.Data[$i]
    $ref = $pos.QuestPrefabRefHash.ToString()
    $name = $ref.Substring($ref.LastIndexOf('/')+1)
    if ($name -cnotin $markerNames) { continue }
    $index = [int]([BitConverter]::ToUInt64($markerBytes,144*$i+112) -band 0x7FFFF)
    if ($always.Nodes[$index].Chunk.GetType().Name -cne 'worldStaticMarkerNode') { throw "Wrong scene marker type $name" }
    $markerRows.Add($name, @{node=$index;ref=$ref})
}
if ($markerRows.Count -ne $markerNames.Count) { throw 'Missing stock scene markers' }

$clubPin = @($capture.providers | Where-Object tag -ceq 'heavy_hearts')[0]
$clubPath = Join-Path $auditDir $clubPin.raw
CheckHash $clubPath $clubPin.sha256
$club = (Read-Cr2wFile $clubPath).RootChunk
$clubStreetPrefab = @($club.PhasePrefabs | Where-Object { $_.PrefabNodeRef.ToString() -ceq '#loc_sts_ep1_06_streetstory' })
if ($clubStreetPrefab.Count -ne 1) { throw 'Missing stock street prefab lease' }
$clubStreetPrefab = $clubStreetPrefab[0]
$blockPath = Join-Path $source $blockDepot
CheckHash $blockPath $before.source_resources[$blockDepot]
$block = ReadWorld $blockPath
$oldDescriptors = @($block.RootChunk.Descriptors | ForEach-Object { TypedJson $_ })
if ($oldDescriptors.Count -ne 2) { throw 'Expected HH1 street and guard descriptors' }
$donorBlock = (ReadWorld $nativeBlock).RootChunk
$descriptor = @($donorBlock.Descriptors | Where-Object { $_.Data.DepotPath.ToString() -ceq $nativeStreetDepot })[0]
if ($descriptor.Category.ToString() -cne 'Quest' -or
    @($donorBlock.Descriptors | Where-Object { $_.Data.DepotPath.ToString() -ceq $marker.depot -and $_.Category.ToString() -ceq 'AlwaysLoaded' }).Count -ne 1) {
    throw 'Stock block type or AlwaysLoaded lease changed'
}

function LeasePrefab([string]$ref) {
    $lease = $clubStreetPrefab.DeepCopy()
    $lease.PrefabNodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($ref)
    return $lease
}
. (Join-Path $PSScriptRoot 'hearts_ambient.ps1')
$ambientFile = NewHeavyHeartsAmbient

New-Item -ItemType Directory -Path $proofDir | Out-Null
$areaRows = foreach ($spec in $areaSets) {
    $file = ReadWorld $street
    $sector = $file.RootChunk
    if ($sector.Version.ToString() -cne '68' -or $sector.VariantIndices[1].ToString() -cne '180' -or
        $sector.PersistentNodes.Count -ne 0 -or @($sector.VariantNodes | Where-Object Count -ne 0).Count -ne 0) {
        throw 'Unexpected stock sector layout'
    }
    $mapping = @{}
    foreach ($i in $spec.keep) {
        $node = $sector.Nodes[$i].Chunk
        if ($i -ge 180 -or $node.GetType().Name -cne 'worldTriggerAreaNode' -or $node.Notifiers.Count -ne 1 -or
            $node.Notifiers[0].Chunk.GetType().Name -cne 'questTriggerNotifier_Quest') { throw "Unexpected trigger donor $i" }
        $mapping.Add($i, $mapping.Count)
    }
    $raw = $sector.NodeData.Buffer.GetBytes()
    if ($raw.Length -ne $sector.NodeData.Data.Count*144) { throw 'Area stride changed' }
    $bytes = [Collections.Generic.List[byte]]::new()
    $placements = @(for ($i=0; $i -lt $sector.NodeData.Data.Count; $i++) {
        $offset = 144*$i
        $bits = [BitConverter]::ToUInt64($raw,$offset+112)
        $index = [int]($bits -band 0x7FFFF)
        if (!$mapping.ContainsKey($index)) { continue }
        $ref = $sector.NodeData.Data[$i].QuestPrefabRefHash.ToString()
        if (!$ref.StartsWith('$/03_night_city/') -or !$ref.Contains('#sts_ep1_06_')) { throw "Unresolved trigger placement $i" }
        $record = [byte[]]$raw[$offset..($offset+143)]
        $bits = ($bits -band ([uint64]::MaxValue -bxor [uint64]0x7FFFF)) -bor [uint64]$mapping[$index]
        [Array]::Copy([BitConverter]::GetBytes($bits),0,$record,112,8)
        $bytes.AddRange($record)
        @{native_node=$index;new_node=$mapping[$index];ref=$ref;payload=(TypedJson $sector.Nodes[$index].Chunk);placement_sha256=(HashBytes $record)}
    })
    if ($placements.Count -ne $spec.keep.Count) { throw 'Expected one placement per area' }
    for ($i=$sector.Nodes.Count-1; $i -ge 0; $i--) {
        if (!$mapping.ContainsKey($i)) { $sector.Nodes.RemoveAt($i) }
    }
    $sector.VariantNodes.Clear()
    $sector.VariantIndices.Clear()
    $sector.VariantIndices.Add([WolvenKit.RED4.Types.CInt32]::op_Implicit(0))
    $sector.NodeData.Buffer.Data = $null
    $sector.NodeData.Buffer.SetBytes($bytes.ToArray())
    $areaPath = Join-Path $source $spec.depot
    if (Test-Path -LiteralPath $areaPath) { throw 'Existing candidate area path' }
    Write-Cr2wFile $file $areaPath
    $saved = (ReadWorld $areaPath).RootChunk
    if ($saved.Nodes.Count -ne $placements.Count -or $saved.NodeData.Data.Count -ne $placements.Count -or
        $saved.VariantIndices.Count -ne 1 -or $saved.VariantIndices[0].ToString() -cne '0' -or $saved.VariantNodes.Count -ne 0 -or
        (HashBytes $saved.NodeData.Buffer.GetBytes()) -cne (HashBytes $bytes.ToArray())) { throw 'Area placement readback failed' }
    foreach ($row in $placements) {
        if ((TypedJson $saved.Nodes[$row.new_node].Chunk) -cne $row.payload) { throw 'Area definition readback failed' }
        $row.Remove('payload')
    }
    $newDescriptor = $descriptor.DeepCopy()
    $newDescriptor.QuestPrefabNodeRef = [WolvenKit.RED4.Types.NodeRef]::op_Implicit($spec.ref)
    $newDescriptor.Data = [Activator]::CreateInstance($descriptor.GetType().GetProperty('Data').PropertyType,
        [object[]]@([WolvenKit.RED4.Types.ResourcePath]::op_Implicit($spec.depot)))
    $newDescriptor.Variants.Clear()
    $newDescriptor.NumNodeRanges = [uint32]1
    $block.RootChunk.Descriptors.Add($newDescriptor)
    @{name=$spec.name;depot=$spec.depot;ref=$spec.ref;placements=$placements;sha256=(Get-FileHash -LiteralPath $areaPath).Hash}
}

Write-Cr2wFile $block $blockPath
$blockSaved = (ReadWorld $blockPath).RootChunk
if ($blockSaved.Descriptors.Count -ne 4) { throw 'Wrong descriptor count' }
for ($i=0; $i -lt 2; $i++) {
    if ((TypedJson $blockSaved.Descriptors[$i]) -cne $oldDescriptors[$i]) { throw 'HH1 descriptor changed' }
    $desc = $blockSaved.Descriptors[2+$i]
    if ($desc.QuestPrefabNodeRef.ToString() -cne $areaSets[$i].ref -or $desc.Data.DepotPath.ToString() -cne $areaSets[$i].depot -or
        $desc.NumNodeRanges.ToString() -cne '1' -or $desc.Variants.Count -ne 0) { throw 'New area descriptor readback failed' }
}

$entryPath = Join-Path $source $entryDepot
CheckHash $entryPath $before.source_resources[$entryDepot]
$entry = Read-Cr2wFile $entryPath
$owner = Get-QuestNode $entry.RootChunk.Graph.Chunk 50
if ($owner.PhaseInstancePrefabs.Count -ne 0 -or $owner.PhaseGraph.Chunk.Nodes.Count -lt 9) { throw 'U9 gig wrapper drift' }
$owner.PhaseInstancePrefabs.Add((LeasePrefab $areaSets[0].ref))
Write-Cr2wFile $entry $entryPath
Export-Cr2wJson (Read-Cr2wFile $entryPath) (Join-Path $proofDir 'gig_entry.json')

$ambientPath = Join-Path $source $ambientDepot
Write-Cr2wFile $ambientFile $ambientPath
Export-Cr2wJson (Read-Cr2wFile $ambientPath) (Join-Path $proofDir 'ambient.json')

@{status='HEAVY_HEARTS_COOKED'; areas=@($areaRows); markers=$markerRows; providers=$observed;
  new_depots=$newDepots; archives_scanned=$archiveFiles.Count;
  edited=@(
      @{depot=$entryDepot;sha256=(Get-FileHash -LiteralPath $entryPath).Hash},
      @{depot=$blockDepot;sha256=(Get-FileHash -LiteralPath $blockPath).Hash},
      @{depot=$ambientDepot;sha256=(Get-FileHash -LiteralPath $ambientPath).Hash}
  )} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $proofDir 'resources.json') -Encoding utf8NoBOM
Write-Output 'Cooked the two trigger sectors, U9 lease, and private ambient owner.'
