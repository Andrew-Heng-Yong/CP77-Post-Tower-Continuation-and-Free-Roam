. ./tools/build_phase2a.ps1 -HelpersOnly -WolvenKitRoot (Join-Path (Get-Location).Path 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package')
$base='prealpha/lizzies_lr2/candidate_01/archive_source'
foreach($d in @('towercontinued\native_gigs_u9\sts_ep1_08_entry.questphase','towercontinued\gig_phone_u9\fixer_cleanup.questphase')){
 $r=Read-Cr2wFile (Join-Path $base $d);Export-Cr2wJson $r (Join-Path $PSScriptRoot (($d.Split('\')[-1])+'.json'))
 $d
 foreach($h in $r.RootChunk.Graph.Chunk.Nodes){$n=$h.Chunk; "$($n.Id): $($n.GetType().Name) $(@($n.Sockets|ForEach-Object {$_.Chunk.Name.ToString()}) -join ',')"}
}
