// The stock serializer loop invokes these virtual writers synchronously.
// All wrappers return the original result and forward exactly once.
using SaveWriter = std::uintptr_t (*)(void*, void*);
SaveWriter saveSystemsOriginal{};
SaveWriter saveQuestsOriginal{};
SaveWriter saveRealClockOriginal{};
SaveWriter saveGameClockOriginal{};
SaveWindow saveWindow;

std::uintptr_t SaveSystems(void* job, void* request)
{
    if (!enabled.load())
        return saveSystemsOriginal(job, request);
    const SaveWindow::Capture capture(saveWindow);
    const auto result = saveSystemsOriginal(job, request);
    const auto summary = capture.Read();
    sdk->logger->InfoF(plugin, "PTFR save systems: id=%llu writers=0x%X duplicates=0x%X active=%u unscoped=%llu",
                      static_cast<unsigned long long>(summary.id), summary.components, summary.duplicates,
                      saveWindow.Active(), static_cast<unsigned long long>(saveWindow.Unscoped()));
    return result;
}

template<SaveComponent Component, SaveWriter& Original>
std::uintptr_t ObserveSaveWriter(void* system, void* stream)
{
    const auto result = Original(system, stream);
    if (enabled.load() && !saveWindow.Record(Component))
        sdk->logger->WarnF(plugin, "PTFR save writer outside observed job: component=0x%X",
                           static_cast<unsigned>(Component));
    return result;
}
