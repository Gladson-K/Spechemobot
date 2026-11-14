from setuptools import find_packages, setup

package_name = "spechemobot_orchestration"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/orchestration.launch.py"]),
        ("share/" + package_name + "/config", ["config/orchestration.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Spechemobot",
    maintainer_email="dev@example.com",
    description="ROS 2 batch and robot-task orchestration for Spechemobot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "robot_task_server = spechemobot_orchestration.robot_task_server:main",
            "batch_orchestrator = spechemobot_orchestration.batch_orchestrator:main",
        ],
    },
)
