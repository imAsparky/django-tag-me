
.. include:: ../extras.rst.txt
.. highlight:: rst
.. index:: contributing ; Index


.. _how-to-contributing:

=============================
Contributing to django-tag-me
=============================

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/imAsparky/django-tag-me/issues

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with `bug``
and `help wanted` is open to whoever wants to implement a fix for it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with `enhancement`
and `help wanted` is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

`Django-Tag-Me` could always use more documentation, whether as part of
the official docs, in docstrings, or even on the web in blog posts, articles,
and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/imAsparky/django-tag-me/issues.

If you are proposing a new feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `django-tag-me` for local

1. Fork the `django-tag-me` repo on GitHub. Create a copy of the project 
on your own GitHub account by clicking the "Fork" button on the main repository 
page: https://github.com/imAsparky/django-tag-me.git

|

2. Clone your fork locally:

   .. code-block:: bash

    $ cd path_for_the_repo
    $ git clone git@github.com:YOUR_NAME/django-tag-me.git

|

3. Assuming you have venv installed you can create a new environment for your local
development by typing:

   .. code-block:: bash

    $ python3.10 -m venv venv
    $ source venv/bin/activate


This should change the shell to look something like:

   .. code-block:: bash

        (venv) $

|

4. Install dependencies: Install the project's requirements:

   .. code-block:: bash

    $ pip install -r requirements.txt

|

5. Install django-tag-me (editable mode):  

   .. code-block:: bash

    $ pip install -e .

This will install `django-tag-me` in editable mode, allowing you to 
see changes you make to the code instantly in the example project.

Refresh your browser to see your changes reflected in the example app.

|

Set up the example project:

   .. code-block:: bash

    $ cd example/blog
    $ ./manage.py nuke  #this command will delete db, migrate and load fixtures.

This command will create a SQLite database, apply migrations, and load initial data for testing.

|

6. Start the development server:

   .. code-block:: bash

    $ ./manage.py runserver

Visit http://127.0.0.1:8000/ in your browser to see the example blog.


|

7. Create a branch for local development:

   .. code-block:: bash

        $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

|

8. Login to the example app:

   The example app has three users pre-loaded:

   * Username: ``user1``, Password: ``user1``
   * Username: ``user2``, Password: ``user2``
   * Username: ``user3``, Password: ``user3``


This not implemented yet.
8. When you're done making changes, check that your changes pass flake8. Since,
this package contains mostly templates the flake should be run for tests
directory:

   .. code-block:: bash

        $ flake8 ./tests

|

9. The next step would be to run the test cases. `django-tag-me` uses
pytest, you can run PyTest. Before you run pytest you should ensure all
dependancies are installed:

   .. code-block:: bash

        $ pip install -r requirements.txt
        $ pytest ./tests


|

10. Before raising a pull request you should also run pytest This will run the
tests across different versions of Python:

   .. code-block:: bash

        $ pytest 


|

11. If your contribution is a bug fix or new feature, you may want to add a test
to the existing test suite. See section Add a New Test below for details.

|

12. Commit your changes and push your branch to GitHub:

   .. code-block:: bash

        $ git add .
        $ git commit -S -m "Your detailed description of your changes."
        $ git push origin name-of-your-bugfix-or-feature


.. note::

   Please note we only accept verified commits.

|

13. Submit a pull request through the GitHub website.

Push to your fork: Push your changes to your forked repository on GitHub.

Create a pull request:  Open a pull request to the main repository's ``main`` branch. We'll review your changes and work with you to get them merged.


|

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated. Put your
   new functionality into a function with a docstring, and add the feature to
   the list in README.rst.

3. The pull request should work for Python 3.6, 3.7, 3.8, 3.9 and PyPy. Check
   https://github.com/imAsparky/django-tag-me/pulls and
   make sure that the tests pass for all supported Python versions.

Add a New Test
--------------

When fixing a bug or adding features, it's good practice to add a test to
demonstrate your fix or new feature behaves as expected. These tests should
focus on one tiny bit of functionality and prove changes are correct.

|

3. Run your test and confirm that your test fails. If your test does not fail, rewrite the test until it fails on the original code:

   .. code-block:: bash

        $ pytest ./tests

|

.. _Git: https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
