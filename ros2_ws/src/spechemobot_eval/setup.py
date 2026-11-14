from setuptools import find_packages, setup

package_name = "spechemobot_eval"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/eval.launch.py"]),
        ("share/" + package_name + "/config", ["config/eval.yaml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Spechemobot",
    maintainer_email="dev@example.com",
    description="Runtime metrics and acceptance evaluation for Spechemobot.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "evaluate_run = spechemobot_eval.evaluate_run:main",
        ],
    },
)
