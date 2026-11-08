# Targeted read of possible controller PS entries for the source-bound saved ID.
# SDK-derived IDs remain candidates until the native hash/serializer binding is proved.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = (Get-Item -LiteralPath (Join-Path $PSScriptRoot '../../../..')).FullName
$output = Join-Path $PSScriptRoot 'vehicle_ps_01'
if (Test-Path -LiteralPath $output) { throw 'Fresh output required' }
$capture = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'capture_01/capture.json') -Raw | ConvertFrom-Json
$decoded = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'decode_02/result.json') -Raw | ConvertFrom-Json
if ($decoded.source_save_sha256 -cne $capture.source_sha256 -or $decoded.target_record.array_0x20.Count -ne 1) { throw 'Exact one-ID evidence required' }
foreach ($path in @($capture.source, $capture.metadata, $PSScriptRoot)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked input/output refused' }
        $item = if ($item -is [IO.DirectoryInfo]) { $item.Parent } else { $item.Directory }
    }
}
if ((Get-FileHash -LiteralPath $capture.source).Hash -cne $capture.source_sha256 -or (Get-FileHash -LiteralPath $capture.metadata).Hash -cne $capture.metadata_sha256) { throw 'Historical input changed' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
Add-Type -TypeDefinition @'
public static class PTFRQR15CandidatePersistentID {
    public static ulong CNameHash(string s) {
        unchecked { ulong h=0xCBF29CE484222325UL; foreach(byte b in System.Text.Encoding.UTF8.GetBytes(s)) h=(h^b)*0x100000001B3UL; return h; }
    }
    public static ulong Mix(ulong entity, string component) {
        unchecked { const ulong m=0xC6A4A7935BD1E995UL; ulong c=m*CNameHash(component); return m*(entity^(m*(c^(c>>47)))); }
    }
}
'@
$entity = [uint64]::Parse($decoded.target_record.array_0x20[0])
$candidates = @()
foreach ($name in @('controller','VehicleController')) {
    $candidates += @{ component = $name; candidate_hash_u64 = [PTFRQR15CandidatePersistentID]::Mix($entity,$name).ToString() }
}
$bytes = [IO.File]::ReadAllBytes($capture.source)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $capture.source_sha256) { throw 'Unstable source snapshot' }
$memory = [IO.MemoryStream]::new($bytes,$false)
$reader = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($memory)
$save = $null
try {
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError') { throw 'Save reader failed' }
    $name = [WolvenKit.RED4.Save.PersistencySystem2Parser]::NodeName
    $nodes = @($save.Nodes | Where-Object Name -ceq $name)
    if ($nodes.Count -ne 1 -or $nodes[0].Value -isnot [WolvenKit.RED4.Save.PersistencySystem2]) { throw 'PS2 parser unavailable' }
    $entries = @($nodes[0].Value.Entries)
    $propertiesField = [WolvenKit.RED4.Types.RedBaseClass].GetField('_properties',[Reflection.BindingFlags]'Instance,NonPublic')
    $rows = @()
    foreach ($candidate in $candidates) {
        $matches = @($entries | Where-Object { $_.Id.ToString() -ceq $candidate.candidate_hash_u64 })
        foreach ($entry in $matches) {
            $className = if ($null -eq $entry.Data) { $null } else { $entry.Data.GetType().FullName }
            $values = @()
            if ($null -ne $entry.Data) {
                $dictionary = $propertiesField.GetValue($entry.Data)
                foreach ($key in $dictionary.Keys) {
                    if ($key -match 'state|visual|door|destroy|init|entity') {
                        $value = $dictionary[$key]
                        $values += @{ property = $key; type = $value.GetType().FullName; parsed_text = $value.ToString() }
                    }
                }
            }
            $rows += @{ component_candidate = $candidate.component; id_u64 = $entry.Id.ToString(); parsed_class = $className; selected_parsed_properties = $values }
        }
    }
    if ((Get-FileHash -LiteralPath $capture.source).Hash -cne $capture.source_sha256 -or (Get-FileHash -LiteralPath $capture.metadata).Hash -cne $capture.metadata_sha256) { throw 'Source changed' }
    New-Item -ItemType Directory -Path $output | Out-Null
    $sdk = Join-Path $workspace 'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/Scripting/Natives/gamePersistentID.hpp'
    @{
        status = 'CANDIDATE_PS_HASH_LOOKUP_NO_STAGE_CERTIFICATE'; source = $capture.source; source_sha256 = $capture.source_sha256
        metadata_sha256 = $capture.metadata_sha256; saved_associated_id_u64 = $entity.ToString(); candidates = $candidates; matches = $rows
        parsed_ps2_entry_count = $entries.Count; ps2_ids_count = $nodes[0].Value.Ids.Count
        sdk_hash_source = $sdk; sdk_hash_source_sha256 = (Get-FileHash -LiteralPath $sdk).Hash
        reader_sha256 = (Get-FileHash -LiteralPath ([WolvenKit.RED4.Save.PersistencySystem2].Assembly.Location)).Hash
        limits = 'SDK hash candidates only; native PersistentID hash/PS2 identity still requires independent binding. Parsed defaults do not prove an originally serialized field. Misses do not prove no PS, no spawn, or incomplete setup. VisualDestructionSet is not a receipt for the specific quest event.'
        source_unchanged = $true; save_writes = 0; game_calls = 0
    } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $output 'result.json') -Encoding utf8NoBOM
    @{ status = 'CANDIDATE_PS_LOOKUP'; candidates = $candidates; matches = $rows; ps2_entries = $entries.Count } | ConvertTo-Json -Depth 7
} finally { $reader.Dispose() }
