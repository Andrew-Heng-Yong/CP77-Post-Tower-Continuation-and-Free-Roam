param([string]$Output='stock_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$W=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$O=Join-Path $PSScriptRoot $Output
if(Test-Path -LiteralPath $O){throw 'Fresh worker output required'}
. (Join-Path $W 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $W 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$targets=@(
 @{id=[uint64]114327022403;label='Cuckoo Dixon scene86 inventory condition, exact numeric ID'},
 @{id=[uint64]145696460765;label='Career native node64 reward'},
 @{id=[uint64]51369838828;label='Items.money'},
 @{id=[uint64]127255451537;label='Items.q304_slider_stash_shard'},
 @{id=[uint64]118124605694;label='Items.Preset_Lexington_Rook'},
 @{id=[uint64]0;label='Null ID negative control'}
)
$controls=@()
foreach($t in $targets|Where-Object {$_.label.StartsWith('Items.')}){
 $actual=[WolvenKit.RED4.Types.TweakDBID]::CalculateHash($t.label)
 if($actual -ne $t.id){throw 'Named ID oracle mismatch'}
 $controls+=,@{name=$t.label;expected=$t.id.ToString();actual=$actual.ToString();pass=$true}
}
$game='C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077';$databases=@();$rows=@()
foreach($name in @('tweakdb.bin','tweakdb_ep1.bin')){
 $path=Join-Path $game ('r6/cache/'+$name);$before=(Get-FileHash -LiteralPath $path).Hash
 $s=[IO.File]::OpenRead($path)
 try{$db=$null;$r=([WolvenKit.RED4.TweakDB.TweakDBReader]::new($s)).ReadFile([ref]$db);if($r.ToString() -ne 'NoError'){throw 'TweakDB read failed'}}finally{$s.Dispose()}
 foreach($t in $targets){
  $record=$db.Records.GetRecord([uint64]$t.id)
  $rows+=,@{id=$t.id.ToString();requested_name=$t.label;database=$path;exists=($null -ne $record);record_type=$(if($null -ne $record){$record.Name}else{$null})}
 }
 if($null -eq $db.Records.GetRecord([uint64]51369838828)){throw 'Positive Items.money stock control missing'}
 if($null -ne $db.Records.GetRecord([uint64]0)){throw 'Null-ID negative control found'}
 if((Get-FileHash -LiteralPath $path).Hash -cne $before){throw 'Stock DB changed during read'}
 $databases+=,@{path=$path;sha256=$before;parse_status='NoError'}
}
[IO.Directory]::CreateDirectory($O)|Out-Null
@{status='READ_ONLY_DIRECT_STOCK_RECORD_LOOKUP';databases=$databases;records=$rows;named_id_controls=$controls;code_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;game_writes=0;limits=@('Base/EP1 definitions are separate, not a runtime merged winner.','No unknown name was invented for numeric114327022403.','DLL, TweakXL, CET computed overrides and live inventory query semantics are not established by stock definitions.')}|ConvertTo-Json -Depth 15|Set-Content -LiteralPath (Join-Path $O 'records.json') -Encoding utf8NoBOM
@{rows=$rows.Count;missing=@($rows|Where-Object {-not $_.exists}).Count;output=$O}|ConvertTo-Json -Compress
