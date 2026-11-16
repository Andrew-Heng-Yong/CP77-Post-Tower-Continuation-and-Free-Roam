#pragma once

#include <algorithm>
#include <array>
#include <charconv>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace ptfr::resume
{
constexpr auto BaseQuest = 0xCA034981517A576BULL;
constexpr auto ExpansionQuest = 0xC4C842994BA818E1ULL;
constexpr std::uint16_t OpenGateNode = 60003;
constexpr std::uint16_t CloseGateNode = 60005;
constexpr std::size_t MaxDepth = 32;
constexpr std::size_t MaxPhases = 16384;
constexpr std::size_t MaxSlots = 65536;
constexpr std::size_t MaxQueue = 8192;
constexpr std::size_t MaxFacts = 65536;
constexpr std::size_t MaxTimers = 128;
constexpr std::size_t MaxBytes = 2 * 1024 * 1024;
constexpr auto ArchiveSHA = "443339C64009C5DB99B1E0FD77B1EF526143C40DADDBEBB05EBEC6BB5D76BB45";
constexpr auto CatalogueSHA = "C518094308849C32611EB2C471A047C548BEC668C30F873B0CCFED00DD5B08DD";

constexpr std::uint64_t Depot(std::string_view path)
{
    std::uint64_t hash = 0xCBF29CE484222325ULL;
    for (const char letter : path)
        hash = (hash ^ static_cast<std::uint8_t>(letter)) * 0x100000001B3ULL;
    return hash;
}

constexpr std::uint32_t FactId(std::string_view name)
{
    std::uint32_t hash = 0x811C9DC5;
    for (const char letter : name)
        hash = (hash ^ static_cast<std::uint8_t>(letter)) * 0x01000193;
    return hash;
}

constexpr std::uint32_t PhaseHash(std::span<const std::uint16_t> path)
{
    std::uint32_t hash = path.empty() || path.front() == 0 ? 0x811C9DC5 : 0x01800013;
    for (const auto word : path)
    {
        hash = (hash ^ (word & 0xFF)) * 0x01000193;
        hash = (hash ^ (word >> 8)) * 0x01000193;
    }
    return hash;
}

constexpr int GateRoute(std::uint64_t depot, std::span<const std::uint16_t> path)
{
    constexpr auto reed = Depot(R"(ep1\quest\main_quests\q307\phases\q307_01_pickup.questphase)");
    constexpr auto hanako = Depot(R"(base\quest\main_quests\part1\q115\phases\q115_00_hanako.questphase)");
    if (depot == reed && path.size() >= 2 && path.front() == 1 && path.back() == 10)
        return 1;
    if (depot == hanako && path.size() >= 3 && path.front() == 0 &&
        path[path.size() - 2] == 3 && path.back() == 113)
        return 2;
    return 0;
}

struct Boundary
{
    const void* quests{};
    const void* facts{};
    std::int32_t ticket{};
    std::int32_t route{};

    bool operator==(const Boundary&) const = default;
};

// The plugin serializes access. An epoch covers the entire native lifecycle
// call, including nested initialization. No capture is admitted mid-transition.
class Gate
{
public:
    void BeginTransition()
    {
        ++transitions;
        Clear();
    }
    void EndTransition() { --transitions; }
    void Clear()
    {
        current = {};
        ++epoch;
    }
    void Open(Boundary key)
    {
        if (transitions == 0 && key.quests && key.facts && key.ticket > 0 && (key.route == 1 || key.route == 2))
            current = key;
    }
    bool Matches(Boundary key) const { return transitions == 0 && current.quests && current == key; }
    std::uint64_t Epoch() const { return epoch; }
    bool Transitioning() const { return transitions != 0; }

private:
    Boundary current;
    std::uint64_t epoch{};
    std::size_t transitions{};
};

struct Phase
{
    std::array<std::uint16_t, MaxDepth> path{};
    std::size_t size{};
    std::uint32_t hash{};
    std::uint64_t depot{};
    std::uint32_t handlers{};

    auto Path() const { return std::span<const std::uint16_t>{path}.first(size); }
};

struct Registration
{
    std::uint64_t type;
    std::uint32_t phase;
    std::uint32_t node;

    bool operator==(const Registration&) const = default;
    bool Empty() const { return *this == Registration{0, 0, 0xFFFF}; }
    bool Valid() const { return type && phase && node < 0xFFFF; }
};
static_assert(sizeof(Registration) == 16);

enum class Binding : std::uint8_t { Unresolved, Live, Ambiguous };
struct Handler
{
    Registration registration;
    std::uint32_t slot;
    Binding binding;
};

struct Fact
{
    std::uint32_t key;
    std::int32_t value;
};

struct NodeInstance
{
    std::uint64_t key;
    std::uint64_t value;
};
static_assert(sizeof(NodeInstance) == 16);

enum class Clock : std::uint8_t { Real, Game };

// Opaque identities are used for comparison during capture and are never serialized.
struct Wait
{
    const void* handler;
    Registration registration;
    std::uint32_t slot;
    Clock clock;
    std::uint64_t timer;

    bool operator==(const Wait&) const = default;
};

struct Timing
{
    std::uint32_t slot;
    Clock clock;
    std::uint64_t serial;
    double remainingSeconds;
    std::uint32_t ageMilliseconds;
};

struct Presentation
{
    std::uint64_t player;
    std::uint32_t tier;
    bool sceneKnown;
    bool inScene;
    bool inDialogue;
    bool sceneCamera;
    bool phoneManagerKnown;
    bool phoneActive;
    bool phoneInfoKnown;
    std::uint64_t contact;
    std::uint8_t phase;
    std::uint8_t mode;
    std::uint8_t callFlags;
    std::uint8_t visuals;
    int talkingState;
};

inline std::optional<Presentation> ReadPresentation(std::span<const std::uint64_t> fields)
{
    if (fields.size() != 15 || fields[1] > 0x7FFFFFFF ||
        std::any_of(fields.begin() + 2, fields.begin() + 9, [](auto flag) { return flag > 1; }) ||
        fields[10] > 3 || fields[11] > 2 || fields[12] > 31 || fields[13] > 1 || fields[14] > 4)
        return std::nullopt;
    return Presentation{fields[0], static_cast<std::uint32_t>(fields[1]),
                        fields[2] != 0, fields[3] != 0, fields[4] != 0, fields[5] != 0,
                        fields[6] != 0, fields[7] != 0, fields[8] != 0, fields[9],
                        static_cast<std::uint8_t>(fields[10]), static_cast<std::uint8_t>(fields[11]),
                        static_cast<std::uint8_t>(fields[12]), static_cast<std::uint8_t>(fields[13]),
                        static_cast<int>(fields[14]) - 1};
}

struct State
{
    std::vector<std::uint64_t> roots;
    std::vector<Phase> phases;
    std::vector<Handler> handlers;
    std::vector<std::uint32_t> notifications;
    std::vector<std::uint64_t> resourceRequests;
    std::array<std::vector<Fact>, 3> facts;
    std::vector<NodeInstance> instances;
    std::vector<Timing> timings;
    std::optional<Presentation> presentation;
    std::size_t waitsObserved{};
};

// Duration readings come from their scheduler jobs, with their individual ages.
// Discard a stale, changed or queued owner instead of treating it as time zero.
inline bool UseTiming(const Wait& current, const Wait& observed, double remaining,
                      std::int64_t ageMs, std::span<const std::uint32_t> notifications)
{
    return current == observed && std::isfinite(remaining) && remaining > 0 &&
           ageMs >= 0 && ageMs <= 250 &&
           std::find(notifications.begin(), notifications.end(), current.slot) == notifications.end();
}

inline bool ValidId(std::string_view id)
{
    return id.size() == 32 && std::all_of(id.begin(), id.end(), [](char c) {
        return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
    });
}

inline std::size_t PackedWords(std::size_t bytes)
{
    return 1 + (bytes + sizeof(std::uint64_t) - 1) / sizeof(std::uint64_t);
}

inline bool Pack(std::string_view id, std::string_view json, std::span<std::uint64_t> words)
{
    const auto length = id.size() + json.size();
    if (!ValidId(id) || json.empty() || json.size() > MaxBytes || words.size() != PackedWords(length))
        return false;
    std::fill(words.begin(), words.end(), 0);
    words.front() = length;
    auto* data = reinterpret_cast<char*>(words.data() + 1);
    std::memcpy(data, id.data(), id.size());
    std::memcpy(data + id.size(), json.data(), json.size());
    return true;
}

inline std::string_view Unpack(std::span<const std::uint64_t> words)
{
    if (words.empty() || words.front() <= 32 || words.front() > MaxBytes + 32 ||
        PackedWords(words.front()) != words.size())
        return {};
    const auto data = reinterpret_cast<const char*>(words.data() + 1);
    const std::string_view value(data, words.front());
    if (!ValidId(value.substr(0, 32)) || value[32] != '{' || value.back() != '}' ||
        value.find('\0') != std::string_view::npos)
        return {};
    return value;
}

class Json
{
public:
    void Text(std::string_view text) { bytes.append(text); }
    void Bool(bool value) { Text(value ? "true" : "false"); }
    template<class T> void Number(T value)
    {
        char buf[64];
        const auto [end, error] = std::to_chars(buf, buf + sizeof(buf), value);
        if (error != std::errc{})
            throw std::length_error("checkpoint number");
        bytes.append(buf, end);
    }
    void Hex(std::uint64_t value)
    {
        constexpr char hex[] = "0123456789abcdef";
        char buf[16];
        for (int i = 15; i >= 0; --i)
        {
            buf[i] = hex[value & 15];
            value >>= 4;
        }
        Text("\"");
        Text(std::string_view{buf, sizeof(buf)});
        Text("\"");
    }
    template<class Collection, class Write> void Array(const Collection& entries, Write write)
    {
        Text("[");
        bool comma = false;
        for (const auto& entry : entries)
        {
            if (comma)
                Text(",");
            write(entry);
            comma = true;
        }
        Text("]");
    }
    std::string Finish()
    {
        if (bytes.size() > MaxBytes)
            return {};
        return std::move(bytes);
    }
private:
    std::string bytes;
};

inline std::string Encode(const State& state, std::string_view id, std::int32_t ticket,
                          std::int32_t route, std::int32_t historyRevision)
{
    if (!ValidId(id) || ticket <= 0 || (route != 1 && route != 2) || historyRevision <= 0)
        return {};
    Json json;
    json.Text("{\"schema\":1,\"origin\":\"pre_native_cleanup\",\"id\":\"");
    json.Text(id);
    json.Text("\",\"ticket\":"); json.Number(ticket);
    json.Text(",\"route\":"); json.Number(route);
    json.Text(",\"history_revision\":"); json.Number(historyRevision);
    json.Text(",\"history_catalogue\":\""); json.Text(CatalogueSHA);
    json.Text("\",\"archive_sha256\":\""); json.Text(ArchiveSHA);
    json.Text("\",\"coverage\":{\"actor_bindings\":\"unread\",\"phone_playhead\":\"unread\","
              "\"scene_position\":\"unread\",\"node_instance_data\":\"raw_native_save_values\","
              "\"timer_sampling\":\"scheduler_job_with_age\",\"timed_handlers\":");
    json.Number(state.waitsObserved);
    json.Text("},\"presentation\":");
    if (const auto& view = state.presentation)
    {
        json.Text("{\"player_entity\":"); json.Hex(view->player);
        json.Text(",\"scene_tier\":"); json.Number(view->tier);
        json.Text(",\"scene_observed\":"); json.Bool(view->sceneKnown);
        json.Text(",\"player_in_scene\":"); json.Bool(view->inScene);
        json.Text(",\"player_in_dialogue\":"); json.Bool(view->inDialogue);
        json.Text(",\"scene_camera_enabled\":"); json.Bool(view->sceneCamera);
        json.Text(",\"phone_manager_observed\":"); json.Bool(view->phoneManagerKnown);
        json.Text(",\"phone_manager_active\":"); json.Bool(view->phoneActive);
        json.Text(",\"phone_info_observed\":"); json.Bool(view->phoneInfoKnown);
        json.Text(",\"last_contact\":"); json.Hex(view->contact);
        json.Text(",\"call_phase\":"); json.Number(view->phase);
        json.Text(",\"call_mode\":"); json.Number(view->mode);
        json.Text(",\"audio_call\":"); json.Bool(view->callFlags & 1);
        json.Text(",\"player_calling\":"); json.Bool(view->callFlags & 2);
        json.Text(",\"player_triggered\":"); json.Bool(view->callFlags & 4);
        json.Text(",\"rejectable\":"); json.Bool(view->callFlags & 8);
        json.Text(",\"show_avatar\":"); json.Bool(view->callFlags & 16);
        json.Text(",\"call_visuals\":"); json.Number(view->visuals);
        json.Text(",\"phone_talking_fact\":"); json.Number(view->talkingState);
        json.Text("}");
    }
    else
        json.Text("null");
    json.Text(",\"roots\":");
    json.Array(state.roots, [&](auto root) { json.Hex(root); });
    json.Text(",\"phases\":");
    json.Array(state.phases, [&](const Phase& phase) {
        json.Text("["); json.Number(phase.hash);
        json.Text(","); json.Hex(phase.depot);
        json.Text(","); json.Number(phase.handlers);
        json.Text(","); json.Array(phase.Path(), [&](auto word) { json.Number(word); });
        json.Text("]");
    });
    json.Text(",\"handlers\":");
    json.Array(state.handlers, [&](const Handler& handler) {
        const auto& [type, phase, node] = handler.registration;
        json.Text("["); json.Number(handler.slot);
        json.Text(","); json.Hex(type);
        json.Text(","); json.Number(phase);
        json.Text(","); json.Number(node);
        json.Text(","); json.Number(static_cast<std::uint8_t>(handler.binding));
        json.Text("]");
    });
    json.Text(",\"notifications\":");
    json.Array(state.notifications, [&](auto slot) { json.Number(slot); });
    json.Text(",\"resource_requests\":");
    json.Array(state.resourceRequests, [&](auto key) { json.Hex(key); });
    json.Text(",\"graph_facts\":");
    json.Array(state.facts, [&](const auto& table) {
        json.Array(table, [&](const Fact& fact) {
            json.Text("["); json.Number(fact.key); json.Text(","); json.Number(fact.value); json.Text("]");
        });
    });
    json.Text(",\"node_instances\":");
    json.Array(state.instances, [&](const NodeInstance& entry) {
        json.Text("["); json.Hex(entry.key); json.Text(","); json.Hex(entry.value); json.Text("]");
    });
    json.Text(",\"timings\":");
    json.Array(state.timings, [&](const Timing& timer) {
        json.Text("["); json.Number(timer.slot);
        json.Text(","); json.Number(static_cast<std::uint8_t>(timer.clock));
        json.Text(","); json.Hex(timer.serial);
        json.Text(","); json.Number(timer.remainingSeconds);
        json.Text(","); json.Number(timer.ageMilliseconds);
        json.Text("]");
    });
    json.Text("}");
    return json.Finish();
}
} // namespace ptfr::resume
