Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ws=Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
. (Join-Path $ws 'tools/build_phase2a.ps1') -HelpersOnly
$out=Join-Path $ws 'research/sidejobs_s28/encounters/official_check_01';if(Test-Path -LiteralPath $out){throw 'Immutable diagnostic exists'};New-Item -ItemType Directory $out|Out-Null
$c=Get-Content (Join-Path $ws 'prealpha/sidejobs_s28/encounters/build/encounters_01/component.json') -Raw|ConvertFrom-Json;$pins=@{}
foreach($p in $c.source_pins.PSObject.Properties){if($p.Name -match '^research/.+/raw/((base|ep1)/.+)$' -and !$p.Name.EndsWith('.journal')){$dep=$Matches[1].Replace('/','\');$pins[$dep]=@{expected=$p.Value;source=$p.Name}}}
foreach($folder in @('native_01','native_02','native_03','native_04')){Get-ChildItem (Join-Path $ws ('research/sidejobs_s28/encounters/'+$folder+'/raw')) -File -Recurse|ForEach-Object {$rel=[IO.Path]::GetRelativePath($ws,$_.FullName).Replace('\','/');$dep=($rel -split '/raw/',2)[1].Replace('/','\');$pins[$dep]=@{expected=(Get-FileHash $_.FullName).Hash;source=$rel}}}
foreach($rel in @('research/sidejobs_s27/heroes/native_04/raw/base/quest/main_quests/part1/q101/q101.questphase','research/q307_extracted/raw/base/quest/cyberpunk2077.questphase','research/q307_extracted/raw/ep1/quest/ep1.questphase')){$dep=($rel -split '/raw/',2)[1].Replace('/','\');$pins[$dep]=@{expected=(Get-FileHash (Join-Path $ws $rel)).Hash;source=$rel}}
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077';$hs=[WolvenKit.Common.Services.HashService]::new();$hs.Load();$rows=@();$archives=@();$keys=@{};foreach($dep in $pins.Keys){$keys[$dep]=[WolvenKit.Common.FNV1A.FNV1A64HashAlgorithm]::HashString($dep)}
$files=@(Get-ChildItem (Join-Path $game 'archive/pc/content') -File -Filter '*.archive')+@(Get-ChildItem (Join-Path $game 'archive/pc/ep1') -File -Filter '*.archive')
foreach($file in $files){$archive=$null;if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($file.FullName,$hs,[ref]$archive).ToString() -ne 'NoError'){throw 'Bad official archive'}
 foreach($dep in $pins.Keys){$key=$keys[$dep];if(!$archive.Files.ContainsKey($key)){continue};$e=$archive.Files[$key];$ms=[IO.MemoryStream]::new();try{$e.Extract($ms);$bytes=$ms.ToArray()}finally{$ms.Dispose()};$hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes));$raw=$null;$json=$null
 if($hash -cne $pins[$dep].expected){$base=Join-Path $out $file.BaseName;$raw=Join-Path $base ('raw/'+$dep);$json=Join-Path $base ('json/'+$dep+'.json');New-Item -ItemType Directory -Force (Split-Path $raw),(Split-Path $json)|Out-Null;[IO.File]::WriteAllBytes($raw,$bytes);Export-Cr2wJson (Read-Cr2wFile $raw) $json}
 $rows+=,@{depot=$dep;archive=$file.FullName;source=$pins[$dep].source;expected=$pins[$dep].expected;actual=$hash;equal=($hash -ceq $pins[$dep].expected);raw=$raw;json=$json}}
 $archives+=,@{path=$file.FullName;length=$file.Length;last_write_utc=$file.LastWriteTimeUtc.ToString('o')}
}
$report=@{status='CURRENT_OFFICIAL_ENCOUNTER_NATIVE_BYTE_DIAGNOSTIC';rows=$rows;archives=$archives;selected=$pins.Count;found=@($rows.depot|Sort-Object -Unique).Count;mismatches=@($rows|Where-Object {!$_.equal}).Count;script_sha256=(Get-FileHash $PSCommandPath).Hash}
[IO.File]::WriteAllText((Join-Path $out 'report.json'),($report|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false));@{selected=$report.selected;found=$report.found;mismatches=$report.mismatches}|ConvertTo-Json
