# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create,
#     modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field
# names.
from __future__ import unicode_literals
import logging

from django.db import models, connections


# Get an instance of a logger
logger = logging.getLogger(__name__)


# Adding a classmethod to Category if you want to enable truncate
# https://books.agiliq.com/projects/django-orm-cookbook/en/latest/truncate.html
class Base():
    "Base class for cryoweb tables"

    @classmethod
    def truncate(cls):
        """Truncate table"""

        # Django.db.connections is a dictionary-like object that allows you
        # to retrieve a specific connection using its alias
        with connections["cryoweb"].cursor() as cursor:
            statement = "TRUNCATE TABLE {0} CASCADE".format(
                cls._meta.db_table)
            logger.debug(statement)
            cursor.execute(statement)


class Animal(Base, models.Model):
    db_animal = models.IntegerField(unique=True, blank=True, null=True)
    db_sire = models.IntegerField(blank=True, null=True)
    db_dam = models.IntegerField(blank=True, null=True)
    db_sex = models.IntegerField(blank=True, null=True)
    db_breed = models.IntegerField(blank=True, null=True)
    db_species = models.IntegerField(blank=True, null=True)
    birth_dt = models.DateField(blank=True, null=True)
    birth_year = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    image_id = models.IntegerField(blank=True, null=True)
    db_org = models.IntegerField(blank=True, null=True)
    la_rep = models.TextField(blank=True, null=True)
    la_rep_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()
    db_hybrid = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    file_id = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'animal'


class ArConstraints(Base, models.Model):
    cons_id = models.IntegerField(unique=True, blank=True, null=True)
    cons_name = models.TextField(blank=True, null=True)
    cons_type = models.TextField(blank=True, null=True)
    cons_desc = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_constraints'
        unique_together = (('cons_name', 'cons_type'),)


class ArDbtdescriptors(Base, models.Model):
    descriptor_id = models.IntegerField(unique=True, blank=True, null=True)
    descriptor_name = models.TextField(blank=True, null=True)
    descriptor_value = models.TextField(blank=True, null=True)
    descriptor_desc = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_dbtdescriptors'
        unique_together = (('descriptor_name', 'descriptor_value'),)


class ArDbtpolicies(Base, models.Model):
    dbtpolicy_id = models.IntegerField(unique=True, blank=True, null=True)
    action_id = models.IntegerField(blank=True, null=True)
    table_id = models.IntegerField(blank=True, null=True)
    descriptor_id = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_dbtpolicies'
        unique_together = (('action_id', 'table_id', 'descriptor_id'),)


class ArDbttables(Base, models.Model):
    table_id = models.IntegerField(unique=True, blank=True, null=True)
    table_name = models.TextField(blank=True, null=True)
    table_columns = models.TextField(blank=True, null=True)
    table_desc = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_dbttables'
        unique_together = (('table_name', 'table_columns'),)


class ArRoleConstraints(Base, models.Model):
    cons_id = models.IntegerField(blank=True, null=True)
    first_role_id = models.IntegerField(blank=True, null=True)
    second_role_id = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_role_constraints'
        unique_together = (('cons_id', 'first_role_id', 'second_role_id'),)


class ArRoleDbtpolicies(Base, models.Model):
    role_id = models.IntegerField(blank=True, null=True)
    dbtpolicy_id = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_role_dbtpolicies'
        unique_together = (('role_id', 'dbtpolicy_id'),)


class ArRoleStpolicies(Base, models.Model):
    role_id = models.IntegerField(blank=True, null=True)
    stpolicy_id = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_role_stpolicies'
        unique_together = (('role_id', 'stpolicy_id'),)


class ArRoles(Base, models.Model):
    role_id = models.IntegerField(unique=True, blank=True, null=True)
    role_name = models.TextField(blank=True, null=True)
    role_long_name = models.TextField(blank=True, null=True)
    role_type = models.TextField(blank=True, null=True)
    role_subset = models.TextField(blank=True, null=True)
    role_descr = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_roles'
        unique_together = (('role_name', 'role_type'),)


class ArStpolicies(Base, models.Model):
    stpolicy_id = models.IntegerField(unique=True, blank=True, null=True)
    stpolicy_name = models.TextField(blank=True, null=True)
    stpolicy_type = models.TextField(blank=True, null=True)
    stpolicy_desc = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_stpolicies'
        unique_together = (('stpolicy_name', 'stpolicy_type'),)


class ArUserRoles(Base, models.Model):
    user_id = models.IntegerField(blank=True, null=True)
    role_id = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_user_roles'
        unique_together = (('user_id', 'role_id'),)


class ArUsers(Base, models.Model):
    user_id = models.IntegerField(unique=True, blank=True, null=True)
    user_login = models.TextField(unique=True, blank=True, null=True)
    user_password = models.TextField(blank=True, null=True)
    user_language_id = models.IntegerField(blank=True, null=True)
    user_marker = models.TextField(blank=True, null=True)
    user_disabled = models.NullBooleanField()
    user_status = models.NullBooleanField()
    user_last_login = models.DateTimeField(blank=True, null=True)
    user_last_activ_time = models.TimeField(blank=True, null=True)
    user_session_id = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_users'


class ArUsersData(Base, models.Model):
    user_id = models.IntegerField(unique=True, blank=True, null=True)
    user_first_name = models.TextField(blank=True, null=True)
    user_second_name = models.TextField(blank=True, null=True)
    user_institution = models.TextField(blank=True, null=True)
    user_email = models.TextField(blank=True, null=True)
    user_country = models.TextField(blank=True, null=True)
    user_street = models.TextField(blank=True, null=True)
    user_town = models.TextField(blank=True, null=True)
    user_zip = models.TextField(blank=True, null=True)
    user_other_info = models.TextField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    creation_dt = models.DateTimeField(blank=True, null=True)
    creation_user = models.TextField(blank=True, null=True)
    end_dt = models.DateTimeField(blank=True, null=True)
    end_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'ar_users_data'


class Blobs(Base, models.Model):
    blob_id = models.IntegerField(blank=True, null=True)
    blob = models.BinaryField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()
    db_mimetype = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'blobs'


class BreedsSpecies(Base, models.Model):
    breed_id = models.IntegerField(unique=True, blank=True, null=True)
    db_breed = models.IntegerField(blank=True, null=True)
    db_species = models.IntegerField(blank=True, null=True)
    efabis_mcname = models.TextField(blank=True, null=True)
    efabis_species = models.TextField(blank=True, null=True)
    efabis_country = models.TextField(blank=True, null=True)
    efabis_lang = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'breeds_species'
        unique_together = (('db_species', 'db_breed'),)


class Codes(Base, models.Model):
    ext_code = models.TextField(blank=True, null=True)
    # Field renamed because it was a Python reserved word.
    class_field = models.TextField(db_column='class', blank=True, null=True)
    db_code = models.IntegerField(unique=True, blank=True, null=True)
    short_name = models.TextField(blank=True, null=True)
    long_name = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'codes'
        unique_together = (
                ('class_field', 'ext_code', 'closing_dt'),
                ('class_field', 'ext_code'),)


class Contacts(Base, models.Model):
    db_contact = models.IntegerField(unique=True, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    salutation = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    second_name = models.TextField(blank=True, null=True)
    third_name = models.TextField(blank=True, null=True)
    birth_dt = models.DateField(blank=True, null=True)
    db_language = models.IntegerField(blank=True, null=True)
    street = models.TextField(blank=True, null=True)
    zip = models.TextField(blank=True, null=True)
    town = models.TextField(blank=True, null=True)
    db_country = models.IntegerField(blank=True, null=True)
    label = models.TextField(blank=True, null=True)
    phone = models.TextField(blank=True, null=True)
    phone2 = models.TextField(blank=True, null=True)
    fax = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)
    bank_name = models.TextField(blank=True, null=True)
    bank_zip = models.TextField(blank=True, null=True)
    account = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contacts'


class Event(Base, models.Model):
    event_id = models.IntegerField(blank=True, null=True)
    db_event_type = models.IntegerField(blank=True, null=True)
    db_sampler = models.IntegerField(blank=True, null=True)
    event_dt = models.DateField(blank=True, null=True)
    db_location = models.IntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'event'
        unique_together = (
                ('event_id', 'db_event_type', 'db_location', 'event_dt'),)


class Inspool(Base, models.Model):
    ds = models.TextField(blank=True, null=True)
    record_seq = models.IntegerField(unique=True, blank=True, null=True)
    in_date = models.DateField(blank=True, null=True)
    ext_unit = models.IntegerField(blank=True, null=True)
    proc_dt = models.DateField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    record = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'inspool'


class InspoolErr(Base, models.Model):
    record_seq = models.IntegerField(blank=True, null=True)
    err_type = models.TextField(blank=True, null=True)
    action = models.TextField(blank=True, null=True)
    dbtable = models.TextField(blank=True, null=True)
    dbcol = models.TextField(blank=True, null=True)
    err_source = models.TextField(blank=True, null=True)
    short_msg = models.TextField(blank=True, null=True)
    long_msg = models.TextField(blank=True, null=True)
    ext_col = models.TextField(blank=True, null=True)
    ext_val = models.TextField(blank=True, null=True)
    mod_val = models.TextField(blank=True, null=True)
    comp_val = models.TextField(blank=True, null=True)
    target_col = models.TextField(blank=True, null=True)
    ds = models.TextField(blank=True, null=True)
    ext_unit = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    err_dt = models.DateTimeField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'inspool_err'


class Languages(Base, models.Model):
    lang_id = models.IntegerField(unique=True, blank=True, null=True)
    iso_lang = models.TextField(unique=True, blank=True, null=True)
    lang = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    creation_dt = models.DateTimeField(blank=True, null=True)
    creation_user = models.TextField(blank=True, null=True)
    end_dt = models.DateTimeField(blank=True, null=True)
    end_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'languages'


class LoadStat(Base, models.Model):
    ds = models.TextField(blank=True, null=True)
    job_start = models.DateTimeField(blank=True, null=True)
    job_end = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    rec_tot_no = models.SmallIntegerField(blank=True, null=True)
    rec_err_no = models.SmallIntegerField(blank=True, null=True)
    rec_ok_no = models.SmallIntegerField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'load_stat'


class Locations(Base, models.Model):
    db_animal = models.IntegerField(blank=True, null=True)
    db_location = models.IntegerField(blank=True, null=True)
    entry_dt = models.DateField(blank=True, null=True)
    db_entry_action = models.IntegerField(blank=True, null=True)
    exit_dt = models.DateField(blank=True, null=True)
    db_exit_action = models.IntegerField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'locations'


class Movements(Base, models.Model):
    movements_id = models.IntegerField(unique=True, blank=True, null=True)
    from_storage = models.IntegerField(blank=True, null=True)
    to_storage = models.IntegerField(blank=True, null=True)
    no_units = models.SmallIntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    action_dt = models.DateTimeField(blank=True, null=True)
    action_type = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movements'


class NewPest(Base, models.Model):
    # Field renamed because it was a Python reserved word.
    class_field = models.TextField(db_column='class', blank=True, null=True)
    key = models.TextField(blank=True, null=True)
    trait = models.TextField(blank=True, null=True)
    estimator = models.FloatField(blank=True, null=True)
    pev = models.FloatField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'new_pest'
        unique_together = (('class_field', 'key', 'trait'),)


class Nodes(Base, models.Model):
    nodename = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'nodes'


class Protocols(Base, models.Model):
    protocol_id = models.IntegerField(blank=True, null=True)
    protocol_name = models.TextField(blank=True, null=True)
    db_material_type = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'protocols'


class Sources(Base, models.Model):
    source = models.TextField(blank=True, null=True)
    tablename = models.TextField(blank=True, null=True)
    # Field renamed because it was a Python reserved word.
    class_field = models.TextField(db_column='class', blank=True, null=True)
    columnnames = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'sources'


class StatusChanges(Base, models.Model):
    status_change_id = models.IntegerField(blank=True, null=True)
    vessels_storage_id = models.IntegerField(blank=True, null=True)
    old_status = models.IntegerField(blank=True, null=True)
    new_status = models.IntegerField(blank=True, null=True)
    action_dt = models.DateTimeField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'status_changes'


class Storage(Base, models.Model):
    storage_id = models.IntegerField(unique=True, blank=True, null=True)
    storage_name = models.TextField(blank=True, null=True)
    parent_id = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'storage'


class StorageHistory(Base, models.Model):
    storage_id = models.IntegerField(blank=True, null=True)
    old_storage_name = models.TextField(blank=True, null=True)
    new_storage_name = models.TextField(blank=True, null=True)
    old_parent_id = models.IntegerField(blank=True, null=True)
    new_parent_id = models.IntegerField(blank=True, null=True)
    old_comment = models.TextField(blank=True, null=True)
    new_comment = models.TextField(blank=True, null=True)
    action_type = models.TextField(blank=True, null=True)
    action_date = models.DateField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'storage_history'


class Targets(Base, models.Model):
    target = models.TextField(blank=True, null=True)
    tablename = models.TextField(blank=True, null=True)
    # Field renamed because it was a Python reserved word.
    class_field = models.TextField(db_column='class', blank=True, null=True)
    columnnames = models.TextField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'targets'


class Transfer(Base, models.Model):
    db_animal = models.IntegerField(blank=True, null=True)
    ext_animal = models.TextField(blank=True, null=True)
    db_unit = models.IntegerField(blank=True, null=True)
    id_set = models.IntegerField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'transfer'
        unique_together = (('db_unit', 'ext_animal'),)


class Unit(Base, models.Model):
    db_unit = models.IntegerField(unique=True, blank=True, null=True)
    ext_unit = models.TextField(blank=True, null=True)
    ext_id = models.TextField(blank=True, null=True)
    db_contact = models.IntegerField(blank=True, null=True)
    db_member = models.IntegerField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'unit'
        unique_together = (
                ('ext_unit', 'ext_id'),
                ('ext_unit', 'ext_id', 'closing_dt'),)


class Vessels(Base, models.Model):
    db_vessel = models.IntegerField(unique=True, blank=True, null=True)
    ext_vessel = models.TextField(unique=True, blank=True, null=True)
    db_animal = models.IntegerField(blank=True, null=True)
    protocol_id = models.IntegerField(blank=True, null=True)
    production_dt = models.DateField(blank=True, null=True)
    freezing_dt = models.DateField(blank=True, null=True)
    db_vessel_type = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)
    db_contributor = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vessels'


class VesselsStorage(Base, models.Model):
    vessels_storage_id = models.IntegerField(blank=True, null=True)
    db_vessel = models.IntegerField(blank=True, null=True)
    storage_id = models.IntegerField(blank=True, null=True)
    no_units = models.SmallIntegerField(blank=True, null=True)
    db_status = models.IntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vessels_storage'
        unique_together = (('db_vessel', 'storage_id', 'db_status'),)


# --- Useful Views
# https://blog.rescale.com/using-database-views-in-django-orm/
class VBreedsSpecies(models.Model):
    v_guid = models.BigIntegerField(primary_key=True)
    breed_id = models.IntegerField(unique=True, blank=True, null=True)
    db_breed = models.IntegerField(blank=True, null=True)
    ext_breed = models.TextField(blank=True, null=True)
    db_species = models.IntegerField(blank=True, null=True)
    ext_species = models.TextField(blank=True, null=True)
    efabis_mcname = models.TextField(blank=True, null=True)
    efabis_species = models.TextField(blank=True, null=True)
    efabis_country = models.TextField(blank=True, null=True)
    efabis_lang = models.TextField(blank=True, null=True)
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    dirty = models.NullBooleanField()
    guid = models.BigIntegerField(primary_key=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    synch = models.NullBooleanField()
    version = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_breeds_species'
        verbose_name = "Breeds Species View"

    def __str__(self):
        return "{breed} ({specie})".format(
                breed=self.efabis_mcname,
                specie=self.ext_species)

    @classmethod
    def get_all_species(cls):
        # get all distinct objects
        queryset = cls.objects.distinct('ext_species').order_by(
            'ext_species')

        return [entry.ext_species for entry in queryset]


class VTransfer(models.Model):
    v_guid = models.BigIntegerField(primary_key=True)
    db_animal = models.IntegerField(unique=True, blank=True, null=True)
    ext_animal = models.TextField(blank=True, null=True)
    db_unit = models.IntegerField(blank=True, null=True)
    ext_unit = models.TextField(blank=True, null=True)
    id_set = models.IntegerField(blank=True, null=True)
    ext_id_set = models.TextField(blank=True, null=True)
    opening_dt = models.DateField(blank=True, null=True)
    closing_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'v_transfer'
        verbose_name = "Transfer View"

    def __str__(self):
        return self.get_fullname()

    def get_fullname(self):
        """No changes in names object"""

        return ":::".join([self.ext_unit, self.ext_animal])


class VAnimal(models.Model):
    v_guid = models.BigIntegerField(primary_key=True)
    db_animal = models.IntegerField(unique=True, blank=True, null=True)
    ext_animal = models.TextField(blank=True, null=True)
    db_sire = models.IntegerField(blank=True, null=True)
    ext_sire = models.TextField(blank=True, null=True)
    db_dam = models.IntegerField(blank=True, null=True)
    ext_dam = models.TextField(blank=True, null=True)
    db_sex = models.IntegerField(blank=True, null=True)
    ext_sex = models.TextField(blank=True, null=True)
    db_breed = models.IntegerField(blank=True, null=True)
    ext_breed = models.TextField(blank=True, null=True)
    db_species = models.IntegerField(blank=True, null=True)
    ext_species = models.TextField(blank=True, null=True)
    birth_dt = models.DateField(blank=True, null=True)
    birth_year = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    image_id = models.IntegerField(blank=True, null=True)
    db_org = models.IntegerField(blank=True, null=True)
    ext_org = models.TextField(blank=True, null=True)
    la_rep = models.TextField(blank=True, null=True)
    la_rep_dt = models.DateField(blank=True, null=True)
    last_change_dt = models.DateTimeField(blank=True, null=True)
    last_change_user = models.TextField(blank=True, null=True)
    dirty = models.NullBooleanField()
    chk_lvl = models.SmallIntegerField(blank=True, null=True)
    guid = models.IntegerField(primary_key=True)
    owner = models.TextField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    synch = models.NullBooleanField()
    db_hybrid = models.IntegerField(blank=True, null=True)
    ext_hybrid = models.TextField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'v_animal'
        verbose_name = "Animal View"

    def efabis_mcname(self):
        "Retrieve efabis mcname from breed_species table"

        # HINT: is this unique in VBreedsSpecies?
        entry = VBreedsSpecies.objects.get(db_breed=self.db_breed)

        return entry.efabis_mcname


# --- Custom functions

# A method to truncate database
def truncate_database():
    """Truncate cryoweb database"""

    logger.warning("Truncating ALL cryoweb tables")

    # call each class and truncate its table by calling truncate method
    Animal.truncate()
    ArConstraints.truncate()
    ArDbtdescriptors.truncate()
    ArDbtpolicies.truncate()
    ArDbttables.truncate()
    ArRoleConstraints.truncate()
    ArRoleDbtpolicies.truncate()
    ArRoleStpolicies.truncate()
    ArRoles.truncate()
    ArStpolicies.truncate()
    ArUserRoles.truncate()
    ArUsers.truncate()
    ArUsersData.truncate()
    Blobs.truncate()
    BreedsSpecies.truncate()
    Codes.truncate()
    Contacts.truncate()
    Event.truncate()
    Inspool.truncate()
    InspoolErr.truncate()
    Languages.truncate()
    LoadStat.truncate()
    Locations.truncate()
    Movements.truncate()
    NewPest.truncate()
    Nodes.truncate()
    Protocols.truncate()
    Sources.truncate()
    StatusChanges.truncate()
    Storage.truncate()
    StorageHistory.truncate()
    Targets.truncate()
    Transfer.truncate()
    Unit.truncate()
    # VBreedsSpecies  # it's a view, not a table
    Vessels.truncate()
    VesselsStorage.truncate()

    logger.warning("All cryoweb tables were truncated")


# A method to discover is cryoweb has data or not
def db_has_data():
    # Test only tables I read data to fill UID
    if (BreedsSpecies.objects.exists() or Transfer.objects.exists() or
            Animal.objects.exists() or Protocols.objects.exists() or
            Vessels.objects.exists()):
        return True
