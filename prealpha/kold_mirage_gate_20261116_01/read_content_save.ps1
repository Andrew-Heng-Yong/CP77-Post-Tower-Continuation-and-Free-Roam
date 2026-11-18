# Read-only content-scheduler projection from the two pinned qualification saves.
param([string]$Name='content_saves_02')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$workspace=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if($Name -notmatch '^[a-z0-9_]+$'){throw 'Unsafe output name'}
$out=Join-Path $PSScriptRoot "work/$Name.json"
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
. (Join-Path $workspace 'tools/build_phase2a.ps1') -HelpersOnly -WolvenKitRoot (Join-Path $workspace 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$readerType=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]
if((Get-FileHash -LiteralPath $readerType.Assembly.Location).Hash -cne 'EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987'){throw 'Parser drift'}
$expected=@{'ManualSave-31'='2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D';'ManualSave-32'='B5698BC909DD2CDDF34BA39E0DDE26E4480DD1769F9B4EE626717D8DBD2A622F'}
$rows=@(foreach($slot in @('ManualSave-31','ManualSave-32')){
 $path=Join-Path 'C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077' "$slot/sav.dat"
 for($item=Get-Item -LiteralPath $path -Force;$null -ne $item;){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked save'};$item=if($item -is [IO.FileInfo]){$item.Directory}else{$item.Parent}}
 $bytes=[IO.File]::ReadAllBytes($path)
 if([Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) -cne $expected[$slot]){throw 'Save drift'}
 $memory=[IO.MemoryStream]::new($bytes,$false);$reader=$readerType::new($memory)
 try{
  $save=$null
  if($reader.ReadFile([ref]$save).ToString() -cne 'NoError' -or $save.FileHeader.SaveVersion -ne 277){throw 'Unsupported save'}
  $selected=@($save.Nodes | Where-Object {$_.Name -match '(?i)content'})
  @{slot=$slot;sha256=$expected[$slot];roots=@($save.Nodes.Name);selected=@($selected | ForEach-Object {
   $n=$_
   @{name=$n.Name;value_type=$n.Value.GetType().FullName;header_hex=[Convert]::ToHexString($n.Value.HeaderBlob);trailing_hex=[Convert]::ToHexString($n.Value.TrailingBlob);fields=@($n.Value.PSObject.Properties | ForEach-Object {
    $v=$_.Value
    @{name=$_.Name;type=if($null -ne $v){$v.GetType().FullName}else{'null'};value=if($null -eq $v -or $v -is [string] -or $v.GetType().IsPrimitive){$v}else{$null};count=if($v -is [Collections.ICollection]){$v.Count}else{$null}}
   });children=@($n.Children | ForEach-Object {$_.Name})}
  })}
 }finally{$reader.Dispose();$memory.Dispose()}
 if((Get-FileHash -LiteralPath $path).Hash -cne $expected[$slot]){throw 'Save changed during read'}
})
@{status='READ_ONLY_CONTENT_SAVE';save_writes=0;game_calls=0;saves=$rows}|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $out -Encoding utf8NoBOM
Write-Output "Saved content projection: $out"
