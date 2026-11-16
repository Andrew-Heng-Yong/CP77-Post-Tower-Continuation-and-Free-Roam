# Capture only CommunitySystem for the exact stage comparison saves.
param([switch]$IncludeSharedPatrols, [switch]$InspectLocker)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ws = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$installed = Join-Path $ws 'prealpha/resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json'
if ((Get-FileHash -LiteralPath $installed).Hash -cne 'AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8') { throw 'RD10 manifest drift' }
$manifest = Get-Content -Raw -LiteralPath $installed | ConvertFrom-Json
if ($IncludeSharedPatrols -and $InspectLocker) { throw 'Select one supplementary capture' }
$out = Join-Path $PSScriptRoot $(if ($InspectLocker) { 'capture_03' } elseif ($IncludeSharedPatrols) { 'capture_02' } else { 'capture_01' })
if (Test-Path -LiteralPath $out) { throw 'Fresh output required' }
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $ws 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$parser = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $parser.Assembly.Location).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Unexpected reader' }
function CheckPlain([string]$Path) {
    for ($item = Get-Item -LiteralPath $Path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path $Path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
CheckPlain $PSScriptRoot
$prefix = '$/03_night_city/se1/loc_sts_bls_ina_07_minefield_prefabBNZWKTY/loc_sts_bls_ina_07_minefield_openworld_prefabK32ADQA/#sts_bls_ina_07_minefield_logic'
$refs = [ordered]@{
    car = "$prefix/#ina_07_com_car"
    drones = "$prefix/loc_sts_bls_ina_07_combat_prefabXE3BW2I/#ina_07_com_drones"
    bandits = "$prefix/loc_sts_bls_ina_07_combat_prefabXE3BW2I/#ina_07_com_bandits"
}
if ($IncludeSharedPatrols) {
    $shared = '$/03_night_city/se1/se1_cs_prefab3O6XMQI'
    $refs['border_patrol'] = "$shared/cs_militech_pre_border_post_prefab2N3DNOY/cs_militech_pre_border_post_openworld_prefab6JRP6MY/cs_militech_pre_border_post_com"
    $refs['heavy_patrol'] = "$shared/cs_heavy_militech_patrol_prefab3V2KS6Q/cs_heavy_militech_patrol_com"
    $refs['droid_patrol'] = "$shared/cs_heavy_militech_patrol_with_droid_prefab6OGBGMA/cs_heavy_militech_patrol_with_droid_com"
}
$targets = [ordered]@{}
foreach ($name in $refs.Keys) { $targets[$name] = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($refs[$name]).ToString() }
if ($InspectLocker) {
    $worldPath = Join-Path $PSScriptRoot 'evidence_02/batch_communities.json'
    $worldHash = (Get-FileHash -LiteralPath $worldPath).Hash
    if ($worldHash -cne '94A58B8068A857F69CA3F4E5B2FBF2BB1F1F11BA261B64D04EF9360C35CF38E7') { throw 'Locker world evidence drift' }
    $world = Get-Content -Raw -LiteralPath $worldPath | ConvertFrom-Json -AsHashtable
    $lockerRef = $world['locker_reference']
    $lockerEntity = [WolvenKit.RED4.Types.NodeRef]::CalculateHash($lockerRef)
    if ($lockerEntity.ToString() -cne '5396063336959311732') { throw 'Locker identity drift' }
    Add-Type -TypeDefinition @'
public static class PTFRLockerPersistentKey {
    public static ulong Of(ulong entity, string component) {
        unchecked {
            const ulong m = 0xC6A4A7935BD1E995UL;
            ulong hash = 0xCBF29CE484222325UL;
            foreach (byte b in System.Text.Encoding.UTF8.GetBytes(component)) hash = (hash ^ b) * 0x100000001B3UL;
            ulong c = m * hash;
            return m * (entity ^ (m * (c ^ (c >> 47))));
        }
    }
}
'@
    $lockerKey = [PTFRLockerPersistentKey]::Of($lockerEntity,'controller').ToString()
    $propertiesField = [WolvenKit.RED4.Types.RedBaseClass].GetField('_properties',[Reflection.BindingFlags]'Instance,NonPublic')
}
[void][IO.Directory]::CreateDirectory($out)
$rows = @(foreach ($slot in 'ManualSave-26','AutoSave-3','AutoSave-5') {
    $source = Join-Path $manifest.save_root "$slot/sav.dat"
    $metadata = Join-Path $manifest.save_root "$slot/metadata.9.json"
    CheckPlain $source
    CheckPlain $metadata
    $digest = (Get-FileHash -LiteralPath $source).Hash
    $metaDigest = (Get-FileHash -LiteralPath $metadata).Hash
    if ($slot -ne 'ManualSave-26') {
        $proof = Join-Path $ws "prealpha/resume_dispatcher_rd5_gigs_20261113_01/saves_01/$slot/manifest.json"
        $before = Get-Content -Raw -LiteralPath $proof | ConvertFrom-Json
        if ($digest -cne $before.source_sha256 -or $metaDigest -cne $before.metadata_sha256) { throw "Stage fixture drift: $slot" }
    } else {
        $proof = Join-Path $ws "prealpha/handler_preservation_hp1_20261112_01/saves_01/$slot/manifest.json"
        $before = Get-Content -Raw -LiteralPath $proof | ConvertFrom-Json
        if ($digest -cne $before.source_sha256 -or $metaDigest -cne $before.metadata_sha256) { throw "Stage fixture drift: $slot" }
    }
    $bytes = [IO.File]::ReadAllBytes($source)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $digest) { throw "Unstable save $slot" }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = $parser::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw "Unsupported save $slot" }
        if ($InspectLocker) {
            $name = [WolvenKit.RED4.Save.PersistencySystem2Parser]::NodeName
            $nodes = @($save.Nodes | Where-Object Name -CEQ $name)
            if ($nodes.Count -ne 1 -or $nodes[0].Value -isnot [WolvenKit.RED4.Save.PersistencySystem2]) { throw 'PS2 unavailable' }
            $allLockers = @($nodes[0].Value.Entries | Where-Object { $_.Data -is [WolvenKit.RED4.Types.SecurityLockerControllerPS] })
            $matches = @(foreach ($entry in $allLockers | Where-Object { $_.Id.ToString() -ceq $lockerKey }) {
                $props = $propertiesField.GetValue($entry.Data)
                @{ key = $entry.Id.ToString(); parsed_has_storage_property = $props.ContainsKey('isStoringPlayerEquipement');
                   storing_player_equipment = $entry.Data.IsStoringPlayerEquipement.ToString() }
            })
            if ((Get-FileHash -LiteralPath $source).Hash -cne $digest -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metaDigest) { throw "Save changed during capture: $slot" }
            @{ slot = $slot; source_sha256 = $digest; metadata_sha256 = $metaDigest; locker_matches = $matches;
               total_locker_class_entries = $allLockers.Count }
            continue
        }
        $nodes = @($save.Nodes | Where-Object Name -CEQ ([WolvenKit.RED4.Save.CommunitySystemParser]::NodeName))
        if ($nodes.Count -ne 1 -or $nodes[0].Value -isnot [WolvenKit.RED4.Save.CommunitySystem]) { throw 'Ambiguous community node' }
        $node = $nodes[0]
        $keys = @($node.Value.Unk_HashList | ForEach-Object { $_.ToString() })
        $tail = $node.Value.TrailingBytes
        if ($tail.Length -gt 8388608 -or $node.TrailingSize -ne 0 -or $node.Size -ne (8 + 8*$keys.Count + $tail.Length)) {
            throw 'Unexpected community layout'
        }
        $path = Join-Path $out "$slot.bin"
        [IO.File]::WriteAllBytes($path, $tail)
        if ((Get-FileHash -LiteralPath $source).Hash -cne $digest -or (Get-FileHash -LiteralPath $metadata).Hash -cne $metaDigest) {
            throw "Save changed during capture: $slot"
        }
        @{ slot = $slot; source_sha256 = $digest; metadata_sha256 = $metaDigest; outer_keys = $keys;
            trailing_path = $path; trailing_sha256 = (Get-FileHash -LiteralPath $path).Hash; node_size = $node.Size }
    } finally { $reader.Dispose(); $memory.Dispose() }
})
if ($InspectLocker) {
    @{ saves = $rows; locker_ref = $lockerRef; entity_candidate = $lockerEntity.ToString(); component_candidate = 'controller';
       persistent_key_candidate = $lockerKey; world_evidence_sha256 = $worldHash;
       parser_sha256 = $parserHash; save_writes = 0 } |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'locker.json') -Encoding utf8NoBOM
    return
}
@{ saves = $rows; targets = $targets; node_refs = $refs; parser_sha256 = $parserHash; save_writes = 0 } |
    ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'manifest.json') -Encoding utf8NoBOM
