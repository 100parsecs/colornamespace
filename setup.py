from setuptools import setup, find_packages
with open('README.md') as f:
    long_description = f.read()

import colornamespace

setup(
    name='colornamespace',
    version=colornamespace.__version__,
    description='Personal color name semantics mapping application',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='GNU General Public License, version 3.0',
    author='Benton Greene',
    author_email='bgreene101@gmail.com',
    url='http://www.trackprofiler.com/gpxpy/index.html',
    packages=find_packages(),
    install_requires=["numpy","scipy","matplotlib","pillow"],
    python_requires=">=3.9",
    entry_points={'gui_scripts':['ColorNameMapper = colornamespace.__main__:main']}
)