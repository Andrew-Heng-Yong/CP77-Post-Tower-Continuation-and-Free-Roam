"""Execute actual opt-in Lua probe under LuaJIT with native mutation tripwires."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "probe.lua"
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime


def run(output):
    source = SOURCE.read_text(encoding="utf-8")
    for banned in ["GetStock(", "GetItemsForSale(", "GetCyberwareForSale(", "FillVendorInventory(", "GetVendorObject(",
                   "GetBuyingPrice(", "GetOrAddVendor(", "SetFact", "GiveItem", "RemoveItem", "Initialize(", "RegenerateStock(",
                   "registerForEvent", "Override(", "io.", "print(", "SetState"]:
        assert banned not in source, banned
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
      events={}; registrationCount=0; failRegistration=nil; mutationCalls=0
      TweakDBID={new=function(s) return s end}
      ItemID={GetTDBID=function(id) return id.record end,CreateQuery=function(s) return {record=s,query=true} end}
      function ObserveAfter(c,m,fn)
        if failRegistration==m then error("registration fixture") end
        registrationCount=registrationCount+1; events[c.."."..m]=fn
      end
      player={quantities={}}; ts={}
      function ts:GetItemQuantity(owner,id) assert(id.query==true); return owner.quantities[id.record] or 0 end
      Game={GetPlayer=function() return player end, GetTransactionSystem=function() return ts end}
      function tripwire() mutationCalls=mutationCalls+1;error("native mutation forbidden") end
      function makeVendor(name)
        local v={m_stockInit=true,m_inventoryInit=true,m_vendorObject={quantities={["Items.AdvancedYakuzaTattoo"]=1}},
          m_stock={{itemID={record="Items.AdvancedYakuzaTattoo"},quantity=1,vendorItemID="Vendors.wat_nid_ripperdoc_01_inline0",isAvailable=true}}}
        function v:GetVendorTweakID() return name end
        function v:IsAttached() return true end
        function v:GetLastInteractionTime() return 15 end
        v.GetStock=tripwire;v.GetVendorObject=tripwire;v.FillVendorInventory=tripwire
        return v
      end
      function makeUI(name)
        local item={};function item:GetID() return {record="Items.AdvancedYakuzaTattoo"} end
        local manager={};function manager:GetVendorID() return name end;manager.GetBuyingPrice=tripwire
        local ui={m_VendorDataManager=manager,m_isActivePanel=true,m_isCapacityBarReady=true,m_isArmorBarReady=true,
          m_isPurchasing=false,m_isInEquipPopup=false,m_isTutorial=false,m_vikTutorial=false,m_screen="Ripperdoc",m_filterArea="HandsCW",m_filterMode="Item",m_hoverArea="HandsCW",ptfrr1BuyOnly="None",m_cachedVendorItems={{Item=item,AdditionalData={IsAvailable=true}}}}
        ui.m_cachedVendorItems={ui.m_cachedVendorItems};return ui,item
      end
      function emitVendor(v) events["Vendor.OnVendorMenuOpen"](v) end
      function emitUI(ui) events["RipperDocGameController.PrepareVendorItems"](ui) end
      function emitClick(ui,item) events["RipperDocGameController.OnSlotClick"](ui,{uiInventoryItem=item,additionalData={IsAvailable=true},actionName="click"}) end
    ''')
    probe = lua.execute(source + "\nreturn createCassiusProbe()")
    g = lua.globals()
    cases = 0
    def check(value):
        nonlocal cases
        assert value
        cases += 1
    check(g.registrationCount == 0)
    check(probe.Snapshot()["armed"] is False)
    check("armed" in probe.Arm())
    check(g.registrationCount == 3)
    check("armed" in probe.Arm())
    check(g.registrationCount == 3)
    vendor = g.makeVendor("Vendors.wat_nid_ripperdoc_01")
    g.emitVendor(g.makeVendor("Vendors.some_other_vendor"))
    check(probe.Snapshot()["observations"]["vendor"] is None)
    g.emitVendor(vendor)
    row = probe.Snapshot()["observations"]["vendor"]
    check(row["stock"]["state"] == "Known")
    check(row["stock"]["rows"][1]["record"] == "Items.AdvancedYakuzaTattoo")
    check(row["stock"]["rows"][1]["available"]["value"] is True)
    check(row["vendorQuantities"]["Items.AdvancedYakuzaTattoo"]["value"] == 1)
    check(row["playerQuantities"]["Items.AdvancedYakuzaTattoo"]["value"] == 0)
    check(row["stockInitialized"]["value"] is True)
    ui,item=g.makeUI("Vendors.wat_nid_ripperdoc_01")
    g.emitUI(ui)
    check(probe.Snapshot()["observations"]["ui"]["items"]["rows"][1]["available"]["value"] is True)
    ui.ptfrr1BuyOnly="tattoo-instance";ui.m_isPurchasing=True
    g.emitClick(ui,item)
    click=probe.Snapshot()["observations"]["click"]
    check(click["fields"]["ptfrr1BuyOnly"]["value"]=="tattoo-instance")
    check(click["fields"]["m_isPurchasing"]["value"] is True)
    check(click["record"]=="Items.AdvancedYakuzaTattoo")
    # Unknown never silently becomes an empty stock/cached-item list.
    vendor.m_stock=None;g.emitVendor(vendor)
    check(probe.Snapshot()["observations"]["vendor"]["stock"]["state"]=="Unknown")
    ui.m_cachedVendorItems=None;g.emitUI(ui)
    check(probe.Snapshot()["observations"]["ui"]["items"]["state"]=="Unknown")
    # A genuine empty observable collection is distinct from unavailable access.
    vendor.m_stock=lua.table();g.emitVendor(vendor)
    check(probe.Snapshot()["observations"]["vendor"]["stock"]["state"]=="Known")
    check(len(probe.Snapshot()["observations"]["vendor"]["stock"]["rows"])==0)
    probe.Stop();vendor.m_stock=None;g.emitVendor(vendor)
    check(probe.Snapshot()["observations"]["vendor"]["stock"]["state"]=="Known")
    check(probe.Snapshot()["armed"] is False)
    check(g.mutationCalls==0)
    # Registration error does not leave partially registered callbacks active.
    g.failRegistration="PrepareVendorItems"
    second=lua.execute(source+"\nreturn createCassiusProbe()")
    check("Refused" in second.Arm())
    check(second.Snapshot()["armed"] is False)
    before=g.registrationCount;g.failRegistration=None
    second.Arm()
    check(g.registrationCount==before+2)
    check(second.Snapshot()["registeredObservers"]==3)
    check(g.mutationCalls==0)
    # Callback errors are buffered rather than escaping into native gameplay.
    g.Game.GetPlayer=lua.eval("function() error('player unavailable') end")
    g.emitVendor(vendor)
    check(second.Snapshot()["observations"]["lastError"] is not None)
    result={"status":"PASS_LUAJIT_READ_ONLY_OPT_IN_PROBE","cases":cases,"mutation_calls":g.mutationCalls,
            "automatic_callbacks":0,"explicit_arm_callbacks":3,"lua_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper(),
            "live_private_field_access":"UNVERIFIED_UNKNOWN_SAFE","fix_implemented":False,"installed":False}
    path=ROOT/output
    assert not path.exists()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":
    run(sys.argv[1])
