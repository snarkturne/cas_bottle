from distutils.core import setup

setup(
    name='CAS_bottle',
    version='1.1',
    packages=['',],
    url = 'http://github.com/snarkturne/cas_bottle/',
    description = '',
    author = 'SnarkTurne',
    author_email = 'snarkturne@gmail.com',
    requires = [
        'bottle (>=0.9)',
        'beaker',
        'six',
    ],
    classifiers = [
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
