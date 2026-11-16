    {
        Bytes<0x309> session;
        int jobs{};
        static std::string_view admissionLog;
        static int logCount{};
        static int polls{};
        static void* sessionArgument{};
        static void* jobsArgument{};
        RED4ext::v1::Logger testLogger{};
        testLogger.Info = [](RED4ext::v1::PluginHandle, const char* message) {
            admissionLog = message;
            ++logCount;
        };
        RED4ext::v1::Sdk testSdk{};
        testSdk.logger = &testLogger;
        sdk = &testSdk;
        enabled.store(true);
        dispatchSavesOriginal = [](void* nativeSession, void* nativeJobs) {
            sessionArgument = nativeSession;
            jobsArgument = nativeJobs;
            ++polls;
        };
        const auto update = [&] { DispatchSaves(session.Data(), &jobs); };
        constexpr std::string_view idle = "PTFR native save handoff admission: idle";
        constexpr std::string_view deferred = "PTFR native save handoff admission: deferred";

        check.Expect(saveAdmissionProbeRequested.load() && admissionLog.empty(),
                     "successful checkpoint probe queues the dispatcher check");
        update();
        check.Expect(admissionLog == idle && logCount == 1 && !saveAdmissionProbeRequested.load() &&
                     sessionArgument == session.Data() && jobsArgument == &jobs && polls == 1,
                     "dispatcher probes its own session and forwards the original call");
        update();
        check.Expect(logCount == 1 && polls == 2, "ordinary updates do not repeat the probe");

        Put(session.Data(), 0x308, std::uint8_t{0x10});
        saveAdmissionProbeRequested.store(true);
        update();
        check.Expect(admissionLog == deferred && logCount == 2 && polls == 3,
                     "the dispatcher's active save bit defers a handoff");
        Put(session.Data(), 0x308, std::uint8_t{0});
        saveAdmissionProbeRequested.store(true);
        update();
        check.Expect(admissionLog == idle && logCount == 3 && polls == 4,
                     "cleared save activity reopens handoff");

        {
            const auto permit = TryBeginNativeHandoff(session.Data());
            saveAdmissionProbeRequested.store(true);
            update();
            check.Expect(permit && admissionLog == deferred && logCount == 4 && polls == 4,
                         "held handoff defers the native dispatcher and the probe");
        }
        update();
        check.Expect(logCount == 4 && polls == 5, "the original dispatcher resumes after handoff release");

        saveAdmissionProbeRequested.store(true);
        {
            const Transition transition;
        }
        update();
        check.Expect(!saveAdmissionProbeRequested.load() && logCount == 4 && polls == 6,
                     "a load or teardown cancels an unconsumed probe");
        Capture disallowed(true);
        check.Expect(!Copy(disallowed, state.quests.Data(), nullptr, nullptr, 0, 0, ReadMode::Probe) &&
                     !saveAdmissionProbeRequested.load(), "a refused checkpoint does not queue save admission");

        enabled.store(false);
        dispatchSavesOriginal = nullptr;
        sdk = nullptr;
    }
