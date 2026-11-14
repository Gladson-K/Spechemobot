from setuptools import find_packages, setup

package_name = "spechemobot_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            [
                "launch/sim.launch.py",
                "launch/reactor_hall.launch.py",
                "launch/furnace_annealing.launch.py",
                "launch/conveyor_sorting.launch.py",
                "launch/sensor_qualification.launch.py",
            ],
        ),
        ("share/" + package_name + "/config", ["config/gz_bridge.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Spechemobot",
    maintainer_email="dev@example.com",
    description="Launch files and bridge configuration for the Spechemobot simulation.",
    license="Apache-2.0",
    entry_points={"console_scripts": []},
)
