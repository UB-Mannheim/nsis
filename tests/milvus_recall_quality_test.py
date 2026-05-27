# -*- coding: utf-8 -*-
# =============================================================================
# milvus_recall_quality_test.py
# =============================================================================
#
# Author:      Dorian Grosch
# E-Mail:      dorian.grosch@sbb.spk-berlin.de
# Institution: Staatsbibliothek zu Berlin
#
# =============================================================================

"""
Milvus Search Recall Quality Test Suite

This module tests the recall quality of Milvus vector searches using the LLM-based
reranker as a proxy for ground truth relevance judgment.

IMPORTANT: This test needs to be run when API is OFFLINE.

Architecture:
    User Query → Facette Extraction → Vector Search (Milvus) → LLM Reranker → Final Results

Supported Databases:
    - bk: Basisklassifikation (coarse classification, ~2,100 classes)
    - gnd-saz: GND Sachbegriffe (fine-grained subject headings, ~205,000 entries)
    - gnd-geo: GND Geografika (geographic names and locations, ~335,000 entries)

Usage Examples:
    # Basic tests for each database
    uv run tests/milvus_recall_quality_test.py --database bk --output bk_report.json
    uv run tests/milvus_recall_quality_test.py --database gnd-saz --output gnd_saz_report.json
    uv run tests/milvus_recall_quality_test.py --database gnd-geo --output gnd_geo_report.json

    # NProbe parameter sweep (test different search granularity values)
    uv run tests/milvus_recall_quality_test.py --database bk --nprobe 1 --nprobe 10 --nprobe 50 --nprobe 100
    uv run tests/milvus_recall_quality_test.py --database gnd-saz --nprobe 50 --nprobe 100 --nprobe 500 --nprobe 1000
    uv run tests/milvus_recall_quality_test.py --database gnd-geo --nprobe 32 --nprobe 64 --nprobe 128 --nprobe 256

    # Top-K scaling test (evaluate performance with different result counts)
    uv run tests/milvus_recall_quality_test.py --database bk --top-k 4 --top-k 8 --top-k 16

    # Run all databases
    uv run tests/milvus_recall_quality_test.py --database all

    # Compare against baseline
    uv run tests/milvus_recall_quality_test.py --baseline baseline.json --output comparison.json

    # Pytest integration
    pytest tests/milvus_recall_quality_test.py -v
    pytest tests/milvus_recall_quality_test.py -v -k bk
    pytest tests/milvus_recall_quality_test.py -v -k gnd_geo
"""

import asyncio
import json
import time
import argparse
import pytest
import sys

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Add project root to path to enable imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import core components
from core.inference.reranker import rerank_search_results # noqa: E402
from app.services.milvus_service import MilvusService  # noqa: E402
from app.config import settings # noqa: E402


# =============================================================================
# TEST QUERY SETS
# =============================================================================

BK_TEST_QUERIES = {
    # === Group 01: Bibliography, Reference Works ===
    "01_Bibliography": [
        "Bibliographische Kontrolle und bibliothekarische Ordnung",
        "Universalbibliographien und nationale Verzeichnisse",
        "Spezialbibliographien für Fachgebiete",
        "Enzyklopädien und allgemeine Nachschlagewerke",
        "Adressbücher und Körperschaftsverzeichnisse",
        "Biographische Wörterbücher und Lexika",
        "Allgemeine Sammelwerke und Anthologien",
    ],

    # === Group 02: Science, Culture, Research ===
    "02_Science_Culture": [
        "Wissenschaftstheorie und Methodologie",
        "Geschichte der Wissenschaft und Geistesgeschichte",
        "Wissenschaftssoziologie und Erkenntnissoziologie",
        "Wissenschaftspolitik und Forschungsförderung",
        "Museologie und Museumspädagogik",
        "Futurologie und Zukunftsforschung",
        "Esoterik und Okkultismus",
        "Freimaurerei und geheime Gesellschaften",
    ],

    # === Group 05: Communication, Media ===
    "05_Communication": [
        "Kommunikationstheorie und Zeichenprozesse",
        "Massenkommunikation und Medienwissenschaft",
        "Journalismus und Pressewesen",
        "Rundfunk und Fernsehen",
        "Filmwissenschaft und Videoproduktion",
        "Neue elektronische Medien und Social Media",
        "Öffentliche Meinung und Propagandaforschung",
        "Telekommunikation und Netzwerktechnik",
    ],

    # === Group 06: Information, Documentation, Library ===
    "06_Information": [
        "Bibliothekswesen und Dokumentation",
        "Bibliotheksgeschichte und Handschriftenkunde",
        "Archivwesen und Aktenkunde",
        "Informationssysteme und Datenbanken",
        "Information Retrieval und Suchmaschinen",
        "Buchproduktion und Verlagswesen",
        "Bibliotheksautomatisierung und Digitalisierung",
    ],

    # === Group 08: Philosophy ===
    "08_Philosophy": [
        "Philosophie der Antike und Griechische Philosophie",
        "Mittelalterliche Philosophie und Scholastik",
        "Erkenntnistheorie und Metaphysik",
        "Ethik und Moralphilosophie",
        "Logik und Sprachphilosophie",
        "Politische Philosophie und Sozialphilosophie",
        "Religionsphilosophie und Ästhetik",
        "Naturphilosophie und Kulturphilosophie",
    ],

    # === Group 10: Humanities ===
    "10_Humanities": [
        "Geisteswissenschaften und Kulturwissenschaften",
        "Methoden der geisteswissenschaftlichen Forschung",
        "Kulturtheorie und Interkulturalität",
    ],

    # === Group 11: Theology, Religion ===
    "11_Theology": [
        "Vergleichende Religionswissenschaft",
        "Bibelwissenschaft und Exegese",
        "Kirchengeschichte und Dogmengeschichte",
        "Systematische Theologie und Dogmatik",
        "Praktische Theologie und Seelsorge",
        "Judentum und Israels Geschichte",
        "Islam und muslimische Theologie",
        "Hinduismus und indische Religionen",
        "Buddhismus und fernöstliche Philosophie",
    ],

    # === Group 15: History ===
    "15_History": [
        "Alte Geschichte und Antike",
        "Mittelalterliche Geschichte",
        "Frühneuzeit und Reformation",
        "Neuere Geschichte und Zeitgeschichte",
        "Wirtschaftsgeschichte und Sozialgeschichte",
        "Kulturgeschichte und Geistesgeschichte",
        "Technikgeschichte und Wissenschaftsgeschichte",
    ],

    # === Group 17: Language, Literature ===
    "17_Language_Literature": [
        "Sprachwissenschaft und Phonologie",
        "Germanistische Linguistik und Germanistik",
        "Literaturgattungen und Stilistik",
        "Textkritik und Editionswissenschaft",
        "Rhetorik und Argumentationstheorie",
        "Pragmatik und Diskursanalyse",
        "Mathematische Linguistik und Computerlinguistik",
    ],

    # === Group 20: Art ===
    "20_Art": [
        "Kunstgeschichte und Epochen",
        "Bildende Kunst und Malerei",
        "Skulptur und Plastik",
        "Grafik und Zeichnung",
        "Architektur und Baukunst",
    ],

    # === Group 24: Theater, Film, Music ===
    "24_Performing_Arts": [
        "Theaterwissenschaft und Dramenanalyse",
        "Filmtheorie und Filmsemiotik",
        "Musikwissenschaft und Musikgeschichte",
        "Musiktheorie und Komposition",
        "Filmgeschichte und Dokumentarfilm",
    ],

    # === Group 30-33: Natural Sciences, Mathematics, Physics ===
    "30_33_Sciences": [
        "Mathematik und Algebra",
        "Geometrie und Topologie",
        "Analysis und Infinitesimalrechnung",
        "Physik und Mechanik",
        "Optik und Wellenlehre",
        "Chemie und Stoffumwandlungen",
        "Mathematische Statistik und Wahrscheinlichkeitsrechnung",
    ],

    # === Group 35-39: Earth Sciences, Geography, Astronomy ===
    "35_39_Earth_Space": [
        "Geographie und Kartographie",
        "Geologie und Mineralogie",
        "Meteorologie und Klimatologie",
        "Astronomie und Raumfahrt",
        "Umweltforschung und Ökologie",
        "Geophysik und Geochemie",
    ],

    # === Group 42-46: Biology, Medicine ===
    "42_46_Bio_Medicine": [
        "Molekularbiologie und Genetik",
        "Botanik und Pflanzensoziologie",
        "Zoologie und Tierphysiologie",
        "Ökologie und Umweltschutz",
        "Anatomie und Physiologie des Menschen",
        "Innere Medizin und Kardiologie",
        "Chirurgie und Anästhesiologie",
        "Psychiatrie und Psychotherapie",
        "Pharmakologie und Toxikologie",
        "Dermatologie und Venerologie",
    ],

    # === Group 50-58: Technology, Engineering ===
    "50_58_Technology": [
        "Maschinenbau und Fertigungstechnik",
        "Elektrotechnik und Nachrichtentechnik",
        "Bauwesen und Architektur",
        "Chemische Verfahrenstechnik",
        "Umwelttechnik und Recycling",
        "Kraftfahrzeugtechnik und Verkehr",
        "Bergbau und Hüttenwesen",
        "Energietechnik und Kraftwerkstechnik",
    ],

    # === Group 70-79: Social Sciences ===
    "70_79_Social_Sciences": [
        "Soziologie und Sozialstruktur",
        "Politikwissenschaft und Politische Theorie",
        "Volkswirtschaft und Betriebswirtschaft",
        "Rechtswissenschaft und Jurisprudenz",
        "Verwaltungswissenschaft und öffentliche Verwaltung",
        "Ethnologie und Kulturanthropologie",
        "Psychologie und Entwicklungspsychologie",
        "Pädagogik und Bildungsforschung",
        "Sozialarbeit und Sozialpädagogik",
    ],

    # === Group 80-89: Law, Economics, Politics ===
    "80_89_Law_Politics": [
        "Verfassungsrecht und Grundrechte",
        "Strafrecht und Strafprozess",
        "Bürgerliches Recht und Schuldrecht",
        "Internationales Recht und Völkerrecht",
        "Wirtschaftspolitik und Konjunkturtheorie",
        "Internationale Beziehungen und Diplomatie",
        "Finanzwissenschaft und Steuerrecht",
    ],

    # === Group 90-99: Miscellaneous ===
    "90_99_Misc": [
        "Sportwissenschaft und Trainingsmethoden",
        "Hauswirtschaft und Ernährungswissenschaft",
        "Landwirtschaft und Forstwirtschaft",
        "Fotografie und Medienproduktion",
        "Industrielle Chemie und Materialwissenschaft",
        "Tiermedizin und Veterinärmedizin",
    ],
}

GND_TEST_QUERIES = {
    # === Mathematics, Natural Sciences (Subject codes: 2x, 28) ===
    "Mathematics": [
        "Mathematik", "Algebra", "Geometrie", "Analysis", "Stochastik",
        "Topologie", "Zahlentheorie", "Kombinatorik", "Mathematische Logik",
        "Näherungsrechnung", "Natürliche Zahl", "Abbildung", "Abakus",
    ],
    "Physics": [
        "Mechanik", "Optik", "Thermodynamik", "Quantenphysik", "Atomphysik",
        "Kernphysik", "Teilchenphysik", "Festkörperphysik", "Elektrodynamik",
        "Atommodell", "Atomphysiker", "Navier-Stokes-Gleichung",
    ],
    "Chemistry": [
        "Organische Chemie", "Anorganische Chemie", "Biochemie", "Analytische Chemie",
        "Physikalische Chemie", "Makromolekulare Chemie", "Lebensmittelchemie",
        "Naturstoff", "Chemische Reaktion", "Katalysator",
    ],
    "Biology": [
        "Molekularbiologie", "Genetik", "Ökologie", "Botanik", "Zoologie",
        "Mikrobiologie", "Bioinformatik", "Zellbiologie", "Entwicklungsbiologie",
        "Aussterben", "Evolution", "Nervensystem", "Atmung",
    ],

    # === Technology, Engineering (Subject codes: 3x) ===
    "Engineering": [
        "Maschinenbau", "Elektrotechnik", "Bauingenieurwesen", "Verfahrenstechnik",
        "Umwelttechnik", "Energietechnik", "Werkstoffkunde", "Messtechnik",
        "Aufbereitung", "Austenitischer Stahl", "Abdichtung",
    ],
    "Automotive": [
        "Kraftfahrzeugtechnik", "Verbrennungsmotor", "Getriebe", "Fahrwerk",
        "KFZ-Elektronik", "Alternative Antriebe", "Verkehrstechnik",
        "Abgaskatalysator", "Abgasreinigung", "Aufladung",
    ],
    "IT_Computing": [
        "Informatik", "Datenverarbeitung", "Softwareentwicklung", "Algorithmen",
        "Künstliche Intelligenz", "Machine Learning", "Cloud Computing", "Cybersicherheit",
        "Attributierte Grammatik", "Natürliche Sprache", "Nachrichtentechnik",
    ],

    # === Medicine, Health (Subject codes: 27x) ===
    "Medicine_Internal": [
        "Innere Medizin", "Kardiologie", "Gastroenterologie", "Pneumologie",
        "Endokrinologie", "Diabetologie", "Nephrologie", "Rheumatologie",
        "Blut", "Herz", "Leber", "Niere",
    ],
    "Medicine_Surgery": [
        "Chirurgie", "Orthopädie", "Traumatologie", "Anästhesiologie",
        "Radiologie", "Onkologie", "Dermatologie", "Ophthalmologie",
        "Narkose", "Augenheilkunde", "Augenchirurgie", "Haut",
    ],
    "Medicine_Psychiatry": [
        "Psychiatrie", "Psychotherapie", "Psychoanalyse", "Neurologie",
        "Kinderpsychiatrie", "Gerontopsychiatrie", "Suchtmedizin",
        "Abwehrmechanismus", "Narzissmus", "Ausdruck", "Tiefenpsychologie",
    ],
    "Pharmacy": [
        "Pharmakologie", "Toxikologie", "Arzneimittelentwicklung",
        "Pharmazeutische Chemie", "Immunologie", "Virologie",
        "ACTH 4-9", "Augmentan", "Nährwert",
    ],

    # === Humanities (Subject codes: 3x, 4x, 8x, 10x, 11x, 15x, 17x) ===
    "History": [
        "Alte Geschichte", "Mittelalterliche Geschichte", "Frühneuzeit", "Neueste Geschichte",
        "Wirtschaftsgeschichte", "Sozialgeschichte", "Kulturgeschichte", "Technikgeschichte",
        "Aufklärung", "Napoleonische Kriege", "Absolutismus",
    ],
    "Philosophy": [
        "Philosophie", "Erkenntnistheorie", "Metaphysik", "Ethik", "Logik",
        "Sprachphilosophie", "Geschichtsphilosophie", "Rechtsphilosophie",
        "Aussage", "Naturphilosophie", "Utopie",
    ],
    "Theology": [
        "Theologie", "Bibelwissenschaft", "Kirchengeschichte", "Systematische Theologie",
        "Praktische Theologie", "Religionswissenschaft", "Ökumenische Theologie",
        "Auferstehung", "Nächstenliebe", "Natürliche Theologie", "Naturrecht",
    ],
    "Literature": [
        "Literaturwissenschaft", "Literaturgeschichte", "Linguistik", "Germanistik",
        "Romanistik", "Anglistik", "Textkritik", "Komparatistik",
        "Abenteuerroman", "Naturalismus", "Neologismus", "Nebensatz",
    ],

    # === Social Sciences (Subject codes: 5x, 7x, 8x, 9x) ===
    "Psychology": [
        "Psychologie", "Entwicklungspsychologie", "Sozialpsychologie", "Klinische Psychologie",
        "Tiefenpsychologie", "Kognitionspsychologie", "Differentialpsychologie",
        "Außersinnliche Wahrnehmung", "Aura", "Abhängigkeit",
    ],
    "Sociology": [
        "Soziologie", "Gesellschaftstheorie", "Sozialstruktur", "Migrationssoziologie",
        "Politische Soziologie", "Wirtschaftssoziologie", "Familiensoziologie",
        "Abweichendes Verhalten", "Ausländer", "Aussiedler", "Nachbarschaft",
    ],
    "Politics": [
        "Politikwissenschaft", "Politische Theorie", "Internationale Politik",
        "Vergleichende Politikwissenschaft", "Europäische Politik", "Entwicklungspolitik",
        "Atomkrieg", "Atomstrategie", "Attentat", "Aufstand", "Nationalismus",
    ],
    "Law": [
        "Rechtswissenschaft", "Verfassungsrecht", "Strafrecht", "Bürgerliches Recht",
        "Verwaltungsrecht", "Völkerrecht", "Europarecht", "Internationales Strafrecht",
        "Aufenthaltsgenehmigung", "Namensrecht", "Nachbarrecht", "Ausschluss",
    ],
    "Economics": [
        "Volkswirtschaftslehre", "Betriebswirtschaftslehre", "Finanzwissenschaft",
        "Makroökonomie", "Mikroökonomie", "Internationale Wirtschaft", "Wirtschaftspolitik",
        "Nachfrage", "Absatz", "Auslandsinvestition", "Außenhandel", "Außenwirtschaft",
    ],

    # === Arts, Culture (Subject codes: 9x, 12x, 13x, 20x) ===
    "Art": [
        "Kunstgeschichte", "Bildende Kunst", "Skulptur", "Grafik",
        "Museologie", "Denkmalkunde", "Kunsthandwerk", "Design",
        "Schmucknadel", "Naive Kunst", "Nationaldenkmal",
    ],
    "Music": [
        "Musikwissenschaft", "Musikgeschichte", "Musiktheorie", "Komposition",
        "Musikpädagogik", "Jazz", "Popmusik", "Musikinstrumente",
    ],
    "Theater_Film": [
        "Theaterwissenschaft", "Filmwissenschaft", "Dramaturgie", "Schauspiel",
        "Filmgeschichte", "Dokumentarfilm", "Medienwissenschaft",
    ],

    # === Geography, Environment (Subject codes: 19x) ===
    "Geography": [
        "Geographie", "Physische Geographie", "Humangeographie", "Kartographie",
        "Geoinformatik", "Landschaftsökologie", "Stadtgeographie",
        "Abfluss", "Auenwald", "Aue", "Naturräumliche Gliederung",
    ],
    "Environment": [
        "Umweltschutz", "Klimawandel", "Nachhaltigkeit", "Naturschutz",
        "Umweltverschmutzung", "Erneuerbare Energien", "Umweltpolitik",
        "Abfall", "Abfallwirtschaft", "Abwasser", "Abwasserreinigung",
        "Naturkatastrophe", "Außerirdisches Leben", "Atmosphäre",
    ],

    # === Special Topics (cross-domain) ===
    "Interdisciplinary": [
        "Interkulturalität", "Globalisierung", "Digitalisierung", "Nachhaltige Entwicklung",
        "Technikfolgenabschätzung", "Wissensmanagement", "Kulturtransfer",
        "Ausbreitung", "Auslese", "Abhängigkeit",
    ],
    "Emerging_Tech": [
        "Künstliche Intelligenz", "Big Data", "Blockchain", "Internet der Dinge",
        "Robotik", "Autonomes Fahren", "Quantencomputer", "3D-Druck",
    ],

    # === Additional diverse topics from GND sample ===
    "Additional_Sampled": [
        # Line ~500-600 from GND file
        "Atkins-Diät", "Audiometrie", "Abdichtungsstoff", "Abfindung",
        # Line ~5000+ from GND file
        "Nachbarrecht", "Nachbarschaft", "Nachfrage", "Nachtarbeit",
        "Narkose", "Nation", "Nationalbewusstsein", "Nationalsozialismus",
        "Nationalstaat", "Natur", "Naturheilkunde", "Naturschutzgebiet",
        "Naturwissenschaften", "Naturwissenschaftler", "Navigation", "Nebel",
        "Nervensystem", "Nervenzelle", "Neugeborenes", "Netzgerät",
    ],
}

# GND-GEO test queries (geographic names - cities, countries, regions, landmarks)
GND_GEO_TEST_QUERIES = {
    # === Europe ===
    "Europe_Countries": [
        "Deutschland", "Frankreich", "Italien", "Spanien", "Polen",
        "Niederlande", "Belgien", "Österreich", "Schweiz", "Tschechien",
        "Ungarn", "Rumänien", "Bulgarien", "Griechenland", "Portugal",
        "Schweden", "Norwegen", "Dänemark", "Finnland", "Estland",
        "Lettland", "Litauen", "Slowakei", "Slowenien", "Kroatien",
    ],
    "Europe_Cities": [
        "Berlin", "München", "Hamburg", "Köln", "Frankfurt am Main",
        "Stuttgart", "Dresden", "Leipzig", "Düsseldorf", "Nürnberg",
        "Paris", "Lyon", "Marseille", "Toulouse", "Straßburg",
        "Rom", "Mailand", "Venedig", "Florenz", "Neapel",
        "Madrid", "Barcelona", "Sevilla", "Valencia", "Bilbao",
        "Wien", "Prag", "Budapest", "Warschau", "Krakau",
    ],
    "Europe_Regions": [
        "Bayern", "Baden-Württemberg", "Nordrhein-Westfalen", "Hessen", "Sachsen",
        "Katalonien", "Andalusien", "Baskenland", "Galicien",
        " Lombardei", "Toskana", "Sizilien", "Sardinien",
        "Schottland", "Wales", "Cornwall", "Bretagne", "Normandie",
        "Thüringen", "Sachsen-Anhalt", "Brandenburg", "Mecklenburg-Vorpommern",
    ],

    # === Americas ===
    "North_America_Cities": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Francisco",
        "Austin", "Seattle", "Denver", "Boston", "Detroit",
        "Portland", "Las Vegas", "Miami", "Atlanta", "Washington D.C.",
        "Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa",
    ],
    "North_America_Regions": [
        "Kalifornien", "Texas", "Florida", "New York", "Illinois",
        "Pennsylvania", "Ohio", "Georgia", "Michigan", "New Jersey",
        "Virginia", "Washington", "Arizona", "Massachusetts", "Tennessee",
    ],
    "South_America_Cities": [
        "São Paulo", "Buenos Aires", "Rio de Janeiro", "Lima", "Bogotá",
        "Santiago", "Caracas", "Brasília", "Salvador", "Fortaleza",
        "Medellín", "Guayaquil", "Montevideo", "Asunción", "La Paz",
    ],
    "South_America_Regions": [
        "Amazonas", "Patagonien", "Anden", "Mittelchile", "Südosten Brasiliens",
        "Cuyo", "Mesopotamia", "Gran Chaco",
    ],

    # === Asia ===
    "Asia_Countries": [
        "China", "Japan", "Indien", "Südkorea", "Indonesien",
        "Thailand", "Vietnam", "Philippinen", "Malaysia", "Singapur",
        "Türkei", "Iran", "Irak", "Saudi-Arabien", "Vereinigte Arabische Emirate",
        "Israel", "Pakistan", "Bangladesh", "Myanmar", "Afghanistan",
    ],
    "Asia_Cities": [
        "Tokio", "Peking", "Shanghai", "Hongkong", "Singapur",
        "Seoul", "Bangkok", "Taipeh", "Hanoi", "Kuala Lumpur",
        "Dubai", "Istanbul", "Tel Aviv", "Jerusalem", "Mumbai",
        "Delhi", "Karatschi", "Dhaka", "Manila", "Jakarta",
    ],

    # === Africa ===
    "Africa_Countries": [
        "Ägypten", "Südafrika", "Nigeria", "Kenia", "Marokko",
        "Algerien", "Tunesien", "Ghana", "Tansania", "Etiopien",
        "Kamerun", "Senegal", "Simbabwe", "Uganda", "Angola",
    ],
    "Africa_Cities": [
        "Kairo", "Johannesburg", "Kapstadt", "Lagos", "Nairobi",
        "Casablanca", "Tunis", "Accra", "Dakar", "Addis Abeba",
    ],

    # === Oceania ===
    "Oceania_Countries": [
        "Australien", "Neuseeland", "Fidschi", "Papua-Neuguinea", "Samoa",
    ],
    "Oceania_Cities": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Auckland", "Wellington", "Christchurch", "Canberra", "Hobart",
    ],

    # === Geographic Features ===
    "Mountains": [
        "Alpen", "Pyrenäen", "Karpaten", "Apennin", "Kaukasus",
        "Himalaya", "Anden", "Rocky Mountains", "Sierra Nevada",
        "Matterhorn", "Mont Blanc", "Zugspitze", "Mount Everest", "K2",
        "Fujisan", "Kilimandscharo", "Montblanc", "Jungfrau", "Monte Rosa",
    ],
    "Rivers": [
        "Rhein", "Donau", "Elbe", "Main", "Mosel",
        "Themse", "Seine", "Rhone", "Po", "Ebro",
        "Nil", "Kongo", "Niger", "Sambesi", "Mekong",
        "Yangtse", "Ganges", "Mississippi", "Amazonas", "Rio Grande",
    ],
    "Seas_Lakes": [
        "Mittelmeer", "Nordsee", "Ostsee", "Adria", "Ägäis",
        "Schwarzes Meer", "Kaspisches Meer", "Rotes Meer", "Golf von Mexiko",
        "Bodensee", "Genfer See", "Comer See", "Gardasee",
        "Victoriasee", "Tanganjika", "Malawisee", "Baikal",
    ],

    # === Historical & Cultural ===
    "Historical_Regions": [
        "Mesopotamien", "Mesopotamien", "Persien", "Byzanz", "Römische Reich",
        "Karolinger Reich", "Heiliges Römisches Reich", "Ostkolonisation",
        "Alte Ägypten", "Kanaan", "Phönizien", "Indus-Kultur",
    ],
    "Cultural_Landmarks": [
        "Akropolis", "Kolosseum", "Eiffelturm", "Big Ben", "Brandenburger Tor",
        "Parthenon", "Machu Picchu", "Angkor Wat", "Taj Mahal", "Große Mauer",
        "Petra", "Pompeji", "Stonehenge", "Chichen Itza", "Forbidden City",
    ],

    # === Additional diverse topics ===
    "Additional_Geographic": [
        "Spreewald", "Schwarzwald", "Bayerischer Wald", "Odenwald", "Pfälzer Wald",
        "Bodden", "Marsch", "Ferner Osten", "Vorderer Orient", "Naher Osten",
        "Mittlerer Osten", "Westjordanland", "Gazastreifen", "Kurdistan",
        "Baskenland", "Katalonien", "Galizien", "Korsika", "Sizilien",
    ],
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class QueryResult:
    """Result of a single query test."""
    query: str
    top_k: int
    search_results_count: int
    reranker_selected_count: int
    acceptance_rate: float
    hit: bool
    quality_tier: str
    selected_indices: List[int]
    search_results: List[str]


@dataclass
class QualityReport:
    """Complete quality test report."""
    test_timestamp: str
    database: str
    total_queries: int
    nprobe_value: int
    top_k: int
    results: List[QueryResult]
    aggregate: Dict


# =============================================================================
# QUALITY TIER DEFINITIONS
# =============================================================================

def get_bk_quality_tier(relevant_count: int) -> str:
    """
    BK Quality Tiers (coarse classification, broader matches expected).

    The Basisklassifikation (BK) is a coarse classification (~2,100 classes)
    used for broad subject categorization.
    """
    if relevant_count == 0:
        return "FAIL"
    elif relevant_count == 1:
        return "POOR"
    elif relevant_count <= 3:
        return "OK"
    elif relevant_count == 4:
        return "GOOD"
    else:  # 5-8 for top_k=8
        return "EXCELLENT"


def get_gnd_quality_tier(relevant_count: int) -> str:
    """
    GND Quality Tiers (fine-grained authority file, precise matches expected).

    The GND-Sachbegriffe is a fine-grained authority file (~205,000 entries)
    providing detailed subject headings.
    """
    if relevant_count == 0:
        return "FAIL"
    elif relevant_count <= 2:
        return "POOR"
    elif relevant_count <= 5:
        return "OK"
    elif relevant_count <= 10:
        return "GOOD"
    else:
        return "EXCELLENT"


def get_gnd_geo_quality_tier(relevant_count: int) -> str:
    """
    GND-GEO Quality Tiers (geographic names - cities, countries, landmarks).

    The GND-Geografika database contains geographic entities like cities,
    countries, rivers, mountains, and landmarks. The naming is typically
    exact for famous locations, so we expect precise matches.
    """
    if relevant_count == 0:
        return "FAIL"
    elif relevant_count <= 1:
        return "POOR"
    elif relevant_count <= 2:
        return "OK"
    elif relevant_count <= 3:
        return "GOOD"
    else:
        return "EXCELLENT"


# =============================================================================
# QUALITY METRICS CALCULATOR
# =============================================================================

def calculate_aggregate_metrics(
    results: List[QueryResult],
    database: str,
    top_k: int
) -> Dict:
    """
    Calculate aggregate quality metrics from individual query results.

    Args:
        results: List of QueryResult objects
        database: "bk" or "gnd-saz"
        top_k: Number of results requested

    Returns:
        Dict containing aggregate metrics
    """
    if not results:
        return {}

    total_queries = len(results)

    # Basic counts
    total_relevant = sum(r.reranker_selected_count for r in results)
    total_search_results = sum(r.search_results_count for r in results)

    # Overall acceptance rate
    overall_acceptance_rate = total_relevant / total_search_results if total_search_results > 0 else 0.0

    # Hit rate (queries with at least 1 relevant result)
    hits = sum(1 for r in results if r.hit)
    hit_rate = hits / total_queries

    # Mean relevant results per query
    mean_relevant_results = total_relevant / total_queries

    # Quality tier distribution
    tier_distribution = {"FAIL": 0, "POOR": 0, "OK": 0, "GOOD": 0, "EXCELLENT": 0}
    for r in results:
        tier = r.quality_tier
        if tier in tier_distribution:
            tier_distribution[tier] += 1

    # Cumulative quality distribution
    # "X% of queries have at least Y relevant results"
    cumulative_quality = {}
    for threshold in [1, 2, 3, 4, 5, 6, 7, 8]:
        if threshold <= top_k:
            count_with_threshold = sum(1 for r in results if r.reranker_selected_count >= threshold)
            cumulative_quality[f"at_least_{threshold}"] = count_with_threshold / total_queries
        else:
            cumulative_quality[f"at_least_{threshold}"] = None  # Not applicable

    # Mean results at each position
    position_hits = {}
    for pos in range(top_k):
        hits_at_pos = sum(1 for r in results if pos in r.selected_indices)
        position_hits[f"position_{pos+1}"] = hits_at_pos / total_queries

    return {
        "overall_acceptance_rate": round(overall_acceptance_rate, 4),
        "hit_rate": round(hit_rate, 4),
        "mean_relevant_results": round(mean_relevant_results, 2),
        "quality_tier_distribution": tier_distribution,
        "cumulative_quality": {k: round(v, 4) if v is not None else None
                              for k, v in cumulative_quality.items()},
        "position_hit_rates": position_hits,
    }


# =============================================================================
# REPORT GENERATORS
# =============================================================================

def generate_json_report(report: QualityReport) -> str:
    """Generate JSON report from QualityReport object."""
    return json.dumps(asdict(report), indent=2, ensure_ascii=False)


def generate_cli_report(report: QualityReport, baseline_report: Optional[QualityReport] = None) -> str:
    """Generate human-readable CLI report."""
    lines = []
    lines.append("=" * 60)
    lines.append("=== Milvus Recall Quality Report ===")
    lines.append("=" * 60)
    lines.append(f"Database:    {report.database.upper()}")
    lines.append(f"Date:        {report.test_timestamp}")
    lines.append(f"NProbe:      {report.nprobe_value}")
    lines.append(f"Top-K:       {report.top_k}")
    lines.append(f"Queries:     {report.total_queries}")
    lines.append("")

    agg = report.aggregate
    lines.append("Overall Metrics:")
    lines.append(f"  Acceptance Rate:  {agg['overall_acceptance_rate']*100:.1f}%")
    lines.append(f"  Hit Rate (>=1):   {agg['hit_rate']*100:.1f}%")
    lines.append(f"  Mean Relevant:    {agg['mean_relevant_results']:.2f}")
    lines.append("")

    lines.append("Quality Tier Distribution:")
    tier_dist = agg['quality_tier_distribution']
    total = sum(tier_dist.values())
    for tier in ["FAIL", "POOR", "OK", "GOOD", "EXCELLENT"]:
        count = tier_dist.get(tier, 0)
        pct = (count / total * 100) if total > 0 else 0
        lines.append(f"  {tier:<10}: {count:>4} ({pct:>5.1f}%)")
    lines.append("")

    lines.append("Cumulative Quality:")
    cum = agg['cumulative_quality']
    for key, value in cum.items():
        if value is not None:
            lines.append(f"  {key}: {value*100:.1f}%")
    lines.append("")

    if baseline_report:
        lines.append("Changes vs Baseline:")
        current = report.aggregate
        baseline = baseline_report.aggregate

        delta_ar = current['overall_acceptance_rate'] - baseline['overall_acceptance_rate']
        delta_hr = current['hit_rate'] - baseline['hit_rate']
        delta_mr = current['mean_relevant_results'] - baseline['mean_relevant_results']

        ar_symbol = "✓" if delta_ar >= 0 else "⚠️"
        hr_symbol = "✓" if delta_hr >= 0 else "⚠️"
        mr_symbol = "✓" if delta_mr >= 0 else "⚠️"

        lines.append(f"  Acceptance Rate: {delta_ar*100:+.1f}% {ar_symbol}")
        lines.append(f"  Hit Rate:        {delta_hr*100:+.1f}% {hr_symbol}")
        lines.append(f"  Mean Relevant:   {delta_mr:+.2f} {mr_symbol}")

    lines.append("=" * 60)

    return "\n".join(lines)


# =============================================================================
# MAIN TEST CLASS
# =============================================================================

class MilvusRecallTester:
    """
    Test suite for evaluating Milvus search recall quality.

    Uses the LLM-based reranker as a proxy for ground truth relevance judgment.
    More selected indices = better recall quality.

    Attributes:
        milvus_service: MilvusService instance for database operations
        nprobe: Search parameter (default from config)
        top_k: Number of results to retrieve per query
    """

    def __init__(self, milvus_service: MilvusService, nprobe: Optional[int] = None, top_k: int = 8, concurrency: int = 15):
        """
        Initialize the recall quality tester.

        Args:
            milvus_service: MilvusService instance
            nprobe: Override nprobe value (optional)
            top_k: Number of results to retrieve (default: 8)
            concurrency: Number of concurrent queries (default: 15, keep well below 450/min rate limit)
        """
        self.milvus_service = milvus_service
        self.top_k = top_k
        self.concurrency = concurrency
        self._semaphore = None

        # Set nprobe for both databases if not specified
        if nprobe is not None:
            self._set_nprobe(nprobe)
        else:
            # Use default values from database configs
            pass

    def _set_nprobe(self, value: int):
        """Set nprobe on all database instances."""
        if self.milvus_service.db_bk:
            self.milvus_service.db_bk.nprobe = value
        if self.milvus_service.db_gnd_head:
            self.milvus_service.db_gnd_head.nprobe = value
        if self.milvus_service.db_gnd_desc:
            self.milvus_service.db_gnd_desc.nprobe = value
        if self.milvus_service.db_gnd_geo:
            self.milvus_service.db_gnd_geo.nprobe = value

    async def _run_search_and_rerank(
        self,
        query: str,
        database: str,
        top_k: int
    ) -> QueryResult:
        """
        Run vector search followed by reranking.

        Args:
            query: Search query string
            database: "bk", "gnd_head", or "gnd_desc"
            top_k: Number of results to retrieve

        Returns:
            QueryResult with search and reranking metrics
        """
        # Initialize semaphore for concurrency control (avoid API rate limits)
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.concurrency)

        async with self._semaphore:
            # Perform vector search
            if database == "bk":
                search_results = await self.milvus_service.search_bk(query, top_k)
                result_labels = [r["entity"]["label"] for r in search_results]
                result_labels_raw = [r["entity"]["label"] for r in search_results]
            elif database == "gnd_head":
                search_results = await self.milvus_service.search_gnd_head(query, top_k)
                result_labels = [r["entity"]["heading"] for r in search_results]
                result_labels_raw = result_labels
            elif database == "gnd_desc":
                search_results = await self.milvus_service.search_gnd_desc(query, top_k)
                result_labels = [r["entity"]["heading"] for r in search_results]
                result_labels_raw = result_labels
            else:
                raise ValueError(f"Unknown database type: {database}")

            search_count = len(search_results)

            # Call reranker
            rerank_type = "bk" if database == "bk" else "gnd-saz"
            reranker_result = await rerank_search_results(query, result_labels, rerank_type)

            # Extract selected indices
            selected_indices = reranker_result.get("indicesOfRelevantTopics", [])
            selected_count = len(selected_indices)

            # Calculate acceptance rate
            acceptance_rate = selected_count / search_count if search_count > 0 else 0.0

            # Determine hit (at least 1 relevant result)
            hit = selected_count >= 1

            # Determine quality tier
            if database == "bk":
                quality_tier = get_bk_quality_tier(selected_count)
            else:
                quality_tier = get_gnd_quality_tier(selected_count)

        return QueryResult(
            query=query,
            top_k=top_k,
            search_results_count=search_count,
            reranker_selected_count=selected_count,
            acceptance_rate=round(acceptance_rate, 4),
            hit=hit,
            quality_tier=quality_tier,
            selected_indices=selected_indices,
            search_results=result_labels_raw
        )

    async def run_bk_tests(
        self,
        queries: Optional[List[str]] = None,
        nprobe: Optional[int] = None
    ) -> QualityReport:
        """
        Run recall quality tests on BK database.

        Args:
            queries: Optional list of queries to test (uses default BK_TEST_QUERIES if None)
            nprobe: Override nprobe value for this test run

        Returns:
            QualityReport with all test results
        """
        if nprobe is not None:
            self._set_nprobe(nprobe)

        # Flatten default queries if not provided
        if queries is None:
            queries = []
            for group_queries in BK_TEST_QUERIES.values():
                queries.extend(group_queries)

        # Get current nprobe value
        current_nprobe = self.milvus_service.db_bk.nprobe if self.milvus_service.db_bk else 10
        current_nprobe = current_nprobe if current_nprobe is not None else 10

        # Run all BK searches in parallel using asyncio.gather (like transformation_service.py)
        search_start = time.time()
        bk_tasks = [self._run_search_and_rerank(query, "bk", self.top_k) for query in queries]
        results = await asyncio.gather(*bk_tasks)
        search_elapsed = time.time() - search_start
        print(f"[BK] Completed {len(queries)} queries in {search_elapsed:.2f}s")

        aggregate = calculate_aggregate_metrics(results, "bk", self.top_k)

        return QualityReport(
            test_timestamp=datetime.now(timezone.utc).isoformat(),
            database="bk",
            total_queries=len(queries),
            nprobe_value=current_nprobe,
            top_k=self.top_k,
            results=results,
            aggregate=aggregate
        )

    async def run_gnd_saz_tests(
        self,
        queries: Optional[List[str]] = None,
        nprobe: Optional[int] = None
    ) -> QualityReport:
        """
        Run recall quality tests on GND-SAZ (Sachbegriffe) databases.

        Note: This method searches both GND head and description databases in parallel
        and combines/deduplicates results.

        Args:
            queries: Optional list of queries to test (uses default GND_TEST_QUERIES if None)
            nprobe: Override nprobe value for this test run

        Returns:
            QualityReport with all test results
        """
        if nprobe is not None:
            self._set_nprobe(nprobe)

        # Flatten default queries if not provided
        if queries is None:
            queries = []
            for group_queries in GND_TEST_QUERIES.values():
                queries.extend(group_queries)

        # Get current nprobe value
        current_nprobe = self.milvus_service.db_gnd_head.nprobe if self.milvus_service.db_gnd_head else 4096
        current_nprobe = current_nprobe if current_nprobe is not None else 4096

        # Run all GND searches in parallel using asyncio.gather (like transformation_service.py)
        async def run_gnd_query(query: str) -> QueryResult:
            # For GND, search both head and desc in parallel
            head_results, desc_results = await asyncio.gather(
                self.milvus_service.search_gnd_head(query, self.top_k),
                self.milvus_service.search_gnd_desc(query, self.top_k)
            )

            # Combine and deduplicate by gnd_id
            seen_ids = set()
            combined_results = []
            for r in head_results + desc_results:
                gnd_id = r["entity"]["gnd_id"]
                if gnd_id not in seen_ids:
                    seen_ids.add(gnd_id)
                    combined_results.append(r)

            # Take top_k from combined
            combined_results = combined_results[:self.top_k]
            result_labels = [r["entity"]["heading"] for r in combined_results]
            search_count = len(combined_results)

            # Call reranker
            reranker_result = await rerank_search_results(query, result_labels, "gnd-saz")
            selected_indices = reranker_result.get("indicesOfRelevantTopics", [])
            selected_count = len(selected_indices)
            acceptance_rate = selected_count / search_count if search_count > 0 else 0.0
            hit = selected_count >= 1
            quality_tier = get_gnd_quality_tier(selected_count)

            return QueryResult(
                query=query,
                top_k=self.top_k,
                search_results_count=search_count,
                reranker_selected_count=selected_count,
                acceptance_rate=round(acceptance_rate, 4),
                hit=hit,
                quality_tier=quality_tier,
                selected_indices=selected_indices,
                search_results=result_labels
            )

        search_start = time.time()
        gnd_tasks = [run_gnd_query(query) for query in queries]
        results = await asyncio.gather(*gnd_tasks)
        search_elapsed = time.time() - search_start
        print(f"[GND] Completed {len(queries)} queries in {search_elapsed:.2f}s")

        aggregate = calculate_aggregate_metrics(results, "gnd-saz", self.top_k)

        return QualityReport(
            test_timestamp=datetime.now(timezone.utc).isoformat(),
            database="gnd-saz",
            total_queries=len(queries),
            nprobe_value=current_nprobe,
            top_k=self.top_k,
            results=results,
            aggregate=aggregate
        )

    async def run_gnd_geo_tests(
        self,
        queries: Optional[List[str]] = None,
        nprobe: Optional[int] = None
    ) -> QualityReport:
        """
        Run recall quality tests on GND Geografika database.

        Args:
            queries: Optional list of queries to test (uses default GND_GEO_TEST_QUERIES if None)
            nprobe: Override nprobe value for this test run

        Returns:
            QualityReport with all test results
        """
        if nprobe is not None:
            self._set_nprobe(nprobe)

        # Flatten default queries if not provided
        if queries is None:
            queries = []
            for group_queries in GND_GEO_TEST_QUERIES.values():
                queries.extend(group_queries)

        # Get current nprobe value
        current_nprobe = self.milvus_service.db_gnd_geo.nprobe if self.milvus_service.db_gnd_geo else 256
        current_nprobe = current_nprobe if current_nprobe is not None else 256

        # Run all GND-GEO searches in parallel using asyncio.gather
        async def run_gnd_geo_query(query: str) -> QueryResult:
            # Search GND-GEO database
            search_results = await self.milvus_service.search_gnd_geo(query, self.top_k)
            result_labels = [r["entity"]["heading"] for r in search_results]
            search_count = len(search_results)

            # Call reranker (using gnd-saz type as it's still GND terminology)
            reranker_result = await rerank_search_results(query, result_labels, "gnd-saz")
            selected_indices = reranker_result.get("indicesOfRelevantTopics", [])
            selected_count = len(selected_indices)
            acceptance_rate = selected_count / search_count if search_count > 0 else 0.0
            hit = selected_count >= 1
            quality_tier = get_gnd_geo_quality_tier(selected_count)

            return QueryResult(
                query=query,
                top_k=self.top_k,
                search_results_count=search_count,
                reranker_selected_count=selected_count,
                acceptance_rate=round(acceptance_rate, 4),
                hit=hit,
                quality_tier=quality_tier,
                selected_indices=selected_indices,
                search_results=result_labels
            )

        search_start = time.time()
        geo_tasks = [run_gnd_geo_query(query) for query in queries]
        results = await asyncio.gather(*geo_tasks)
        search_elapsed = time.time() - search_start
        print(f"[GND-GEO] Completed {len(queries)} queries in {search_elapsed:.2f}s")

        aggregate = calculate_aggregate_metrics(results, "gnd-geo", self.top_k)

        return QualityReport(
            test_timestamp=datetime.now(timezone.utc).isoformat(),
            database="gnd-geo",
            total_queries=len(queries),
            nprobe_value=current_nprobe,
            top_k=self.top_k,
            results=results,
            aggregate=aggregate
        )

    async def run_nprobe_sweep(
        self,
        database: str,
        nprobe_values: List[int],
        top_k: int = 8
    ) -> Dict[int, QualityReport]:
        """
        Run tests across multiple nprobe values to find optimal performance.

        Args:
            database: "bk" or "gnd-saz"
            nprobe_values: List of nprobe values to test
            top_k: Number of results to retrieve

        Returns:
            Dict mapping nprobe value to QualityReport
        """
        results = {}

        for nprobe in nprobe_values:
            print(f"\n{'='*60}")
            print(f"Testing nprobe={nprobe}")
            print(f"{'='*60}\n")

            self._set_nprobe(nprobe)

            if database == "bk":
                report = await self.run_bk_tests(nprobe=nprobe)
            else:
                report = await self.run_gnd_saz_tests(nprobe=nprobe)

            results[nprobe] = report

            print(f"\nResults for nprobe={nprobe}:")
            print(f"  Acceptance Rate: {report.aggregate['overall_acceptance_rate']*100:.1f}%")
            print(f"  Hit Rate:        {report.aggregate['hit_rate']*100:.1f}%")
            print(f"  Mean Relevant:   {report.aggregate['mean_relevant_results']:.2f}")

        return results

    async def run_top_k_scaling(
        self,
        database: str,
        top_k_values: List[int]
    ) -> Dict[int, QualityReport]:
        """
        Run tests across multiple top_k values to evaluate scaling behavior.

        Args:
            database: "bk" or "gnd-saz"
            top_k_values: List of top_k values to test

        Returns:
            Dict mapping top_k value to QualityReport
        """
        results = {}
        original_top_k = self.top_k

        for tk in top_k_values:
            print(f"\n{'='*60}")
            print(f"Testing top_k={tk}")
            print(f"{'='*60}\n")

            self.top_k = tk

            if database == "bk":
                report = await self.run_bk_tests()
            else:
                report = await self.run_gnd_saz_tests()

            results[tk] = report

            print(f"\nResults for top_k={tk}:")
            print(f"  Acceptance Rate: {report.aggregate['overall_acceptance_rate']*100:.1f}%")
            print(f"  Hit Rate:        {report.aggregate['hit_rate']*100:.1f}%")
            print(f"  Mean Relevant:   {report.aggregate['mean_relevant_results']:.2f}")

        # Restore original top_k
        self.top_k = original_top_k

        return results


# =============================================================================
# CLI INTERFACE
# =============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Milvus Search Recall Quality Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run BK tests with default queries
  python -m tests.test_milvus_recall_quality --database bk --output bk_report.json

  # Run GND tests with specific nprobe values
  python -m tests.test_milvus_recall_quality --database gnd-saz --nprobe 50 --nprobe 100 --output gnd_report.json

  # Compare against baseline
  python -m tests.test_milvus_recall_quality --database bk --baseline baseline.json --output comparison.json

  # Pytest integration
  pytest tests/test_milvus_recall_quality.py -v -k bk
        """
    )

    parser.add_argument(
        "--database", "-d",
        choices=["bk", "gnd-saz", "gnd-geo", "all"],
        default="all",
        help="Database to test (default: all)"
    )
    parser.add_argument(
        "--nprobe", "-n",
        action="append",
        type=int,
        help="Nprobe value(s) to test. Can be specified multiple times."
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=8,
        help="Number of results to retrieve (default: 8)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path for JSON report"
    )
    parser.add_argument(
        "--baseline", "-b",
        help="Path to baseline JSON report for comparison"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


async def main():
    """Main entry point for CLI."""
    args = parse_args()

    # Load baseline if provided
    baseline_report = None
    if args.baseline:
        with open(args.baseline, 'r') as f:
            baseline_data = json.load(f)
            # Reconstruct as QualityReport if needed
            baseline_report = QualityReport(**baseline_data)

    # Initialize Milvus service
    print("Initializing Milvus service...")
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    # Create tester
    nprobe = args.nprobe[0] if args.nprobe and len(args.nprobe) == 1 else None
    tester = MilvusRecallTester(milvus_service, nprobe=nprobe, top_k=args.top_k)

    # Run tests
    reports = []

    if args.database in ["bk", "all"]:
        print("\n" + "="*60)
        print("Running BK Recall Quality Tests")
        print("="*60)

        if args.nprobe and len(args.nprobe) > 1:
            # Multiple nprobe values
            sweep_results = await tester.run_nprobe_sweep("bk", args.nprobe, args.top_k)
            for nprobe_val, report in sweep_results.items():
                reports.append((f"bk_nprobe_{nprobe_val}", report))
        else:
            report = await tester.run_bk_tests()
            reports.append(("bk", report))

    if args.database in ["gnd-saz", "all"]:
        print("\n" + "="*60)
        print("Running GND Recall Quality Tests")
        print("="*60)

        if args.nprobe and len(args.nprobe) > 1:
            # Multiple nprobe values
            sweep_results = await tester.run_nprobe_sweep("gnd-saz", args.nprobe, args.top_k)
            for nprobe_val, report in sweep_results.items():
                reports.append((f"gnd_nprobe_{nprobe_val}", report))
        else:
            report = await tester.run_gnd_saz_tests()
            reports.append(("gnd-saz", report))

    if args.database in ["gnd-geo", "all"]:
        print("\n" + "="*60)
        print("Running GND-GEO Recall Quality Tests")
        print("="*60)

        if args.nprobe and len(args.nprobe) > 1:
            # Multiple nprobe values
            sweep_results = await tester.run_nprobe_sweep("gnd-geo", args.nprobe, args.top_k)
            for nprobe_val, report in sweep_results.items():
                reports.append((f"gnd-geo_nprobe_{nprobe_val}", report))
        else:
            report = await tester.run_gnd_geo_tests()
            reports.append(("gnd-geo", report))

    # Generate and output reports
    for name, report in reports:
        print("\n" + generate_cli_report(report, baseline_report))

        if args.output:
            # Add identifier to output filename
            base, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'json')
            output_path = f"tests/milvus_tests/{base}_{name}.{ext}"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(generate_json_report(report))
            print(f"\nReport saved to: {output_path}")

    await milvus_service.shutdown()


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("database", ["bk", "gnd-saz", "gnd-geo"])
async def test_recall_quality(database):
    """Test recall quality for specified database."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)

        if database == "bk":
            report = await tester.run_bk_tests()
        elif database == "gnd-geo":
            report = await tester.run_gnd_geo_tests()
        else:
            report = await tester.run_gnd_saz_tests()

        # Basic assertions
        assert report.total_queries > 0
        assert report.aggregate['overall_acceptance_rate'] >= 0
        assert report.aggregate['hit_rate'] >= 0
    finally:
        await milvus_service.shutdown()


@pytest.mark.asyncio
async def test_bk_recall_quality():
    """Test BK recall quality with default queries."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)
        report = await tester.run_bk_tests()

        # Print report for visibility
        print(generate_cli_report(report))

        # Verify reasonable quality
        assert report.total_queries >= 100, "Should have at least 100 BK test queries"
        assert report.aggregate['hit_rate'] >= 0.5, "BK should have at least 50% hit rate"
    finally:
        await milvus_service.shutdown()


@pytest.mark.asyncio
async def test_gnd_recall_quality():
    """Test GND recall quality with default queries."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)
        report = await tester.run_gnd_saz_tests()

        # Print report for visibility
        print(generate_cli_report(report))

        # Verify reasonable quality
        assert report.total_queries >= 200, "Should have at least 200 GND test queries"
        assert report.aggregate['hit_rate'] >= 0.3, "GND should have at least 30% hit rate"
    finally:
        await milvus_service.shutdown()


@pytest.mark.asyncio
async def test_gnd_geo_recall_quality():
    """Test GND Geografika recall quality with default queries."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)
        report = await tester.run_gnd_geo_tests()

        # Print report for visibility
        print(generate_cli_report(report))

        # Verify reasonable quality
        assert report.total_queries >= 200, "Should have at least 200 GND-GEO test queries"
        assert report.aggregate['hit_rate'] >= 0.3, "GND-GEO should have at least 30% hit rate"
    finally:
        await milvus_service.shutdown()


@pytest.mark.asyncio
async def test_nprobe_sweep():
    """Test nprobe parameter sweep on BK database."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)

        # Test a subset of nprobe values (full sweep is expensive)
        nprobe_values = [1, 10, 50, 100]
        results = await tester.run_nprobe_sweep("bk", nprobe_values, top_k=8)

        # Verify results
        assert len(results) == len(nprobe_values)
        for nprobe, report in results.items():
            assert report.aggregate['overall_acceptance_rate'] >= 0
            assert report.aggregate['hit_rate'] >= 0

        # Print comparison
        print("\nNProbe Comparison:")
        print(f"{'nprobe':<10} {'Acceptance Rate':<20} {'Hit Rate':<15} {'Mean Relevant':<15}")
        print("-" * 60)
        for nprobe, report in sorted(results.items()):
            agg = report.aggregate
            print(f"{nprobe:<10} {agg['overall_acceptance_rate']*100:>15.1f}% "
                  f"{agg['hit_rate']*100:>13.1f}% {agg['mean_relevant_results']:>13.2f}")
    finally:
        await milvus_service.shutdown()


@pytest.mark.asyncio
async def test_top_k_scaling():
    """Test top_k parameter scaling on BK database."""
    milvus_service = MilvusService(
        device=settings.milvus_device,
        bk_db_path=settings.milvus_bk_db_path,
        bk_csv_path=settings.milvus_bk_csv_path,
        gnd_saz_head_db_path=settings.milvus_gnd_saz_head_db_path,
        gnd_saz_head_csv_path=settings.milvus_gnd_saz_head_csv_path,
        gnd_saz_desc_db_path=settings.milvus_gnd_saz_desc_db_path,
        gnd_saz_desc_csv_path=settings.milvus_gnd_saz_desc_csv_path,
        gnd_geo_db_path=settings.milvus_gnd_geo_db_path,
        gnd_geo_csv_path=settings.milvus_gnd_geo_csv_path,
    )
    await milvus_service.initialize()

    try:
        tester = MilvusRecallTester(milvus_service, top_k=8)

        # Test top_k values
        top_k_values = [4, 8, 16]
        results = await tester.run_top_k_scaling("bk", top_k_values)

        # Verify results
        assert len(results) == len(top_k_values)
        for tk, report in results.items():
            assert report.aggregate['overall_acceptance_rate'] >= 0
            assert report.aggregate['hit_rate'] >= 0

        # Print comparison
        print("\nTop-K Scaling Comparison:")
        print(f"{'top_k':<10} {'Acceptance Rate':<20} {'Hit Rate':<15} {'Mean Relevant':<15}")
        print("-" * 60)
        for tk, report in sorted(results.items()):
            agg = report.aggregate
            print(f"{tk:<10} {agg['overall_acceptance_rate']*100:>15.1f}% "
                  f"{agg['hit_rate']*100:>13.1f}% {agg['mean_relevant_results']:>13.2f}")
    finally:
        await milvus_service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())