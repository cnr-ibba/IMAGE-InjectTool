=======
History
=======

0.9.0.dev0
----------

TODO
^^^^

* Upgrade to the last django LTS version (2.2) (issue `#34 <https://github.com/cnr-ibba/IMAGE-InjectTool/issues/34>`_)
* Move InjectTool URLs outside /image/ location (issue `#66 <https://github.com/cnr-ibba/IMAGE-InjectTool/issues/66>`_)

0.8.0 (2019-11-07)
------------------

Features
^^^^^^^^

- add a missed migration
- deal with improved token duration
- read EBI endpoints from configuration files and determine if they are tests endpoint or not
- remove test warning banner relying on templatetags
- ``biosample.forms`` updated
- map to default breed if possible
- add ``IMAGE submission id`` attribute to identify the original submission into InjectTool
- improved ``image_app.admin`` and ``biosample.admin``
- move ``image_app`` to ``uid`` application
- refactor ``Animal`` and ``Sample`` models by removing ``Name`` model
- link to ``ValidationResult`` through generic relation
- fix name collision issue (``Animal`` and ``Sample`` with same names)
- New constrain to ``Animal`` and ``Sample`` model to determine uniqueness in user space
- Ignore already loaded ``Animal`` and ``Sample`` relying on their names if loaded in a different submission
- Sort by relationship when submitting to BioSamples through SQL
- Submit a ``Sample`` only submission (if ``Animal`` are defined in another submission)
- improved error reporting while importing from *excel* for ``time/units`` fields
- updated docs
