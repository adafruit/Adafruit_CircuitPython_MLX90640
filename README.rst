Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-mlx90640/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/mlx90640/en/latest/
    :alt: Documentation Status

.. image:: https://img.shields.io/discord/327254708534116352.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_MLX90640/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_MLX90640/actions
    :alt: Build Status

Driver for the MLX90640 thermal camera


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `Bus Device <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `Register <https://github.com/adafruit/Adafruit_CircuitPython_Register>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_.

Installing from PyPI
=====================
On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-mlx90640/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-mlx90640

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-mlx90640

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install adafruit-circuitpython-mlx90640

Usage Example
=============

.. code-block:: python

	import time
	import board
	import busio
	import adafruit_mlx90640

	i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

	mlx = adafruit_mlx90640.MLX90640(i2c)
	print("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])

        # if using higher refresh rates yields a 'too many retries' exception,
        # try decreasing this value to work with certain pi/camera combinations
	mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ

	frame = [0] * 768
	while True:
	    try:
		mlx.getFrame(frame)
	    except ValueError:
		# these happen, no biggie - retry
		continue

	    for h in range(24):
		for w in range(32):
		    t = frame[h*32 + w]
		    print("%0.1f, " % t, end="")
                print()
            print()

Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/mlx90640/en/latest/>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_MLX90640/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.

Documentation
=============

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.
