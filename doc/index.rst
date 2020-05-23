.. Pysh documentation master file, created by
   sphinx-quickstart on Fri May 22 20:15:36 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pysh's documentation!
================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


.. TODO:
   * Document remaining API: filters, cmd.
   * Publish docs!  And link from README.
   * Add some commentary and/or examples, and/or link back to README etc.

.. TODO: fix up CSS where <ul> appears inside a function's <dd>, as
   for pysh.shwords.

.. TODO: find a way to autodoc pysh.DEVNULL etc.  Closest ways I've
   found result in showing the name like `pysh.subprocess.DEVNULL`.


Preparing command lines
-----------------------

.. autofunction:: pysh.shwords

.. autofunction:: pysh.shwords_f


Running commands
----------------

.. automodule:: pysh.subprocess

.. py:data:: pysh.DEVNULL

   Has the same meaning for *stdout*/*stderr* arguments of these
   functions, and of `.cmd.run`, as for :class:`subprocess.Popen`.

.. py:data:: pysh.STDOUT

   Has the same meaning for *stderr* arguments of these functions,
   and of `.cmd.run`, as for :class:`subprocess.Popen`.

.. autofunction:: pysh.check_cmd
.. autofunction:: pysh.check_cmd_f
.. autofunction:: pysh.try_cmd
.. autofunction:: pysh.try_cmd_f
.. autofunction:: pysh.slurp_cmd
.. autofunction:: pysh.slurp_cmd_f
.. autofunction:: pysh.try_slurp_cmd
.. autofunction:: pysh.try_slurp_cmd_f


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
