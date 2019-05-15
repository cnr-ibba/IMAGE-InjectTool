
InjectTool TODO
===============

* documentation?
  - Sphynx module documentation?
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* Regarding libraries upgrades and downgrades
  - Need to test if we can migrate to newer django release?
  - waiting for the next LTS version (April 2019). No stable branch with a non-LTS version
  - celery-flower need to be removed if it is not necessary

* regarding docker configuration:
  - move flower to another port (eg 15555; however is flower needed?)
  - move /image/ location to injecttool (or use a CNAME domain)

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - IMAGE-metadata define fields in .xls used for import. There is a correspondance
    between IMAGE-metadata columns and UID database columns
  - Exporting data in IMAGE-metadata excel template, could be useful for data
    cleaning?
  - if needed, should be implemented using [django-rest-framework](https://www.django-rest-framework.org/)

* Regarding data submissions
  - How I can update an already loaded biosample using a different submission from
    the first one? Need to refator things in user spaces (no same name for same user)
  - Think about renaming EditSubmissionView with a more useful name
  - Submission to biosample using threads?
  - mail to admin when there are issues in USI?
  - implement the sameAs key for already submitted biosamples:
    ```
    "sampleRelationships": [
      {
        "relationshipNature": "same as",
        "alias": "502-W-133-4FE274B"
      }
    ]
    ```
  - Supposing a submission has issues in USI validation. Shuold I track it in
    validation tables? should I have tables for USI errors, since if the
    data is validated using `image_validation` is not a user error?
    
* regarding issues in cryoweb:
  - ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
    Using google refine? For the moment, no duplicate can be inserted into database,
    the second occurrence will not be included in database.
  - tag problematic fields?
  - breed changes for animal <VAnimal: ANIMAL:::ID:::CS01_1999 (Cinta Senese) (sire:ANIMAL:::ID:::CT01_1999, dam:ANIMAL:::ID:::unknown_dam)>
    and its father
  - check for duplicate breeds - names

* NGINX media folder can serve media files (jpg, etc).
  - add subdirs in media folder `data_source/` - using a subdir for each template
    could avoid name collision and visualize the original file name

* Django enhancements
  - all foreign keys in django.admin dropdown lists are rendered in HTML page, and this make the
    pages bigger. At the moment, pages are rendered using `raw_id_fields` as described
    [here](https://books.agiliq.com/projects/django-admin-cookbook/en/latest/many_fks.html).
    Others solutions could be [autocomplete fields](http://django-extensions.readthedocs.io/en/latest/admin_extensions.html?highlight=ForeignKeyAutocompleteAdmin)
    or using [django-salmonella](https://github.com/lincolnloop/django-dynamic-raw-id)
  - django `contettype` framework to model relations between Name and Sample and
    animal
  - see [django_filters](https://django-filter.readthedocs.io/) and [django_tables](https://django-tables2.readthedocs.io/en/latest/).
    For an example tutorial see [here](https://www.craigderington.me/generic-list-view-with-django-tables/)
  - [django-pgcrypto](https://django-pgcrypto-expressions.readthedocs.io/en/latest/)?

* import June code:
  - geo standardization
  - date standardization
  - import ontology code in zooma module
  - zooma:
    - high confidence: use it
    - good: ask to user?
    - Add a special confidence status when supplied breed is different from
      mapped_breed (need revisions)

* Regarding Data validation:
  - mock up time consuming modules (`validation.tests.test_helpers`)
    - hard task: maybe pickling `image_validation.use_ontology.OntologyCache`?
  - Can validation start after data load, and after calling zooma? See celery
    chains
  - I could validate a data for an already submitted object (rules may change).
    but if the validation is ok, I don't need to change the status nor submit
    this object
  - Validation summary (could combine with submission summary):
    - How many unknown, pass, warning, and error
    - If possible, what is the most occurred error, which may lead to batch
      correction, e.g. add decimal degrees to the coordinate as units
    - SubmissionReport must be calculated once, or cached (if this,must be
      invalidated when validation happens)
  - reloading submission should invalidate validationresults
  - calculate submission statics after validation
  - templatetags for ValidationSummary

* Regarding data fields and attributes:
  - Mother and Father are not mandatory, for the moment; They should have unknown
    values for other data than cryoweb. When they are unknown, they shouldn't be
    exported.
  - return a default ontology for breed if non mapping occours
  - model other field types

* Biosample manager user should do:
  - ask for user intervention / notify success

* Regarding `EditSubmissionView`
  - search?

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
  - test each management command, or at least that it works

* Regarding languages, dictionaries and ontology terms:
  - Where managing tasks like zooma are called? before validation pages?
    - breed and species annotation could start after loading data. Check for
      celery chains
  - breeds and countries need to be validated against dictionary tables
  - browse by languages, see all synonym in every language (add navigation links)
  - update ontology urls (see Jun's code)
  - add a custom synonym manually
  - organism parts shold be modelled in dictionary tables (ex Hair (Peli) -> strand of hair (UBERON_0001037))

* Regarding site visualization
  - Token generation could be requested using modals when submitting to biosample,
    there's no difference from a web page, however, is only aesthetic
  - Add breadcrumb for pages
  - Add messages when views are called or code executed
  - Error handling (API?/String messages?)
  - Navbar for tools (zooma, dictionary tables, etc)?
  - serving all 3rd party javascript scripts (jquery, bootstrap and popper using
    static files)
  - replace text placeholder (Lorem ipsum...)
  - Pagination: missing jumping to a particular page function

* Issues relative to UID:
  - rename `image_app` application into `uid`?
  - `contenttypes` framework for `Name` relations?
  - `contenttypes` framework to model errors?
  - Having a unknown animal as  mother/father should be equal having this foreign
    key with a NULL value
  - display the real name of file for the uploaded file
    - not so easy, maybe: add a CharField for user filename; Create a custom
      `django.forms.fields.FileField` or a validation function that track the
      realfilename and set it to a hidden field. Save to a `model.CharField` and
      display that field in DetailViews
    - add the uploaded time for file?
  - Change WAITING in PROCESSING (implies something happening)
  - deal with errors when create a submission with the same parameters of another
    submission:
      duplicate key value violates unique constraint "image_app_submission_gene_bank_name_gene_bank_0c9b8ecc_uniq"
        DETAIL:  Key (gene_bank_name, gene_bank_country_id, datasource_type, datasource_version, owner_id)=(Cryoweb DE, 7, 0, test, 2) already exists.
  - `Submission.message` as `ArrayField` (to store more messages?)
  - [Soft-delete](https://github.com/upgrad/django-deletes) items? can I store
    items with a `deleted` attribute?
  - `Sample.storage_type` and `Sample.storage_processing` as enum values?

* Think about a message module to store info useful to the user (into a view):
  - The token is expired during submission; resume submission
  - Submission fails with errors
  - Validation fails with errors

* Related to celery
  - Write celery tasks as classes
  - consider using `celery-once` to do exclusive tasks
  - test celery task against these [rules](https://blog.daftcode.pl/working-with-asynchronous-celery-tasks-lessons-learned-32bb7495586b):
    - idenpotence (select_for_update)
    - acks late

* Relate to templatetags
  - process and render pagination with get parameters. See:
    - https://simpleisbetterthancomplex.com/snippet/2016/08/22/dealing-with-querystring-parameters.html
    - https://gist.github.com/benbacardi/d6cd0fb8c85e1547c3c60f95f5b2d5e1
  - [customize queryset](https://stackoverflow.com/questions/22902457/django-listview-customising-queryset)
  - Read documentation about [advanced templatetags](https://djangobook.com/advanced-custom-template-tags/)

* Related to CRBanim
  - alternative_id issue (now is a duplicate of sample/animal name)
  - deal with biosample records
