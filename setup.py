from setuptools import setup


setup(
    name='pblock',
    version='1.0',
    py_modules=['pblock'],
    scripts=[
        'pblock-srv',
        'pblock-read',
        'pblock-mix',
    ],
    install_requires=[
        'varint',
    ],
)
