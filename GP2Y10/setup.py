from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages, Extension
import sys

# Check if an explicit platform was chosen with a command line parameter.
# Kind of hacky to manipulate the argument list before calling setup, but it's
# the best simple option for adding optional config to the setup.
# Pick the right extension to compile based on the platform.
extensions = []
extensions.append(Extension("ZhyuIoT_GP2Y10.Raspberry_Pi_Driver", 
								["source/_Raspberry_Pi_Driver.c", "source/Raspberry_Pi/pi_gp2y10_read.c"], 
								libraries=['rt'],
								extra_compile_args=['-std=gnu99']))

# Call setuptools setup function to install package.
setup(name              = 'ZhyuIoT_GP2Y10',
	  version           = '1.0.0',
	  author            = 'Kane Zhu',
	  author_email      = 'kane.mx@gmail.com',
	  description       = 'Library to get readings from the optical duster sensor Sharp GP2Y10 on a Raspberry Pi.',
	  license           = 'MIT',
	  url               = 'https://github.com/zxkane/ZhyuIoT/',
	  packages          = find_packages(),
	  ext_modules       = extensions)
