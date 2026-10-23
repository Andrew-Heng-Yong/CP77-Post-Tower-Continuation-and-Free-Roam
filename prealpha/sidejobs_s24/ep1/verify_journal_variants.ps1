param([string]$Revision='journal_variants_01')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$out=Join-Path $ws ('research/sidejobs_s24/ep1/'+$Revision)
if($Revision -cnotmatch '^journal_variants_\d{2}$' -or (Test-Path -LiteralPath $out)){throw 'Immutable evidence revision required'}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077'
$source='research/sidejobs_s24/ep1/native_02/raw/base/journal/cooked_journal.journal'
$depot='base\journal\cooked_journal.journal'
$archives=@('archive/pc/content/basegame_4_gamedata.archive','archive/pc/ep1/ep1_2_gamedata.archive')
New-Item -ItemType Directory -Path $out|Out-Null
$rows=@()
for($i=0;$i -lt $archives.Count;$i++){
 $ap=Join-Path $game $archives[$i];$target=Join-Path $out ('variant_'+$i)
 & (Join-Path $ws 'tools/extract_resources.ps1') -ResourcePaths @($depot) -OutputRoot $target -ArchivePaths @($ap)
 $raw=Join-Path $target ('raw/'+$depot);$json=Join-Path $target ('json/'+$depot+'.json')
 $rows+=,@{archive=$ap;depot=$depot;sha256=(Get-FileHash $raw).Hash;raw=('research/sidejobs_s24/ep1/'+$Revision+'/variant_'+$i+'/raw/'+$depot.Replace('\','/'));json=('research/sidejobs_s24/ep1/'+$Revision+'/variant_'+$i+'/json/'+$depot.Replace('\','/')+'.json');json_sha256=(Get-FileHash $json).Hash}
}
$report=@{status='OFFICIAL_JOURNAL_VARIANTS_EXTRACTED_NOT_SEMANTIC_PROOF';depot=$depot;source=$source;source_sha256=(Get-FileHash (Join-Path $ws $source)).Hash;variants=$rows;extractor_sha256=(Get-FileHash $PSCommandPath).Hash;game_writes=$false}
[IO.File]::WriteAllText((Join-Path $out 'extraction.json'),($report|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false))
$report|Select-Object status,source_sha256|ConvertTo-Json
