
InjectTool TODO
===============

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
  - Think about renaming `EditSubmissionView` with a more useful name
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
  - see [django_filters](https://django-filter.readthedocs.io/) and [django_tables](https://django-tables2.readthedocs.io/en/latest/).
    For an example tutorial see [here](https://www.craigderington.me/generic-list-view-with-django-tables/)
  - [django-pgcrypto](https://django-pgcrypto-expressions.readthedocs.io/en/latest/)?

* Regarding Data validation:
  - Can validation start after data load, and after calling zooma? See celery
    chains
  - reloading submission should invalidate validationresults

* Biosample manager user should do:
  - ask for user intervention / notify success

* Regarding `EditSubmissionView`
  - search?

* Regarding django 3rd party modules:
  - Install `django.contrib.sites` (it is useful?)
  - Use django-bootstrap4 to render forms
  - django-braces: it is useful?
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
  - Navbar for tools (zooma, dictionary tables, etc)?
  - serving all 3rd party modules using CDN when possible
  - replace text placeholder (Lorem ipsum...)
  - Pagination: missing jumping to a particular page function

* Issues relative to UID:
  - rename `image_app` application into `uid`?
  - `contenttypes` framework for `Name` relations?
  - `contenttypes` framework to model errors?
  - display the real name of file for the uploaded file
    - not so easy, maybe: add a CharField for user filename; Create a custom
      `django.forms.fields.FileField` or a validation function that track the
      realfilename and set it to a hidden field. Save to a `model.CharField` and
      display that field in DetailViews
    - add the uploaded time for file?
  - Change `WAITING` in `PROCESSING` (implies something happening)
  - deal with errors when create a submission with the same parameters of another
    submission:
      duplicate key value violates unique constraint "image_app_submission_gene_bank_name_gene_bank_0c9b8ecc_uniq"
        DETAIL:  Key (gene_bank_name, gene_bank_country_id, datasource_type, datasource_version, owner_id)=(Cryoweb DE, 7, 0, test, 2) already exists.
  - `Submission.message` as `ArrayField` (to store more messages?)
  - [Soft-delete](https://github.com/upgrad/django-deletes) items? can I store
    items with a `deleted` attribute?

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

* Regarding biosample submission: related items should belong to the same submission:
  check relationship between objects and try to append related items together:
  ```sql
  SELECT t1.id, t3.id as submission_id, t1.alternative_id, t4.name AS father_name, t5.name AS mother_name, t2.name FROM image_app_animal AS t1 INNER JOIN image_app_name AS t2 ON t1.name_id = t2.id INNER JOIN image_app_submission AS t3 ON t2.submission_id = t3.id INNER JOIN image_app_name as t4 ON t1.father_id = t4.id INNER JOIN image_app_name AS t5 on t1.mother_id = t5.id WHERE t3.id = 6 AND t4.name != 'ANIMAL:::
ID:::unknown_sire' AND t5.name != 'ANIMAL:::ID:::unknown_dam' LIMIT 10;
  ```
