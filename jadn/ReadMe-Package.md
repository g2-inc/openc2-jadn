# OpenC2 Python Package

## Pre build
1. Edit the version.json file as necessary

## Building the JADN Schema pkg manually
	1. Install required packages for building - setuptools, wheel
		- setuptools should be installed with pip

		```bash
		pip install setuptools wheel
		```

	2. Run command to build the wheel

		```bash
		python3 setup.py sdist bdist_wheel
		```

	3. Use the build whl to install the JADN pkg where needed
		- The file is located in the dist folder with the naming schema of
			- {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
