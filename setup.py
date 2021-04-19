from setuptools import setup
import Cplotter
setup(name='Cplotter',
      version=Cplotter.__version__,
      description='Python package for runtime interaction with plots allowing users to add or remove data points, '
                  'modify axis and figure layouts.',
      long_description=open('README.md').read(),
      classifiers=['Intended Audience :: Science/Research',
                   'Programming Language :: Python :: 3.7'],
      url='https://github.com/arcunique/Cplotter',
      author='Aritra Chakrabarty',
      author_email='aritra@iiap.res.in',
      install_requires=['numpy', 'matplotlib'],
      zip_safe=False)
