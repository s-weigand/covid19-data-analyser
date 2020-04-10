Used Data Sources
=================

The data used by this project, is scraped from other sources and transformed in a uniform pattern,
which than can be used by the analysis code.
To be transparent about where the data originates from and also give props to the sources we list them here.

funkeinteraktiv (Funke Media Gruppe)
------------------------------------

The funkeinteraktiv datasets originate from the `funkeinteraktiv API`_, which is used by
`morgenpost Corona Monitor`_ and very detailed for germany (county resolution).
Since it provides labels in german as well as english, we thought it would be best to split
it two different datasets for the german and international audience.

.. _`funkeinteraktiv API`: https://funkeinteraktiv.b-cdn.net/history.v4.csv
.. _`morgenpost Corona Monitor`: https://funkeinteraktiv.b-cdn.net/history.v4.csv

JHU (Johns Hopkins University)
------------------------------

The JHU dataset comes directly from the `JHU github repository`_,
which provides the data for the `JHU dashboard`_.



.. _`JHU github repository`: https://github.com/CSSEGISandData/COVID-19
.. _`JHU dashboard`: https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6
