# Export selected installed entry graphs and read their handlers in unchanged MS32.
# Writes only new workspace evidence. No save writer, game calls, build or deployment.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$out = Join-Path $PSScriptRoot 'saved_01'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence output required' }
$inventory = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'sources_01/inventory.json') -Raw | ConvertFrom-Json
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
$parserHash = (Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash
if ($parserHash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
function Plain([string]$path) {
    for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
function PhaseKey([uint16[]]$words) {
    $hash = if ($words[0] -eq 0) { [uint64]2166136261 } elseif ($words[0] -eq 1) { [uint64]0x01800013 } else { throw 'Unknown root seed' }
    foreach ($word in $words) {
        $hash = (($hash -bxor ($word -band 255)) * 16777619) -band 4294967295
        $hash = (($hash -bxor ($word -shr 8)) * 16777619) -band 4294967295
    }
    [uint32]$hash
}
Plain $PSScriptRoot
[void](New-Item -ItemType Directory -Path $out)
$prefixes = @{}
foreach ($entry in $inventory.entries) {
    Plain $entry.raw_path
    if ((Get-FileHash -LiteralPath $entry.raw_path).Hash -cne $entry.raw_sha256) { throw 'Packed source drift' }
    Export-Cr2wJson (Read-Cr2wFile $entry.raw_path) (Join-Path $out ($entry.id + '.json'))
    $prefixes[[string]$entry.saved_prefix] = [string]$entry.id
}
$savePath = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077/ManualSave-32/sav.dat'
Plain $savePath
$saveHash = (Get-FileHash -LiteralPath $savePath).Hash
if ($saveHash -cne 'B5698BC909DD2CDDF34BA39E0DDE26E4480DD1769F9B4EE626717D8DBD2A622F') { throw 'MS32 fixture drift' }
$bytes = [IO.File]::ReadAllBytes($savePath)
if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $saveHash) { throw 'Input changed during copy' }
$memory = [IO.MemoryStream]::new($bytes, $false)
$reader = $readerType::new($memory)
try {
    $save = $null
    if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw 'Unsupported save' }
    $roots = @($save.Nodes | Where-Object Name -CEQ 'questSystem')
    if ($roots.Count -ne 1) { throw 'Ambiguous quest root' }
    $catalog = @($roots[0].Children | Where-Object Name -CEQ 'customArray')
    $events = @($roots[0].Children | Where-Object Name -CEQ 'eventManager')
    if ($catalog.Count -ne 1 -or $events.Count -ne 1) { throw 'Ambiguous stores' }
    $words = $catalog[0].Value.Unknown
    $paths = @{}
    $selected = [Collections.Generic.List[object]]::new()
    for ($at=0; $at -lt $words.Count;) {
        $length = [int]$words[$at]; $at++
        if ($length -lt 1 -or $length -gt $words.Count-$at) { throw 'Invalid path' }
        $route = [uint16[]]::new($length)
        for ($i=0; $i -lt $length; $i++) { $route[$i]=$words[$at+$i] }
        $at += $length
        $key=PhaseKey $route
        $routeString=$route -join '/'
        if ($paths.ContainsKey($key)) { throw 'Phase hash collision' }
        $paths[$key]=$routeString
        if ($length -ge 2 -and $prefixes.ContainsKey(($route[0..1] -join '/'))) {
            $selected.Add(@{route=$routeString; key=$key; id=$prefixes[($route[0..1] -join '/')]})
        }
    }
    $selectedKeys=@{}
    foreach ($row in $selected) { $selectedKeys[[uint32]$row.key]=$row }
    $handlers=@(for ($i=0; $i -lt $events[0].Value.Unknown.Count; $i++) {
        $event=$events[0].Value.Unknown[$i]
        if ($event.Unknown1 -and $event.Unknown3 -ne 65535 -and $selectedKeys.ContainsKey([uint32]$event.Unknown2)) {
            $row=$selectedKeys[[uint32]$event.Unknown2]
            @{slot=$i; route=$row.route; id=$row.id; node=[int]$event.Unknown3; type_token=[string]$event.Unknown1}
        }
    })
    if ((Get-FileHash -LiteralPath $savePath).Hash -cne $saveHash) { throw 'Save changed during read' }
    @{status='READ_ONLY_SELECTED_PRIVATE_HANDLERS'; save_sha256=$saveHash; parser_sha256=$parserHash;
      interned=$selected.ToArray(); handlers=$handlers; path_count=$paths.Count; event_count=$events[0].Value.Unknown.Count;
      save_unchanged=$true; save_writes=0; game_calls=0;
      limits=@('Saved registrations are a point-in-time snapshot, not current-session liveness.',
               'External child graph dependencies require their own resource resolution.')
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $out 'handlers.json') -Encoding utf8NoBOM
    Write-Output ("Read-only handler capture complete: {0} registrations" -f $handlers.Count)
} finally { $reader.Dispose(); $memory.Dispose() }
