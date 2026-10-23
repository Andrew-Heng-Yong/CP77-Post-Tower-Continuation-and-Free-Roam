param([Parameter(Mandatory)][string]$Build)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$Build=[IO.Path]::GetFullPath($Build)
if(!$Build.StartsWith($ws+'\prealpha\postending_pa5\camera\build\',[StringComparison]::OrdinalIgnoreCase) -or (Test-Path (Join-Path $Build 'tests.json'))){throw 'Fresh scoped camera test result required'}
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$checks=[Collections.Generic.List[string]]::new()
function Check($ok,$name){if(!$ok){throw ('FAILED: '+$name)};$checks.Add($name)}
function J($v){[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($v,[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new())}
function Hash($p){(Get-FileHash -LiteralPath $p).Hash}
$b=Get-Content -Raw (Join-Path $Build 'build.json')|ConvertFrom-Json -Depth 100
$c=Get-Content -Raw (Join-Path $Build 'compile.json')|ConvertFrom-Json -Depth 100
Check ($c.status -ceq 'PASS_COMPONENT_FULL_COMPILE_AND_READBACK_NOT_LIVE') 'Headless/full SCC and body readback passed'
Check ($c.build_sha256 -ceq (Hash (Join-Path $Build 'build.json'))) 'Compile report bound to exact build'
Check ($b.package_files.Count -eq 3 -and $b.resources.Count -eq 2) 'Only archive, XL, script; exactly scene and owner resources'
foreach($f in $b.package_files){Check ((Hash (Join-Path $b.package_root $f.relative)) -ceq $f.sha256) ('Package hash '+$f.relative)}
$native=Read-Cr2wFile (Join-Path $ws 'research/b0_h10_generalization/extracted_interactions/raw/base/quest/minor_quests/mq000/scenes/mq000_01_apartment.scene')
$nativeSection=@($native.RootChunk.SceneGraph.Chunk.Graph|Where-Object {$_.Chunk.NodeId.Id.ToString() -eq '660'})[0].Chunk
$scene=Read-Cr2wFile (Join-Path $Build 'source/towercontinued/postending_pa5/camera/optics_reset.scene')
$r=$scene.RootChunk;$nodes=@($r.SceneGraph.Chunk.Graph|ForEach-Object {$_.Chunk})
Check ($nodes.Count -eq 3 -and (($nodes|ForEach-Object {$_.GetType().Name}) -join '|') -ceq 'scnStartNode|scnSectionNode|scnEndNode') 'Only Start/reset-section/End scene nodes'
$section=$nodes[1];$e=$section.Events[0].Chunk
Check ($section.Events.Count -eq 1 -and (J $e) -ceq (J $nativeSection.Events[0].Chunk)) 'Every native reset event property exactly retained'
Check ($e.CameraOverrideSettings.OverrideDof.ToString() -eq 'False' -and $e.CameraOverrideSettings.OverrideFov.ToString() -eq 'False') 'Literal native lens numbers are inactive, not new overrides'
Check ($e.CameraOverrideSettings.ResetDof.ToString() -eq 'True' -and $e.CameraOverrideSettings.ResetFov.ToString() -eq 'True') 'Stock player FOV/DOF reset flags retained'
Check ($e.IsPlayerCamera.ToString() -eq 'True' -and $e.CameraRef.ToString() -eq '0' -and $e.TargetActor.Id.ToString() -eq '4294967040') 'Player camera target, no external camera/NPC reference'
Check ($section.SectionDuration.Stu.ToString() -eq '1500' -and $e.Duration.ToString() -eq '1500' -and $e.StartTime.ToString() -eq '0') 'Stock 1.5 second duration and event timing retained'
Check ($r.Actors.Count -eq 0 -and $r.PlayerActors.Count -eq 0 -and $r.Props.Count -eq 0 -and $section.ActorBehaviors.Count -eq 0) 'No actors acquired or native unrelated actor behaviors retained'
Check ($r.Workspots.Count -eq 0 -and $r.EffectDefinitions.Count -eq 0 -and $r.RidResources.Count -eq 0 -and $r.ResouresReferences.CinematicAnimSets.Count -eq 0) 'No workspot/effect/animation resource bindings'
Check ($nodes[0].OutputSockets[0].Destinations[0].NodeId.Id.ToString() -eq '660' -and $section.OutputSockets[0].Destinations.Count -eq 1 -and $section.OutputSockets[0].Destinations[0].NodeId.Id.ToString() -eq '2') 'Single scene execution path ends normally'
Check ($r.EntryPoints.Count -eq 1 -and $r.ExitPoints.Count -eq 1 -and $r.EntryPoints[0].Name.ToString() -eq 'Start 0' -and $r.ExitPoints[0].Name.ToString() -eq 'End 0') 'Scene bindings match quest scene sockets'
$owner=Read-Cr2wFile (Join-Path $Build 'source/towercontinued/postending_pa5/camera/owner.questphase');$g=$owner.RootChunk.Graph.Chunk
$expected=@('0.Out -> 1.In','1.Out -> 2.In','2.Out -> 3.In','3.True -> 12.In','12.Out -> 2.In','3.False -> 4.In','4.True -> 5.In','4.False -> 13.In','13.Out -> 11.In','5.Out -> 6.Start 0','5.Out -> 20.In','6.End 0 -> 7.In','7.Out -> 8.In','8.CutSource -> 20.CutDestination','8.Out -> 9.In','6.Default INT -> 10.In','6.Default RET -> 10.In','10.Out -> 11.In','20.Out -> 21.In','21.Out -> 11.In','11.CutSource -> 6.CutDestination','11.CutSource -> 20.CutDestination','11.Out -> 9.In')
Check (@(Compare-Object ($expected|Sort-Object) @(Get-GraphEdges $g)).Count -eq 0) 'Exact native owner admission/output/scoped watchdog topology'
Check ($g.Nodes.Count -eq 16 -and $owner.RootChunk.PhasePrefabs.Count -eq 0) 'Owner has16nodes and no world prefab mutation'
Check ((Get-QuestNode $g 3).Condition.Chunk.Type.Chunk.GetType().Name -eq 'questCreditsRolling_ConditionType') 'Live native credits-rolling query, no guessed UI fact'
Check ((J (Get-QuestNode $g 2).Condition.Chunk) -ceq (J (Get-QuestNode $g 4).Condition.Chunk)) 'Full native admission rechecked after credits test'
Check ((Get-QuestNode $g 5).Type.Chunk.FactName.ToString() -eq 'PTFRPA5O_Issued' -and (Get-QuestNode $g 7).Type.Chunk.FactName.ToString() -eq 'PTFRPA5O_NativeOut') 'Issue written before native scene; output only on native End'
Check ((Get-QuestNode $g 20).Condition.Chunk.Type.Chunk.Seconds.ToString() -eq '10' -and (Get-QuestNode $g 20).Condition.Chunk.Type.Chunk.Miliseconds.ToString() -eq '0') 'Native10second watchdog bound'
$writers=@($g.Nodes|Where-Object {$_.Chunk.GetType().Name -eq 'questFactsDBManagerNodeDefinition'}|ForEach-Object {$_.Chunk.Type.Chunk.FactName.ToString()})
Check (@($writers|Where-Object {!$_.StartsWith('PTFRPA5O_')}).Count -eq 0) 'Only component-owned facts written'
Check (@($g.Nodes|Where-Object {$_.Chunk.GetType().Name -match 'Teleport|RenderFx|TimeManager|Save|Journal'}).Count -eq 0) 'No teleport/render fade/time/save/journal side effects'
$script=[IO.File]::ReadAllText((Join-Path $b.package_root 'r6/scripts/PTFR_PreAlpha/PA5/CameraOpticsPA5.reds'))
foreach($forbidden in @('\.SetFOV\(','\.SetZoom\(','\.Activate\(','SetSceneSystemCameraControl','SaveGame\(','LoadGame\(','GameOptions','SetTimeOfDay','ForceReset')){Check ($script -notmatch $forbidden) ('No forbidden optical/global write: '+$forbidden)}
foreach($required in @('CameraOpticsPA5.Get(gameInstance)','optics.Restored()','epoch != this.epoch','this.returnTicks > 120','this.pendingTicks > 80','DOF=not-exposed','visual DOF still requires playtest')){Check ($script.Contains($required)) ('Required reload/timeout/disclosure: '+$required)}
Check ($script -notmatch 'persistent let (before|after): String') 'No invalid persisted String schema'
Check ($script.Contains('AbsF(fpp.GetFOV()) < 1000.0') -and $script.Contains('AbsF(fpp.GetZoom()) < 1000.0')) 'FPP zero/default getters do not block repair'
$auth=[regex]::Match($script,'private func Authorized\(\) -> Bool \{(?<body>[\s\S]*?)\n  \}').Groups['body'].Value
Check ($auth -notmatch 'FreeRoamActive|Prepared|PTFRPA2_Finished|\.Ready\(') 'No readiness cycle on profile/gig/free-roam preparation or PA2Finished'
$inspect=[regex]::Match($script,'public func Inspect\(\) -> String \{(?<body>[\s\S]*?)\n  \}').Groups['body'].Value
Check ($inspect -notmatch 'this.Set\(') 'Inspect is read-only'
# Pure admission model: each required fact independently blocks, including
# completed/pending/faulted owned lifetime. This is logic coverage, not engine proof.
$facts=@{};foreach($p in $b.gate_facts.PSObject.Properties){$facts[$p.Name]=[int]$p.Value}
function Admit($state,$rolling){if($rolling){return $false};foreach($k in $facts.Keys){if(!$state.ContainsKey($k) -or $state[$k] -ne $facts[$k]){return $false}};return $true}
Check (Admit $facts $false) 'Native guard model admits exact safe facts with credits closed'
Check (!(Admit $facts $true)) 'Native guard model refuses credits still rolling'
foreach($k in $facts.Keys){$bad=$facts.Clone();$bad[$k]=1-$bad[$k];Check (!(Admit $bad $false)) ('Guard negative '+$k)}
$missing=$facts.Clone();$missing.Remove('PTFRPA5O_Permit');Check (!(Admit $missing $false)) 'Missing native permission does not admit'
$readyBody=[regex]::Match($script,'public func Ready\(\) -> Bool \{(?<body>[\s\S]*?)\n  \}').Groups['body'].Value
Check ($readyBody.Contains('this.Fact(n"PTFRPA5O_Done") == 1 && this.Fact(n"PTFRPA5O_NativeOut") == 1 && this.Fact(n"PTFRPA5O_Fault") == 0')) 'Ready requires owned native output plus stable-check acknowledgement and no fault'
$report=@{status='PASS_OFFLINE_NOT_LIVE';build_sha256=Hash (Join-Path $Build 'build.json');compile_sha256=Hash (Join-Path $Build 'compile.json');checks=$checks;count=$checks.Count;limitations=@('No engine execution/rendered optics proof.','Scene output does not measure final DOF.','ArchiveXL collisions across combined installed manifest are root integration responsibility.','Native renderer operation must be tested on preserved Auto19 and one fresh continuous ending.')}
[IO.File]::WriteAllText((Join-Path $Build 'tests.json'),($report|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
Write-Output ('CAMERA_TEST_PASS='+$checks.Count)
