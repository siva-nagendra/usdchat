from setuptools import find_packages, setup

setup(
    name="usdchat",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "PySide6",
        "openai",
        "usd-core",
    ],
    include_package_data=True,
    description="usdchat is an expert AI assistant in Pixar OpenUSD, \
                capable of coding, chatting, editing 3D scenes, \
                fetching stage info, and interacting with usdview.",
    long_description=open("README.md").read(),
    url="https://github.com/siva-nagendra/usdchat",
    author="Siva Nagendra Savarapu",
    author_email="siva_nagendra@outlook.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
