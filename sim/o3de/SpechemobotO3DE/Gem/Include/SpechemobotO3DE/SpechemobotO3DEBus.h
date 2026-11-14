#pragma once

#include <SpechemobotO3DE/SpechemobotO3DETypeIds.h>

#include <AzCore/EBus/EBus.h>
#include <AzCore/Interface/Interface.h>

namespace SpechemobotO3DE
{
    class SpechemobotO3DERequests
    {
    public:
        AZ_RTTI(SpechemobotO3DERequests, SpechemobotO3DERequestsTypeId);
        virtual ~SpechemobotO3DERequests() = default;
    };

    class SpechemobotO3DEBusTraits
        : public AZ::EBusTraits
    {
    public:
        static constexpr AZ::EBusHandlerPolicy HandlerPolicy = AZ::EBusHandlerPolicy::Single;
        static constexpr AZ::EBusAddressPolicy AddressPolicy = AZ::EBusAddressPolicy::Single;
    };

    using SpechemobotO3DERequestBus = AZ::EBus<SpechemobotO3DERequests, SpechemobotO3DEBusTraits>;
    using SpechemobotO3DEInterface = AZ::Interface<SpechemobotO3DERequests>;
}
