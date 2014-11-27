import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [
    'maxcarrot',
    'maxclient [wsgi]',
    'apns_client==0.1.8',
    'gcm-client',
    'rabbitpy',
    'gevent'
]

setup(name='maxbunny',
      version='4.0.13.dev0',
      description='Consumer of AMPQ queues for MAX',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='UPCnet Plone Team',
      author_email='plone.team@upcnet.es',
      url='https://github.com/upcnet/maxbunny',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      extras_require={
          'test': ['HTTPretty']
      },
      test_suite="maxbunny",
      entry_points="""\
      [console_scripts]
      maxbunny = maxbunny:main
      """,
      )
