
* documentation?
  - Sphynx module documentation?
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* Regarding libraries upgrades and downgrades
  - Need to test if we can migrate to newer django release?
  - waiting for the next LTS version. No stable branch with a non-LTS version
  - celery-flower need to be removed if it is not necessary
  - Upgrade `docker-compose.yml` to latest version format

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - IMAGE-metadata define fields in .xls used for import. There is a correspondance
    between IMAGE-metadata columns and UID database columns
  - Data will be exported using JSON (preferably).
  - Exporting data in IMAGE-metadata excel template, could be useful for data
    cleaning?

* Openrefine integration:
  - need to place Openrefine in docker compose?
  - can I place data directly in OpenRefine? I need to download data from Inject-Tool
    then load into OpenRefine? when data are ready, I need to place them back to Inject-Tool?
  - test [OpenRefine client](https://github.com/OpenRefine/refine-client-py)

* Regarding data submissions
  - Submission table need to track the batch biosample upload
  - How I can update an already loaded biosample using a different submission from
    the first one?
  - Need to check UID integrity **before** loading data into submission?
  - If data loading fails, were I can fix my data? update submission view?
  - what the `edit data` in the submission detail view means? editing data into UID?
    Update submission view? if `uploaded_file` fields changes, what I have
    to do?

* regarding issues in data into UID:
  - ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
    U sing google refine? For the moment, no duplicate can be inserted into database,
    the second occurrence will not be included in database.
  - tag problematic fields?
  - Data need to be isolated from a user POV

* regarding performance issues:
  - What happens if two user load data in the same time? deal with concurrency
  - isolation with an asyncronous queue system? celery
  - deal with timeout when uploading data sources. Implement import_from_cryoweb
    as celery task
  - When google cache is active, two pages are loaded: all scripts will be executed
    using celery tasks
  - fix logging in celery modules (each log is printed two times, one for django
    and one for task itself)

* NGINX media folder can serve media files (jpg, etc).
  - Deal with dump files (permissions?)
  - Protect media files froun un-authenticated user. See
    [this gist](https://gist.github.com/cobusc/ea1d01611ef05dacb0f33307e292abf4),
    [private media with django](http://racingtadpole.com/blog/private-media-with-django/),
    [How to Serve Protected Content With Django](https://wellfire.co/learn/nginx-django-x-accel-redirects/)
    and [Django: What setting to be done in NGINX Conf to serve media file to logged in users only](https://www.digitalocean.com/community/questions/django-what-setting-to-be-done-in-nginx-conf-to-serve-media-file-to-logged-in-users-only)
  - add subdirs in media folder `data_source/`

* Django enhancements
  - all foreign keys in django.admin dropdown lists are rendered in HTML page, and this make the
    pages bigger. At the moment, pages are rendered using `raw_id_fields` as described
    [here](https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html).
    Others solutions could be [autocomplete fields](http://django-extensions.readthedocs.io/en/latest/admin_extensions.html?highlight=ForeignKeyAutocompleteAdmin)
    or using [django-salmonella](https://github.com/lincolnloop/django-dynamic-raw-id)
  - django admin wil be not accessible to normal user?
  - Using LoginRequiredMixing for class based view authentication (update all classes)
  - add migrations in git repository, as suggested from official django documentation
    [cit needed] and [here](https://stackoverflow.com/questions/28035119/should-i-be-adding-the-django-migration-files-in-the-gitignore-file)
  - django `contettype` framework to model relations between Name and Sample and
    animal

* import June code:
  - geo standardization
  - date standardization
  - zooma:
    - high confidence: use it
    - good: ask to user?
    - Add a special confidence status when supplied breed is different from
      mapped_breed (need revisions)

* Regarding data submission into biosample:
  - Mother and Father are not mandatory, for the moment; They should have unknown
    values for other data than cryoweb. When they are unknown, they shouldn't be
    exported.
  - return a default ontology for breed if non mapping occours
  - check for mandatory fields in IMAGE-metadata rules: tests for mandatory
  - model other field types

* Dashboard page: database status and links of all applications developed
  - report and links for datasource (upload datasource, views datasources etc)
  - report and links for cryoweb staging area
  - check for duplicate breeds - names

* cryoweb tables need to be filled using django ORM:
  - can test using correct test database: now functions and pandas function use
    hardcoded cryoweb database even in tests.
  - implement [views](https://blog.rescale.com/using-database-views-in-django-orm/)
    in cryoweb models
  - remove sqlalchemy `image_app.helpers` classes
  - remove pandas
  - fixtures and pre calculated data in test database are recordered in transactions:
    I need to see object using the same connection (see loaded fixtures with
    the same connection)
  - remove unused view `import_from_cryoweb`

* metadata rules
  - taxon (= specie) is a mandatory fields for biosample, taxonId not but is better
    to map it into the specie table
  - check mandatory fields for biosample. Other fields are attributes
  - geo fields were added in last metadata rules

* Biosample manager user should do:
  - Monitor biosample submission to see if sample are validated or not (by team/user)
  - finalize submission after biosample validation occours
  - ask for user intervention / notify success
  - fetch biosample id when submission is finalized and completed

* proposed change for `Name` table (that can become a summary table a user will see)
  - all columns: name, biosampleid, status, last_change, last_submitted.
  - track status: need to known if a sample has been submitted or need to be submitted
    or updated
  - track time for changes and submission: if I change one sample after submission,
    i need to patch

* Regarding django 3rd party modules:
  - Install `django.contrib.sites` (it is useful?)
  - Use django-bootstrap4 to render forms
  - django-braces: what does it?
  - Use [pytest-django](https://pytest-django.readthedocs.io/en/latest/)
  - check out the django [validators](https://docs.djangoproject.com/en/1.11/ref/validators/)
    documentation
  - read about django [session](https://docs.djangoproject.com/en/1.11/topics/http/sessions/)

* Regarding tests:
  - implement functional testing
  - a user can't use an already register email for activation. Test it
  - test each management command, or at least that it works

* Regarding languages, dictionaries and ontology terms:
  - Where managing tasks like zooma are called? before validation pages?
  - species and countries need to be validated against dictionary tables
  - check for synonim before cryoweb insert into dictspecie table.
  - what happens when uploading a submission with no synonim loaded? The loading
    process fails, I need to free staging databases but fill the dictionary tables
    requiring user intervention.

* Regarding site visualization
  - Token generation shuld be requested using modals when submitting to biosample
  - Add breadcrumb for pages
  - Add messages when views are called or code executed
  - Data changes that are not POST request, will be modeled using celery
  - all GET requests need to be idenpotent
  - Error handling (API?/String messages?)
  - Navbar for tools (zooma, dictionary tables, etc)?

* Issues relative to UID:
  - check the CASCADE foreign keys
  - implement the `truncate` class method
  - `truncate_image_tables` management command need to rely on django ORM
  - remove the `image_app.helpers` unuseful classes
  - `Publication` table is empty at the moment
  - records (like `Name`) need to have a column in which the status is recorded
    (need revisions, submitted, ...)
  - check the Relation type between `Sample` and `Name`: need to be One2One
  - rename `image_app` application into `uid`?
  - More user can belong to same organization?
  - `contenttypes` framework for `Name` relations?
  - `contenttypes` framework to model errors?
