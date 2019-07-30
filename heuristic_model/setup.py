from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension

import os
import sys

extension = Extension( name='jsp_bbs',
                       sources=['jsp_bbs.pyx',
                                'c_utils.cpp',
                                ],
                       language="c++",
                       extra_compile_args=['-std=c++11'],
                      )

setup(
    ext_modules = cythonize(extension)
)

try:
    print("checking existence of compiled file *.so")
    if not(os.path.exists('../bin')):
      os.makedirs('../bin')
      print("make bin directory")
    # compile it into  .o file
    assert os.system("mv *.so ../bin") == 0
except:
    if not os.path.exists("./.so"):
      print("Error building dynamic library of cython")
      sys.exit(1)