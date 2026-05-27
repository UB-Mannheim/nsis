#!/bin/bash
# -*- coding: utf-8 -*-
# =============================================================================
# convert_gnd_sachbegriffe_to_csv.sh
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

catmandu convert MARC --type XML to CSV --sep_char ";" --fields "id,gnd,subject,heading,alt_term,definition" --fix 'marc_map(001,id); marc_map(024a,gnd, -join => ", "); marc_map(065a,subject, -join => ", "); marc_map(150a,heading, -join => ", "); marc_map(450a,alt_term, -join => ", "); marc_map(677a,definition, -join => ", ");' < authorities-gnd-sachbegriffe_dnbmarc.mrc.xml > gnd-sachbegriffe.csv
