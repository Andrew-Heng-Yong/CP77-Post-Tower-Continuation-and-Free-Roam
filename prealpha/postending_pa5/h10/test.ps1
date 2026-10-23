$ErrorActionPreference='Stop'
$ws=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$source=Join-Path $PSScriptRoot 'source/RestorationBaseline.reds'
$base=Join-Path $ws 'build/RestorationBaseline_R1/game/r6/scripts/PTFR_RestorationBaseline/RestorationBaseline.reds'
$out=Join-Path $ws 'research/postending_pa5/h10'
if(Test-Path -LiteralPath (Join-Path $out 'tests.json')){throw 'Existing component report; use a new revision.'}
New-Item -ItemType Directory -Force -Path $out|Out-Null
$checks=[Collections.Generic.List[object]]::new()
function Check([string]$name,[bool]$pass){$checks.Add(@{name=$name;pass=$pass});if(!$pass){throw "FAIL $name"}}
function Hash([string]$p){return (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash}
$baseHash=Hash $base
Check 'Pinned baseline identity' ($baseHash -ceq 'D31B11ACD881CA5D5759FF8D66C6C2D6C84945513A5DCAFFF62A095ADA67545B')
$old=([IO.File]::ReadAllText($base)).Replace("`r`n","`n").TrimEnd()
$new=([IO.File]::ReadAllText($source)).Replace("`r`n","`n").TrimEnd()
$pattern='(?s)  // PA5: acquire the existing H10 prefabs.*?(?=  private func Startup\()'
$helper=[regex]::Match($new,$pattern).Value
Check 'Exactly one helper block' (@([regex]::Matches($new,$pattern)).Count -eq 1)
Check 'Five expanded geometry gates' (@([regex]::Matches($new,'if h10Geometry &&')).Count -eq 5)
$restored=[regex]::Replace($new,$pattern,'').Replace('if h10Geometry &&','if corridor &&').Replace("    let h10Geometry = corridor || (high == 1 && tier == 1 && this.H10OffsiteReady(q,p));`n",'')
Check 'Exact normalized delta: helpers, one envelope line and five predicates only' ($restored -ceq $old)
Check 'Helpers have no fact or owner mutations' ($helper -notmatch '(?:SetFact|this\.Set\(|\.Restore\(|\.Enable\(|\.Start\(|QueueEvent|Request|RegisterMappin)\(')
$newWrites=([regex]::Matches($new,'this\.Set\([^\r\n]+')|ForEach-Object{$_.Value}) -join "`n"
$oldWrites=([regex]::Matches($old,'this\.Set\([^\r\n]+')|ForEach-Object{$_.Value}) -join "`n"
Check 'All existing writes identical' ($newWrites -ceq $oldWrites)
Check 'No graph / entitlement / counter reset introduced' ($helper -notmatch '(?:SetFact|Set\().*(?:apartment_on|interior_manager_on|OwnerEntered|Claimed|Hold|Rejected|Interrupted)')
Check 'Required public interfaces' ($new.Contains('public func H10GeometryReady() -> Bool') -and $new.Contains('public func H10Status() -> String'))
Check 'No handoff circularity' ($helper -notmatch 'PTFRPA2_(Prepared|Reveal|Finished)' -and $helper.Contains('PTFRPA2_ControlReady') -and $helper.Contains('PTFRPA2_Teleported'))
Check 'Positive acknowledgement reads all five native layers' (@([regex]::Matches($helper,'this\.H10LayerReady\(q,')).Count -eq 5 -and $helper.Contains('q.GetFact(hold) == 0'))
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
Check 'Runtime baseline still unchanged' ((Hash (Join-Path $game 'r6/scripts/PTFR_PreAlpha/PTFR_RestorationBaseline/RestorationBaseline.reds')) -ceq $baseHash)
$compare=Get-Content -Raw -LiteralPath (Join-Path $ws 'research/post_ending_regression_20261013/h10_package_compare.json')|ConvertFrom-Json
Check 'All 24 native H10 members previously compared byte-identical' ($compare.member_count -eq 24 -and $compare.all_present_and_byte_equal)
Check 'Active native archive still matches comparison' ((Hash (Join-Path $game 'archive/pc/mod/TowerContinued_PreAlpha.archive')) -ceq $compare.active_archive_sha256)

# Model mirrors candidate constants; source assertions bind them explicitly.
Check 'Envelope source constants bound' ($helper.Contains('dx*dx+dy*dy >= 40000.0 || AbsF(p.Z-124.0) >= 75.0'))
Check 'Position validity source bound' ($helper.Contains('p.X > -100000.0 && p.X < 100000.0 && p.Y > -100000.0 && p.Y < 100000.0') -and $helper.Contains('p.Z > -10000.0 && p.Z < 10000.0'))
function Offsite([double]$x,[double]$y,[double]$z,[int]$teleported=1,[int]$control=1,[int]$fault=0){
 if($teleported -ne 1 -or $control -ne 1 -or $fault -ne 0){return $false}
 if(!($x -gt -100000 -and $x -lt 100000 -and $y -gt -100000 -and $y -lt 100000 -and $z -gt -10000 -and $z -lt 10000)){return $false}
 $dx=$x+1382.02319;$dy=$y-1272.61865
 return ($dx*$dx+$dy*$dy -ge 40000 -or [Math]::Abs($z-124) -ge 75)
}
Check 'New H10 street arrival admitted offsite' (Offsite -1432.13672 1261.04565 23.0654984)
Check 'Current Auto19 street position admitted offsite' (Offsite -1556.0311 1246.0214 19.0609)
Check 'Apartment center excluded' (!(Offsite -1382.02319 1272.61865 124))
Check 'Elevator late sample excluded' (!(Offsite -1435.085205 1312.849365 108.916306))
Check 'Near-floor corridor excluded from new offsite path' (!(Offsite -1400 1272.61865 123))
Check 'Old corridor still available in caller' ($new.Contains('corridor || (high == 1 && tier == 1 && this.H10OffsiteReady(q,p))'))
Check 'Vertical inner edge excluded' (!(Offsite -1382.02319 1272.61865 49.001))
Check 'Vertical separation edge admitted' (Offsite -1382.02319 1272.61865 49)
Check 'Horizontal inner edge excluded' (!(Offsite (-1382.02319+199.999) 1272.61865 124))
Check 'Horizontal separation edge admitted' (Offsite (-1382.02319+200.001) 1272.61865 124)
foreach($axis in 0..2){foreach($value in @([double]::NaN,[double]::PositiveInfinity,[double]::NegativeInfinity,100001,-100001)){$p=@(-1432.13672,1261.04565,23.0654984);$p[$axis]=$value;Check "Reject invalid axis $axis value $value" (!(Offsite $p[0] $p[1] $p[2]))}}
Check 'No arrival handoff admission before teleport' (!(Offsite -1432.13672 1261.04565 23.0654984 0 1 0))
Check 'No arrival handoff admission before control' (!(Offsite -1432.13672 1261.04565 23.0654984 1 0 0))
Check 'Faulted handoff refused' (!(Offsite -1432.13672 1261.04565 23.0654984 1 1 1))

# All available variant placements and collision extents, not just default variant.
$dir=Join-Path $ws 'research/b0_missing_content/h10_architecture/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default'
$sectors=@();$placements=0;$collisionRows=0;$maxRadius=0.0;$minZ=10000.0;$maxZ=-10000.0
foreach($path in Get-ChildItem -LiteralPath $dir -Filter '*.streamingsector.json'){
 $root=(Get-Content -Raw -LiteralPath $path.FullName|ConvertFrom-Json -Depth 100).Data.RootChunk
 foreach($row in $root.nodeData.Data){
  $placements++;$node=$root.nodes[$row.NodeIndex].Data
  $radius=0.0
  if($node.'$type' -eq 'worldCollisionNode'){
   $collisionRows++;$scale=[Math]::Max([Math]::Abs($row.Scale.X),[Math]::Max([Math]::Abs($row.Scale.Y),[Math]::Abs($row.Scale.Z)))
   $e=$node.extents;$radius=[Math]::Sqrt($e.X*$e.X+$e.Y*$e.Y+$e.Z*$e.Z)*$scale
  }
  $p=$row.Position;$dx=$p.X+1382.02319;$dy=$p.Y-1272.61865
  $xyRadius=[Math]::Sqrt($dx*$dx+$dy*$dy)+$radius
  $maxRadius=[Math]::Max($maxRadius,$xyRadius);$minZ=[Math]::Min($minZ,$p.Z-$radius);$maxZ=[Math]::Max($maxZ,$p.Z+$radius)
 }
 $sectors+=@{path=$path.FullName;sha256=(Hash $path.FullName);placements=$root.nodeData.Data.Count}
}
Check 'Exactly five native sector evidence inputs' ($sectors.Count -eq 5)
Check '873 placements covered' ($placements -eq 873)
Check '71 collision placements covered' ($collisionRows -eq 71)
Check 'Conservative collision sphere stays within 20m XY of apartment center' ($maxRadius -lt 20)
Check 'Conservative collision sphere stays within z110..140' ($minZ -gt 110 -and $maxZ -lt 140)
Check 'New offsite clearance exceeds collision bounds by at least 50m vertically' ($minZ-49 -gt 50 -and 199-$maxZ -gt 50)
$bounds=@{status='ALL_FIVE_NATIVE_VARIANT_COLLISION_PLACEMENTS_BOUNDED_NOT_RENDER_PROOF';placements=$placements;collision_placements=$collisionRows;max_xy_collision_sphere_radius=$maxRadius;min_z_collision_sphere=$minZ;max_z_collision_sphere=$maxZ;sectors=$sectors;note='worldNodeData Bounds fields are sometimes degenerate. Collision extents are treated as enclosing spheres and joined to world node positions; no whole-building bound is claimed.'}
[IO.File]::WriteAllText((Join-Path $out 'native_bounds.json'),($bounds|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))

$rules=(Get-Content -Raw -LiteralPath (Join-Path $ws 'research/restoration_baseline/rules.json')|ConvertFrom-Json)
$geometry=@($rules.rules|Where-Object {$_.kind -eq 'geometry'})
Check 'Five existing request rules' ($geometry.Count -eq 5)
$caseCount=0
function Admit($rule,$facts){foreach($p in $rules.common.PSObject.Properties){if($facts[$p.Name] -ne $p.Value){return $false}};foreach($p in $rule.guards.PSObject.Properties){if($facts[$p.Name] -ne $p.Value){return $false}};return $true}
foreach($rule in $geometry){
 $facts=@{};foreach($p in $rules.common.PSObject.Properties){$facts[$p.Name]=$p.Value};foreach($p in $rule.guards.PSObject.Properties){$facts[$p.Name]=$p.Value}
 Check ('Native/driver rule still admits '+$rule.write) (Admit $rule $facts)
 foreach($name in @($facts.Keys)){$mutant=$facts.Clone();$mutant[$name]=$mutant[$name]+1;Check ('Guard retained '+$rule.write+'/'+$name) (!(Admit $rule $mutant));$caseCount++}
 # Request-once and saved entered ownership must not reacquire on reload.
 $prefix=$rule.write.Replace('Request','');$duplicate=$facts.Clone();$duplicate[$prefix+'Claimed']=1;$duplicate[$prefix+'OwnerEntered']=1
 Check ('Saved acquired owner never re-requested '+$prefix) (!(Admit $rule $duplicate))
}
$report=[ordered]@{status='PASS_SOURCE_AND_MODEL_NOT_LIVE';source=$source;source_sha256=(Hash $source);baseline=$base;baseline_sha256=$baseHash;check_count=$checks.Count;guard_mutants=$caseCount;checks=$checks;native_bounds_sha256=(Hash (Join-Path $out 'native_bounds.json'));runtime_writes=0;save_writes=0;limitations=@('Source/contract checks and native resource bounds do not establish rendered geometry or native engine acquisition.','Full compile and combined package integration are parent-owned.','Public megabuilding lobby/atrium/elevators are not restored or verified by this apartment-only component.')}
[IO.File]::WriteAllText((Join-Path $out 'tests.json'),($report|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
'H10_PA5_TESTS_PASS='+$checks.Count
