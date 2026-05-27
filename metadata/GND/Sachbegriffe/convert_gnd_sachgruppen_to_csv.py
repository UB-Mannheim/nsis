# -*- coding: utf-8 -*-
# =============================================================================
# convert_gnd_sachgruppen_to_csv.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

import rdflib
import csv
# from rdflib import Namespace

def turtle_to_csv(input_file, output_file):
    # Create a new RDF graph
    g = rdflib.Graph()

    # Parse the turtle file
    g.parse(input_file, format='turtle')

    # Define namespaces
    # SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')

    # SPARQL query to get the required properties
    query = """
    SELECT ?notation ?prefLabel_en ?prefLabel_de
    WHERE {
        ?subject skos:notation ?notation .
        ?subject skos:prefLabel ?prefLabel_en .
        ?subject skos:prefLabel ?prefLabel_de .
        FILTER(LANG(?prefLabel_en) = 'en')
        FILTER(LANG(?prefLabel_de) = 'de')
    }
    ORDER BY ?notation
    """

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')

        # Write header
        writer.writerow(['notation', 'prefLabel@en', 'prefLabel@de'])

        # Execute query and write results
        for row in g.query(query):
            writer.writerow([
                row.notation,  # type: ignore[attr-defined]
                row.prefLabel_en,  # type: ignore[attr-defined]
                row.prefLabel_de  # type: ignore[attr-defined]
            ])

if __name__ == "__main__":
    input_file = "gnd-sachgruppen.ttl"
    output_file = "gnd-sachgruppen.csv"

    try:
        turtle_to_csv(input_file, output_file)
        print(f"Conversion completed. Output saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
