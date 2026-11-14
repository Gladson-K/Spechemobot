#include <AzCore/Memory/SystemAllocator.h>
#include <AzCore/Module/Module.h>

#include <SpechemobotO3DE/SpechemobotO3DETypeIds.h>
#include <SpechemobotO3DESystemComponent.h>

namespace SpechemobotO3DE
{
    class SpechemobotO3DEModule
        : public AZ::Module
    {
    public:
        AZ_RTTI(SpechemobotO3DEModule, SpechemobotO3DEModuleTypeId, AZ::Module);
        AZ_CLASS_ALLOCATOR(SpechemobotO3DEModule, AZ::SystemAllocator);

        SpechemobotO3DEModule()
            : AZ::Module()
        {
            m_descriptors.insert(m_descriptors.end(), {
                SpechemobotO3DESystemComponent::CreateDescriptor(),
            });
        }

        AZ::ComponentTypeList GetRequiredSystemComponents() const override
        {
            return AZ::ComponentTypeList{
                azrtti_typeid<SpechemobotO3DESystemComponent>(),
            };
        }
    };
}

#if defined(O3DE_GEM_NAME)
AZ_DECLARE_MODULE_CLASS(AZ_JOIN(Gem_, O3DE_GEM_NAME), SpechemobotO3DE::SpechemobotO3DEModule)
#else
AZ_DECLARE_MODULE_CLASS(Gem_SpechemobotO3DE, SpechemobotO3DE::SpechemobotO3DEModule)
#endif
