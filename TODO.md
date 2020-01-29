
InjectTool TODO
===============

* Data export: How data needs to be exported? How IMAGE metadata works?
  - IMAGE metadata defines fields in .xls used for import. There is a correspondance
    between IMAGE metadata columns and UID database columns
  - Exporting data in IMAGE metadata excel template, could be useful for data
    cleaning?
  - if needed, should be implemented using [django-rest-framework](https://www.django-rest-framework.org/)

* Regarding data submissions
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
  - reloading submission should invalidate validationresults

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
  - browse by languages, see all synonym in every language (add navigation links)
  - add a custom synonym manually

* Regarding site visualization
  - Token generation could be requested using modals when submitting to biosample,
    there's no difference from a web page, however, is only aesthetic
  - Add breadcrumb for pages
  - serving all 3rd party modules using CDN when possible
  - Pagination: missing jumping to a particular page function

* Issues relative to UID:
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

* Relate to templatetags
  - process and render pagination with get parameters. See:
    - https://simpleisbetterthancomplex.com/snippet/2016/08/22/dealing-with-querystring-parameters.html
    - https://gist.github.com/benbacardi/d6cd0fb8c85e1547c3c60f95f5b2d5e1
  - [customize queryset](https://stackoverflow.com/questions/22902457/django-listview-customising-queryset)
  - Read documentation about [advanced templatetags](https://djangobook.com/advanced-custom-template-tags/)

* Related to CRBanim
  - deal with biosample records
