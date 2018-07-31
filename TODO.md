
* documentation?
  - Sphynx module documentation?
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* define users to do different works
  - [sqlalchemy serializer](https://stackoverflow.com/questions/2786664/how-to-create-and-restore-a-backup-from-sqlalchemy)
    can be useful?

* Django was updated to 2.0. Urls changed!!! Need to test if we can migrate to newer
  django release? - This version However is a LTS version - not so important a the moment

* [Django REST framework](http://www.django-rest-framework.org/) to get json data?
  to work with OpenRefine client?
  - This module is strictly related to models. If I want to get a JSON object like
    biosample, I need to think a model with relations as the json will be. For the
    moment is better to think a biosample object as a django view. This module could
    be an option in modifying attributes

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - IMAGE-metadata define fields in .xls used for import. There is a correspondance
    between IMAGE-metadata columns and UID database columns
  - Data will be exported using JSON (preferably).
  - Exporing data in IMAGE-metadata excel template, could be useful for data
    cleaning?

* Openrefine integration:
  - need to place Openrefine in docker compose?
  - can I place data directly in OpenRefine? I need to download data from Inject-Tool
    then load into OpenRefine? when data are ready, I need to place them back to Inject-Tool?
  - test [OpenRefine client](https://github.com/OpenRefine/refine-client-py)

* Should the columns exported from Inject-Tool be the same of IMAGE-metadata? yes
  UID need to have the same columns of IMAGE-metadata git project.
  - import cryoweb data accordingly to database definition (map column to IDS)
  - data export has to follow IMAGE-metadata.

* Usability: remove unuseful or danger links from home page (ie: truncate database):
  define a more friendly interface to users.
  - check for the admin user

* Add messages when views are called or code executed

* Those tables are empty at the moment:
  - Publications

* Submission table
  - Submission table need to track the batch biosample upload
  - Need to extend submission table in submission.models in order to model
    additional fields (eg submission status)

* ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
  Using google refine? For the moment, no duplicate can be inserted into database,
  the second occurrence will not be included in database.

* NGINX media folder can serve media files (jpg, etc). Deal with dump files (permissions?)

* deal with timeout when uploading data sources

* When google cache is active, two pages are loaded: deal with executing scripts in
  the same session

* What happens if two user load data in the same time? deal with concurrency
  - Data need to be isolated from a user POV
  - isolation with an asyncronous queue system?

* record need to have a column in which the status is recorded (need revisions,
  submitted, ...)

* Django-admin performance issues:
  - all foreign keys dropdown lists are rendered in HTML page, and this make the
  pages bigger. At the moment, pages are rendered using `raw_id_fields` as described
  [here](https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html).
  Others solutions could be [autocomplete fields](http://django-extensions.readthedocs.io/en/latest/admin_extensions.html?highlight=ForeignKeyAutocompleteAdmin)
  or using [django-salmonella](https://github.com/lincolnloop/django-dynamic-raw-id)

* import June code:
  - geo standardization
  - date standardization
  - zooma:
    - high confidence: use it
    - good: ask to user?
    - Add a special confidence status when supplied breed is different from
      mapped_breed (need revisions)

* Status code for submission

* Error handling (API?/String messages?)

* Data source name will change with metadata rules

* Mother and Father are not mandatory, for the moment; They should have unknown
  values for other data than cryoweb. When they are unknown, they shouldn't be
  exported.

* rename image_app application into UID?

* Dashboard page: database status and links of all applications developed
  - report and links for datasource (upload datasource, views datasources etc)
  - report and links for cryoweb staging area
    - check for duplicate breeds - names

* return a default ontology for breed if non mapping occours

* species and countries need to be validated against dictionary tables
  - check for synonim before cryoweb insert into dictspecie table.

* cryoweb tables need to be filled using django ORM:
  - can test using correct test database: now functions and pandas function use
    hardcoded cryoweb database even in tests.
  - implement [views](https://blog.rescale.com/using-database-views-in-django-orm/) in cryoweb models
  - no more config and helper module
  - remove pandas
  - fixtures and pre calculate data in test database are recordered in transactions:
    I need to see object using the same connection (see loaded fixtures with
    the same connection)

* check out the django [validators](https://docs.djangoproject.com/en/1.11/ref/validators/)
  documentation

* BiosampleJSON views need to be renamed to ValidationJSON or something similar

* create to_biosample() python dictionary like biosample need
  - check for mandatory fields in IMAGE-metadata rules: tests for mandatory
    fields need to be moved into validation module
  - use fixtures to upload data into UID for tests

* Recording submission ids in submission table
  - did I need also the sample ids?
  - how the submission table will reflect users submissions?

* How I can update an already loaded biosample using a different submission from
  the first one?

* taxon (= specie) is a mandatory fields for biosample, taxonId not but is better
  to map it into the specie table
  - check mandatory fields for biosample. Other fields are attributes
  - check status for submission.

* read about django [session](https://docs.djangoproject.com/en/1.11/topics/http/sessions/)
  - automate [clearsession](https://docs.djangoproject.com/en/1.11/topics/http/sessions/#clearing-the-session-store)

* Remove empty sampleRelationships from biosample json

* Biosample manager user should do:
  - Monitor biosample submission to see if sample are validated or not (by team/user)
  - finalize submission after validation occours
  - ask for user intervention / notify success
  - create team and add user which can add sample. Submission will be done for
    each user indipendently
  - fetch biosample id when submission is finalized and completed

* proposed change for `Name` table (that can become a summary table a user will see)
  - all columns: name, biosampleid, status, last_change, last_submitted.
  - track status: need to known if a sample has been submitted or need to be submitted
    or updated
  - track time for changes and submission: if I change one sample after submission,
    i need to patch

* add migrations in git repository, as suggested from official django documentation
  [cit needed] and [here](https://stackoverflow.com/questions/28035119/should-i-be-adding-the-django-migration-files-in-the-gitignore-file)

* More user can belong to same organization?

* Install `django.contrib.sites` (it is useful?)

* Using LoginRequiredMixing for class based view authentication (update all classes)

* Use django-bootstrap4 to render forms

* django-braces: what does it?

* Accounts:
  - if I key is activated with success, inform user that the activation
    process is already done - test it
  - the `registration_activation_complete` page, should redirect to `dashboard` if
    a biosample accounts is already registered?
  - a user can't use an already register email for activation

* Use [pytest-django](https://pytest-django.readthedocs.io/en/latest/)

* fixtures need to be organized in directories
