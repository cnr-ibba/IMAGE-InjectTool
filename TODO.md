
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
  - deal with `ConnectionError(MaxRetryError('None: Max retries exceeded with url: /api/submissions/fcc2fec8-dd03-4cdf-b487-a4a2de737334/contents/samples (Caused by None)',),)`

```
Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/urllib3/connection.py", line 171, in _new_conn
    (self._dns_host, self.port), self.timeout, **extra_kw)
  File "/usr/local/lib/python3.6/site-packages/urllib3/util/connection.py", line 56, in create_connection
    for res in socket.getaddrinfo(host, port, family, socket.SOCK_STREAM):
  File "/usr/local/lib/python3.6/socket.py", line 745, in getaddrinfo
    for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
socket.gaierror: [Errno -2] Name or service not known

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py", line 600, in urlopen
    chunked=chunked)
  File "/usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py", line 343, in _make_request
    self._validate_conn(conn)
  File "/usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py", line 849, in _validate_conn
    conn.connect()
  File "/usr/local/lib/python3.6/site-packages/urllib3/connection.py", line 314, in connect
    conn = self._new_conn()
  File "/usr/local/lib/python3.6/site-packages/urllib3/connection.py", line 180, in _new_conn
    self, "Failed to establish a new connection: %s" % e)
urllib3.exceptions.NewConnectionError: <urllib3.connection.VerifiedHTTPSConnection object at 0x7f637fb0acc0>: Failed to establish a new connection: [Errno -2] Name or service not known

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/requests/adapters.py", line 445, in send
    timeout=timeout
  File "/usr/local/lib/python3.6/site-packages/urllib3/connectionpool.py", line 638, in urlopen
    _stacktrace=sys.exc_info()[2])
  File "/usr/local/lib/python3.6/site-packages/urllib3/util/retry.py", line 398, in increment
    raise MaxRetryError(_pool, url, error or ResponseError(cause))
urllib3.exceptions.MaxRetryError: HTTPSConnectionPool(host='submission-test.ebi.ac.uk', port=443): Max retries exceeded with url: /api/submissions/fcc2fec8-dd03-4cdf-b487-a4a2de737334/contents/samples (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f637fb0acc0>: Failed to establish a new connection: [Errno -2] Name or service not known',))

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/usr/local/lib/python3.6/site-packages/celery/app/trace.py", line 382, in trace_task
    R = retval = fun(*args, **kwargs)
  File "/usr/local/lib/python3.6/site-packages/celery/app/trace.py", line 641, in __protected_call__
    return self.run(*args, **kwargs)
  File "/var/uwsgi/image/biosample/tasks.py", line 94, in submit
    biosample_submission.create_sample(animal.to_biosample())
  File "/usr/local/lib/python3.6/site-packages/pyEBIrest/client.py", line 871, in create_sample
    response = self.post(link, payload=sample_data, headers=headers)
  File "/usr/local/lib/python3.6/site-packages/pyEBIrest/client.py", line 89, in post
    return requests.post(url, json=payload, headers=headers)
  File "/usr/local/lib/python3.6/site-packages/requests/api.py", line 112, in post
    return request('post', url, data=data, json=json, **kwargs)
  File "/usr/local/lib/python3.6/site-packages/requests/api.py", line 58, in request
    return session.request(method=method, url=url, **kwargs)
  File "/usr/local/lib/python3.6/site-packages/requests/sessions.py", line 512, in request
    resp = self.send(prep, **send_kwargs)
  File "/usr/local/lib/python3.6/site-packages/requests/sessions.py", line 622, in send
    r = adapter.send(request, **kwargs)
  File "/usr/local/lib/python3.6/site-packages/requests/adapters.py", line 513, in send
    raise ConnectionError(e, request=request)
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='submission-test.ebi.ac.uk', port=443): Max retries exceeded with url: /api/submissions/fcc2fec8-dd03-4cdf-b487-a4a2de737334/contents/samples (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f637fb0acc0>: Failed to establish a new connection: [Errno -2] Name or service not known',))
```
  - check `submission.status` before finalize

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

* Regarding data submission into biosample:
  - Mother and Father are not mandatory, for the moment; They should have unknown
    values for other data than cryoweb. When they are unknown, they shouldn't be
    exported.
  - return a default ontology for breed if non mapping occours
  - model other field types

* metadata rules
  - test against example `json` files, don't derive reference on the fly (it
    seems difficult update validation tests)

* Biosample manager user should do:
  - Monitor biosample submission to see if sample are validated or not (by team/user)
  - finalize submission after biosample validation occours.
  - ask for user intervention / notify success
  - fetch biosample id when submission is finalized and completed
  - after submission is completed, don't ask for the same submission

* proposed change for `Name` table (that can become a summary table a user will see)
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
    there's no difference from a web page, however, is only estetic
  - Add breadcrumb for pages
  - Add messages when views are called or code executed
  - Error handling (API?/String messages?)
  - Navbar for tools (zooma, dictionary tables, etc)?

* Issues relative to UID:
  - rename `image_app` application into `uid`?
  - `contenttypes` framework for `Name` relations?
  - `contenttypes` framework to model errors?

* create a `commons` library to store all common stuff

* regarding `pyEBIrest` library:
  - fetch submission by name: it is possible?
  - rename library?
