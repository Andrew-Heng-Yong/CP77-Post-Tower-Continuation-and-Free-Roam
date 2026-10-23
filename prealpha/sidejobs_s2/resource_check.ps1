param([string]$Revision='s2_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($Revision -cnotmatch '^s2_\d{2}$'){throw 'Invalid immutable S2 revision'}
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$build=Join-Path $PSScriptRoot ('build/'+$Revision)
$manifestPath=Join-Path $build 'build.json'
$dest=Join-Path $build 'resource_check.json'
if(Test-Path -LiteralPath $dest){throw 'Evidence pinned; use a new build revision'}
if(!(Test-Path -LiteralPath $manifestPath -PathType Leaf)){throw 'Build manifest missing'}
$manifestHash=(Get-FileHash -LiteralPath $manifestPath).Hash
$checkerHash=(Get-FileHash -LiteralPath $PSCommandPath).Hash
$manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json

function WorkspaceFile([string]$relative){
    if([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)'){throw "Unsafe source pin: $relative"}
    $full=[IO.Path]::GetFullPath((Join-Path $workspace $relative))
    if(!$full.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Source pin escaped workspace'}
    if(!(Test-Path -LiteralPath $full -PathType Leaf)){throw "Pinned file missing: $relative"}
    return $full
}
function ValidDepot([string]$depot){
    if($depot -cnotmatch '^[a-z0-9_]+(?:\\[a-z0-9_.-]+)+$' -or $depot.Contains('..')){throw "Invalid depot: $depot"}
}
function ResourceHash($entry){
    $memory=[IO.MemoryStream]::new()
    try{$entry.Extract($memory);return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($memory.ToArray()))}
    finally{$memory.Dispose()}
}

# This explicit minimum prevents an accidentally incomplete extraction/pin loop
# from turning a partial closure scan into a reported successful owner audit.
$requiredNative=@(
 'base\quest\minor_quests\minorquests.questphase',
 'base\quest\minor_quests\mq032\mq032_sacrum.questphase',
 'base\quest\minor_quests\mq032\phases\mq032_01_hook.questphase',
 'base\quest\minor_quests\mq032\phases\mq032_02_maelstrom.questphase',
 'base\quest\minor_quests\mq032\phases\mq032_03_epilogue.questphase',
 'base\quest\minor_quests\mq032\phases\mq032_combat.questphase',
 'base\quest\minor_quests\mq032\scenes\mq032_01_hook.scene',
 'base\quest\minor_quests\mq032\scenes\mq032_02_maelstrom.scene',
 'base\quest\minor_quests\mq032\scenes\mq032_03_epilogue.scene',
 'base\quest\minor_quests\mq032\characters\mq032_maelstrom.community',
 'base\quest\minor_quests\mq032\characters\mq032_monk_brother.community',
 'base\quest\minor_quests\mq032\characters\mq032_monk_cyberware.community',
 'base\quest\minor_quests\mq008\mq008.questphase',
 'base\quest\minor_quests\mq008\phases\mq008_01_hook.questphase',
 'base\quest\minor_quests\mq008\phases\mq008_02_shooting_contest.questphase',
 'base\quest\minor_quests\mq008\phases\mq008_cleanup.questphase',
 'base\quest\minor_quests\mq008\scenes\mq008_01_party_chats.scene',
 'base\quest\minor_quests\mq008\scenes\mq008_02_shooting_contest.scene',
 'base\quest\minor_quests\mq008\communities\mq008_6th_street_party.community',
 'base\quest\minor_quests\mq008\communities\mq008_background.community',
 'base\quest\minor_quests\mq008\communities\mq008_representative.community',
 'base\quest\minor_quests\mq008\communities\mq008_shooting_competitors.community'
)
$requiredBoots=@('towercontinued\sidejobs_s2\mq032_sacrum.questphase','towercontinued\sidejobs_s2\mq008_party.questphase')
$native=@{};$sources=@{};$pins=@{};$wanted=@{}
foreach($pin in $manifest.source_pins.PSObject.Properties){
    if($pin.Value -cnotmatch '^[A-F0-9]{64}$'){throw "Invalid pinned hash: $($pin.Name)"}
    $full=WorkspaceFile $pin.Name
    if((Get-FileHash -LiteralPath $full).Hash -cne $pin.Value){throw "Source pin changed: $($pin.Name)"}
    $pins[$pin.Name]=$pin.Value
    if($pin.Name -match '^research/sidejobs_s2/(sacrum_audit|stadium_audit)/[^/]+/raw/(.+)$'){
        $depot=$Matches[2].Replace('/','\');ValidDepot $depot
        if($native.ContainsKey($depot) -and $native[$depot] -cne $pin.Value){throw "Conflicting extracted copies: $depot"}
        $native[$depot]=$pin.Value;$wanted[$depot]=$pin.Value
        if(!$sources.ContainsKey($depot)){$sources[$depot]=@()}
        $sources[$depot]+=,$pin.Name
    }
}
foreach($depot in $requiredNative){if(!$native.ContainsKey($depot)){throw "Native closure pin missing: $depot"}}
if($manifest.official_resource_count -ne $native.Count){throw 'Manifest official-resource count differs from unique pinned native depots'}
foreach($folder in @('sacrum_audit','stadium_audit')){
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $workspace ('research/sidejobs_s2/'+$folder)) -Recurse -File){
        if($file.FullName -notmatch '[\\/]raw[\\/]'){continue}
        $relative=[IO.Path]::GetRelativePath($workspace,$file.FullName).Replace('\','/')
        if(!$pins.ContainsKey($relative)){throw "Audit raw source not pinned by build: $relative"}
        if(!$pins.ContainsKey($relative.Replace('/raw/','/json/')+'.json')){throw "Decoded source not pinned: $relative"}
    }
}
$resourceProperties=@($manifest.resources.PSObject.Properties)
if($resourceProperties.Count -ne 2 -or @($manifest.boots).Count -ne 2){throw 'S2 must own exactly two boot resources'}
foreach($depot in $requiredBoots){
    if($depot -cnotin @($resourceProperties.Name) -or $depot -cnotin @($manifest.boots)){throw "S2 boot identity missing: $depot"}
}
foreach($property in $resourceProperties){
    ValidDepot $property.Name
    if($property.Name -cnotin $requiredBoots -or $native.ContainsKey($property.Name)){throw 'Unexpected official override or new resource'}
    $path=Join-Path (Join-Path $build 'source') $property.Name
    if((Get-FileHash -LiteralPath $path).Hash -cne $property.Value){throw "Built resource differs: $($property.Name)"}
    $wanted[$property.Name]=$property.Value
}
if(@($manifest.official_overrides).Count -ne 0){throw 'Official overrides are outside the S2 scope'}

# HelpersOnly loads the parser types; it does not execute a pinned build.
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$modRoot=Join-Path $game 'archive/pc/mod'
if(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order needs a separate audit'}
$hashService=[WolvenKit.Common.Services.HashService]::new();$hashService.Load()
$keys=@{}
foreach($depot in $wanted.Keys){
    $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
    if($keys.ContainsKey($key) -and $keys[$key] -cne $depot){throw 'Target FNV64 collision'}
    $keys[$key]=$depot
}
$mods=@();$modBefore=@(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name)
foreach($file in $modBefore){
    $before=(Get-FileHash -LiteralPath $file.FullName).Hash;$archive=$null
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hashService,[ref]$archive).ToString() -ne 'NoError'){throw "Cannot read installed archive: $($file.Name)"}
    foreach($key in $archive.Files.Keys){
        if($keys.ContainsKey([uint64]$key)){throw "Unexpected installed override: $($file.Name) $($keys[[uint64]$key])"}
    }
    if((Get-FileHash -LiteralPath $file.FullName).Hash -cne $before){throw "Installed archive changed during audit: $($file.Name)"}
    $mods+=,@{name=$file.Name;sha256=$before;resource_count=$archive.Files.Count}
}

# Both official gamedata archives are searched. This checks each native depot
# once while retaining every archive occurrence, and rejects differing copies.
$officialNames=@('archive/pc/content/basegame_4_gamedata.archive','archive/pc/ep1/ep1_2_gamedata.archive')
$found=@{};$officialArchives=@()
foreach($relative in $officialNames){
    $official=Join-Path $game $relative;$before=Get-Item -LiteralPath $official;$archive=$null
    if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($official,$hashService,[ref]$archive).ToString() -ne 'NoError'){throw "Cannot read official archive: $relative"}
    foreach($depot in $native.Keys|Sort-Object){
        $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
        if(!$archive.Files.ContainsKey($key)){continue}
        $hash=ResourceHash $archive.Files[$key]
        if($hash -cne $native[$depot]){throw "Official bytes differ: $relative $depot"}
        if(!$found.ContainsKey($depot)){$found[$depot]=@()}
        $found[$depot]+=,$official
    }
    foreach($depot in $requiredBoots){
        $key=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($depot)
        if($archive.Files.ContainsKey($key)){throw "New boot collides with official resource: $depot"}
    }
    $after=Get-Item -LiteralPath $official
    if($before.Length -ne $after.Length -or $before.LastWriteTimeUtc.Ticks -ne $after.LastWriteTimeUtc.Ticks){throw "Official archive changed during audit: $relative"}
    $officialArchives+=,@{path=$official;length=$after.Length;last_write_utc=$after.LastWriteTimeUtc.ToString('o');resource_hashes_verified=$true;whole_archive_sha256=$null}
}
$rows=@()
foreach($depot in $native.Keys|Sort-Object){
    if(!$found.ContainsKey($depot)){throw "Native resource missing from official archives: $depot"}
    $rows+=,@{depot=$depot;sha256=$native[$depot];archives=$found[$depot];source_pins=$sources[$depot]}
}
if(@(Compare-Object @($modBefore.Name) @(Get-ChildItem -LiteralPath $modRoot -File -Filter '*.archive'|Sort-Object Name|ForEach-Object Name)).Count -ne 0){throw 'Installed archive set changed during audit'}
if(Test-Path -LiteralPath (Join-Path $modRoot 'modlist.txt')){throw 'Explicit load order appeared during audit'}
foreach($mod in $mods){
    if((Get-FileHash -LiteralPath (Join-Path $modRoot $mod.name)).Hash -cne $mod.sha256){throw "Installed archive changed after scan: $($mod.name)"}
}
foreach($official in $officialArchives){
    $current=Get-Item -LiteralPath $official.path
    if($current.Length -ne $official.length -or $current.LastWriteTimeUtc.ToString('o') -cne $official.last_write_utc){throw "Official archive changed after scan: $($official.path)"}
}
foreach($pin in $pins.GetEnumerator()){
    if((Get-FileHash -LiteralPath (WorkspaceFile $pin.Key)).Hash -cne $pin.Value){throw "Source changed during audit: $($pin.Key)"}
}
foreach($property in $resourceProperties){
    if((Get-FileHash -LiteralPath (Join-Path (Join-Path $build 'source') $property.Name)).Hash -cne $property.Value){throw "Built resource changed during audit: $($property.Name)"}
}
if((Get-FileHash -LiteralPath $manifestPath).Hash -cne $manifestHash -or (Get-FileHash -LiteralPath $PSCommandPath).Hash -cne $checkerHash){throw 'Build manifest or checker changed during audit'}
$report=[ordered]@{
 status='PASS_NOT_LIVE';build_sha256=$manifestHash;checker_sha256=$checkerHash
 source_pin_count=$pins.Count;native_depot_count=$native.Count;native_raw_copy_count=@($sources.Values|ForEach-Object {$_}).Count
 target_depot_count=$wanted.Count;new_boots=$requiredBoots;official=$rows;official_archives=$officialArchives
 installed_archives=$mods;installed_resource_count=($mods|Measure-Object -Property resource_count -Sum).Sum
 overrides=@();modlist_absent=$true;official_overrides=@();game_writes=0;save_writes=0
 scope='Original parent, two native owners, all audited phase/scene/community resource paths and two mod-owned boots. Resource-path collision and official-byte audit only; no world-prefab runtime, save-history, visual or gameplay proof.'
}
# CreateNew is intentional: evidence can never silently replace a prior report.
$stream=[IO.File]::Open($dest,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($report|ConvertTo-Json -Depth 12));$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
@{status=$report.status;official_resources=$rows.Count;installed_archives=$mods.Count;target_depots=$wanted.Count;overrides=0}|ConvertTo-Json
