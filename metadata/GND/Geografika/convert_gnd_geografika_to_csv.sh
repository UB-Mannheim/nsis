#!/bin/bash
# -*- coding: utf-8 -*-
# =============================================================================
# convert_gnd_geografika_to_csv.sh
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

catmandu convert MARC --type XML to CSV --sep_char ";" --fields "id,gnd,heading,notes" --fix 'marc_map(001,id); marc_map(024a,gnd, -join => ", "); marc_map(151a,heading, -join => ", "); marc_map(678b,notes, -join => ", ");' < authorities-gnd-geografika_dnbmarc.mrc.xml > gnd-geografika.csv
