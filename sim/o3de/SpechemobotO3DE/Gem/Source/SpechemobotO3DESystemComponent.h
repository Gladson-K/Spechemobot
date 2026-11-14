#pragma once

#include <AzCore/Component/Component.h>

#include <SpechemobotO3DE/SpechemobotO3DEBus.h>

namespace SpechemobotO3DE
{
    class SpechemobotO3DESystemComponent
        : public AZ::Component
        , protected SpechemobotO3DERequestBus::Handler
    {
    public:
        AZ_COMPONENT_DECL(SpechemobotO3DESystemComponent);

        static void Reflect(AZ::ReflectContext* context);
        static void GetProvidedServices(AZ::ComponentDescriptor::DependencyArrayType& provided);
        static void GetIncompatibleServices(AZ::ComponentDescriptor::DependencyArrayType& incompatible);
        static void GetRequiredServices(AZ::ComponentDescriptor::DependencyArrayType& required);
        static void GetDependentServices(AZ::ComponentDescriptor::DependencyArrayType& dependent);

        SpechemobotO3DESystemComponent();
        ~SpechemobotO3DESystemComponent() override;

    protected:
        void Init() override;
        void Activate() override;
        void Deactivate() override;
    };
}
