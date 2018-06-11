#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May  7 16:52:15 2018

@author: Paolo Cozzi <paolo.cozzi@ptp.it>

4.4.2 Uncommon App Modules (Two Scoops of Django)
A good name for placement of app-level settings. If there are enough of them
involved in an app, breaking them out into their own module can add clarity to
a project
"""

# main production server
ZOOMA_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate"

# test zooma server
ZOOMA_TEST = "http://snarf.ebi.ac.uk:8480/spot/zooma/v2/api/services/annotate"

# Ontologies list
# according to IMAGE ruleset, only these ontology libraries are allowed in the
# ruleset, so not search others. gaz is for countries
ONTOLOGIES = ['efo', 'uberon', 'obi', 'NCBITaxon', 'lbo', 'pato', 'gaz']

# taxonomy service
TAXONOMY_URL = "https://www.ebi.ac.uk/ena/data/taxonomy/v1/taxon/"
