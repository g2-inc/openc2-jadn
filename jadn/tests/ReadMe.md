# JADN Schema Tests

## Requirements
- Python 3.6+
- Development of package
    - To install in development mode, run the following command from the 'jadn' directory 
        ```bash
        python setup.py develop
        ```
        
        - This will 'install' the package to the system python packages via a link to the source code of the package
    - To remove/uninstall the development package, run the following command from the 'jadn' directory
        ```bash
        python setup.py develope --uninstall
        ```

## Tests
##### Note: Install the package (normal or development) prior to running the test scripts

- jadn_merge.py
- jadn_translate.py
- message_decoders.py
- schema-translators.py
- test_codec.py
- test_openc2.py
- test_openc2_exp.py

