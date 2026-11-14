from setuptools import find_packages, setup

package_name = "spechemobot_dataset"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/record.launch.py"]),
        ("share/" + package_name + "/config", ["config/dataset.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Spechemobot",
    maintainer_email="dev@example.com",
    description="Dataset recording and manifest generation for Spechemobot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "record_dataset = spechemobot_dataset.record_dataset:main",
            "make_manifest = spechemobot_dataset.make_manifest:main",
        ],
    },
)
