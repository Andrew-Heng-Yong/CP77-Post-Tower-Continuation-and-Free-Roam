"""Build an alpha-only diagnostic overlay; never change the installed game."""
from pathlib import Path
import hashlib,json,re,zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
OUT=HERE/'build/candidate_01'
TAG='v0.1.1-alpha.20261024'
ZIP=ROOT/f'dist/{TAG}/TowerContinuation-{TAG}.zip'
MANIFEST=ROOT/f'release/manifest-{TAG}.json'
EQUIP='r6/scripts/PTFR_PreAlpha/PTFR_Restrictions_R1/EquipmentHooks.reds'
COVER='r6/scripts/TowerContinued_Loading_LC1/StartupCoverLC1.reds'

def sha(data):return hashlib.sha256(data).hexdigest().upper()
def once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)

HELPER='''
// CD1 diagnostics only. No saved fields, retries or inventory writes.
public abstract class CyberwareDiagnosticsCD1 {
  public static func Item(id: ItemID) -> String {
    return TDBID.ToStringDEBUG(ItemID.GetTDBID(id)) + " hash=" + ToString(ItemID.GetCombinedHash(id)) + " seed=" + ToString(ItemID.GetRngSeed(id)) + " query=" + ToString(ItemID.IsQuery(id)) + " structure=" + ToString(EnumInt(ItemID.GetStructure(id)));
  }
  public static func Parts(parts: array<InnerItemData>) -> String {
    let text = ""; let i = 0;
    while i < ArraySize(parts) && i < 64 {
      text += " [" + ToString(i) + "] " + CyberwareDiagnosticsCD1.Item(InnerItemData.GetItemID(parts[i])) + " slot=" + TDBID.ToStringDEBUG(InnerItemData.GetSlotID(parts[i]));
      i += 1;
    }
    if i < ArraySize(parts) { text += " [diagnostic list capped at 64; all parts still checked]"; }
    return text;
  }
}
'''

def equipment(text):
    text=once(text,'  item.GetItemParts(before);',
      '  item.GetItemParts(before);\n  ModLog(n"PTFR_CyberwareCD1", "BEFORE item=" + CyberwareDiagnosticsCD1.Item(id) + " dataID=" + CyberwareDiagnosticsCD1.Item(item.GetID()) + " quantity=" + ToString(quantity) + " area/slot=" + ToString(area) + "/" + ToString(slot) + " parts=" + ToString(ArraySize(before)) + CyberwareDiagnosticsCD1.Parts(before));')
    text=once(text,'  if !IsDefined(readback) || ts.GetItemQuantity(this.m_owner, id) != quantity { return -1; }',
      '  if !IsDefined(readback) || ts.GetItemQuantity(this.m_owner, id) != quantity {\n    ModLog(n"PTFR_CyberwareCD1", "FAIL item_or_quantity item=" + CyberwareDiagnosticsCD1.Item(id) + " readbackDefined=" + ToString(IsDefined(readback)) + " quantityBefore/after=" + ToString(quantity) + "/" + ToString(ts.GetItemQuantity(this.m_owner, id)) + " equippedNow=" + CyberwareDiagnosticsCD1.Item(this.GetItemInEquipSlot(area, slot)));\n    return -1;\n  }')
    text=once(text,'  readback.GetItemParts(after);',
      '  readback.GetItemParts(after);\n  ModLog(n"PTFR_CyberwareCD1", "AFTER item=" + CyberwareDiagnosticsCD1.Item(id) + " dataID=" + CyberwareDiagnosticsCD1.Item(readback.GetID()) + " quantity=" + ToString(ts.GetItemQuantity(this.m_owner, id)) + " equippedNow=" + CyberwareDiagnosticsCD1.Item(this.GetItemInEquipSlot(area, slot)) + " parts=" + ToString(ArraySize(after)) + CyberwareDiagnosticsCD1.Parts(after));')
    text=once(text,'  if ArraySize(before) != ArraySize(after) { return -1; }',
      '  if ArraySize(before) != ArraySize(after) {\n    ModLog(n"PTFR_CyberwareCD1", "FAIL part_count item=" + CyberwareDiagnosticsCD1.Item(id) + " before/after=" + ToString(ArraySize(before)) + "/" + ToString(ArraySize(after)));\n    return -1;\n  }')
    text=once(text,'    if !found { return -1; }',
      '    if !found {\n      ModLog(n"PTFR_CyberwareCD1", "FAIL part_identity_or_slot item=" + CyberwareDiagnosticsCD1.Item(id) + " beforeIndex=" + ToString(i));\n      return -1;\n    }')
    return text+HELPER

FAULT_LINE='''      this.SetStage("Setup stopped","Arrival/optics/housing faults: "+ToString(this.Fact(n"PTFRPA2_Fault"))+"/"+ToString(this.Fact(n"PTFRPA5O_Fault"))+"/"+ToString(this.Fact(n"PTFRH1_Fault"))+"\\nBody: "+StrAfterFirst(body.GetStatus()," | ")+"\\nProfile: "+StrAfterFirst(profile.GetStatus()," | "));return false;'''
REPLACEMENT='''      let cd1Flags="Arrival/optics/housing faults: "+ToString(this.Fact(n"PTFRPA2_Fault"))+"/"+ToString(this.Fact(n"PTFRPA5O_Fault"))+"/"+ToString(this.Fact(n"PTFRH1_Fault"))+"\\nBody/profile/cyberware fault: "+ToString(body.PTFRR3Faulted())+"/"+ToString(profile.PTFRPAFaulted())+"/"+ToString(!chrome.PTFRR2Healthy());
      if NotEquals(this.stage,"Setup stopped") {
        ModLog(n"PTFR_CyberwareCD1",cd1Flags+"\\nBody: "+body.GetStatus()+"\\nProfile: "+profile.GetStatus()+"\\nCyberware: "+chrome.GetStatus()+"\\nCyberware audit: "+chrome.GetAudit());
      }
      this.SetStage("Setup stopped",cd1Flags+"\\n"+(!chrome.PTFRR2Healthy() ? "Cyberware item-preservation check failed." : "A setup safety check failed.")+"\\nCD1 details are in CET gamelog.log. Keep the original test save.");return false;'''

def normalized(text):return re.sub(r'\s+','',text)

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    rows={r['path']:r for r in json.loads(MANIFEST.read_text())['files']}
    changes=[]
    with zipfile.ZipFile(ZIP) as z:
        for name,row in rows.items():assert sha(z.read(name))==row['sha256'],name
        for name,transform in [(EQUIP,equipment),(COVER,lambda t:once(t,FAULT_LINE,REPLACEMENT))]:
            before=z.read(name);original=before.decode('utf-8-sig').replace('\r\n','\n');updated=transform(original)
            if name==EQUIP:
                # Removing diagnostic log statements/helper must recover every
                # original gate, native call, comparison and return unchanged.
                stripped=updated[:-len(HELPER)]
                stripped=re.sub(r'^.*ModLog\(n"PTFR_CyberwareCD1".*\n','',stripped,flags=re.M)
                assert normalized(stripped)==normalized(original)
            else:assert updated.replace(REPLACEMENT,FAULT_LINE)==original
            assert re.findall(r'private persistent let [^;]+;',original)==re.findall(r'private persistent let [^;]+;',updated)
            after=updated.replace('\n','\r\n').encode('utf-8')
            for folder,data in [('before',before),('package',after)]:
                dest=OUT/folder/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
            changes.append({'path':name,'before':sha(before),'after':sha(after),'bytes':len(after)})
    report={'status':'DIAGNOSTICS_ONLY_NOT_A_GAMEPLAY_FIX','base_release':TAG,'base_zip_sha256':sha(ZIP.read_bytes()),'changes':changes,'saved_fields_unchanged':True,'original_equipment_control_flow_unchanged':True,'cover_fault_predicate_and_readiness_barrier_unchanged':True,'game_writes':False}
    (OUT/'changes_01.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
