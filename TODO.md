
* documentation?
  - Sphynx module documentation?
  - document how to reconstruct database (internal)
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* define users to do different works
  - [sqlalchemy serializer](https://stackoverflow.com/questions/2786664/how-to-create-and-restore-a-backup-from-sqlalchemy)
    can be useful?

* Django was updated to 2.0. Urls changed!!! Need to test if we can migrate to newer
  django release? - This version However is a LTS version - not so important a the moment

* get_json_1 need to be modified
  - The json extracted from database is different from exampleJSONfromUIDafterEnhancement.json
    need to add the following sections:
    * person
    * organization
    * species
  - check that attrib in sample, breed animals correspond (doesn't seem)
    * fix into tables? fix in json dumps? (table seems better)
  - ontologies need to be already present in JSON
  - [validate json](https://jsonlint.com/) output
    * NaN is not a valid Json value
    * NaT is not a valid Json value
  - submission:
    * Does Inject-Tool manage more than one submission at time?
    * I need to get data relying on submission? is submission a foreign key?

* Sampletab need to be modified
  - Sampletab columns have to reflect IMAGE-metadata?
  - Sampletab need to be removed: biosample is planning to import only JSON

* [Django REST framework](http://www.django-rest-framework.org/) to get json data?
  to work with OpenRefine client?
  - This module is strictly related to models. If I want to get a JSON object like
    biosample, I need to think a model with relations as the json will be. For the
    moment is better to think a biosample object as a django view. This module could
    be an option in modifying attributes

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - IMAGE-metadata define fields in .xls used for import. There is a correspondance
    between IMAGE-metadata columns and UID database columns
  - Data will be exported using JSON (preferably). Sampletab could be useful
    for testing purpose.
  - Exporing data in IMAGE-metadata excel template, could be useful for data
    cleaning?

* Suppose to fill up ontlogy terms in some way (or data useful to many Inject-Tool
  installation). Common data need to be in a common database? Or the should be a copy
  of them in each database?

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

* Add messages when views are called or code executed

* Unittest?

* Those tables are empty at the moment:
  - Databases

* Submission table is not referenced by any other table.
  - Should I retrieve information using a submission id? Is submission the first
    requirement to fill up when importing data?
  - Suppose I want to do two separate submission. I have to wipe every time? if
    yes, were data will be placed? If I do a submission, then I want to change something,
    need I to modify the submission in my database? need I modify data downloaded
    from biosample?

* Where Submission takes place? could be a one to many Samples or Animals?

* ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
  Using google refine? For the moment, no duplicate can be inserted into database,
  the second occurrence will not be included in database.

* NGINX media folder can serve media files (jpg, etc). Deal with dump files (permissions?)

* add a message when uploading data source

* deal with timeout when uploading data sources

* When google cache is active, two pages are loaded: deal with executing scripts in
  the same session

* when truncating image tables, unset the loaded flag in data sources table

* Filter out the admin person (add the admin role? - not in EF0)

* What happens if two user load data in the same time? deal with concurrency

* record need to have a column in which the status is recorded (need revisions,
  submitted, ...)

* Latitude and longitude need to be TEXT for the moment: we may help user to transform
  values.

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

* One instance of UID and Inject-tool. (all hosted at PTP). Each user is isolated
  from the others. Same UID? UID for each each user? Maybe UID centralized and isolate
  user data.

* Status code for submission

* Error handling (API?/String messages?)

* Data source name will change with metadata rules

* Mother and Father are not mandatory, for the moment; They should have unknown
  values for other data than cryoweb. When they are unknown, they shouldn't be
  exported.
