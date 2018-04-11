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

from django.db import models


class Animal(models.Model):
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


class ArConstraints(models.Model):
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


class ArDbtdescriptors(models.Model):
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


class ArDbtpolicies(models.Model):
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


class ArDbttables(models.Model):
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


class ArRoleConstraints(models.Model):
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


class ArRoleDbtpolicies(models.Model):
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


class ArRoleStpolicies(models.Model):
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


class ArRoles(models.Model):
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


class ArStpolicies(models.Model):
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


class ArUserRoles(models.Model):
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


class ArUsers(models.Model):
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


class ArUsersData(models.Model):
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


class Blobs(models.Model):
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


class BreedsSpecies(models.Model):
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


class Codes(models.Model):
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


class Contacts(models.Model):
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


class Event(models.Model):
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


class Inspool(models.Model):
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


class InspoolErr(models.Model):
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


class Languages(models.Model):
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


class LoadStat(models.Model):
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


class Locations(models.Model):
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


class Movements(models.Model):
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


class NewPest(models.Model):
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


class Nodes(models.Model):
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


class Protocols(models.Model):
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


class Sources(models.Model):
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


class StatusChanges(models.Model):
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


class Storage(models.Model):
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


class StorageHistory(models.Model):
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


class Targets(models.Model):
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


class Transfer(models.Model):
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


class Unit(models.Model):
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


class Vessels(models.Model):
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


class VesselsStorage(models.Model):
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
