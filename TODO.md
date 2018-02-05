
* SQL commands to generate data only dumps (for cryoweb)
  - data export, default schema (public?)
  - API to import from an external database?

* deal with temporary file?
  - clean up (using Andrea's commands - management)

* documentation?
  - Sphynx module documentation?
  - document how to reconstruct database (internal)
  - link to project sections, refer to IMAGE-metadata?
  - PEP8?

* define users to do different works
  - Add a distinct user to import data (avoid sql  injection) - I removed it by mistake
  - [sqlalchemy serializer](https://stackoverflow.com/questions/2786664/how-to-create-and-restore-a-backup-from-sqlalchemy)
    can be useful?

* Remove **all** passwords in repository. Create an environment file for passwords
  - try to use [python decouple](https://simpleisbetterthancomplex.com/2015/11/26/package-of-the-week-python-decouple.html)

* DDL for imported_from_cryoweb

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

* person, organization comes from authentication

* Where JSON is in the whole pipeline? Is requested to fill data?

* [Django REST framework](http://www.django-rest-framework.org/) to get json data?
  to work with OpenRefine client?

* update documentation:
  - need to explain how to generate database
  - need to explain how define permissions

* Distribution: Inject tool is inside or infrastructure? or a user need to run its
  own instance

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - I need to export a .xlsx table with a sheet for each category of IMAGE-metadata?
  - Should I do the validation? or it can be external? in such case, what external tool
    use? FAANG?

* Data import: maybe UID need to have the same columns name as defined by IMAGE-metadata

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
  - data export have to follow IMAGE-metadata.

* Usability: remove unuseful or danger links from home page: define a more friendly
  interface to users.

* Unittest?

* Those tables are unclear (and empty at the moment):
  - Databases
  - Term sources

* organization roles has only one column. Could be a column of organization table?

* Submission table is not referenced by any other table.
  - Should I retrieve information using a submission id? Is submission the first
    requirement to fill up when importing data?
  - Suppose I want to do two separate submission. I have to wipe every time? if
    yes, were data will be placed? If I do a submission, then I want to change something,
    need I to modify the submission in my database? need I modify data downloaded
    from biosample?

* Check UID columns, IMAGE-metadata and IMAGE_sample_empty_template_20180122 columns
  are not the same

* Animal (or samples) could have the same names (ie ANIMAL:::ID:::123456) so the
  unique identifier is composed by "data source name", "data source version", "animal data source id"-> "Cryoweb de", "version 1", "ANIMAL:::ID:::123456". Data version and source need to be defined when loading
  data.

* Animal (and samples) could have spaces in their names, so replace them with `_`:
  if name is already present (in the same data source and version) take it
  - Rename backup table and Object in data source
  - Rename Transfer into Name (to store names for samples and animal).
  - Link Name to data source

* Where Submission takes place? could be a one to many Samples or Animals?

* ANIMAL:::ID:::Ramon_142436 is present two times in database how to fix it?
  Using google refine? For the moment, no duplicate can be inserted into database
