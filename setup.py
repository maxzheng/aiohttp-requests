import setuptools


setuptools.setup(
    name='aiohttp-requests',
    version='0.2.3',

    author='Max Zheng',
    author_email='maxzheng.os @t gmail.com',

    description='A thin wrapper for aiohttp client with Requests simplicity',
    long_description=open('README.rst').read(),

    url='https://github.com/maxzheng/aiohttp-requests',

    install_requires=open('requirements.txt').read(),

    license='MIT',

    packages=setuptools.find_packages(),
    include_package_data=True,

    python_requires='>=3.6',
    setup_requires=['setuptools-git', 'wheel'],

    classifiers=[
      'Development Status :: 5 - Production/Stable',

      'Intended Audience :: Developers',
      'Topic :: Software Development :: Libraries :: Python Modules',

      'License :: OSI Approved :: MIT License',

      'Programming Language :: Python :: 3',
    ],

    keywords='aiohttp HTTP client async requests',
)
