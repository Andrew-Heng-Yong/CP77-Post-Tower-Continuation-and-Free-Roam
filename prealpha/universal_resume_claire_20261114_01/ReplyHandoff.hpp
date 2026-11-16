#pragma once
#include <cstdint>
#include <optional>

namespace ptfr
{
constexpr std::uint32_t ClaireReplySeconds = 172800;

struct ReplyDuration
{
    std::int32_t ticket;
    std::uint32_t seconds;

    bool operator==(const ReplyDuration&) const = default;
};

class ReplyHandoff
{
public:
    void Observe(ReplyDuration observed)
    {
        if (!committed && Valid(observed))
            duration = observed;
    }

    std::uint32_t Read(std::int32_t ticket) const
    {
        return duration && duration->ticket == ticket ? duration->seconds : 0;
    }

    bool Commit(ReplyDuration capture)
    {
        if (!Valid(capture) || Read(capture.ticket) != capture.seconds)
            return false;
        committed = true;
        return true;
    }

    void Invalidate() { if (!committed) duration.reset(); }
    bool Held() const { return committed; }
    void Abort()
    {
        committed = false;
        duration.reset();
        prepared.reset();
    }

    bool Prepare(ReplyDuration saved, bool exclusiveOwner)
    {
        if (!Valid(saved) || !exclusiveOwner || scheduled ||
            (committed && Read(saved.ticket) != saved.seconds))
            return false;
        prepared = saved;
        return true;
    }

    std::uint32_t ScheduledDuration(std::int32_t ticket) const
    {
        return prepared && prepared->ticket == ticket && !scheduled ? prepared->seconds : 0;
    }

    void MarkScheduled() { scheduled = true; }

private:
    static bool Valid(ReplyDuration value)
    {
        return value.ticket > 0 && value.seconds > 0 && value.seconds <= ClaireReplySeconds;
    }

    std::optional<ReplyDuration> duration;
    std::optional<ReplyDuration> prepared;
    bool committed = false;
    bool scheduled = false;
};
} // namespace ptfr
