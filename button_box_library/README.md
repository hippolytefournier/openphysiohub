# button_box_library

This directory must contain the RTBox Python driver.

Obtain `RTBox.py` from the official repository:

> https://github.com/xiangruili/RTBox_py

The file has no open-source license; it is not redistributed here.
Copy it into this directory before running the experiment.

**Note:** OpenPhysioHub uses a direct serial implementation and does not
`import RTBox` at runtime. The file is kept here as a reference for the
original RTBox protocol that the serial loop in `rtbox.py` implements.
