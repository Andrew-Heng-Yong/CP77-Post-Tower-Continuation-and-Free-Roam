param([Parameter(Mandatory=$true)][string]$Inputs,[Parameter(Mandatory=$true)][string]$Output)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$w=(Get-Location).Path;$worker=[IO.Path]::GetFullPath($PSScriptRoot)
$o=if([IO.Path]::IsPathRooted($Output)){[IO.Path]::GetFullPath($Output)}else{[IO.Path]::GetFullPath((Join-Path $w $Output))}
if(-not $o.StartsWith($worker+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Private worker output containment required'}
if(Test-Path -LiteralPath $o){throw 'Fresh private output required'}
New-Item -ItemType Directory -Path $o|Out-Null
. (Join-Path $w 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
[void][Reflection.Assembly]::LoadFrom((Join-Path $w 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/YamlDotNet.dll'))
$pin=Get-Content -LiteralPath $Inputs -Raw|ConvertFrom-Json
if((Get-FileHash -LiteralPath $pin.archive).Hash -ne $pin.archive_sha256){throw 'Final archive changed'}
$expected=@{};foreach($p in $pin.canonical_resources.PSObject.Properties){$key=[string][WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($p.Name);if($expected.ContainsKey($key)){throw 'Canonical depot FNV collision'};$expected[$key]=@{depot=$p.Name;sha256=$p.Value}}
$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$a=$null
if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($pin.archive,$hs,[ref]$a).ToString() -ne 'NoError'){throw 'Final archive unreadable'}
$memberDir=Join-Path $o 'members';New-Item -ItemType Directory -Path $memberDir|Out-Null
$rows=@();foreach($entry in $a.Files.GetEnumerator()){
 $key=[string]$entry.Key;$raw=Join-Path $memberDir ($key+'.bin');$memory=[IO.MemoryStream]::new()
 try{$entry.Value.Extract($memory);[IO.File]::WriteAllBytes($raw,$memory.ToArray())}finally{$memory.Dispose()}
 $known=$expected.ContainsKey($key);$row=@{fnv64=$key;raw=$raw;raw_sha256=(Get-FileHash -LiteralPath $raw).Hash;bytes=(Get-Item -LiteralPath $raw).Length;known_canonical_key=$known}
 if($known){$row.depot=$expected[$key].depot;$row.canonical_sha256=$expected[$key].sha256
  if($pin.expected_proposal_delta.PSObject.Properties.Name -contains $row.depot){$json=$raw+'.json';try{Export-Cr2wJson (Read-Cr2wFile $raw) $json;$row.typed_json=$json;$row.typed_json_sha256=(Get-FileHash -LiteralPath $json).Hash;$row.typed_status='FRESH_ACTUAL_ARCHIVE_MEMBER_READBACK'}catch{$row.typed_status='BLOCKED';$row.typed_error=$_.Exception.ToString()}}
 }
 $rows+=,$row
}
function YNode($n){
 if($n -is [YamlDotNet.RepresentationModel.YamlScalarNode]){return @{kind='scalar';value=$n.Value}}
 if($n -is [YamlDotNet.RepresentationModel.YamlSequenceNode]){return @{kind='sequence';items=@($n.Children|ForEach-Object {YNode $_})}}
 if($n -is [YamlDotNet.RepresentationModel.YamlMappingNode]){return @{kind='mapping';entries=@($n.Children.GetEnumerator()|ForEach-Object {@{key=(YNode $_.Key);value=(YNode $_.Value)}})}}
 throw 'Unsupported YAML node'
}
$xl=@();foreach($path in @($pin.baseline_XL,$pin.final_XL)){$ys=[YamlDotNet.RepresentationModel.YamlStream]::new();$sr=[IO.StringReader]::new([IO.File]::ReadAllText($path));try{$ys.Load($sr);if($ys.Documents.Count -ne 1){throw 'Expected one XL document'};$xl+=@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash;document=(YNode $ys.Documents[0].RootNode)}}finally{$sr.Dispose()}}
if((Get-FileHash -LiteralPath $pin.archive).Hash -ne $pin.archive_sha256){throw 'Archive changed during extraction'}
@{scope='Independent whole final archive extraction and focused actual member typed readback; no source/candidate/package writes';inputs=$Inputs;inputs_sha256=(Get-FileHash -LiteralPath $Inputs).Hash;members=$rows;XL=$xl;script_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;archive_sha256=(Get-FileHash -LiteralPath $pin.archive).Hash;candidate_writes=0;game_writes=0}|ConvertTo-Json -Depth 100|Set-Content -LiteralPath (Join-Path $o 'manifest.json') -Encoding utf8NoBOM
Write-Output ('Independently extracted '+$rows.Count+' final archive members')
