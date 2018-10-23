
InjectTool TODO
===============

* documentation?
  - Sphynx module documentation?
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* Regarding libraries upgrades and downgrades
  - Need to test if we can migrate to newer django release?
  - waiting for the next LTS version. No stable branch with a non-LTS version
  - celery-flower need to be removed if it is not necessary

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
  - How I can update an already loaded biosample using a different submission from
    the first one?
  - If data loading fails, were I can fix my data? update submission view?
  - What I have to do for fails in 3rd party API (ie: temporary issues on biosample
    site)?
  - what the `edit data` in the submission detail view means? editing data into UID?
    Update submission view? if `uploaded_file` fields changes, what I have
    to do?
  - what happens if I update something after submission to biosample? need I track
    what changes I see and patch in a new submission?
  - what if a token expires during a submission?
  - a partial submission need to be resumed  
  - simplify submission form: return form invalid if a token is near to expire;
    ask for token credentials as non mandatory fields, return to subission:detail
    after launching task

* regarding issues in data into UID:
  - ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
    Using google refine? For the moment, no duplicate can be inserted into database,
    the second occurrence will not be included in database.
  - tag problematic fields?
  - Data need to be isolated from a user POV
  - breed changes for animal <VAnimal: ANIMAL:::ID:::CS01_1999 (Cinta Senese) (sire:ANIMAL:::ID:::CT01_1999, dam:ANIMAL:::ID:::unknown_dam)>
    and its father
  - check for duplicate breeds - names

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
  - django admin will be not accessible to normal user?
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

* Regarding data fields and attributes:
  - Mother and Father are not mandatory, for the moment; They should have unknown
    values for other data than cryoweb. When they are unknown, they shouldn't be
    exported.
  - return a default ontology for breed if non mapping occours
  - model other field types

* metadata rules
  - test against example `json` files, don't derive reference on the fly (it
    seems difficult update validation tests)

* Biosample manager user should do:
  - ask for user intervention / notify success
  - fetch biosample id when submission is finalized and completed
  - track sample failed if submission fails.

* Regarding table `Name`:
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
  - [django-crispy-forms](https://simpleisbetterthancomplex.com/tutorial/2018/08/13/how-to-use-bootstrap-4-forms-with-django.html)

* Regarding tests:
  - implement functional testing
  - a user can't use an already register email for activation. Test it
  - test each management command, or at least that it works
  - simplify fixture, remove redundancy

* Regarding languages, dictionaries and ontology terms:
  - Where managing tasks like zooma are called? before validation pages?
  - species and countries need to be validated against dictionary tables
  - check for synonim before cryoweb insert into dictspecie table.
  - what happens when uploading a submission with no synonim loaded? The loading
    process fails, I need to free staging databases but fill the dictionary tables
    requiring user intervention.
  - "Semen" has not an ontology term

* Regarding site visualization
  - Token generation could be requested using modals when submitting to biosample,
    there's no difference from a web page, however, is only aesthetic
  - Add breadcrumb for pages
  - Add messages when views are called or code executed
  - Error handling (API?/String messages?)
  - Navbar for tools (zooma, dictionary tables, etc)?

* Issues relative to UID:
  - rename `image_app` application into `uid`?
  - `contenttypes` framework for `Name` relations?
  - `contenttypes` framework to model errors?

* create a `commons` library to store all common stuff

* Think about a message module to store info useful to the user:
  - The token is expired during submission; resume submission
  - Submission fails with errors
  - Validation fails with errors
