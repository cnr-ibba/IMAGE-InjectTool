# -*- coding: utf-8 -*-
"""
Created on Fri Jul  6 11:39:15 2018

@author: Paolo Cozzi <cozzi@ibba.cnr.it>
"""

from django.contrib import admin

from .models import Account, ManagedTeam

# Register your models here.
admin.site.register(Account)
admin.site.register(ManagedTeam)
