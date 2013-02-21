from setuptools import setup, find_packages

version = '0.1'

long_description = open('README.rst').read()

setup(name='webtest-selenium',
      version=version,
      description="Selenium testing with WebTest",
      long_description=long_description,
      classifiers=[],
      keywords='selenium webtest wsgi',
      author='Gael Pasgrimaud',
      author_email='gael@gawel.org',
      url='http://github.com/gawel/webtest-selenium',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'webtest',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
