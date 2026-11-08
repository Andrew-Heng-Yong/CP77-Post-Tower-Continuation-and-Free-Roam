param(
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][datetime]$SinceUtc,
 [string]$GameRoot='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077',
 [string]$Output
)
# Read/copy existing logs only. This does not start/stop the game, install a
# diagnostic, execute a console command, inspect save content, or set facts.
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($RunId -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$'){throw 'Simple bounded run ID required'}
$taskRoot=[IO.Path]::GetFullPath($PSScriptRoot)
if(-not $Output){$Output=Join-Path $taskRoot "acceptance_observations/$RunId"}
$dest=[IO.Path]::GetFullPath($Output)
if(-not $dest.StartsWith($taskRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Output must be a fresh QR8 subdirectory'}
if(Test-Path -LiteralPath $dest){throw 'Never overwrite an observation'}
$probe=[IO.DirectoryInfo]::new($dest)
while($probe){if($probe.Exists -and($probe.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked output ancestor'};$probe=$probe.Parent}
$game=[IO.Path]::GetFullPath($GameRoot);if(-not(Test-Path -LiteralPath $game -PathType Container)){throw 'Game root missing'}
$groups=@(
 @{relative='red4ext/plugins/ArchiveXL';filter='ArchiveXL*.log';limit=3},
 @{relative='red4ext/logs';filter='red4ext-*.log';limit=3},
 @{relative='r6/logs';filter='redscript_rCURRENT.log';limit=1},
 @{relative='bin/x64/plugins/cyber_engine_tweaks';filter='scripting.log';limit=1},
 @{relative='bin/x64/plugins/cyber_engine_tweaks';filter='cyber_engine_tweaks.log';limit=1},
 @{relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_PreAlpha';filter='PTFR_PreAlpha.log';limit=1},
 @{relative='bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1';filter='PTFR_HistorySnapshotHS1.log';limit=1}
)
New-Item -ItemType Directory -Path $dest|Out-Null
$rows=@();$missing=@();$ordinal=0
foreach($g in $groups){
 $dir=Join-Path $game $g.relative
 if(-not(Test-Path -LiteralPath $dir -PathType Container)){$missing+=,$g;continue}
 $files=@(Get-ChildItem -LiteralPath $dir -Filter $g.filter -File|Sort-Object LastWriteTimeUtc -Descending|Select-Object -First $g.limit)
 if(-not $files.Count){$missing+=,$g;continue}
 foreach($f in $files){
  if(-not $f.FullName.StartsWith($game+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Unexpected input containment'}
  if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked input log'}
  $before=(Get-FileHash -LiteralPath $f.FullName).Hash;$oldLength=$f.Length;$oldTime=$f.LastWriteTimeUtc
  $to=Join-Path $dest ("{0:D2}_{1}" -f $ordinal,$f.Name);Copy-Item -LiteralPath $f.FullName -Destination $to
  $copy=(Get-FileHash -LiteralPath $to).Hash;$after=(Get-FileHash -LiteralPath $f.FullName).Hash
  $rows+=,@{source=$f.FullName;copied=$to;source_before_sha256=$before;copy_sha256=$copy;source_after_sha256=$after;consistent_snapshot=($before -ceq $copy -and $copy -ceq $after);source_bytes_before=$oldLength;source_last_write_utc=$oldTime.ToString('o');newer_than_run_start=($oldTime -ge $SinceUtc.ToUniversalTime())}
  $ordinal++
 }
}
$dll=Join-Path $game 'red4ext/plugins/ArchiveXL/ArchiveXL.dll';$framework=$null
if(Test-Path -LiteralPath $dll -PathType Leaf){$v=[Diagnostics.FileVersionInfo]::GetVersionInfo($dll);$framework=@{path=$dll;sha256=(Get-FileHash -LiteralPath $dll).Hash;file_version=$v.FileVersion;product_version=$v.ProductVersion}}
@{status='READ_ONLY_EXISTING_LOG_SNAPSHOT_NOT_GAMEPLAY_PASS';run_id=$RunId;requested_since_utc=$SinceUtc.ToUniversalTime().ToString('o');captured_utc=[DateTime]::UtcNow.ToString('o');rows=$rows;missing_groups=$missing;ArchiveXL=$framework;limits=@('Stale logs remain explicitly labelled; no new run is inferred.','An inconsistent live-growing log snapshot must be captured again into another fresh directory.','Absence of log text is not proof a fact/controller never executed.','No runtime probe or fact mutation was performed by this collector.')}|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $dest 'manifest.json') -Encoding utf8NoBOM
'READ_ONLY_LOG_SNAPSHOT_COMPLETE'
