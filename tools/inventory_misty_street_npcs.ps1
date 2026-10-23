param([string]$WorkspaceRoot=(Split-Path -Parent $PSScriptRoot))
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'build_phase2a.ps1') -WorkspaceRoot $WorkspaceRoot -HelpersOnly
$out=Join-Path $WorkspaceRoot 'research\misty_viktor_world\street_npc_sources'
New-Item -ItemType Directory -Force $out|Out-Null
$hash=[WolvenKit.Common.Services.HashService]::new();$hash.Load()
$game='C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\archive\pc'
$found=[Collections.Generic.List[object]]::new()
foreach($folder in @('ep1','content')){
 foreach($path in (Get-ChildItem -LiteralPath (Join-Path $game $folder) -Filter '*.archive' -File)){
  if($path.Name -notmatch 'nightcity|gamedata|characters'){continue}
  $arc=$null
  if(([WolvenKit.RED4.Archive.IO.ArchiveReader]::new()).ReadArchive($path.FullName,$hash,[ref]$arc).ToString() -ne 'NoError'){throw 'Archive read failed'}
  foreach($e in $arc.Files.Values){
   if($e.Name -match '(?i)q307.*\.(community|ent)$'){
    $row=[ordered]@{archive=$path.FullName;resource=$e.Name;bytes=$e.Size}
    $dst=Join-Path $out ('raw\'+$e.Name);New-Item -ItemType Directory -Force (Split-Path -Parent $dst)|Out-Null
    $stream=[IO.File]::Create($dst);try{$e.Extract($stream)}finally{$stream.Dispose()}
    $row.sha256=(Get-FileHash -LiteralPath $dst).Hash
    try{
      $file=Read-Cr2wFile $dst;$json=Join-Path $out ('json\'+$e.Name+'.json')
      New-Item -ItemType Directory -Force (Split-Path -Parent $json)|Out-Null
      Export-Cr2wJson $file $json;$row.exported=$true
    }catch{$row.exported=$false;$row.error=$_.Exception.Message}
    $found.Add([pscustomobject]$row)
   }
  }
 }
}
[IO.File]::WriteAllText((Join-Path $out 'inventory.json'),(@($found)|ConvertTo-Json -Depth 5))
$found|Select-Object resource,exported|Format-Table -AutoSize
