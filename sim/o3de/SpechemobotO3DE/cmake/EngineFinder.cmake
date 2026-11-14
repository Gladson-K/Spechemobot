include_guard()

set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/project.json)

if(DEFINED ENV{O3DE_HOME} AND EXISTS "$ENV{O3DE_HOME}/cmake/Findo3de.cmake")
    list(APPEND CMAKE_MODULE_PATH "$ENV{O3DE_HOME}/cmake")
    set(PACKAGE_VERSION_COMPATIBLE TRUE)
    message(STATUS "Spechemobot: using O3DE SDK at $ENV{O3DE_HOME}")
    return()
endif()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/user/project.json")
    file(READ "${CMAKE_CURRENT_SOURCE_DIR}/user/project.json" user_project_json)
    string(JSON engine_path ERROR_VARIABLE json_error GET "${user_project_json}" engine_path)
    if(NOT json_error AND engine_path AND EXISTS "${engine_path}/cmake/Findo3de.cmake")
        list(APPEND CMAKE_MODULE_PATH "${engine_path}/cmake")
        set(PACKAGE_VERSION_COMPATIBLE TRUE)
        message(STATUS "Spechemobot: using O3DE SDK at ${engine_path}")
        return()
    endif()
endif()

message(FATAL_ERROR "O3DE SDK not found. Set O3DE_HOME or run: ubuntu@sandbox:~$ o3de register --this-engine")
