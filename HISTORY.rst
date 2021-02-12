=======
History
=======

TODO
----

* ``django-tables`` and ``django-filters`` integration
* *same as* relationship support
* fix readthedocs build

0.9.6.dev0
----------

* pinning package dependences
* solved issue with celery autoscaling

0.9.5 (2020-06-08)
------------------

Features
^^^^^^^^

* keep at least two worker running
* swap latitude and longitude row order in AnimalDetailView
* add id columns to admin views
* fix bug in reload submission (no more need to change version or type)
* update template upload file (removed unused columns and encoded in ``UTF-8``)
* track and clean up orphaned BioSample IDs
  - add task to track ``IMAGE`` BioSamples id not tracked in InjectTool
  - Notify admins about orphan BioSamples
  - Patch BioSample by submitting the mandatory attributes with a ``releaseDate``
    in the future
  - finalize and retrieve data from patched BioSamples using management scripts
  - deal with already removed samples
* deal with issues when calling zooma
* authenticate once when querying BioSamples
* describe BioSamples submission statuses
* update uploading data docs

0.9.4 (2020-03-03)
------------------

Features
^^^^^^^^

* refactor ``language.templates``
* returning bootstrap alert messages with zooma call
* refactor ``uid.templates``
* simplified error message in token generation
* model *USI* errors as ``ValidationResult`` objects
* minor refactor
* changed APP registration and about pages
* add missing names to batch update
* mark mandatory fields in forms with CSS
* update ``uid.models.DictRole``
* schedule cleanup registration
* refactor account activation message
* upgrade ``Django`` to ``2.2.10``

0.9.3 (2020-01-31)
------------------

Features
^^^^^^^^

* No more ``50x`` page when creating a submission with the same attributes of another one
* Minor refactor
* No edit submission with no data
* forcing constraints for mandatory attributes
* No more validation with ``READY`` state
* rename empty template and download from ``CreateSubmissionView``
* changed ``URI`` for about pages
* documentation review
* truncate mail body sizes
* track samples count and status in ``biosample.models.Submission``
* truncate error messages sent by emails
* tune celery worker (autoscaling processes)
* refactor admin Submission classes
* suppress warnings for ``Processing`` submission status
* pin pyUSIrest library to ``v0.3.1`` and fix an issue in patching sample
* fix a bug when recovering a submission
* Improve wording in webpages
* add missing staticfiles

0.9.2 (2020-01-17)
------------------

Features
^^^^^^^^

* upgrade ``Django`` to ``2.2.9``
* pinning ``pyUSIrest`` dependency to ``v0.3.0``
* documenting the BioSamples submission process in sphinx
* export *BioSamples IDs* as a CSV from *Edit Submission view*
* force excel date cells into ``datetime.date`` objects
* remove duplicated ``animal_age_at_collection`` column from excel template

0.9.1 (2019-12-19)
------------------

Features
^^^^^^^^

* fix issue in excel import when more that one animal is found in
  ``excel.helpers.ExcelTemplateReader.get_animal_from_sample``
* upgraded ``pyUSIrest`` module to support the BioSamples submission to
  production environment
* fix ``wp5image.eu`` links in sphinx docs and templates
* update documentation
* minor fixes

0.9.0 (2019-11-15)
------------------

Features
^^^^^^^^
- remove ``/image/`` location from django settings
- remove ``/image/`` location from NGINX
- update docs
- Upgrade Django to last LTS version (2.2)
- Tests and code were fixed
- Migrations were resetted to initial state
- model the new species/translations in ``initializedb``
- a better error message when uploading missing relationship with ``excel.helpers``
- catch import from cryoweb errors
- clean up biosample.models.Submission
- moved ``PersonMixinTestCase`` into ``uid.tests.mixins``
- add UpdateOrganizationView
- update dashboard and submission delete templates

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
