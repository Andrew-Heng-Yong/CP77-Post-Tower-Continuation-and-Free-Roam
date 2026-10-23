param(
 [string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot),
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath($WorkspaceRoot)
$audit=Join-Path $workspace 'research\misty_viktor_world'
$out=Join-Path $workspace 'build\ZetatechTerryR11'
New-Item -ItemType Directory -Force $out|Out-Null
$recordPath=Join-Path $audit 'terry_record_audit.json'
$record=Get-Content -LiteralPath $recordPath -Raw|ConvertFrom-Json
if($record.record -ne 'Character.q307_thug_01' -or $record.display_name -ne 'Terry' -or $record.display_key -ne '81616' -or $record.appearance -ne 'man_average__q307__streetkid_01' -or @($record.tags).Count -ne 1 -or $record.tags[0] -ne 'Invulnerable' -or $record.original_record_mutations -ne 0){throw 'Terry record audit contract changed'}
$communityPath=Join-Path $audit 'street_npc_sources\json\ep1\quest\main_quests\q307\communities\q307_com_thugs.community.json'
$community=(Get-Content -LiteralPath $communityPath -Raw|ConvertFrom-Json).Data.RootChunk.communityTemplate.Data
$terry=@($community.entries|Where-Object {$_.Data.entryName.'$value' -eq 'q307_thug_01'})
if($terry.Count -ne 1 -or $terry[0].Data.characterRecordId.'$value' -ne $record.record){throw 'Terry community identity changed'}
$idle=@($terry[0].Data.phases|Where-Object {$_.Data.phaseName.'$value' -eq 'q307_ws_thug_01_alley'})
if($idle.Count -ne 1 -or $idle[0].Data.appearances.Count -ne 1 -or $idle[0].Data.appearances[0].'$value' -ne $record.appearance -or $idle[0].Data.timePeriods[0].spotNodeRefs[0].'$value' -ne '#q307_ws_thug_01_alley'){throw 'Terry idle identity changed'}
$sectorPath=Join-Path $audit 'r6_wall_nav_sources\ep1_1_nightcity\json\base\worlds\03_night_city\_compiled\default\ep1\quest_bb3937b6e34a251c.streamingsector.json'
if((Get-FileHash -LiteralPath $sectorPath).Hash -ne '6DF10E0B989F3154B8C03B5E5DE361319CDD7E4E648E16A12D47A02ADC1EC535'){throw 'Terry source sector changed'}
$sector=(Get-Content -LiteralPath $sectorPath -Raw|ConvertFrom-Json).Data.RootChunk
if($sector.nodes[12].Data.debugName.'$value' -ne '{q307_ws_thug_01_alley}'){throw 'Terry source node changed'}
$placements=@($sector.nodeData.Data|Where-Object NodeIndex -eq 12)
if($placements.Count -ne 1){throw 'Terry source placement count changed'}
$placement=$placements[0]
$expectedPosition=@(-1551.20374,1172.57251,16.3103752)
$expectedOrientation=@(-0.0191563722,-0.0170180015,0.996187747,-0.0833877027)
for($i=0;$i -lt 3;$i++){if([Math]::Abs([double]$placement.Position.(@('X','Y','Z')[$i])-$expectedPosition[$i]) -gt 0.000001){throw 'Terry source position changed'}}
for($i=0;$i -lt 4;$i++){if([Math]::Abs([double]$placement.Orientation.(@('i','j','k','r')[$i])-$expectedOrientation[$i]) -gt 0.000000001){throw 'Terry source orientation changed'}}

$yaml=Join-Path $workspace 'tweaks\TowerContinued_MistyViktor_Terry_R11.yaml'
$driver=Join-Path $workspace 'redscript\PTFR_MistyViktor_Terry_R11\TerryR11.reds'
$yamlLines=@(Get-Content -LiteralPath $yaml|Where-Object {$_ -notmatch '^\s*#' -and $_ -match '\S'})
if(($yamlLines -join "`n") -cne ('Character.PTFRMV_Terry:'+"`n"+'  $base: Character.q307_thug_01'+"`n"+'  tags: []')){throw 'TweakXL must only clone the original and clear its sole audited Invulnerable tag'}
$text=Get-Content -LiteralPath $driver -Raw
foreach($required in @('spec.recordID = t"Character.PTFRMV_Terry"','spec.appearanceName = n"man_average__q307__streetkid_01"','spec.persistState = false','spec.persistSpawn = false','spec.alwaysSpawned = true','this.attempts < 3','!this.everSpawned && !this.dead','q.GetFact(n"PTFRMV11_Registered") == 1','q.GetFact(n"PTFRMV_AccessRevision") == 11','system.GetTaggedIDs(n"PTFRMV11_Terry")','system.IsManaged(ids[index]) && system.IsTagged(ids[index], n"PTFRMV11_Terry")','ArrayContains(tags, n"Invulnerable")')){if(-not $text.Contains($required)){throw "Terry runtime contract missing: $required"}}
if($text -match 'q307_thug_01_attack|q307_com_thugs|SetGodMode|SetImmortality|ForceKill|TweakDBInterface\.Set|SaveGame|LoadGame'){throw 'Forbidden Terry runtime mutation/scene route'}
$writes=@([regex]::Matches($text,'this\.Count\(n"([^"]+)"\)')|ForEach-Object {$_.Groups[1].Value}|Sort-Object -Unique)
if(@($writes|Where-Object {$_ -notlike 'PTFRMV11_Terry*'}).Count -gt 0 -or ([regex]::Matches($text,'\.SetFact\(')).Count -ne 1){throw 'Terry diagnostic fact write scope changed'}
$codeware=Join-Path $GameRoot 'red4ext\plugins\Codeware\Scripts\Codeware.Global.reds'
$tweakxl=Join-Path $GameRoot 'red4ext\plugins\TweakXL\TweakXL.dll'
if(-not (Test-Path -LiteralPath $codeware) -or -not (Test-Path -LiteralPath $tweakxl)){throw 'Installed Codeware/TweakXL dependencies are missing'}
$api=Get-Content -LiteralPath $codeware -Raw
foreach($signature in @('public native class DynamicEntitySpec','public native func CreateEntity(spec: ref<DynamicEntitySpec>) -> EntityID','public native func DeleteEntity(id: EntityID) -> Bool','public native func GetTaggedIDs(tag: CName) -> array<EntityID>','public native func RegisterListener(tag: CName, target: ref<IScriptable>, function: CName)','public native let persistSpawn: Bool;','public native let persistState: Bool;')){if(-not $api.Contains($signature)){throw "Required installed Codeware API absent: $signature"}}
$cli=Join-Path $workspace 'research\finalboards_dismissal\tooling\redscript-cli.exe'
$cache=Join-Path $GameRoot 'r6\cache\final.redscripts.modded'
$lint=(& $cli lint -s $driver -b $cache 2>&1|Out-String)
[IO.File]::WriteAllText((Join-Path $out 'redscript_lint.log'),$lint,[Text.UTF8Encoding]::new($false))
if($lint -notmatch 'Lint successful' -or $lint -match 'ERROR'){throw ('Terry runtime compile failed: '+$lint)}
$payloads=@(
 [ordered]@{source=$yaml;relative='r6\tweaks\TowerContinued_MistyViktor_Terry_R11.yaml';sha256=(Get-FileHash -LiteralPath $yaml).Hash},
 [ordered]@{source=$driver;relative='r6\scripts\PTFR_MistyViktor_Terry_R11\TerryR11.reds';sha256=(Get-FileHash -LiteralPath $driver).Hash}
)
$manifest=[ordered]@{
 status='BUILT_TERRY_R11_PRIVATE_CLONE_RUNTIME_LIVE_PENDING';tests_pass=$true;payloads=$payloads
 private_record='Character.PTFRMV_Terry';base_record=$record.record;display_name='Terry';name_key='81616';appearance=$record.appearance
 changed_record_fields=@('tags: [Invulnerable] -> [] on private clone only');original_record_mutations=0
 source_position=$expectedPosition;source_orientation=$expectedOrientation;source_node=12;source_ref=$placement.QuestPrefabRefHash.'$value'
 sources=@([ordered]@{path=$recordPath;sha256=(Get-FileHash -LiteralPath $recordPath).Hash},[ordered]@{path=$communityPath;sha256=(Get-FileHash -LiteralPath $communityPath).Hash},[ordered]@{path=$sectorPath;sha256=(Get-FileHash -LiteralPath $sectorPath).Hash})
 dependencies=@('Existing Codeware DynamicEntitySystem','Existing TweakXL','Existing redscript','Native R11 registered/access revision and R7 world Applied/Enabled')
 codeware_api_sha256=(Get-FileHash -LiteralPath $codeware).Hash;tweakxl_sha256=(Get-FileHash -LiteralPath $tweakxl).Hash
 documentation=@('https://github.com/psiberx/cp2077-codeware/blob/main/scripts/World/DynamicEntitySpec.reds','https://github.com/psiberx/cp2077-codeware/blob/main/scripts/World/DynamicEntitySystem.reds')
 lifecycle=[ordered]@{private_tag='PTFRMV11_Terry';persistState=$false;persistSpawn=$false;alwaysSpawned=$true;creation_radius_m=60;player_overlap_exclusion_m=3;max_failed_creation_attempts=3;async_ready_wait=$true;duplicate_lookup_includes_pending=$true;successful_spawn_consumed_for_runtime_session=$true;death_recreation=$false;departure_recreation=$false;owned_cleanup_on_guard_loss_and_detach=$true;save_load_death_persistence='Not implemented: disposable-session candidate'}
 diagnostic_counters=$writes
 tests=@('Exact original Terry identity/appearance and sole Invulnerable tag','Exact authored idle position and orientation','Exact private-only TweakXL record delta','Installed Codeware API signature availability','Private fact write/scene/mutation boundary','Successful compile against installed modded redscript cache')
 installed=$false;live_tested=$false;live_pending=@('One correctly named/appearing Terry on street','Normal idle/AI and combat reactions','Damage and death','No duplicates on streaming or return','No resurrection after death in same runtime session','Owned cleanup on release','Reload behavior after future explicit save approval')
 limits=@('No native community or workspot is activated; spawned NPC uses inherited normal behavior rather than promising original smoking animation','Removing source Invulnerable tag and omitting assault scene does not prove absence of every possible engine/runtime immortality source','Persistent production death state across save/load is intentionally not claimed','No direct save-file, original character, story fact, restriction-profile or ending-scene changes')
}
$manifestPath=Join-Path $audit 'terry_r11_manifest.json'
[IO.File]::WriteAllText($manifestPath,($manifest|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{status=$manifest.status;tests_pass=$true;payloads=$payloads;live_tested=$false}|ConvertTo-Json -Depth 5
