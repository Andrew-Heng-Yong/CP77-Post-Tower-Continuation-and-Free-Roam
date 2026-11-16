#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#include <bcrypt.h>
#include <RED4ext/RED4ext.hpp>
#include <RED4ext/Scripting/Natives/Generated/quest/QuestsSystem.hpp>

#include "../universal_resume_eagles_20261114_01/GameTimeWait.hpp"
#include "../universal_resume_retirement_20261114_01/RetiredQuestSlot.hpp"
#include "ReplyHandoff.hpp"

#include <array>
#include <atomic>
#include <cstdio>
#include <mutex>

namespace
{
using ptfr::NativeField;
constexpr std::uint32_t OriginalPhase = 0xCCF9887E;
constexpr std::uint32_t ReplyPhase = 0xC37CF97F;
constexpr std::uint64_t TimerType = 0xA384AD807139CF67;
constexpr std::array<std::uint16_t, 8> OriginalPath{0,2,82,4,9,3,98,103};
constexpr std::array<std::uint16_t, 3> ReplyPath{1,141,61102};
constexpr std::array<std::uint32_t, 5> OriginalNodes{80,88,89,90,209};
constexpr std::array<std::uint64_t, 5> OriginalTypes{
    TimerType,0x43B4E8D9E9E3C95F,0x43B4E8D9E9E3C95F,0x43B4E8D9E9E3C95F,0xB3333F2B5B40E255};
constexpr auto QuestSystem = 0x30BCE78;
constexpr auto FactsManager = 0x306FA58;
constexpr auto TimeSystem = 0x30BD228;
constexpr auto PhaseContext = 0x3040630;
constexpr auto PhaseInstance = 0x308A948;
constexpr auto WaitHandler = 0x31C2388;
constexpr auto TimerRecord = 0x30A75A8;
constexpr auto InitialCallback = 0x36A1D50;
constexpr auto LoadedCallback = 0x36A1D20;

constexpr std::uint32_t FactId(const char* name)
{
    std::uint32_t hash = 0x811C9DC5;
    for (; *name; ++name)
        hash = (hash ^ static_cast<unsigned char>(*name)) * 0x01000193;
    return hash;
}

using Register = void (*)(void*,std::uint32_t,std::uint64_t,const void*);
using Tick = void (*)(void*,float,const void*);
using Retire = void (*)(void*,std::uint32_t);
using StopHandler = void (*)(void*,std::uint32_t,void*);
using EraseChild = void (*)(void*,void*,const void*,std::uint8_t);
using Drain = void (*)(void*);
using ReadFact = std::int32_t (*)(const void*,std::uint32_t,std::uint32_t);
using ReadClock = std::uint32_t* (*)(const void*,std::uint32_t*);
using Schedule = std::uint32_t (*)(void*,void*,std::uint32_t,std::int32_t,std::uint8_t,std::uint32_t,
                                   std::uint64_t,std::uint64_t);
using EnqueueTimer = bool (*)(void*,const ptfr::NativeGameTimerReference*);
using TimerTick = std::uint8_t (*)(void*,std::uint32_t);
using Load = void (*)(void*,void*,void*,void*);
using Teardown = void (*)(void*,void*);

const RED4ext::v1::Sdk* sdk;
RED4ext::v1::PluginHandle plugin;
const std::uint8_t* image;
Register registerOriginal;
Tick tickOriginal;
Retire retireOriginal;
StopHandler stopOriginal;
EraseChild eraseChildOriginal;
Drain drainOriginal;
Schedule scheduleOriginal;
EnqueueTimer enqueueTimerOriginal;
TimerTick timerTickOriginal;
Load loadOriginal;
Teardown teardownOriginal;
std::array<RED4ext::CGlobalFunction*,3> functions{};
std::atomic_bool active{};

struct WatchedRegistration
{
    void* handler{};
    std::uint32_t slot{};
    bool closing{};
};

std::recursive_mutex stateMutex;
ptfr::ReplyHandoff handoff;
std::array<WatchedRegistration,OriginalNodes.size()> original{};
std::array<std::optional<ptfr::RetiredQuestSlot>,OriginalNodes.size()> reservations;
std::optional<ptfr::QuestNotificationDrain> drain;
std::uint64_t lifetime{};
void* questSystem{};
void* timeSystem{};
std::uint32_t timerId{};
std::uint32_t replacementTimerId{};
std::uint32_t replacementAuthoredSeconds{};
const void* originalTimer{};
std::optional<ptfr::ReplyDuration> requested;
bool replacementRegistered{};
void* replacementSystem{};
const void* replacementHandler{};
bool replacementClockLogged{};
std::uint32_t observedReplySeconds{};
std::uint32_t observedAuthoredSeconds{};
bool ownerConfirmed{};
std::optional<unsigned> replacementDuration;
bool schedulerAccepted{};
bool captureInvalid{};
bool dispatchingNotifications{};
bool originalPhaseDetached{};
bool originalRegisteredInSession{};
std::atomic_bool watchedSession{};
std::atomic<const void*> savedTimerIdentity{};
std::atomic<const void*> watchedQuestSystem{};
std::array<std::optional<std::uint32_t>,OriginalNodes.size()> reservedIndices;
thread_local const void* initializingHandler{};
thread_local bool registeringReplacement{};

template<class Method>
Method MethodAt(std::uintptr_t rva) { return reinterpret_cast<Method>(image + rva); }

void Log(const char* event, std::uint32_t value = 0)
{
    char line[144];
    std::snprintf(line,sizeof(line),"claire-reply %s value=%u",event,value);
    sdk->logger->Info(plugin,line);
}

void Reset(void* quests)
{
    const std::lock_guard lock(stateMutex);
    handoff = {};
    original = {};
    for (auto& item : reservations)
        item.reset();
    reservedIndices={};
    questSystem = quests;
    watchedQuestSystem.store(quests);
    timeSystem = nullptr;
    replacementSystem=nullptr;
    replacementHandler=nullptr;
    replacementClockLogged=false;
    observedReplySeconds=0;
    observedAuthoredSeconds=0;
    originalTimer=nullptr;
    savedTimerIdentity.store(nullptr);
    timerId = replacementTimerId = 0;
    replacementAuthoredSeconds=0;
    replacementRegistered=ownerConfirmed=schedulerAccepted=captureInvalid=false;
    dispatchingNotifications=false;
    originalPhaseDetached=false;
    originalRegisteredInSession=false;
    watchedSession.store(false);
    replacementDuration.reset();
    requested.reset();
    drain.reset();
    drain.emplace(++lifetime);
}

bool HasCompetingRows(const void* quests)
{
    const auto* events=NativeField<const void*>(quests,0xE8);
    if (!events)
        return true;
    const auto count=NativeField<std::uint32_t>(events,0x14);
    const auto* rows=NativeField<const ptfr::RegistrationRow*>(events,8);
    if (!rows || !count || count>1000000)
        return true;
    constexpr std::array<std::uint16_t,8> setupPath{0,2,82,4,9,3,98,370};
    constexpr std::array<std::uint16_t,7> parentPath{0,2,82,4,9,3,98};
    constexpr std::array<std::uint16_t,4> s29ResolutionPath{1,141,64000,103};
    const auto setup=ptfr::PhaseHash(setupPath);
    const auto parent=ptfr::PhaseHash(parentPath);
    const auto fresh=ptfr::PhaseHash(s29ResolutionPath);
    return std::ranges::any_of(std::span(rows,count),[=](const auto& row){
        return row.type && (row.phaseHash==OriginalPhase || row.phaseHash==ReplyPhase ||
                            row.phaseHash==setup || row.phaseHash==parent || row.phaseHash==fresh);
    });
}

bool AlreadyQueued(const void* quests, std::uint32_t slot)
{
    auto* lock=const_cast<std::uint8_t*>(static_cast<const std::uint8_t*>(quests)+0x150);
    MethodAt<ptfr::QuestSlotMethods::Lock>(0x22CA300)(lock);
    const auto* slots=NativeField<const std::uint32_t*>(quests,0x158);
    const auto count=NativeField<std::uint32_t>(quests,0x164);
    const auto capacity=NativeField<std::uint32_t>(quests,0x160);
    const bool pending=count>capacity || (count && !slots) ||
        (count && std::find(slots,slots+count,slot)!=slots+count);
    std::atomic_ref(*lock).store(0,std::memory_order_release);
    return pending;
}

std::int32_t GetFact(const void* quests, const char* name)
{
    const auto* facts = NativeField<const void*>(quests,0xF8);
    return facts && NativeField<const void*>(facts,0) == image + FactsManager ?
        MethodAt<ReadFact>(0x2B2270)(facts,1,FactId(name)) : -1;
}

bool IsCutoff(const void* quests, std::int32_t ticket)
{
    return ticket>0 && GetFact(quests,"PTFRHS3_GateTicket")==ticket &&
        GetFact(quests,"PTFRHS3_GateOpen")==1 && GetFact(quests,"PTFRHS3_GateResult")==0 &&
        GetFact(quests,"PTFRHS3_GateRoute")==1 && GetFact(quests,"q307_point_of_no_return")>0 &&
        GetFact(quests,"q115_point_of_no_return")==0 && GetFact(quests,"q307_2079")==0 &&
        GetFact(quests,"q307_debug_reset")==0 && GetFact(quests,"q307_main_game_killed")==0 &&
        GetFact(quests,"q307_ep1_killed")==0 && GetFact(quests,"q307_done")==0 &&
        GetFact(quests,"q307_finished")==0;
}

bool IsContinuation(const void* quests, std::int32_t ticket)
{
    return ticket>0 && GetFact(quests,"PTFRHS3_GateTicket")==ticket &&
        GetFact(quests,"PTFRHS3_GateOpen")==0 && GetFact(quests,"PTFRHS3_GateResult")==1 &&
        GetFact(quests,"PTFRHS3_GateRoute")==1 && GetFact(quests,"q307_done")==1 &&
        GetFact(quests,"q307_finished")==1 && GetFact(quests,"q307_2079")==1 &&
        GetFact(quests,"q307_debug_reset")==0 && GetFact(quests,"q307_main_game_killed")==1 &&
        GetFact(quests,"q307_ep1_killed")==1 && GetFact(quests,"PostTowerFreeRoamActive")==1 &&
        GetFact(quests,"PTFRPA2_Finished")==1 && GetFact(quests,"PTFRPA2_Fault")==0 &&
        GetFact(quests,"mq058_done")==1 && GetFact(quests,"mq058_active")==0 &&
        GetFact(quests,"PTFRS29_mq058_semimaru_crystalcoat_Issued")==0;
}

std::uint32_t PhaseOf(const void* phase)
{
    if (!phase || NativeField<const void*>(phase,0)!=image+PhaseInstance)
        return 0;
    const auto checked = ptfr::CopyPhaseAddress(phase);
    if (!checked)
        return 0;
    const auto path = std::span(checked->words).first(checked->size);
    const auto hash = NativeField<std::uint32_t>(phase,0x80);
    if ((hash==OriginalPhase && std::ranges::equal(path,OriginalPath)) ||
        (hash==ReplyPhase && std::ranges::equal(path,ReplyPath)))
        return hash;
    return 0;
}

void RegisterHandler(void* context,std::uint32_t node,std::uint64_t type,const void* ref)
{
    const auto* state = context && NativeField<const void*>(context,0)==image+PhaseContext ?
                        NativeField<const void*>(context,0x220) : nullptr;
    using CurrentPhase = void* (*)(const void*);
    using FindHandler = void* (*)(const void*,std::uint32_t);
    const auto* phase = active && state ? MethodAt<CurrentPhase>(0x2B224C)(state) : nullptr;
    const auto hash = PhaseOf(phase);
    if (!hash)
    {
        registerOriginal(context,node,type,ref);
        return;
    }
    const auto index = std::ranges::find(OriginalNodes,node);
    if (index == OriginalNodes.end() || type!=OriginalTypes[static_cast<std::size_t>(index-OriginalNodes.begin())])
    {
        registerOriginal(context,node,type,ref);
        return;
    }
    const std::lock_guard lock(stateMutex);
    const auto* previous=initializingHandler;
    const bool previousReplacement=registeringReplacement;
    initializingHandler=ref ? NativeField<void*>(ref,0) : nullptr;
    registeringReplacement=hash==ReplyPhase && node==80 && type==TimerType;
    registerOriginal(context,node,type,ref);
    initializingHandler=previous;
    registeringReplacement=previousReplacement;
    const auto* events = NativeField<const void*>(state,0x10);
    auto* quests = NativeField<void*>(state,0x128);
    auto* handler = MethodAt<FindHandler>(0x2B1B64)(phase,node);
    if (!events || !quests || !handler || !ref || handler!=NativeField<void*>(ref,0) ||
        NativeField<const void*>(quests,0)!=image+QuestSystem)
        return;
    const auto slot = NativeField<std::uint32_t>(handler,0x28);
    if (!ptfr::MatchesRegistration(events,slot,hash,node,type))
        return;
    if (!questSystem)
        Reset(quests);
    if (questSystem!=quests)
        return;
    if (hash==OriginalPhase)
    {
        originalPhaseDetached=false;
        originalRegisteredInSession=true;
        ownerConfirmed=false;
        auto& watch=original[static_cast<std::size_t>(index-OriginalNodes.begin())];
        watch = {handler,slot,false};
        watchedSession=true;
        if (node==80 && type==TimerType && NativeField<const void*>(handler,0)==image+WaitHandler)
        {
            timeSystem=NativeField<void*>(context,0xE8);
            timerId=NativeField<std::uint32_t>(handler,0x40);
            Log("original-timer",timerId);
        }
    }
    else if (node==80)
    {
        replacementSystem=NativeField<void*>(context,0xE8);
        replacementHandler=handler;
        watchedSession=true;
        replacementTimerId=NativeField<std::uint32_t>(handler,0x40);
        replacementRegistered=true;
        if (schedulerAccepted || NativeField<std::uint8_t>(state,1)==2) {
            Log(NativeField<std::uint8_t>(state,1)==2 ? "timer-handler-reloaded" : "replacement-timer-registered",
                replacementTimerId);
        } else {
            Log("replacement-timer-registration-unconfirmed",replacementTimerId);
        }
    }
}

using Notify = void (*)(void*,std::uint32_t);
Notify notifyOriginal;
void EnqueueNotification(void* quests,std::uint32_t slot)
{
    if (!active || !watchedSession || quests!=watchedQuestSystem.load()) {
        notifyOriginal(quests,slot);
        return;
    }
    const std::lock_guard lock(stateMutex);
    if (quests==questSystem) {
        const bool reserved=std::ranges::any_of(reservedIndices,
            [slot](const auto& index){return index && *index==slot;});
        const auto watched=std::ranges::find_if(original,[slot](auto row){return row.handler && row.slot==slot;});
        if (reserved || (watched!=original.end() && handoff.Held())) {
            captureInvalid=true;
            ownerConfirmed=false;
            Log(reserved?"late-original-notification":"original-became-ready-during-cut",slot);
            return;
        }
        if (watched!=original.end())
            handoff.Invalidate();
    }
    // Hold the capture lock until the native queue insertion is visible.
    notifyOriginal(quests,slot);
}

ptfr::QuestSlotMethods SlotMethods()
{
    return {retireOriginal,MethodAt<ptfr::QuestSlotMethods::Lock>(0x22CA300),
            MethodAt<ptfr::QuestSlotMethods::Append>(0x1E07BC)};
}

void RetireSlot(void* events,std::uint32_t slot)
{
    const auto row = ptfr::CopyRegistration(events,slot);
    if (!active || !row || (row->phaseHash!=OriginalPhase && row->phaseHash!=ReplyPhase))
    {
        retireOriginal(events,slot);
        return;
    }
    const std::lock_guard lock(stateMutex);
    if (row->phaseHash==ReplyPhase) {
        if (row->node==80 && questSystem && NativeField<const void*>(questSystem,0xE8)==events) {
            replacementSystem=nullptr;
            replacementHandler=nullptr;
        }
        retireOriginal(events,slot);
        return;
    }
    const auto index=std::ranges::find(OriginalNodes,row->node);
    if (index==OriginalNodes.end() || !questSystem || !drain ||
        NativeField<const void*>(questSystem,0xE8)!=events)
    {
        retireOriginal(events,slot);
        return;
    }
    const auto position=static_cast<std::size_t>(index-OriginalNodes.begin());
    // Registration removal precedes Uninitialize. Keep the cleared index
    // reserved until the owner and game-clock checks can run after dispatch.
    const bool tracked=original[position].handler && original[position].slot==slot;
    if (tracked && handoff.Held()) {
        const auto prior=reservations[position].has_value();
        if (!prior) {
            auto reservation=ptfr::RetiredQuestSlot::Retire(SlotMethods(),events,slot,*drain);
            if (reservation) {
                reservations[position].emplace(std::move(*reservation));
                reservedIndices[position]=slot;
            } else
                captureInvalid=true;
        } else {
            retireOriginal(events,slot);
        }
    } else {
        retireOriginal(events,slot);
    }
    if (tracked)
        original[position].closing=true;
    handoff.Invalidate();
    Log("original-slot-retired",row->node);
}

void StopOriginalHandler(void* phase,std::uint32_t node,void* context)
{
    const bool watched=active && PhaseOf(phase)==OriginalPhase;
    stopOriginal(phase,node,context);
    if (!watched)
        return;
    const auto index=std::ranges::find(OriginalNodes,node);
    if (index==OriginalNodes.end())
        return;
    const std::lock_guard lock(stateMutex);
    const auto position=static_cast<std::size_t>(index-OriginalNodes.begin());
    auto& row=original[position];
    if (row.closing) {
        row={};
    }
}

void EraseQuestChild(void* parent,void* context,const void* child,std::uint8_t permanent)
{
    const auto* phase=child ? NativeField<const void*>(child,0) : nullptr;
    const bool watched=active && PhaseOf(phase)==OriginalPhase && ptfr::HasChild(parent,phase)==true;
    eraseChildOriginal(parent,context,child,permanent);
    if (!watched || ptfr::HasChild(parent,phase)!=false)
        return;
    const std::lock_guard lock(stateMutex);
    originalPhaseDetached=true;
    Log("original-phase-detached");
}

void DrainNotifications(void* quests)
{
    if (!active || quests!=watchedQuestSystem.load()) {
        drainOriginal(quests);
        return;
    }
    {
        const std::lock_guard lock(stateMutex);
        if (active && quests==questSystem)
            dispatchingNotifications=true;
    }
    drainOriginal(quests);
    if (!active)
        return;
    const std::lock_guard lock(stateMutex);
    if (quests!=questSystem || !drain)
        return;
    dispatchingNotifications=false;
    drain->CompletePass();
    // Native Uninitialize must finish before slot reuse. The game-clock
    // worker also confirms its callback is gone before we proceed.
    if (std::ranges::any_of(original,[](auto row){return row.handler!=nullptr;}) ||
        (timeSystem && timerId))
        return;
    if (!requested && !std::ranges::any_of(reservations,[](const auto& item){return item.has_value();}))
        return;
    auto* graphLock=static_cast<std::uint8_t*>(quests)+0x60;
    std::uint8_t unlocked=0;
    if (!std::atomic_ref(*graphLock).compare_exchange_strong(unlocked,0xFF,std::memory_order_acquire))
        return;
    for (std::size_t index=0;index<reservations.size();++index) {
        auto& slot=reservations[index];
        if (slot && slot->Settle(SlotMethods(),quests,*drain,true)==ptfr::RetiredSlotStatus::Released) {
            slot.reset();
            reservedIndices[index].reset();
        }
    }
    const bool competing=HasCompetingRows(quests);
    std::atomic_ref(*graphLock).store(0,std::memory_order_release);
    if (requested && !ownerConfirmed && !replacementRegistered && !competing && !captureInvalid &&
        (!originalRegisteredInSession || originalPhaseDetached) &&
        !std::ranges::any_of(reservations,[](const auto& item){return item.has_value();}) &&
        IsContinuation(quests,requested->ticket)) {
        ownerConfirmed=handoff.Prepare(*requested,true);
        if (ownerConfirmed)
            Log("original-owner-absent",static_cast<unsigned>(requested->ticket));
    }
}

void TickTime(void* system,float seconds,const void* time)
{
    tickOriginal(system,seconds,time);
    if (!active || !watchedSession)
        return;
    const std::lock_guard lock(stateMutex);
    if (!questSystem || NativeField<const void*>(system,0)!=image+TimeSystem)
        return;
    if (system==replacementSystem && replacementHandler && replacementTimerId && !replacementClockLogged) {
        std::uint32_t now{};
        MethodAt<ReadClock>(0x468358)(system,&now);
        const auto row=ptfr::FindGameTimer(system,replacementTimerId);
        const auto authored=row && row->timer ? NativeField<std::uint32_t>(row->timer,0x90) : 0;
        const auto timer=authored && authored<=ptfr::ClaireReplySeconds &&
            (!replacementAuthoredSeconds || authored==replacementAuthoredSeconds) ?
            ptfr::ReadOneShotGameWait(system,replacementTimerId,now,authored,
                image+TimerRecord,image+InitialCallback,image+LoadedCallback,replacementHandler) :
            std::nullopt;
        if (timer) {
            replacementClockLogged=true;
            observedReplySeconds=timer->wait.seconds;
            observedAuthoredSeconds=authored;
            Log("native-remaining-game-seconds",timer->wait.seconds);
        }
    }
    if (system!=timeSystem)
        return;
    if (timerId && std::ranges::none_of(original,[](auto row){return row.handler!=nullptr;})) {
        const auto old=ptfr::FindGameTimer(system,timerId);
        if (old && !old->timer) {
            timerId=0;
            originalTimer=nullptr;
            savedTimerIdentity.store(nullptr);
            Log("old-native-timer-absent");
        }
        return;
    }
    const auto ticket=GetFact(questSystem,"PTFRHS3_GateTicket");
    if (handoff.Held() && GetFact(questSystem,"PTFRHS3_GateOpen")==0 &&
        GetFact(questSystem,"PTFRHS3_GateResult")==0) {
        handoff.Abort();
        captureInvalid=true;
        Log("cutoff-closed-without-ack");
    }
    if (handoff.Held() || captureInvalid || !IsCutoff(questSystem,ticket) ||
        !std::ranges::all_of(original,[](auto row){return row.handler && !row.closing;}))
        return;
    std::uint32_t now{};
    MethodAt<ReadClock>(0x468358)(system,&now);
    const auto timer=ptfr::ReadOneShotGameWait(system,timerId,now,ptfr::ClaireReplySeconds,
                    image+TimerRecord,image+InitialCallback,image+LoadedCallback,original[0].handler);
    if (timer && !ptfr::HandlerReady(original[0].handler)) {
        originalTimer=timer->reference.timer;
        savedTimerIdentity.store(originalTimer);
        handoff.Observe({ticket,timer->wait.seconds});
    } else {
        originalTimer=nullptr;
        savedTimerIdentity.store(nullptr);
        handoff.Invalidate();
    }
}

std::uint8_t DispatchGameTimer(void* timer,std::uint32_t clock)
{
    if (active && savedTimerIdentity.load()==timer) {
        const std::lock_guard lock(stateMutex);
        if (timer==originalTimer && originalTimer &&
            NativeField<const void*>(timer,0)==image+TimerRecord &&
            NativeField<std::uint32_t>(timer,0x88)==timerId) {
            if (handoff.Held())
                return 0;
            // Invalidate while serialized with CommitWait. Do not publish an
            // earlier sample across a native callback already about to run.
            const auto deadline=NativeField<std::uint32_t>(timer,0x40);
            if (clock>=deadline)
                handoff.Invalidate();
        }
    }
    return timerTickOriginal(timer,clock);
}

void LoadQuests(void* quests,void* context,void* status,void* reader)
{
    Reset(quests);
    loadOriginal(quests,context,status,reader);
}

void TearDown(void* quests,void* context)
{
    Reset(nullptr);
    teardownOriginal(quests,context);
}

void ReadWait(RED4ext::IScriptable*,RED4ext::CStackFrame* frame,std::int32_t* out,std::int64_t)
{
    RED4ext::Handle<RED4ext::quest::QuestsSystem> quests;
    std::int32_t ticket{};
    RED4ext::GetParameter(frame,&quests);
    RED4ext::GetParameter(frame,&ticket);
    ++frame->code;
    if (!out)
        return;
    const std::lock_guard lock(stateMutex);
    *out=active && quests && quests.GetPtr()==questSystem && IsCutoff(questSystem,ticket) ?
        static_cast<std::int32_t>(handoff.Read(ticket)) : 0;
}

bool Eligible(const void* quests,std::int32_t ticket,std::int32_t seconds)
{
    return active && quests && NativeField<const void*>(quests,0)==image+QuestSystem && ticket>0 &&
           seconds>0 && seconds<=static_cast<std::int32_t>(ptfr::ClaireReplySeconds);
}

void CommitWait(RED4ext::IScriptable*,RED4ext::CStackFrame* frame,bool* out,std::int64_t)
{
    RED4ext::Handle<RED4ext::quest::QuestsSystem> quests;
    std::int32_t ticket{},seconds{};
    RED4ext::GetParameter(frame,&quests);
    RED4ext::GetParameter(frame,&ticket);
    RED4ext::GetParameter(frame,&seconds);
    ++frame->code;
    if (!out)
        return;
    const std::lock_guard lock(stateMutex);
    *out=Eligible(quests.GetPtr(),ticket,seconds) && quests.GetPtr()==questSystem &&
        IsCutoff(questSystem,ticket) && originalTimer && !dispatchingNotifications &&
        std::ranges::all_of(original,[](auto row){
            return row.handler && !row.closing && !ptfr::HandlerReady(row.handler) &&
                !AlreadyQueued(questSystem,row.slot);
        }) && handoff.Commit({ticket,static_cast<std::uint32_t>(seconds)});
}

void PrepareOwner(RED4ext::IScriptable*,RED4ext::CStackFrame* frame,bool* out,std::int64_t)
{
    RED4ext::Handle<RED4ext::quest::QuestsSystem> quests;
    std::int32_t ticket{},seconds{};
    RED4ext::GetParameter(frame,&quests);
    RED4ext::GetParameter(frame,&ticket);
    RED4ext::GetParameter(frame,&seconds);
    ++frame->code;
    if (!out)
        return;
    *out=false;
    const std::lock_guard lock(stateMutex);
    if (!Eligible(quests.GetPtr(),ticket,seconds) || !IsContinuation(quests.GetPtr(),ticket))
        return;
    // Run the physical owner check on the quest dispatch worker. The script
    // poll supplies the save-local request, then consumes its proof.
    if (!questSystem)
        Reset(quests.GetPtr());
    if (quests.GetPtr()!=questSystem || captureInvalid)
        return;
    if (GetFact(questSystem,"PTFRClaire_Issued")==1) {
        *out=replacementRegistered && replacementHandler && observedReplySeconds>0 &&
            observedAuthoredSeconds==static_cast<std::uint32_t>(seconds);
        return;
    }
    watchedSession=true;
    const ptfr::ReplyDuration duration{ticket,static_cast<std::uint32_t>(seconds)};
    if (!requested || requested->ticket!=ticket || requested->seconds!=duration.seconds) {
        requested=duration;
        ownerConfirmed=false;
    }
    *out=ownerConfirmed && handoff.ScheduledDuration(ticket)==duration.seconds;
}

std::uint32_t ScheduleTimer(void* system,void* callback,std::uint32_t seconds,std::int32_t repetitions,
                            std::uint8_t flag,std::uint32_t mode,std::uint64_t tag,std::uint64_t payload)
{
    if (active && registeringReplacement && initializingHandler && callback &&
        NativeField<const void*>(callback,0)==image+InitialCallback &&
        NativeField<const void*>(callback,8)==initializingHandler &&
        seconds==ptfr::ClaireReplySeconds && repetitions==1 && mode==0 && questSystem && ownerConfirmed) {
        const auto ticket=GetFact(questSystem,"PTFRHS3_GateTicket");
        const auto restored=handoff.ScheduledDuration(ticket);
        if (restored && IsContinuation(questSystem,ticket)) {
            replacementDuration=restored;
            schedulerAccepted=false;
            const auto result=scheduleOriginal(system,callback,restored,repetitions,flag,mode,tag,payload);
            replacementDuration.reset();
            if (schedulerAccepted) {
                handoff.MarkScheduled();
                replacementAuthoredSeconds=restored;
                Log("remaining-game-seconds",restored);
            }
            return result;
        }
    }
    return scheduleOriginal(system,callback,seconds,repetitions,flag,mode,tag,payload);
}

bool Enqueue(void* queue,const ptfr::NativeGameTimerReference* timer)
{
    const bool accepted=enqueueTimerOriginal(queue,timer);
    if (replacementDuration && registeringReplacement)
        schedulerAccepted=accepted;
    return accepted;
}

template<class Call>
void RegisterFunction(std::size_t index,const char* name,Call call,const char* type,bool withSeconds)
{
    auto* fn=RED4ext::CGlobalFunction::Create(name,name,call);
    if (!fn)
        return;
    fn->flags.isNative=true;
    fn->flags.isStatic=true;
    fn->AddParam("handle:questQuestsSystem","quests");
    fn->AddParam("Int32","ticket");
    if (withSeconds)
        fn->AddParam("Int32","seconds");
    fn->SetReturnType(type);
    RED4ext::CRTTISystem::Get()->RegisterFunction(fn);
    functions[index]=fn;
}

void RegisterFunctions()
{
    RegisterFunction(0,"PTFR.HistorySnapshotHS1.ReadClaireReplyWait",&ReadWait,"Int32",false);
    RegisterFunction(1,"PTFR.HistorySnapshotHS1.CommitClaireReplyWait",&CommitWait,"Bool",true);
    RegisterFunction(2,"PTFR.HistorySnapshotHS1.PrepareClaireReplyOwner",&PrepareOwner,"Bool",true);
}

bool VerifyExecutable()
{
    constexpr std::uint8_t expected[] = {0xD3,0x6E,0x74,0xC4,0x75,0x92,0xE9,0xC6,
        0x56,0xAE,0x25,0x00,0x78,0xCB,0x40,0xB2,0xBE,0x63,0xC7,0x82,0xAF,0x5B,0xFB,0xEF,
        0xF2,0x28,0x0D,0x43,0xE6,0x53,0xFA,0xB4};
    wchar_t path[MAX_PATH];
    const auto length = GetModuleFileNameW(nullptr,path,MAX_PATH);
    if (!length || length>=MAX_PATH)
        return false;
    const auto file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ | FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,0,nullptr);
    if (file==INVALID_HANDLE_VALUE)
        return false;
    BCRYPT_ALG_HANDLE algorithm=nullptr;
    BCRYPT_HASH_HANDLE hash=nullptr;
    std::uint8_t digest[32];
    bool ok=BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0 &&
            BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)>=0;
    std::uint8_t bytes[16384];
    while (ok)
    {
        DWORD count=0;
        ok=ReadFile(file,bytes,sizeof(bytes),&count,nullptr)!=FALSE;
        if (!ok || !count)
            break;
        ok=BCryptHashData(hash,bytes,count,0)>=0;
    }
    ok=ok && BCryptFinishHash(hash,digest,sizeof(digest),0)>=0 &&
       std::memcmp(digest,expected,sizeof(expected))==0;
    if (hash)
        BCryptDestroyHash(hash);
    if (algorithm)
        BCryptCloseAlgorithmProvider(algorithm,0);
    CloseHandle(file);
    return ok;
}

struct Hook { std::uintptr_t rva; const char* prefix; void* detour; void** original; };
template<class Call>
Hook MakeHook(std::uintptr_t rva,const char* prefix,Call detour,Call& original)
{
    return {rva,prefix,reinterpret_cast<void*>(detour),reinterpret_cast<void**>(&original)};
}
const Hook Hooks[] = {
    MakeHook(0x2B0800,"\x48\x89\x5C\x24\x18\x48\x89\x6C",&RegisterHandler,registerOriginal),
    MakeHook(0x88BC58,"\x89\x54\x24\x10\x53\x48\x83\xEC",&EnqueueNotification,notifyOriginal),
    MakeHook(0x2FCFD0,"\x89\x54\x24\x10\x53\x48\x83\xEC",&RetireSlot,retireOriginal),
    MakeHook(0x2FCF0C,"\x89\x54\x24\x10\x55\x53\x56\x57",&StopOriginalHandler,stopOriginal),
    MakeHook(0xBEC890,"\x48\x89\x5C\x24\x08\x57\x48\x83",&EraseQuestChild,eraseChildOriginal),
    MakeHook(0x3534DC,"\x48\x89\x5C\x24\x18\x55\x56\x57",&DrainNotifications,drainOriginal),
    MakeHook(0x7C0CA0,"\x48\x8B\xC4\x55\x53\x56\x57\x41",&TickTime,tickOriginal),
    MakeHook(0xA09BC4,"\x44\x89\x4C\x24\x20\x44\x89\x44",&ScheduleTimer,scheduleOriginal),
    MakeHook(0x2179B80,"\x48\x83\xEC\x28\x44\x8B\x09\x4C",&Enqueue,enqueueTimerOriginal),
    MakeHook(0x193B00,"\x48\x89\x5C\x24\x08\x57\x48\x83",&DispatchGameTimer,timerTickOriginal),
    MakeHook(0x739578,"\x48\x8B\xC4\x48\x89\x58\x08\x48",&LoadQuests,loadOriginal),
    MakeHook(0x35EAEC,"\x40\x53\x56\x57\x48\x83\xEC\x40",&TearDown,teardownOriginal),
};
std::size_t installedHooks{};
std::size_t attachedMask{};

bool Detach()
{
    active=false;
    bool ok=true;
    for (auto index=installedHooks;index>0;--index)
    {
        const auto bit=std::size_t{1}<<(index-1);
        if (!(attachedMask&bit))
            continue;
        if (sdk->hooking->Detach(plugin,const_cast<std::uint8_t*>(image+Hooks[index-1].rva)))
            attachedMask &= ~bit;
        else
            ok=false;
    }
    return ok;
}
} // namespace

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle handle,RED4ext::v1::EMainReason reason,
                                      const RED4ext::v1::Sdk* api)
{
    if (reason==RED4ext::v1::EMainReason::Unload)
    {
        if (auto* rtti=RED4ext::CRTTISystem::Get())
        {
            for (auto* function : functions)
                if (function)
                    rtti->UnregisterFunction(function);
        }
        return Detach();
    }
    if (reason!=RED4ext::v1::EMainReason::Load || !api || !api->hooking || !api->logger)
        return false;
    sdk=api;
    plugin=handle;
    image=reinterpret_cast<const std::uint8_t*>(GetModuleHandleW(nullptr));
    auto* rtti=RED4ext::CRTTISystem::Get();
    if (!image || !rtti || !VerifyExecutable())
        return false;
    for (const auto& hook : Hooks)
        if (std::memcmp(image+hook.rva,hook.prefix,8)!=0)
            return false;
    for (const auto& hook : Hooks)
    {
        if (!sdk->hooking->Attach(plugin,const_cast<std::uint8_t*>(image+hook.rva),hook.detour,hook.original))
            return !Detach();
        attachedMask|=std::size_t{1}<<installedHooks++;
    }
    rtti->AddPostRegisterCallback(&RegisterFunctions);
    active=true;
    Log("probe-loaded");
    return true;
}

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* info)
{
    info->name=L"PTFR Claire Reply Handoff";
    info->author=L"Post Tower Continuation";
    info->version=RED4EXT_V1_SEMVER(0,1,0);
    info->runtime=RED4EXT_V1_RUNTIME_VERSION_2_50;
    info->sdk=RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT std::uint32_t RED4EXT_CALL Supports() { return RED4EXT_API_VERSION_1; }
