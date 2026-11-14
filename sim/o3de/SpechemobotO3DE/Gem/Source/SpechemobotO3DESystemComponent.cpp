#include <AzCore/Serialization/SerializeContext.h>

#include <SpechemobotO3DE/SpechemobotO3DETypeIds.h>
#include <SpechemobotO3DESystemComponent.h>

namespace SpechemobotO3DE
{
    AZ_COMPONENT_IMPL(
        SpechemobotO3DESystemComponent,
        "SpechemobotO3DESystemComponent",
        SpechemobotO3DESystemComponentTypeId);

    void SpechemobotO3DESystemComponent::Reflect(AZ::ReflectContext* context)
    {
        if (auto serializeContext = azrtti_cast<AZ::SerializeContext*>(context))
        {
            serializeContext->Class<SpechemobotO3DESystemComponent, AZ::Component>()
                ->Version(0);
        }
    }

    void SpechemobotO3DESystemComponent::GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided)
    {
        provided.push_back(AZ_CRC_CE("SpechemobotO3DEService"));
    }

    void SpechemobotO3DESystemComponent::GetIncompatibleServices(AZ::ComponentDescriptor::DependencyArrayType& incompatible)
    {
        incompatible.push_back(AZ_CRC_CE("SpechemobotO3DEService"));
    }

    void SpechemobotO3DESystemComponent::GetRequiredServices(
        [[maybe_unused]] AZ::ComponentDescriptor::DependencyArrayType& required)
    {
    }

    void SpechemobotO3DESystemComponent::GetDependentServices(
        [[maybe_unused]] AZ::ComponentDescriptor::DependencyArrayType& dependent)
    {
    }

    SpechemobotO3DESystemComponent::SpechemobotO3DESystemComponent()
    {
        if (SpechemobotO3DEInterface::Get() == nullptr)
        {
            SpechemobotO3DEInterface::Register(this);
        }
    }

    SpechemobotO3DESystemComponent::~SpechemobotO3DESystemComponent()
    {
        if (SpechemobotO3DEInterface::Get() == this)
        {
            SpechemobotO3DEInterface::Unregister(this);
        }
    }

    void SpechemobotO3DESystemComponent::Init()
    {
    }

    void SpechemobotO3DESystemComponent::Activate()
    {
        SpechemobotO3DERequestBus::Handler::BusConnect();
    }

    void SpechemobotO3DESystemComponent::Deactivate()
    {
        SpechemobotO3DERequestBus::Handler::BusDisconnect();
    }
}
