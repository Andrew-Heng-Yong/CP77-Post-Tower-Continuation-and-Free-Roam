param()
$ErrorActionPreference='Stop'
$workspace='C:\Users\Ayong\Documents\cp77 modding\tower ws'
$resultPath=Join-Path $workspace 'research\postending_pa5\gigs\tests.json'
if(Test-Path -LiteralPath $resultPath){throw 'Preserve prior test evidence; select a new result path for another revision.'}
$script=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'GigDiagnosticsPA5.reds') -Raw
$data=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'GigDiagnosticsDataPA5.generated.reds') -Raw
$manifest=Get-Content -LiteralPath (Join-Path $workspace 'research\postending_pa5\gigs\data_manifest.json') -Raw|ConvertFrom-Json
$checks=[Collections.Generic.List[object]]::new()
function Check([string]$name,[bool]$ok){$checks.Add([ordered]@{name=$name;pass=$ok});if(-not $ok){throw ('Failed: '+$name)}}
Check 'Exactly 72 diagnostic rows' ($manifest.rows.Count -eq 72)
Check 'Indices are exactly 0 through 71' ((($manifest.rows.index|Sort-Object) -join ',') -eq ((0..71) -join ','))
Check 'Whitelist IDs unique' (@($manifest.rows.id|Sort-Object -Unique).Count -eq 72)
Check 'Generated data hash' ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'GigDiagnosticsDataPA5.generated.reds') -Algorithm SHA256).Hash -eq $manifest.generated_sha256)
Check 'No runtime mutation calls' (-not [regex]::IsMatch($script,'\.(SetFact|AddFact|ChangeEntryState|SetEntryVisited|TrackEntry|SetMappinTrackingAlternative|RegisterMappin|UnregisterMappin|StartAll|Start|RestoreCertified|RequestForcedCheckpoint|Teleport)\s*\('))
Check 'No wrap or replace hooks' (-not [regex]::IsMatch($script,'@(wrapMethod|replaceMethod|addMethod)'))
Check 'No attach-time actions or background callbacks' (-not [regex]::IsMatch($script,'OnAttach|OnDetach|DelayCallback|DelaySystem|Schedule|Poll\('))
Check 'Unknown ID rejected before catalogue indexing' ($script.IndexOf('if i < 0') -gt $script.IndexOf('public func Inspect(id: String)') -and $script.IndexOf('if i < 0') -lt $script.IndexOf('let owner ='))
Check 'Mappins matched by native quest hash' ($script.Contains('poi.GetJournalQuestPathHash() == hash'))
Check 'Only first four duplicate mappins formatted' ($script.Contains('if matches <= 4'))
Check 'Missing entry distinct from inactive' ($script.Contains('IsDefined(entry) ? EnumInt(jm.GetEntryState(entry)) : -1'))
Check 'Entry difference details bounded to six' ($script.Contains('if count <= 6'))
Check 'No rendered-icon proof overclaim' ($script.Contains('not rendered-icon proof'))
Check 'Requested parent main cleanup counts separated' ($script.Contains('requested/parent/main/cleanup='))
Check 'Summary POI counts restricted to main-owned entries' ($script.Contains('this.Own(id, "Started") == 1 && this.State(this.POIPath(i)'))
Check 'Inspectable state numbers documented' ($script.Contains('-1 missing,1 inactive,2 active,3 succeeded,4 failed'))
Check 'No marker fallback allocation' (-not [regex]::IsMatch($script,'new\s+(NewMappinID|MappinData)|:\s*(NewMappinID|MappinData)\s*;'))
Check 'Public entry points available' ($script.Contains('public func Summary()') -and $script.Contains('public func Inspect(id: String)') -and $script.Contains('public func InspectOwned()'))
Check 'Shark source gate facts retained for inspection' (@($manifest.rows|Where-Object id -eq 'sts_wat_kab_06')[0].facts -contains 'sts_wat_kab_tier_1_4')
Check 'Heywood discovery dependency inspected' (@($manifest.rows|Where-Object id -eq 'sts_hey_rey_06')[0].facts -contains 'padre_visited')
Check 'Westbrook discovery dependency inspected' (@($manifest.rows|Where-Object id -eq 'sts_wbr_hil_07')[0].facts -contains 'wakako_visited')
Check 'Read-only parent facts are not setters' ($data -notmatch 'SetFact|ChangeEntryState|RegisterMappin')
$report=[ordered]@{status='PASS_STATIC_DIAGNOSTIC_CHECKS_ENGINE_COMPILE_AND_LIVE_PENDING';check_count=$checks.Count;checks=$checks.ToArray();files=@('GigDiagnosticsPA5.reds','GigDiagnosticsDataPA5.generated.reds')|ForEach-Object{@{path=(Join-Path $PSScriptRoot $_);sha256=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $_) -Algorithm SHA256).Hash}};runtime_writes=0;limitations=@('Static safety checks do not prove REDscript compilation or live map getter delivery.','No mocked result is presented as a live rendering observation.')}
[IO.File]::WriteAllText($resultPath,($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
'PASS '+$checks.Count+' static diagnostic checks.'
