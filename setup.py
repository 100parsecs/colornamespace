from setuptools import setup, find_packages
with open('README.md') as f:
    long_description = f.read()

setup(
    name='colornamespace',
    version='0.8.1',
    description='Personal color name semantics mapping application',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GNU General Public License, version 3.0',
    author='Benton Greene',
    author_email='bgreene101@gmail.com',
    packages=find_packages(),
    install_requires=["numpy","scipy","matplotlib","pillow"],
    python_requires=">=3.7",
    entry_points={'gui_scripts':['ColorNameMapper = colornamespace.__main__:main']}
)