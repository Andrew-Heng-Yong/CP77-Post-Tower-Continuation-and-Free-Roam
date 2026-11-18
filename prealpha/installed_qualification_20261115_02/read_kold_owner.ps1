# Read-only comparison of saved KOLD native and private phase registrations.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspace = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$saveRoot = 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077'
$out = Join-Path $PSScriptRoot 'manual31_32_owner.json'
if (Test-Path -LiteralPath $out) { throw 'Fresh evidence output required' }
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType = [WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if ((Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987') { throw 'Parser drift' }
function PhaseKey([uint16[]]$words) {
    $hash = if ($words[0] -eq 0) { [uint64]2166136261 } elseif ($words[0] -eq 1) { [uint64]0x01800013 } else { throw 'Unknown root seed' }
    foreach ($word in $words) {
        $hash = (($hash -bxor ($word -band 255)) * 16777619) -band 4294967295
        $hash = (($hash -bxor ($word -shr 8)) * 16777619) -band 4294967295
    }
    [uint32]$hash
}
function Plain([string]$path) {
    for ($item=Get-Item -LiteralPath $path -Force; $null -ne $item;) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked input: $path" }
        $item = if ($item -is [IO.FileInfo]) { $item.Directory } else { $item.Parent }
    }
}
$rows = @(foreach ($slot in @('ManualSave-31','ManualSave-32')) {
    $path = Join-Path $saveRoot "$slot/sav.dat"
    Plain $path
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
    $bytes = [IO.File]::ReadAllBytes($path)
    if ([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $hash) { throw 'Input changed during copy' }
    $memory = [IO.MemoryStream]::new($bytes, $false)
    $reader = $readerType::new($memory)
    try {
        $save = $null
        if ($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277) { throw 'Unsupported save' }
        $roots = @($save.Nodes | Where-Object Name -CEQ 'questSystem')
        if ($roots.Count -ne 1) { throw 'Ambiguous quest root' }
        $quest = $roots[0]
        $catalog = @($quest.Children | Where-Object Name -CEQ 'customArray')
        $events = @($quest.Children | Where-Object Name -CEQ 'eventManager')
        if ($catalog.Count -ne 1 -or $events.Count -ne 1) { throw 'Ambiguous owner stores' }
        $words = $catalog[0].Value.Unknown
        $paths = @{}
        $selected = [Collections.Generic.List[object]]::new()
        for ($at=0; $at -lt $words.Count;) {
            $length = [int]$words[$at]; $at++
            if ($length -lt 1 -or $length -gt $words.Count - $at) { throw 'Invalid interned path' }
            $route = [uint16[]]::new($length)
            for ($i=0; $i -lt $length; $i++) { $route[$i] = $words[$at+$i] }
            $at += $length
            $key = PhaseKey $route
            $routeString = $route -join '/'
            if ($paths.ContainsKey($key)) { throw "Phase key collision $key" }
            $paths[$key] = $routeString
            if ($routeString -eq '0/2/82/6' -or $routeString.StartsWith('0/2/82/6/5')) {
                $selected.Add(@{route=$routeString; key=$key})
            }
        }
        $handlers = @(for ($i=0; $i -lt $events[0].Value.Unknown.Count; $i++) {
            $event = $events[0].Value.Unknown[$i]
            if ($event.Unknown1 -and $event.Unknown3 -ne 65535 -and $paths.ContainsKey($event.Unknown2)) {
                $route = $paths[$event.Unknown2]
                if ($route -eq '0/2/82/6' -or $route.StartsWith('0/2/82/6/5')) {
                    @{slot=$i; route=$route; node=[int]$event.Unknown3; type_token=[string]$event.Unknown1}
                }
            }
        })
        if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -cne $hash) { throw 'Save changed during read' }
        @{slot=$slot; save_sha256=$hash; interned=$selected.ToArray(); handlers=$handlers; owner_store_path_count=$paths.Count; owner_store_event_count=$events[0].Value.Unknown.Count}
    } finally { $reader.Dispose(); $memory.Dispose() }
})
@{status='READ_ONLY_KOLD_OWNER_PROJECTION'; saves=$rows; limits='Selected native route only; private phase identity and executing owner require separate source/runtime review. An interned path alone is not an active handler.'; save_writes=0; game_calls=0} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "KOLD owner projection complete: $out"
