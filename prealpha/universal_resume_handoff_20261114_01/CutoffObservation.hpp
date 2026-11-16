#pragma once

#include <cmath>
#include <cstdint>
#include <optional>

#include "../universal_resume_boundary_20261114_01/TimerRecord.hpp"

namespace ptfr
{
struct LiveWait
{
    const void* handler;
    void* delay;
    const void* facts;
    std::uint64_t timer;

    bool operator==(const LiveWait&) const = default;
};

struct GateTicket
{
    const void* facts;
    std::int32_t route;
    std::int32_t ticket;

    bool operator==(const GateTicket&) const = default;
};

struct CaptureRequest
{
    GateTicket gate;
    LiveWait wait;
    std::uint64_t revision;
};

struct GateOutcome
{
    GateTicket gate;
    bool sampled;
};

// Callers serialize this state. The returned request may cross a native call,
// where the gate, handler and scheduler may have changed in the meantime.
class CutoffObservation
{
public:
    std::uint64_t BeginWatch(const void* handler)
    {
        pending.reset();
        initializing = handler;
        ++revision;
        return ++watchWrite;
    }

    bool Watch(LiveWait wait, std::uint64_t write)
    {
        if (write != watchWrite || wait.handler != initializing)
            return false;
        initializing = nullptr;
        pending = wait;
        ++revision;
        return true;
    }

    void Invalidate(const void* handler)
    {
        if (initializing == handler)
        {
            initializing = nullptr;
            ++watchWrite;
        }
        if (pending && pending->handler == handler)
        {
            pending.reset();
            ++revision;
        }
    }

    std::uint64_t BeginGateWrite(const void* facts, std::optional<GateOutcome>& previous)
    {
        previous.reset();
        if (gate && gate->facts == facts)
        {
            previous = GateOutcome{*gate, sampled};
            gate.reset();
        }
        ++revision;
        return ++gateWrite;
    }

    bool Open(GateTicket ticket, std::uint64_t write)
    {
        if (write != gateWrite || !ticket.facts || (ticket.route != 1 && ticket.route != 2) ||
            ticket.ticket <= 0 || lastGate == ticket)
            return false;
        gate = ticket;
        lastGate = ticket;
        sampled = false;
        ++revision;
        return true;
    }

    void Reset()
    {
        pending.reset();
        gate.reset();
        lastGate.reset();
        initializing = nullptr;
        ++revision;
        ++gateWrite;
        ++watchWrite;
    }

    std::optional<CaptureRequest> Request(const void* delay) const
    {
        if (!gate || !pending || sampled || pending->delay != delay || pending->facts != gate->facts ||
            !SchedulerId::FromNative(pending->timer).IsQuestDelay())
            return std::nullopt;
        return CaptureRequest{*gate, *pending, revision};
    }

    bool Accept(const CaptureRequest& request, float remainingSeconds, float frameSeconds)
    {
        if (request.revision != revision || gate != request.gate || pending != request.wait || sampled ||
            !std::isfinite(remainingSeconds) || !std::isfinite(frameSeconds) || frameSeconds < 0 ||
            remainingSeconds <= frameSeconds)
            return false;
        sampled = true;
        return true;
    }

    bool IsCurrentSample(const CaptureRequest& request) const
    {
        return sampled && request.revision == revision && gate == request.gate && pending == request.wait;
    }

private:
    std::optional<LiveWait> pending;
    const void* initializing = nullptr;
    std::optional<GateTicket> gate;
    std::optional<GateTicket> lastGate;
    std::uint64_t revision = 0;
    std::uint64_t gateWrite = 0;
    std::uint64_t watchWrite = 0;
    bool sampled = false;
};
} // namespace ptfr
