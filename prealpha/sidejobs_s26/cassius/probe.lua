-- Integrated into the manual S26 helper by its builder. No callbacks until Arm().
-- Observation only: never call native stock initialization, listing or refresh APIs.
local function createCassiusProbe()
  local P = {}
  local armed, installed, buffer = false, {}, {}
  local vendorName = "Vendors.wat_nid_ripperdoc_01"
  local itemNames = {"Items.YakuzaTattoo", "Items.AdvancedYakuzaTattoo"}
  local function read(fn)
    local ok, value = pcall(fn)
    if not ok then return {state="Unknown", error=tostring(value)} end
    if value == nil then return {state="Unknown", error="nil"} end
    local kind = type(value)
    if kind ~= "string" and kind ~= "number" and kind ~= "boolean" and kind ~= "table" then value=tostring(value) end
    return {state="Known", value=value}
  end
  local function matches(id, name)
    local ok, value = pcall(function() return id == TweakDBID.new(name) end)
    return ok and value == true
  end
  local function itemName(id)
    for _, name in ipairs(itemNames) do
      local ok, value = pcall(function() return ItemID.GetTDBID(id) end)
      if ok and matches(value, name) then return name end
    end
    return nil
  end
  local function quantities(owner)
    local result={}
    for _, name in ipairs(itemNames) do
      result[name]=read(function()
        if owner==nil then error("owner unavailable") end
        return Game.GetTransactionSystem():GetItemQuantity(owner, ItemID.CreateQuery(TweakDBID.new(name)))
      end)
    end
    return result
  end
  local function stock(vendor)
    local rows={}
    local ok, err=pcall(function()
      local native=vendor.m_stock
      if native==nil then error("private stock inaccessible") end
      for _, stack in ipairs(native) do
        local name=itemName(stack.itemID)
        if name then
          rows[#rows+1]={record=name, instance=tostring(stack.itemID), quantity=read(function() return stack.quantity end),
            ware=read(function() return tostring(stack.vendorItemID) end), available=read(function() return stack.isAvailable end)}
        end
      end
    end)
    if not ok then return {state="Unknown", error=tostring(err)} end
    return {state="Known", rows=rows}
  end
  local function vendorOpen(vendor)
    local ok, id=pcall(function() return vendor:GetVendorTweakID() end)
    if not ok or not matches(id,vendorName) then return end
    local _, owner=pcall(function() return vendor.m_vendorObject end)
    buffer.vendor={event="after_native_vendor_open", id=tostring(id),
      attached=read(function() return vendor:IsAttached() end),
      stockInitialized=read(function() return vendor.m_stockInit end),
      inventoryInitialized=read(function() return vendor.m_inventoryInit end),
      lastInteractionTime=read(function() return vendor:GetLastInteractionTime() end),
      stock=stock(vendor), vendorQuantities=quantities(owner), playerQuantities=quantities(Game.GetPlayer())}
  end
  local function isCassiusUI(ui)
    local ok,id=pcall(function() return ui.m_VendorDataManager:GetVendorID() end)
    return ok and matches(id,vendorName)
  end
  local function uiState(ui)
    local fields={}
    for _, name in ipairs({"m_isActivePanel","m_isCapacityBarReady","m_isArmorBarReady","m_isPurchasing","m_isInEquipPopup",
        "m_isTutorial","m_vikTutorial"}) do
      fields[name]=read(function() return ui[name] end)
    end
    for _, name in ipairs({"m_screen","m_filterArea","m_filterMode","m_hoverArea","ptfrr1BuyOnly"}) do
      fields[name]=read(function() local v=ui[name];if v==nil then error("field unavailable") end;return tostring(v) end)
    end
    return fields
  end
  local function prepared(ui)
    if not isCassiusUI(ui) then return end
    local rows={}
    local ok,err=pcall(function()
      local groups=ui.m_cachedVendorItems
      if groups==nil then error("private UI cache inaccessible") end
      for area,group in ipairs(groups) do
        for _,wrapped in ipairs(group) do
          local id=wrapped.Item:GetID();local name=itemName(id)
          if name then
            rows[#rows+1]={record=name,instance=tostring(id),cacheArea=area,
              available=read(function() return wrapped.AdditionalData.IsAvailable end)}
          end
        end
      end
    end)
    buffer.ui={event="after_native_prepare_vendor_items", fields=uiState(ui), items=ok and {state="Known",rows=rows} or {state="Unknown",error=tostring(err)}}
  end
  local function clicked(ui,event)
    if not isCassiusUI(ui) then return end
    local ok,id=pcall(function() return event.uiInventoryItem:GetID() end)
    if not ok then return end
    local name=itemName(id);if not name then return end
    buffer.click={event="after_user_tattoo_click",record=name,instance=tostring(id),fields=uiState(ui),
      available=read(function() return event.additionalData.IsAvailable end),
      action=read(function() return tostring(event.actionName) end)}
  end
  local hooks={{"Vendor","OnVendorMenuOpen",vendorOpen},{"RipperDocGameController","PrepareVendorItems",prepared},{"RipperDocGameController","OnSlotClick",clicked}}
  function P.Arm()
    armed=false;buffer={}
    if type(ObserveAfter)~="function" then return "Refused: ObserveAfter unavailable; nothing armed" end
    for i,hook in ipairs(hooks) do
      if not installed[i] then
        local callback=hook[3]
        local ok,err=pcall(function()
          ObserveAfter(hook[1],hook[2],function(...)
            if not armed then return end
            local good,why=pcall(callback,...)
            if not good then buffer.lastError=tostring(why) end
          end)
        end)
        if not ok then return "Refused: observer registration failed; nothing armed: "..tostring(err) end
        installed[i]=true
      end
    end
    armed=true
    return "Cassius read-only probe armed. Open Cassius's shop normally, select Hands, try the free tattoo if visible, close the shop, then Capture(). No stock is created or refreshed by this probe."
  end
  function P.Stop() armed=false;return "Cassius read-only probe stopped; buffered observations retained" end
  function P.Snapshot()
    local count=0;for _ in pairs(installed) do count=count+1 end
    return {armed=armed,registeredObservers=count,callbacksAutomaticOnLoad=0,observations=buffer,
      limitations="Buffered events only; private-field access may be Unknown. No reward-history or cause inferred. No stock initialization, restock, item grant, installation, journal/fact changes or forced completion."}
  end
  return P
end
