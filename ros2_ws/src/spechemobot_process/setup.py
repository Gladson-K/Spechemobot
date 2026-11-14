from setuptools import find_packages, setup

package_name = "spechemobot_process"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/process.launch.py"]),
        ("share/" + package_name + "/config", ["config/process.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Spechemobot",
    maintainer_email="dev@example.com",
    description="Chemical process, furnace, safety, and container models for Spechemobot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "tep_replay_node = spechemobot_process.tep_replay_node:main",
            "furnace_model_node = spechemobot_process.furnace_model_node:main",
            "safety_monitor_node = spechemobot_process.safety_monitor_node:main",
            "container_manager_node = spechemobot_process.container_manager_node:main",
        ],
    },
)
