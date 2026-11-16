
// TP1 reads presentation state only. Logical attachment/visibility fields do
// not prove rendered pixels; retain that distinction in every assessment.
public abstract class PresentationTraceTP1 {
  public static func Capture(game: GameInstance, reason: CName) -> Void {
    let player=GameInstance.GetPlayerSystem(game).GetLocalPlayerControlledGameObject() as PlayerPuppet;
    if !IsDefined(player) || !player.IsAttached() || player.IsReplacer() { return; }
    ModLog(n"PTFR_PresentationTP1", "capture="+NameToString(reason));
    let ts=GameInstance.GetTransactionSystem(game);
    let data=EquipmentSystem.GetData(player);
    if IsDefined(ts) && IsDefined(data) {
      let arm=ts.GetItemInSlot(player,t"AttachmentSlots.RightArm");
      ModLog(n"PTFR_PresentationTP1", "hands equipped="+TDBID.ToStringDEBUG(ItemID.GetTDBID(data.GetItemInEquipSlot(gamedataEquipmentArea.RightArm,0)))+
        " fists="+TDBID.ToStringDEBUG(ItemID.GetTDBID(data.GetItemInEquipSlot(gamedataEquipmentArea.BaseFists,0)))+
        " attached="+ToString(IsDefined(arm))+" spawning="+ToString(ts.IsSlotSpawningAnyItem(player,t"AttachmentSlots.RightArm")));
      if IsDefined(arm) { PresentationTraceTP1.Meshes(arm,n"RightArm"); }
    }
    PresentationTraceTP1.Meshes(player,n"player");
    let cw=GameInstance.GetScriptableSystemsContainer(game).Get(n"CyberwareCustomizationSystem") as CyberwareCustomizationSystem;
    if IsDefined(cw) {
      let saved=cw.GetSavedData();
      ModLog(n"PTFR_PresentationTP1", "customization enabled="+ToString(saved.enabled)+" switcher="+NameToString(saved.switcherName)+
        " index="+ToString(saved.switcherIndex)+" maxtac="+ToString(saved.hasMaxTacApperanceEquipped));
    }
    PresentationTraceTP1.Layer(n"inkLoadingLayer");
    PresentationTraceTP1.Layer(n"inkMenuLayer");
    PresentationTraceTP1.Layer(n"inkGameNotificationsLayer");
    PresentationTraceTP1.Layer(n"inkHUDLayer");
  }
  private static func Meshes(entity: ref<Entity>, label: CName) -> Void {
    let components=entity.GetComponents();
    let i=0;
    let count=0;
    while i<ArraySize(components) && count<32 {
      let mesh=components[i] as MeshComponent;
      if IsDefined(mesh) {
        ModLog(n"PTFR_PresentationTP1", NameToString(label)+" mesh="+NameToString(mesh.GetName())+
          " type="+NameToString(mesh.GetClassName())+" enabled="+ToString(mesh.IsEnabled())+
          " renderEnabled="+ToString(mesh.isEnabled)+" appearance="+NameToString(mesh.meshAppearance)+" mask="+ToString(mesh.chunkMask)+" plane="+ToString(EnumInt(mesh.renderingPlane)));
        count+=1;
      }
      i+=1;
    }
    ModLog(n"PTFR_PresentationTP1", NameToString(label)+" components="+ToString(ArraySize(components))+" meshesLogged="+ToString(count));
    let rep=entity.FindComponentByType(n"gameTPPRepresentationComponent") as gameTPPRepresentationComponent;
    if IsDefined(rep) {
      ModLog(n"PTFR_PresentationTP1", NameToString(label)+" TPP configuration detached/attached/affected="+
        ToString(ArraySize(rep.detachedObjectInfo))+"/"+ToString(ArraySize(rep.attachedObjectInfo))+"/"+ToString(ArraySize(rep.affectedAppearanceSlots)));
    }
  }
  private static func Layer(name: CName) -> Void {
    let ink=GameInstance.GetInkSystem();
    if !IsDefined(ink) { return; }
    let layer=ink.GetLayer(name);
    if !IsDefined(layer) { ModLog(n"PTFR_PresentationTP1", NameToString(name)+" unavailable");return; }
    let controllers=layer.GetGameControllers();
    ModLog(n"PTFR_PresentationTP1", NameToString(name)+" controllers="+ToString(ArraySize(controllers)));
    let i=0;
    let remaining=32;
    while i<ArraySize(controllers) && i<8 && remaining>0 {
      let controller=controllers[i];
      if IsDefined(controller) {
        let label=NameToString(name)+"/"+NameToString(controller.GetClassName());
        remaining-=PresentationTraceTP1.Widget(controller.GetRootWidget(),label,0,remaining);
      }
      i+=1;
    }
  }
  private static func Widget(widget: wref<inkWidget>, path: String, depth: Int32, budget: Int32) -> Int32 {
    if !IsDefined(widget) || budget<=0 { return 0; }
    let name=path+"/"+NameToString(widget.GetName());
    let size=widget.GetSize();
    ModLog(n"PTFR_PresentationTP1", name+" visible="+ToString(widget.IsVisible())+" opacity="+ToString(widget.GetOpacity())+
      " size="+ToString(size.X)+"/"+ToString(size.Y));
    let used=1;
    let group=widget as inkCompoundWidget;
    if depth<2 && IsDefined(group) {
      let i=0;
      while i<group.GetNumChildren() && used<budget && i<12 {
        used+=PresentationTraceTP1.Widget(group.GetWidgetByIndex(i),name,depth+1,budget-used);
        i+=1;
      }
    }
    return used;
  }
}
