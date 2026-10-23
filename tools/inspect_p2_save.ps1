param([string]$SavePath='C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077\ManualSave-11\sav.dat', [string]$OutputPath='research/phase2b_p2/save_summary.json')
$ErrorActionPreference='Stop'
$wkP2='C:\Users\Ayong\Documents\WolvenKit-8.20.0'
foreach($a in @('WolvenKit.Core.dll','WolvenKit.Common.dll','WolvenKit.RED4.dll')) { [void][Reflection.Assembly]::LoadFrom((Join-Path $wkP2 $a)) }
$before=(Get-FileHash -LiteralPath $SavePath -Algorithm SHA256).Hash
$stream=[IO.File]::Open($SavePath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
try {
    $reader=[WolvenKit.RED4.Save.IO.CyberpunkSaveReader]::new($stream)
    $save=$null
    $result=$reader.ReadFile([ref]$save)
    if($result.ToString() -ne 'NoError'){ throw "Save read: $result" }
    $nodes=@($save.Nodes | ForEach-Object { [pscustomobject]@{Name=$_.Name;Type=if($_.Value){$_.Value.GetType().FullName}else{'NULL'};Size=$_.Size} })
    $j=($save.Nodes | Where-Object Name -eq 'JournalManager').Value
    $selected=@($j.Entries | ForEach-Object { $b=[byte[]]$_.UnkownBytes; $h=[BitConverter]::ToUInt32($b,0); if($h -in @([uint32]3310831952,[uint32]3340669932)){[pscustomobject]@{Hash=$h;Raw15=[Convert]::ToHexString($b);StateCandidate=[BitConverter]::ToUInt32($b,4)}} })
    $ps=($save.Nodes | Where-Object Name -eq 'PersistencySystem2').Value
    $doors=@($ps.Entries | Where-Object Id -in @([uint64]13806931541592989805,[uint64]6805700156449448318))
    foreach($door in $doors){
        $opt=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializerOptions]::new()
        $serialized=[WolvenKit.RED4.CR2W.JSON.RedJsonSerializer]::Serialize($door.Data,$opt)
        New-Item -ItemType Directory -Force -Path (Split-Path $OutputPath) | Out-Null
        $serialized | Set-Content (Join-Path (Split-Path $OutputPath) ('door_'+$door.Id+'.json')) -Encoding utf8NoBOM
    }
    $output=[ordered]@{Save=$SavePath;Hash=$before;Result=$result.ToString();Nodes=$nodes;Journal=$selected;Tracked=$j.Unk1_TrackedQuestPath;DoorEntries=@($doors | ForEach-Object { [pscustomobject]@{Id=$_.Id;Type=$_.Data.GetType().FullName} })}
    New-Item -ItemType Directory -Force -Path (Split-Path $OutputPath) | Out-Null
    $output | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding utf8NoBOM
    $nodes | Where-Object Name -Match 'journal|persist|quest|device' | Format-Table
    $selected | ConvertTo-Json -Depth 5
    $output.DoorEntries | Format-Table
} finally { $stream.Dispose() }
if((Get-FileHash -LiteralPath $SavePath -Algorithm SHA256).Hash -ne $before){throw 'Save changed during read'}
