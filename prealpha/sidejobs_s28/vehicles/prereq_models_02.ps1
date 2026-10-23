# Authoring models for script RTTI classes. Engine implementations are in S28 REDS.
# No class fields are serialized: each script class has one fixed read-only check.
$modelSource=@'
using WolvenKit.RED4.Types;
namespace PTFRS28Authoring {
 public class HighwaymanPrereq : gameIScriptablePrereq, IDynamicClass {

  public CName ClassName {get;set;} = "PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq";
 }
 public class HoonPrereq : gameIScriptablePrereq, IDynamicClass {

  public CName ClassName {get;set;} = "PTFR.SideJobsS28.PTFRS28HoonVehicleUnownedPrereq";
 }
 public class HoonWorldPrereq : gameIScriptablePrereq, IDynamicClass {

  public CName ClassName {get;set;} = "PTFR.SideJobsS28.PTFRS28HoonWorldKeyAbsentPrereq";
 }
}
'@
Add-Type -TypeDefinition $modelSource -ReferencedAssemblies ([WolvenKit.RED4.Types.RedBaseClass].Assembly.Location)
$script:S28PrereqTypes=@{
 'PTFR.SideJobsS28.PTFRS28HighwaymanVehicleUnownedPrereq'=[PTFRS28Authoring.HighwaymanPrereq]
 'PTFR.SideJobsS28.PTFRS28HoonVehicleUnownedPrereq'=[PTFRS28Authoring.HoonPrereq]
 'PTFR.SideJobsS28.PTFRS28HoonWorldKeyAbsentPrereq'=[PTFRS28Authoring.HoonWorldPrereq]
}
foreach($entry in $script:S28PrereqTypes.GetEnumerator()){
 [void][WolvenKit.RED4.Types.RedReflection]::AddRedType($entry.Value)
 [WolvenKit.RED4.Types.RedReflection]::GetTypes()[$entry.Key]=$entry.Value
}

