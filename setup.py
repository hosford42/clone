from setuptools import setup

setup(
    name='clone',
    version='0.0',
    packages=['clone'],
    url='https://github.com/hosford42/clone',
    license='MIT',
    author='Aaron Hosford',
    author_email='hosford42@gmail.com',
    description='Clone Git repositories without installing Git',
    entry_points={
        'console_scripts': [
            'clone = clone:main',
        ],
    }
)
