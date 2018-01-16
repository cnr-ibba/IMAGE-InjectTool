
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
  - sqlalchemy serializer: https://stackoverflow.com/questions/2786664/how-to-create-and-restore-a-backup-from-sqlalchemy
    can be useful?

* Remove **all** passwords in repository. Create an environment file for passwords

* DDL for imported_from_cryoweb

* Django was updated to 2.0. Urls changed!!! Need to test if we can migrate to newer
  django release? - This version However is a LTS version - not so important a the moment

* get_json_1 need to be modified
  - The json extracted from database is different from exampleJSONfromUIDafterEnhancement.json
    need to add the following sections:
    * submission
    * person
    * organization
    * species
  - check that attrib in sample, breed animals correspond (doesn't seem)
  - ontologies need to be already present in JSON

* Where JSON is in the whole pipeline? Is requested to fill data?

* update documentation:
  - need to explain how to generate database
  - need to explain how define permissions

* Distribution: Inject tool is inside or infrastructure? or a user need to run its
  own instance

* Data export: How data needs to be exported? how IMAGE-metadata works?
  - I need to export a .xlsx table with a sheet for each category of IMAGE-metadata?
  - Should I do the validation? or it can be external? in such case, what external tool
    use? FAANG?

* Suppose to fill up ontlogy terms in some way (or data useful to many Inject-Tool
  installation). Common data need to be in a common database? Or the should be a copy
  of them in each database?

* Openrefine integration:
  - need to place Openrefine in docker compose?
  - can I place data directly in OpenRefine? I need to download data from Inject-Tool
    then load into OpenRefine? when data are ready, I need to place them back to Inject-Tool?

* Should the columns exported from Inject-Tool be the same of IMAGE-metadata? check
  column consistencies.

* Usability: remove unuseful or danger links from home page: define a more friendly
  interface to users.

* Unittest?
