##################
Calendar generator
##################

*Generate a personalized Dutch week calendar for any given year*

The generated calendar will be in Open Document Text format (odt).


***
How
***

#. Clone this project.

   .. code-block:: sh

       ~$ git clone https://github.com/remcohaszing/calendar-generator.git
       ~$ cd calendar-generator

#. Use Pipenv to create a Python3 virtual environment and install the dependencies

   .. code-block:: sh

       ~/calendar-generator$ pipenv sync

#. Create a YAML configuration file.

   .. code-block:: sh

       year: 2016

       special dates:
         03-04: May the Fourth be with you
         03-05: Revenge of the Fifth

       birthdays:
         1991-01-11:
           - Remco
         1991-08-25:
           - Linux

       weddings:
         2006-06-06
           - - Husband
             - Wife

#. Generate the calendar:

   .. code-block:: sh

       ~/calendar-generator$ pipenv run generate config.yaml


************
Contributing
************

Contributions can be made in the following form:

* Bug report.
* Pull request fixing a bug.
* Adding additional holidays.
* Add support for multiple locales and more specific dates.
