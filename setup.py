from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open('README', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rfm12-mqtt-gateway',

    version='0.1.0',

    description='Two-way RFM12 to MQTT gateway',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/ricklupton/rfm12-mqtt-gateway',

    # Author details
    author='Rick Lupton',
    author_email='r.lupton@gmail.com',

    # Choose your license
    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.6',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.2',
        # 'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='rfm12 mqtt gateway openenergymonitor raspberrypi',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['rfm12_mqtt_gateway'],

    install_requires=['PyYAML', 'pyserial', 'paho-mqtt'],

    extras_require={
        'test': ['coverage'],
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'rfm12-mqtt-gateway=rfm12_mqtt_gateway.__main__:main',
        ],
    },
)
