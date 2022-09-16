from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="core_base",
    version="1.0.2",
    author="cx",
    author_email="2256807897@qq.com",
    description="处理Django Rbac权限,日志等",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://so.szyfd.xyz/",
    project_urls={
        "Bug Tracker": "https://so.szyfd.xyz/",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[
        "Django >= 3.2",  # Replace "X.Y" as appropriate
        "Pillow >= 9.0.1",
        "django-cors-headers >= 3.11.0",
        "django-filter >= 21.1",
        "djangorestframework >= 3.13.1",
        "djangorestframework-simplejwt >= 5.2.0",
        "requests >= 2.28.1",
        "six >= 1.16.0",
        "user-agents >= 2.2.0",
        "django-restql >= 0.15.2",
        "openpyxl >= 3.0.10",
        "pypinyin >= 0.47.1",
        "django-simple-captcha >= 0.4",
        "django-tenants >= 0.4",
        "django-timezone-field >= 1.0",
    ]
)
