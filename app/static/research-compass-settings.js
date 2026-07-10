/* ================================================================
   CONFIGURATION
   Application settings and constants.
   ================================================================ */
const CONFIG = {
    // ROOT_PATH is derived from the current page URL (e.g. "/ai" or "/nsis")
    ROOT_PATH: '/' + window.location.pathname.split('/')[1],
    // API_BASE_URL uses ROOT_PATH directly to avoid circular reference
    API_BASE_URL: window.location.origin + '/' + window.location.pathname.split('/')[1] + '/api/v1',
    // VUFIND_BASE_URL: fallback value, injected at runtime from .env
    VUFIND_BASE_URL: 'https://stabikat.de',
    MAX_HISTORY: 5,
    FETCH_DEBOUNCE_MS: 800,
    LOCAL_STORAGE_KEY: 'research-compass-history',
    LOCAL_STORAGE_KEY_SETTINGS: 'research-compass-settings',
    SHOW_DEBUG_PANEL: false,
    UI_LANGUAGE: 'de'
};

/* ================================================================
   UI STRINGS (German)
   Static user-facing text labels and messages.
   ================================================================ */
const UI_STRINGS = {
    // Page
    pageTitle: "Recherche-Kompass | KaRMa",
    logoText: "Recherche-Kompass",
    aboutLink: "Über den Recherche-Kompass",
    aboutLinkMobile: "Über",

    // Search History Sidebar
    searchHistory: "Suchverlauf",
    clearHistoryBtn: "Verlauf löschen",
    emptyHistory: "Noch keine Suchen",

    // Search Examples Sidebar
    searchExamples: "Suchbeispiele",
    searchExamplesTooltip: "Klicken Sie auf ein Beispiel, um die Suche mit einer Beispielanfrage zu starten.",

    // Sidebar About
    sidebarAbout: "Über den Recherche-Kompass",

    // Search Section
    searchTitle: "Automatische Rechercheberatung",
    searchPlaceholder: "Beschreiben Sie, wonach Sie suchen …",
    clearInputBtn: "Eingabe löschen",
    searchBtn: "Suchen",

    // Debug Panel
    debugInfo: "Debug-Informationen",
    debugShortcut: "(Strg+Alt+D)",
    generatedUrl: "Generierte URL",
    searchIntent: "Search Intent",
    queryExpansion: "Query Expansion",
    queryTransformation: "Query Transformation",
    debounceInterval: "Debounce-Intervall: ",

    // Results Section
    foundResults: "Gefundene Ergebnisse",
    hitsInVuFind: "Treffer in KaRMa",
    qualityScore: "Passgenauigkeit: ",
    openAllResults: "Alle Ergebnisse in KaRMa öffnen",
    waitingForResults: "Warten auf Ergebnisse …",
    resultsLoading: "Ergebnisse werden geladen …",
    noResultsAvailable: "Noch keine Ergebnisse verfügbar",

    // Options Section
    searchOptions: "Suchoptionen",
    optionsLoading: "Suchoptionen werden geladen …",
    noSearchOptionsAvailable: "Noch keine Suchoptionen verfügbar",
    activeOptions: "Aktive Optionen",
    resetBtn: "Zurücksetzen",

    // Sort labels
    sortRelevance: "Relevanz",
    sortAuthor: "Autor",
    sortTitle: "Titel",
    sortDate: "Datum",
    sortCallnumber: "Signatur",
    sortLabel: "Sortierung:",

    // Vocab Popup
    selectOptions: "Optionen auswählen",
    close: "Schließen",
    selectAll: "Alle auswählen",
    deselectAll: "Alle abwählen",
    add: "Hinzufügen",

    // About Popup Title
    aboutPopup: "Über den Recherche-Kompass",

    // Welcome Popup Title and Logo
    welcomePopup: "Willkommen bei KaRMa Recherche-Kompass",
    compassLeftText: "Recherche",
    compassRightText: "Kompass",

    // Report Accessibility Issue Popup Title
    reportAccessibilityIssue: "Barriere melden",

    // Footer Links Text
    privacyLinkText: "Datenschutz",
    accessibilityLinkText: "Barrierefreiheit",
    reportAccessibilityIssueLinkText: "Barriere melden",
    imprintLinkText: "Impressum",

    // Language Switcher
    langDe: "DE",
    langEn: "EN",
    langDeTitle: "Wechsel zu Deutsch",
    langEnTitle: "Wechsel zu Englisch",

    // Alt Text
    logoAltText: "UB Mannheim Logo",
    footerLogoAltText: "Universitätsbibliothek Mannheim",

    // Search Examples
    searchExample1Text: "Klimawandel-Artikel (Deutsch)",
    searchExample1Query: "Deutsche Artikel über Klimawandel und Umweltpolitik",
    searchExample2Text: "Python Data Science E-Books",
    searchExample2Query: "E-Books über Python-Programmierung für Data Science",
    searchExample3Text: "Frauenrechte in Bolivien",
    searchExample3Query: "Bücher und Artikel in Englisch und Spanisch aus den letzten 40 Jahren über Frauenrechte in Bolivien",
    searchExample4Text: "Artikel von R. Willemsen (letzte 50 Jahre)",
    searchExample4Query: "Artikel von Roger Willemsen aus den letzten 50 Jahren",
    searchExample5Text: "Hist. Karten Berlin (vor 1900)",
    searchExample5Query: "Historische Karten von Berlin und Brandenburg vor dem Jahr 1900",

    // Sidebar About Content
    sidebarAboutParagraph: "Der KaRMa Recherche-Kompass nutzt künstliche Intelligenz, um Sie bei Ihrer Recherche zu unterstützen. Suchanfragen in natürlicher Sprache werden in strukturierte KaRMa-Abfragen umgewandelt. Alle Ergebnisse stammen aus dem KaRMa der Universitätsbibliothek Mannheim.",
    sidebarAboutFeaturesLabel: "Funktionen:",
    sidebarAboutFeature1: "Vorschau der Suchergebnisse",
    sidebarAboutFeature2: "Verwandte Suchbegriffe",
    sidebarAboutFeature3: "Präzise thematische Suche",
    sidebarAboutFeature4: "Suche in Themenbereichen",
    sidebarAboutFeature5: "Medientyp-Filter",
    sidebarAboutFeature6: "Inhaltsgenre-Filter",
    sidebarAboutFeature7: "Sprach-Filter",
    sidebarAboutFeature8: "Datumsbereich-Filter",

    // About Popup Content (HTML)
    aboutPopupBodyHTML: `
    <p>Der <strong>Recherche-Kompass</strong> ist eine API-gestützte Suchschnittstelle, die KaRMa mit modernen KI-Technologien verbindet. Ziel der Anwendung ist, Nutzende bei der Formulierung präziser Suchanfragen zu unterstützen und so die Qualität ihrer Suchergebnisse zu verbessern. Die API verarbeitet Eingaben in natürlicher Sprache und wandelt sie in strukturierte, katalogtaugliche Suchparameter um.</p>
    <br>
    <p><strong>Kernfunktionen</strong> umfassen die Analyse der Suchintention, die Erweiterung von Suchbegriffen mit semantisch verwandten Termen, sowie die Extraktion von Facetten und Filtern direkt aus der Suchanfrage. Zusätzlich bietet das System eine semantische Suche in kontrollierten Normdateien wie der GND (Gemeinsame Normdatei) und der Basisklassifikation (BK). Die Passgenauigkeitsbewertung ermöglicht es, die Relevanz der erzielten Ergebnisse einzuschätzen.</p>
    <br>
    <p><strong>Technisch</strong> basiert der Recherche-Kompass auf FastAPI (Python) und stellt die Web-Schnittstelle als Single-Page-Application zur Verfügung. Der Recherche-Kompass integriert Large Language Models (LLMs) für die semantische Analyse der Suchanfragen, eine Vektordatenbank für die Suche in den kontrollierten Vokabularen sowie die VuFind-Katalog-API als Quelle für bibliographische Daten.</p>
    <br>
    <p><strong>Kontakt:</strong> <a href="mailto:renat.shigapov@uni-mannheim.de?subject=KaRMa%20Recherche-Kompass">Renat Kaufmann</a> (Universitätsbibliothek Mannheim)</p>
    `,

    // Welcome Popup Content (HTML)
    welcomePopupBodyHTML: `<p>Willkommen beim <strong>KaRMa Recherche-Kompass</strong>!</p>
    <br>
    <p>Der KaRMa Recherche-Kompass unterstützt Sie bei der Recherche in den Beständen der Universitätsbibliothek Mannheim. Mithilfe künstlicher Intelligenz werden Ihre natürlichsprachigen Suchanfragen automatisch in optimierte Suchoptionen für KaRMa umgewandelt. Die Treffer stammen dabei gesichert aus den Beständen der Universitätsbibliothek Mannheim.</p>
    <br>
    <p>Zur Verarbeitung Ihrer Suchanfragen werden externe Dienstleister eingebunden. Bitte geben Sie keine personenbezogenen Daten ein. Weiterhin werden keine personenbezogenen Daten erfasst, übermittelt oder gespeichert.</p>`,

    // Report Accessibility Issue Content (HTML)
    reportAccessibilityIssueBodyHTML: `
    <p>Sind Ihnen Mängel beim barrierefreien Zugang zu Inhalten dieser Webseite aufgefallen? Oder haben Sie Fragen zum Thema Barrierefreiheit? Dann können Sie sich gerne bei uns melden:</p>
    <br>
    <p>Universitätsbibliothek Mannheim</p>
    <br>
    <p>E-Mail: <a href="mailto:ub.info@uni-mannheim.de">ub.info@uni-mannheim.de</a></p>
    <br>
    <p>Im Rahmen der Kontaktaufnahme werden gegebenenfalls personenbezogene Daten verarbeitet. Genaue Informationen finden Sie in unserer <a href="https://staatsbibliothek-berlin.de/extras/allgemeines/impressum/datenschutz-privacy-policy/" target="_blank">Datenschutzerklärung</a>.</p>
    `,

    // Dynamic Strings (used in JavaScript)
    searchInProgress: "Suche läuft …",
    noResultsFound: "Keine Ergebnisse",
    noTitle: "Ohne Titel",
    negatedBadge: "OHNE",
    keywordDuplicate: "Suchbegriff ist bereits vorhanden",
    vocabEmptyResults: "Keine Ergebnisse zu Ihrem Suchbegriff gefunden",
    removeOption: "Entfernen",
    qualityTooltip: "Passgenauigkeit der Ergebnisse in Bezug auf die ursprüngliche Suchanfrage.\n\nEine ausführliche Begründung dieses Wertes befindet sich im blauen Kasten über den Ergebnissen.",
    dateFromLabel: "Ab",
    dateToLabel: "Bis",

    // Placeholder texts for custom inputs
    customKeywordPlaceholder: "Eigenen Suchbegriff eingeben …",
    customTopicPlaceholder: "Thema suchen …",
    customBlkNumberPlaceholder: "Themenbereich suchen …",
    processingPlaceholder: "Wird verarbeitet …",
};

/* ================================================================
   UI STRINGS (English)
   Static user-facing text labels and messages.
   ================================================================ */
const UI_STRINGS_EN = {
    // Page
    pageTitle: "Research Compass | KaRMa",
    logoText: "Research Compass",
    aboutLink: "About the Research Compass",
    aboutLinkMobile: "About",

    // Search History Sidebar
    searchHistory: "Search history",
    clearHistoryBtn: "Clear history",
    emptyHistory: "No searches yet",

    // Search Examples Sidebar
    searchExamples: "Search Examples",
    searchExamplesTooltip: "Click on an example to start searching with a sample query.",

    // Sidebar About
    sidebarAbout: "About the Research Compass",

    // Search Section
    searchTitle: "Automatic research consultation",
    searchPlaceholder: "Describe what you are looking for ...",
    clearInputBtn: "Clear Input",
    searchBtn: "Search",

    // Debug Panel
    debugInfo: "Debug Information",
    debugShortcut: "(Ctrl+Alt+D)",
    generatedUrl: "Generated URL",
    searchIntent: "Search Intent",
    queryExpansion: "Query Expansion",
    queryTransformation: "Query Transformation",
    debounceInterval: "Debounce Interval: ",

    // Results Section
    foundResults: "Found Results",
    hitsInVuFind: "Hits in KaRMa",
    qualityScore: "Relevance: ",
    openAllResults: "Open all results in KaRMa",
    waitingForResults: "Waiting for results ...",
    resultsLoading: "Loading results ...",
    noResultsAvailable: "No results available yet",

    // Options Section
    searchOptions: "Search Options",
    optionsLoading: "Loading search options ...",
    noSearchOptionsAvailable: "No search options available yet",
    activeOptions: "Active Options",
    resetBtn: "Reset",

    // Sort labels
    sortRelevance: "Relevance",
    sortAuthor: "Author",
    sortTitle: "Title",
    sortDate: "Date",
    sortCallnumber: "Call Number",
    sortLabel: "Sort:",

    // Vocab Popup
    selectOptions: "Select Options",
    close: "Close",
    selectAll: "Select All",
    deselectAll: "Deselect All",
    add: "Add",

    // About Popup Title
    aboutPopup: "About the Research Compass",

    // Report Accessibility Issue Popup Title
    reportAccessibilityIssue: "Report accessibility issue",

    // Footer Links Text
    privacyLinkText: "Privacy",
    accessibilityLinkText: "Accessibility",
    reportAccessibilityIssueLinkText: "Report accessibility issue",
    imprintLinkText: "Imprint",

    // Language Switcher
    langDe: "DE",
    langEn: "EN",
    langDeTitle: "Switch to German",
    langEnTitle: "Switch to English",

    // Alt Text
    logoAltText: "UB Mannheim Logo",
    footerLogoAltText: "Mannheim University Library",

    // Search Examples
    searchExample1Text: "Climate Change Articles (German)",
    searchExample1Query: "German articles about climate change and environmental policy",
    searchExample2Text: "Python Data Science E-Books",
    searchExample2Query: "E-Books about Python programming for Data Science",
    searchExample3Text: "Women's Rights in Bolivia",
    searchExample3Query: "Books and articles in English and Spanish from the last 40 years about women's rights in Bolivia",
    searchExample4Text: "Articles by R. Willemsen (last 50 years)",
    searchExample4Query: "Articles by Roger Willemsen from the last 50 years",
    searchExample5Text: "Hist. Maps of Berlin (before 1900)",
    searchExample5Query: "Historical maps of Berlin and Brandenburg before the year 1900",

    // Sidebar About Content
    sidebarAboutParagraph: "The KaRMa Research Compass uses artificial intelligence to assist you with your research. Natural language search queries are transformed into structured KaRMa queries. All results come from the KaRMa of the Mannheim University Library.",
    sidebarAboutFeaturesLabel: "Features:",
    sidebarAboutFeature1: "Preview of search results",
    sidebarAboutFeature2: "Related search terms",
    sidebarAboutFeature3: "Precise topic search",
    sidebarAboutFeature4: "Search in subject areas",
    sidebarAboutFeature5: "Media type filter",
    sidebarAboutFeature6: "Content genre filter",
    sidebarAboutFeature7: "Language filter",
    sidebarAboutFeature8: "Date range filter",

    // About Popup Content (HTML)
    aboutPopupBodyHTML: `
    <p>The <strong>Research Compass</strong> is an API-powered search interface that connects KaRMa with modern AI technologies. The goal of the application is to support users in formulating precise search queries and thereby improving the quality of their search results. The API processes natural language inputs and transforms them into structured, catalog-compatible search parameters.</p>
    <br>
    <p><strong>Core features</strong> include search intent analysis, expansion of search terms with semantically related terms, as well as the extraction of facets and filters directly from the search query. Additionally, the system offers semantic search in controlled authority files such as the GND (German integrated authority file) and the Basisklassifikation (BK). The relevance scoring allows users to assess the quality of the obtained results.</p>
    <br>
    <p><strong>Technically</strong>, the Research Compass is based on FastAPI and integrates Large Language Models (LLMs) for semantic analysis, a vector database for searching in controlled authority files, and the VuFind catalog API as a source for bibliographic data.</p>
    <br>
    <p><strong>Contact:</strong> <a href="mailto:dorian.grosch@sbb.spk-berlin.de?subject=KaRMa%20Research%20Compass">Dorian Grosch</a> (Staatsbibliothek zu Berlin)</p>
    `,

    // Report Accessibility Issue Content (HTML)
    reportAccessibilityIssueBodyHTML: `
    <p>Have you noticed barriers to accessing content on this website? Or do you have questions about accessibility? Please feel free to contact us:</p>
    <br>
    <p>Universitätsbibliothek Mannheim</p>
    <br>
    <p>Email: <a href="mailto:ub.info@uni-mannheim.de">ub.info@uni-mannheim.de</a></p>
    <br>
    <p>When contacting us, personal data may be processed. For detailed information, please see our <a href="https://staatsbibliothek-berlin.de/extras/allgemeines/impressum/datenschutz-privacy-policy/" target="_blank">Privacy Policy</a>.</p>
    `,

    // Welcome Popup Content (HTML)
    welcomePopupBodyHTML: `<p>Welcome to the <strong>KaRMa Research Compass</strong>!</p>
    <br>
    <p>The KaRMa Research Compass supports you in researching the collections of the Mannheim University Library. Using artificial intelligence, your natural language search queries are automatically transformed into optimized search options for KaRMa. The results reliably come from the holdings of the Mannheim University Library.</p>
    <br>
    <p>External service providers are used to process your search queries. Please do not enter any personal data. Furthermore, no personal data is collected, transmitted, or stored.</p>`,

    // Dynamic Strings (used in JavaScript)
    searchInProgress: "Searching ...",
    noResultsFound: "No results found",
    noTitle: "Untitled",
    negatedBadge: "NOT",
    keywordDuplicate: "Search term already exists",
    vocabEmptyResults: "No results found for your search term",
    removeOption: "Remove",
    qualityTooltip: "Relevance of the results in relation to the original search query.\n\nA detailed explanation of this value can be found in the blue box above the results.",
    dateFromLabel: "From",
    dateToLabel: "To",

    // Placeholder texts for custom inputs
    customKeywordPlaceholder: "Enter custom search term ...",
    customTopicPlaceholder: "Search topic ...",
    customBlkNumberPlaceholder: "Search subject area ...",
    processingPlaceholder: "Processing ...",
};

/* ================================================================
   UI ELEMENTS
   URLs and other element references.
   ================================================================ */
const UI_ELEMENTS = {
    // Images
    logoSrc: CONFIG.ROOT_PATH + "/static/images/logo.svg",
    footerLogoSrc: CONFIG.ROOT_PATH + "/static/images/logo.svg",
    faviconSrc: CONFIG.ROOT_PATH + "/static/images/favicon.ico",

    // External Resources
    // TODO: avoid external URLs
    fontsUrl: "https://fonts.bunny.net/css",
    iconsUrl: "https://unpkg.com/@fortawesome/fontawesome-free@6.5.1/css/all.min.css",

    // External Links
    institutionUrl: "https://www.bib.uni-mannheim.de/",
    privacyUrl: "https://www.uni-mannheim.de/datenschutzerklaerung/",
    accessibilityUrl: "https://www.uni-mannheim.de/digitale-barrierefreiheit/",
    imprintUrl: "https://www.uni-mannheim.de/impressum/",

    // Search Example Icons
    searchExample1Icon: "fa-solid fa-earth-americas fa-fw",
    searchExample2Icon: "fa-solid fa-laptop fa-fw",
    searchExample3Icon: "fa-solid fa-venus fa-fw",
    searchExample4Icon: "fa-solid fa-newspaper fa-fw",
    searchExample5Icon: "fa-solid fa-map-location-dot fa-fw",

    // Options Config Icons
    keywordIcon: "fa-magnifying-glass",
    topicIcon: "fa-bullseye",
    bklIcon: "fa-folder",
    formatIcon: "fa-desktop",
    formatDetailsIcon: "fa-star",
    languageIcon: "fa-language",
    authorIcon: "fa-user",
    dateIcon: "fa-calendar",
};

/* ================================================================
   LANGUAGE MANAGEMENT
   Handles language switching and persistence.
   ================================================================ */

/**
 * Gets the current UI language from localStorage, falling back to CONFIG default.
 * Also updates CONFIG.UI_LANGUAGE to the current value.
 * @returns {string} Language code ('de' or 'en')
 */
function getLanguage() {
    // Check localStorage
    try {
        const settings = localStorage.getItem(CONFIG.LOCAL_STORAGE_KEY_SETTINGS);
        if (settings) {
            const parsed = JSON.parse(settings);
            if (parsed.language && (parsed.language === 'de' || parsed.language === 'en')) {
                CONFIG.UI_LANGUAGE = parsed.language;
                return parsed.language;
            }
        }
    } catch (e) {
        // Ignore parse errors
    }
    // Default to UI_LANGUAGE setting from CONFIG (already 'de')
    return CONFIG.UI_LANGUAGE;
}

/**
 * Saves the language preference to localStorage and updates CONFIG.UI_LANGUAGE.
 * @param {string} language - Language code ('de' or 'en')
 */
function saveLanguage(language) {
    try {
        CONFIG.UI_LANGUAGE = language;
        let settings = {};
        const existing = localStorage.getItem(CONFIG.LOCAL_STORAGE_KEY_SETTINGS);
        if (existing) {
            try {
                settings = JSON.parse(existing);
            } catch (e) {}
        }
        settings.language = language;
        localStorage.setItem(CONFIG.LOCAL_STORAGE_KEY_SETTINGS, JSON.stringify(settings));
    } catch (e) {
        console.warn('Failed to save language preference:', e);
    }
}

/**
 * Gets the active UI strings based on the current language.
 * @returns {Object} UI strings object for the current language
 */
function getStrings() {
    const lang = getLanguage();
    return lang === 'en' ? UI_STRINGS_EN : UI_STRINGS;
}

/**
 * Updates the language switcher UI to reflect the current language.
 * @param {string} lang - Current language code
 */
function updateLanguageSwitcherUI(lang) {
    const langDeLink = document.getElementById('langDe');
    const langEnLink = document.getElementById('langEn');
    if (langDeLink) langDeLink.classList.toggle('active', lang === 'de');
    if (langEnLink) langEnLink.classList.toggle('active', lang === 'en');
}

/**
 * Gets the OPTIONS_CONFIG object based on the current language.
 * @param {string} [lang] - Optional language override; if not provided, uses getLanguage()
 * @returns {Object} OPTIONS_CONFIG object for the current language
 */
function getOptionsConfig(lang = null) {
    return (lang || getLanguage()) === 'en' ? OPTIONS_CONFIG_EN : OPTIONS_CONFIG;
}

/**
 * Gets the CATEGORY_LABELS object based on the current language.
 * @param {string} [lang] - Optional language override; if not provided, uses getLanguage()
 * @returns {Object} CATEGORY_LABELS object for the current language
 */
function getCategoryLabels(lang = null) {
    return (lang || getLanguage()) === 'en' ? CATEGORY_LABELS_EN : CATEGORY_LABELS;
}

/**
 * Gets the MEDIA_FORM_LABELS object based on the current language.
 * @param {string} [lang] - Optional language override; if not provided, uses getLanguage()
 * @returns {Object} MEDIA_FORM_LABELS object for the current language
 */
function getMediaFormLabels(lang = null) {
    return (lang || getLanguage()) === 'en' ? MEDIA_FORM_LABELS_EN : MEDIA_FORM_LABELS;
}

/**
 * Gets the LANGUAGE_LABELS object based on the current language.
 * @param {string} [lang] - Optional language override; if not provided, uses getLanguage()
 * @returns {Object} LANGUAGE_LABELS object for the current language
 */
function getLanguageLabels(lang = null) {
    return (lang || getLanguage()) === 'en' ? LANGUAGE_LABELS_EN : LANGUAGE_LABELS;
}

/* ================================================================
   UI INITIALIZATION
   Populates UI elements with localized strings.
   ================================================================ */

/**
 * Initializes UI elements by populating text content, attributes, and URLs based on data-i18n-* attributes.
 * Scans the document for elements with data-i18n, data-i18n-title, data-i18n-placeholder, data-i18n-src,
 * data-i18n-alt, data-i18n-data, data-i18n-class, data-i18n-html, and data-i18n-href attributes,
 * then populates the corresponding element properties with values from UI_STRINGS or UI_ELEMENTS.
 *
 *  Uses the current language from getLanguage() to determine which strings to use.
 * @param {string} [lang] - Optional language override; if not provided, uses getLanguage()
 */
function initUI(lang = null) {
    const currentLang = lang || getLanguage();
    const strings = currentLang === 'en' ? UI_STRINGS_EN : UI_STRINGS;

    // Update language switcher active state
    updateLanguageSwitcherUI(currentLang);

    // Text content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (strings[key]) {
            el.textContent = strings[key];
        }
    });
    // Title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (strings[key]) {
            el.title = strings[key];
        }
    });
    // Placeholder attributes
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (strings[key]) {
            el.placeholder = strings[key];
        }
    });
    // Src attributes
    document.querySelectorAll('[data-i18n-src]').forEach(el => {
        const key = el.getAttribute('data-i18n-src');
        if (UI_ELEMENTS[key]) {
            el.src = UI_ELEMENTS[key];
        }
    });
    // Alt attributes
    document.querySelectorAll('[data-i18n-alt]').forEach(el => {
        const key = el.getAttribute('data-i18n-alt');
        if (strings[key]) {
            el.alt = strings[key];
        }
    });
    // Data-query attributes
    document.querySelectorAll('[data-i18n-data]').forEach(el => {
        const key = el.getAttribute('data-i18n-data');
        if (strings[key]) {
            el.setAttribute('data-query', strings[key]);
        }
    });
    // Class attributes
    document.querySelectorAll('[data-i18n-class]').forEach(el => {
        const key = el.getAttribute('data-i18n-class');
        if (UI_ELEMENTS[key]) {
            el.className = UI_ELEMENTS[key];
        }
    });
    // InnerHTML attributes
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        if (strings[key]) {
            el.innerHTML = strings[key];
        }
    });
    // Href attributes
    document.querySelectorAll('[data-i18n-href]').forEach(el => {
        const key = el.getAttribute('data-i18n-href');
        if (UI_ELEMENTS[key]) {
            el.href = UI_ELEMENTS[key];
        }
    });
}

/* ================================================================
   VUFIND PARAMETERS
   VuFind-specific URL parameters and search constants.
   Externalized for easy adaptation to different VuFind instances.
   ================================================================ */
const VUFIND_PARAMS = {
    // URL Configuration
    SEARCH_PATH: '/Search/Results',

    // Search Type Constants
    SEARCH_TYPE_ALL_FIELDS: 'AllFields',
    SEARCH_TYPE_SUBJECT: 'Subject',

    // Filter Field Prefixes (for ~field:"value" syntax)
    FILTER_FORMAT: '~format',
    FILTER_FORMAT_DETAILS: '~format_details_str_mv',
    FILTER_LANGUAGE: '~language',
    FILTER_AUTHOR: '~author_facet',
    FILTER_BK: '~bklnumber',

    // URL Parameter Names
    PARAM_LOOKFOR: 'lookfor',
    PARAM_TYPE: 'type',
    PARAM_BOOL: 'bool',
    PARAM_JOIN: 'join',
    PARAM_FILTER_ARRAY: 'filter[]',
    PARAM_DATERANGE_ARRAY: 'daterange[]',
    PARAM_PUBLISH_DATE: 'publishDate',
    PARAM_PUBLISH_DATE_FROM: 'publishDatefrom',
    PARAM_PUBLISH_DATE_TO: 'publishDateto',
    PARAM_SORT: 'sort',

    // Sort Options
    SORT_RELEVANCE: 'relevance',
    SORT_AUTHOR: 'author',
    SORT_TITLE: 'title',
    SORT_DATE: 'publishDate',
    SORT_CALLNUMBER: 'callnumber',

    // Boolean Operators
    BOOL_AND: 'AND',
    BOOL_OR: 'OR',
};

/* ================================================================
   OPTIONS CONFIGURATION (German)
   Configuration for search option categories.
   ================================================================ */
const OPTIONS_CONFIG = {
    keyword: {
        label: 'Suchbegriffe',
        icon: UI_ELEMENTS.keywordIcon,
        tooltip: 'Automatisch vorgeschlagene Suchbegriffe zu Ihrer Suche.'
    },
    topic_facet: {
        label: 'Themen',
        icon: UI_ELEMENTS.topicIcon,
        tooltip: 'Präzise Schlagwörter, die Ihre Suche auf bestimmte Themen eingrenzen.\n\nAusgewählte Optionen führen zu weniger Resultaten, erhöhen aber die Passgenauigkeit.\n\nDurch "' + UI_STRINGS.customTopicPlaceholder + '" wird eine semantische Suche in allen verfügbaren Themen ausgelöst.'
    },
    bklnumber: {
        label: 'Themenbereiche',
        icon: UI_ELEMENTS.bklIcon,
        tooltip: 'Bibliothekarische Klassifikationen, die Ihre Suche auf bestimmte Themenbereiche eingrenzen.\n\nAusgewählte Optionen führen zu weniger Resultaten, erhöhen aber die Passgenauigkeit.\n\nDurch "' + UI_STRINGS.customBlkNumberPlaceholder + '" wird eine semantische Suche in allen verfügbaren Themenbereichen ausgelöst.'
    },
    format: {
        label: 'Medientyp',
        icon: UI_ELEMENTS.formatIcon,
        tooltip: 'Inhaltstypen, die Ihre Suche auf bestimmte inhaltliche Formen (z.B. Buch, Artikel) eingrenzen.'
    },
    format_details: {
        label: 'Inhaltsgenre',
        icon: UI_ELEMENTS.formatDetailsIcon,
        tooltip: 'Inhaltstypen, die Ihre Suche auf bestimmte inhaltliche Formen (z.B. Belletristik, Konferenzschriften) eingrenzen.'
    },
    language: {
        label: 'Sprache',
        icon: UI_ELEMENTS.languageIcon,
        tooltip: 'Eingrenzen der Suche auf spezifische Sprachen des Materials.'
    },
    author_facet: {
        label: 'Autor',
        icon: UI_ELEMENTS.authorIcon,
        tooltip: 'Eingrenzen der Suche auf spezifische Autoren und Urheber.'
    },
    date: {
        label: 'Erscheinungsdatum',
        icon: UI_ELEMENTS.dateIcon,
        tooltip: 'Eingrenzen der Suche auf einen spezifischen Erscheinungszeitraum.'
    },
};

/* ================================================================
   OPTIONS CONFIGURATION (English)
   Configuration for search option categories.
   ================================================================ */
const OPTIONS_CONFIG_EN = {
    keyword: {
        label: 'Search Terms',
        icon: UI_ELEMENTS.keywordIcon,
        tooltip: 'Automatically suggested search terms for your query.'
    },
    topic_facet: {
        label: 'Topics',
        icon: UI_ELEMENTS.topicIcon,
        tooltip: 'Precise subject headings that narrow your search to specific topics.\n\nSelected options result in fewer results, but increase relevance.\n\nUsing "' + UI_STRINGS_EN.customTopicPlaceholder + '" triggers a semantic search in all available topics.'
    },
    bklnumber: {
        label: 'Subject Areas',
        icon: UI_ELEMENTS.bklIcon,
        tooltip: 'Library classifications that narrow your search to specific subject areas.\n\nSelected options result in fewer results, but increase relevance.\n\nUsing "' + UI_STRINGS_EN.customBlkNumberPlaceholder + '" triggers a semantic search in all available subject areas.'
    },
    format: {
        label: 'Media Type',
        icon: UI_ELEMENTS.formatIcon,
        tooltip: 'Content types that narrow your search to specific formats (e.g., book, article).'
    },
    format_details: {
        label: 'Content Genre',
        icon: UI_ELEMENTS.formatDetailsIcon,
        tooltip: 'Content types that narrow your search to specific genres (e.g., fiction, conference proceedings).'
    },
    language: {
        label: 'Language',
        icon: UI_ELEMENTS.languageIcon,
        tooltip: 'Narrow your search to specific languages of the material.'
    },
    author_facet: {
        label: 'Author',
        icon: UI_ELEMENTS.authorIcon,
        tooltip: 'Narrow your search to specific authors and creators.'
    },
    date: {
        label: 'Publication Date',
        icon: UI_ELEMENTS.dateIcon,
        tooltip: 'Narrow your search to a specific publication period.'
    },
};

/* ================================================================
   OPTIONS ORDER
   Defines the display order of option categories in the UI.
   ================================================================ */
const OPTIONS_ORDER = [
    'keyword',
    'topic_facet',
    'bklnumber',
    'format',
    'format_details',
    'language',
    'author_facet',
    'date'
];

/* ================================================================
   CATEGORY → DISPLAY LABEL MAPPING (German)
   Maps category keys to display labels shown on option badges.
   ================================================================ */
const CATEGORY_LABELS = {
    keyword:                'Begriff',
    topic_facet:            'Thema',
    bklnumber:              'Bereich',
    format:                 'Format',
    format_details:         'Genre',
    language:               'Sprache',
    author_facet:           'Autor',
    date:                   'Datum',
};

/* ================================================================
   CATEGORY → DISPLAY LABEL MAPPING (English)
   Maps category keys to display labels shown on option badges.
   ================================================================ */
const CATEGORY_LABELS_EN = {
    keyword:                'Term',
    topic_facet:            'Topic',
    bklnumber:              'Area',
    format:                 'Format',
    format_details:         'Genre',
    language:               'Language',
    author_facet:           'Author',
    date:                   'Date',
};

/* ================================================================
   MEDIA FORM VALUE → DISPLAY LABEL MAPPING (German)
   Maps backend media form values to German display labels.
   ================================================================ */
const MEDIA_FORM_LABELS = {
    'Article':              'Aufsatz (gedruckt)',
    'electronic Article':   'Aufsatz (online)',
    'Serial Volume':        'Band einer Zeitschrift/Zeitung',
    'Picture':              'Bild',
    'Book':                 'Buch (gedruckt)',
    'Data Media':           'Datenträger',
    'eBook':                'E-Book',
    'eJournal':             'E-Journal',
    'Motion Picture':       'Film',
    'Mixed Materials':      'Gemischte Materialien',
    'Manuscript':           'Handschrift',
    'Map':                  'Karte',
    'Microform':            'Mikroform',
    'Musical Score':        'Musikalien',
    'Projected Medium':     'Projektion',
    'Monograph Series':     'Schriftenreihe',
    'Game':                 'Spiel',
    'Sound Recording':      'Tonaufnahme',
    'Journal':              'Zeitschrift/Zeitung (gedruckt)',
};

/* ================================================================
   MEDIA FORM VALUE → DISPLAY LABEL MAPPING (English)
   Maps backend media form values to English display labels.
   ================================================================ */
const MEDIA_FORM_LABELS_EN = {
    'Article':              'Article (print)',
    'electronic Article':   'Article (online)',
    'Serial Volume':        'Volume of a journal/newspaper',
    'Picture':              'Image',
    'Book':                 'Book (print)',
    'Data Media':           'Data Media',
    'eBook':                'eBook',
    'eJournal':             'eJournal',
    'Motion Picture':       'Film',
    'Mixed Materials':      'Mixed materials',
    'Manuscript':           'Manuscript',
    'Map':                  'Map',
    'Microform':            'Microform',
    'Musical Score':        'Musical score',
    'Projected Medium':     'Projectied medium',
    'Monograph Series':     'Monograph series',
    'Game':                 'Game',
    'Sound Recording':      'Sound recording',
    'Journal':              'Journal/Newspaper (print)',
};

/* ================================================================
   LANGUAGE VALUE → DISPLAY LABEL MAPPING (German)
   Maps backend language values to German display labels.
   ================================================================ */
const LANGUAGE_LABELS = {
    'Abkhaz': 'Abchasisch',
    'Achinese': 'Achinese',
    'Acoli': 'Akoli',
    'Adygei': 'Adygei',
    'Afar': 'Afar',
    'Afrikaans': 'Afrikaans',
    'Afroasiatic (Other)': 'Afroasiatisch (Andere)',
    'Akan': 'Akan',
    'Akkadian': 'Akkadisch',
    'Albanian': 'Albanisch',
    'Aleut': 'Aleutisch',
    'Algonquian (Other)': 'Algonkisch (Andere)',
    'Altaic (Other)': 'Altaisch (Andere)',
    'Amharic': 'Amharisch',
    'Apache languages': 'Apachen-Sprachen',
    'Arabic': 'Arabisch',
    'Aragonese Spanish': 'Aragonisch Spanisch',
    'Aramaic': 'Aramäisch',
    'Arapaho': 'Arapaho',
    'Arawak': 'Arawak',
    'Armenian': 'Armenisch',
    'Artificial (Other)': 'Künstlich (Andere)',
    'Assamese': 'Assamisch',
    'Athapascan (Other)': 'Athapaskisch (Andere)',
    'Australian languages': 'Australische Sprachen',
    'Austronesian (Other)': 'Austronesisch (Andere)',
    'Avaric': 'Awarisch',
    'Avestan': 'Avestisch',
    'Awadhi': 'Awadhi',
    'Aymara': 'Aymara',
    'Azerbaijani': 'Aserbaidschanisch',
    'Bable': 'Bable',
    'Balinese': 'Balinisch',
    'Baltic (Other)': 'Baltisch (Andere)',
    'Baluchi': 'Baluchi',
    'Bambara': 'Bambara',
    'Bantu (Other)': 'Bantu (Andere)',
    'Basa': 'Basa',
    'Bashkir': 'Baschkirisch',
    'Basque': 'Baskisch',
    'Batak': 'Batak',
    'Beja': 'Beja',
    'Belarusian': 'Weißrussisch',
    'Bemba': 'Bemba',
    'Bengali': 'Bengalisch',
    'Berber (Other)': 'Berber (Andere)',
    'Bhojpuri': 'Bhojpuri',
    'Bihari': 'Bhari',
    'Bikol': 'Bikol',
    'Bislama': 'Bislama',
    'Bosnian': 'Bosnisch',
    'Braj': 'Braj',
    'Breton': 'Bretonisch',
    'Bugis': 'Bugis',
    'Bulgarian': 'Bulgarisch',
    'Buriat': 'Buriat',
    'Burmese': 'Birmanisch',
    'Caddo': 'Caddo',
    'Carib': 'Karibisch',
    'Catalan': 'Katalanisch',
    'Caucasian (Other)': 'Kaukasisch (Andere)',
    'Cebuano': 'Cebuano',
    'Celtic (Other)': 'Keltisch (Andere)',
    'Central American Indian (Other)': 'Mittelamerikanischer Indianer (Andere)',
    'Chagatai': 'Chagatai',
    'Chamic languages': 'Chamische Sprachen',
    'Chamorro': 'Chamorro',
    'Chechen': 'Tschetschenisch',
    'Cherokee': 'Cherokee',
    'Cheyenne': 'Cheyenne',
    'Chibcha': 'Chibcha',
    'Chinese': 'Chinesisch',
    'Chinook jargon': 'Chinook-Jargon',
    'Chipewyan': 'Chipewyan',
    'Choctaw': 'Choctaw',
    'Church Slavic': 'Kirchenslawisch',
    'Chuvash': 'Tschuwaschisch',
    'Coptic': 'Koptisch',
    'Cornish': 'Kornisch',
    'Corsican': 'Korsisch',
    'Cree': 'Kreeisch',
    'Creek': 'Creek',
    'Creoles and Pidgins (Other)': 'Kreolen und Pidgins (Andere)',
    'Creoles and Pidgins, English-based (Other)': 'Kreolen und Pidgins, englischsprachig (Andere)',
    'Creoles and Pidgins, French-based (Other)': 'Kreolen und Pidgins, französischsprachige (Andere)',
    'Creoles and Pidgins, Portuguese-based (Other)': 'Kreolen und Pidgins, portugiesisch-basiert (Andere)',
    'Crimean Tatar': 'Krimtatarisch',
    'Croatian': 'Kroatisch',
    'Cushitic (Other)': 'Kuschitisch (Andere)',
    'Czech': 'Tschechisch',
    'Dakota': 'Dakota',
    'Danish': 'Dänisch',
    'Dargwa': 'Dargwa',
    'Dayak': 'Dayak',
    'Delaware': 'Delaware',
    'Dinka': 'Dinka',
    'Divehi': 'Divehi',
    'Dogri': 'Dogri',
    'Dravidian (Other)': 'Dravidisch (Andere)',
    'Duala': 'Duala',
    'Dutch, Middle (ca. 1050-1350)': 'Niederländisch, mittel (ca. 1050-1350)',
    'Dutch': 'Niederländisch',
    'Dzongkha': 'Dzongkha',
    'Edo': 'Edo',
    'Efik': 'Efik',
    'Egyptian': 'Ägyptisch',
    'Elamite': 'Elamitisch',
    'English, Middle (1100-1500)': 'Englisch, Mittelenglisch (1100-1500)',
    'English, Old (ca. 450-1100)': 'Englisch, Alt-Englisch (ca. 450-1100)',
    'English': 'Englisch',
    'Eskimo languages': 'Eskimo-Sprachen',
    'Esperanto': 'Esperanto',
    'Estonian': 'Estnisch',
    'Ethiopic': 'Äthiopisch',
    'Ewe': 'Ewe',
    'Ewondo': 'Ewondo',
    'Fang': 'Fang',
    'Fanti': 'Fanti',
    'Faroese': 'Färöisch',
    'Fijian': 'Fidschianisch',
    'Finnish': 'Finnisch',
    'Finno-Ugrian (Other)': 'Finno-Ugrisch (Andere)',
    'Fon': 'Fon',
    'French, Middle (ca. 1400-1600)': 'Französisch, mittelfranzösisch (ca. 1400-1600)',
    'French, Old (ca. 842-1400)': 'Französisch, Altfranzösisch (ca. 842-1400)',
    'French': 'Französisch',
    'Frisian': 'Friesisch',
    'Friulian': 'Friaulisch',
    'Fula': 'Fula',
    'Ga': 'Ga',
    'Galician': 'Galicisch',
    'Ganda': 'Ganda',
    'Gayo': 'Gayo',
    'Gbaya': 'Gbaya',
    'Georgian': 'Georgisch',
    'German, Middle High (ca. 1050-1500)': 'Deutsch, Mittelhochdeutsch (ca. 1050-1500)',
    'German, Old High (ca. 750-1050)': 'Deutsch, Althochdeutsch (ca. 750-1050)',
    'German': 'Deutsch',
    'Germanic (Other)': 'Germanisch (Andere)',
    'Gilbertese': 'Gilbertisch',
    'Gondi': 'Gondi',
    'Gothic': 'Gotisch',
    'Grebo': 'Grebo',
    'Greek, Ancient (to 1453)': 'Griechisch, Altgriechisch (bis 1453)',
    'Greek, Modern (1453- )': 'Griechisch, Neuzeitlich (1453- )',
    'Guarani': 'Guarani',
    'Gujarati': 'Gujarati',
    'Gwich-in': 'Gwich-in',
    'Haida': 'Haida',
    'Haitian French Creole': 'Haitianisches Französisch-Kreolisch',
    'Hausa': 'Hausa',
    'Hawaiian': 'Hawaiianisch',
    'Hebrew': 'Hebräisch',
    'Herero': 'Herero',
    'Hiligaynon': 'Hiligaynon',
    'Himachali': 'Himachali',
    'Hindi': 'Hindi',
    'Hiri Motu': 'Hiri Motu',
    'Hittite': 'Hethitisch',
    'Hmong': 'Hmong',
    'Hungarian': 'Ungarisch',
    'Iban': 'Ibanisch',
    'Icelandic': 'Isländisch',
    'Ido': 'Ido',
    'Igbo': 'Igbo',
    'Ijo': 'Ijo',
    'Iloko': 'Iloko',
    'Indic (Other)': 'Indisch (Andere)',
    'Indo-European (Other)': 'Indo-Europäisch (Andere)',
    'Indonesian': 'Indonesisch',
    'Ingush': 'Inguschisch',
    'Interlingua (International Auxiliary Language Association)': 'Interlingua (Internationale Vereinigung der Hilfssprachen)',
    'Interlingue': 'Interlingue',
    'Inuktitut': 'Inuktitut',
    'Inupiaq': 'Inupiaq',
    'Iranian (Other)': 'Iranisch (Andere)',
    'Irish, Middle (ca. 1100-1550)': 'Irisch, mittel (ca. 1100-1550)',
    'Irish, Old (to 1100)': 'Irisch, Alt (bis 1100)',
    'Irish': 'Irisch',
    'Iroquoian (Other)': 'Irokesen (Andere)',
    'Italian': 'Italienisch',
    'Japanese': 'Japanisch',
    'Javanese': 'Javanisch',
    'Judeo-Arabic': 'Judäo-Arabisch',
    'Judeo-Persian': 'Judäo-Persisch',
    'Kabardian': 'Kabardisch',
    'Kabyle': 'Kabyleisch',
    'Kachin': 'Kachinisch',
    'Kalatdlisut': 'Kalatdlisut',
    'Kalmyk': 'Kalmücken',
    'Kamba': 'Kamba',
    'Kannada': 'Kannada',
    'Kanuri': 'Kanuri',
    'Kara-Kalpak': 'Kara-Kalpak',
    'Karen': 'Karen',
    'Kashmiri': 'Kaschmir',
    'Kawi': 'Kawi',
    'Kazakh': 'Kasachisch',
    'Khasi': 'Khasi',
    'Khmer': 'Khmer',
    'Khoisan (Other)': 'Khoisan (Andere)',
    'Khotanese': 'Khotanisch',
    'Kikuyu': 'Kikuyu',
    'Kimbundu': 'Kimbundu',
    'Kinyarwanda': 'Kinyarwanda',
    'Komi': 'Komi',
    'Kongo': 'Kongo',
    'Konkani': 'Konkani',
    'Korean': 'Koreanisch',
    'Kpelle': 'Kpelle',
    'Kru': 'Kru',
    'Kuanyama': 'Kuanyama',
    'Kumyk': 'Kumyk',
    'Kurdish': 'Kurdisch',
    'Kurukh': 'Kurukh',
    'Kusaie': 'Kusaie',
    'Kyrgyz': 'Kirgisisch',
    'Ladino': 'Ladino',
    'Lahnda': 'Lahnda',
    'Lamba': 'Lamba',
    'Lao': 'Laotisch',
    'Latin': 'Lateinisch',
    'Latvian': 'Lettisch',
    'Letzeburgesch': 'Letzeburgisch',
    'Lezgian': 'Lezgisch',
    'Limburgish': 'Limburgisch',
    'Lingala': 'Lingala',
    'Lithuanian': 'Litauisch',
    'Low German': 'Niederdeutsch',
    'Lozi': 'Lozi',
    'Luba-Katanga': 'Luba-Katanga',
    'Luba-Lulua': 'Luba-Lulua',
    'Lunda': 'Lunda',
    'Luo (Kenya and Tanzania)': 'Luo (Kenia und Tansania)',
    'Lushai': 'Lushai',
    'Macedonian': 'Mazedonisch',
    'Madurese': 'Madurisch',
    'Magahi': 'Magahi',
    'Maithili': 'Maithili',
    'Makasar': 'Makasar',
    'Malagasy': 'Madagassisch',
    'Malay': 'Malaiisch',
    'Malayalam': 'Malayalam',
    'Maltese': 'Maltesisch',
    'Manchu': 'Mandschu',
    'Mandar': 'Mandar',
    'Mandingo': 'Mandingo',
    'Manipuri': 'Manipuri',
    'Manobo languages': 'Manobo-Sprachen',
    'Manx': 'Manx',
    'Maori': 'Maori',
    'Mapuche': 'Mapuche',
    'Marathi': 'Marathi',
    'Mari': 'Mari',
    'Marshallese': 'Marschallisch',
    'Marwari': 'Marwari',
    'Masai': 'Massai',
    'Mayan languages': 'Maya-Sprachen',
    'Mende': 'Mende',
    'Micmac': 'Micmac',
    'Minangkabau': 'Minangkabau',
    'Miscellaneous languages': 'Verschiedene Sprachen',
    'Mohawk': 'Mohawk',
    'Mon-Khmer (Other)': 'Mon-Khmer (Andere)',
    'Mongo-Nkundu': 'Mongo-Nkundu',
    'Mongolian': 'Mongolisch',
    'Moore': 'Moore',
    'Multiple languages': 'Mehrere Sprachen',
    'Munda (Other)': 'Munda (Andere)',
    'Nahuatl': 'Nahuatl',
    'Nauru': 'Nauru',
    'Navajo': 'Navajo',
    'Ndebele (South Africa)': 'Ndebele (Südafrika)',
    'Ndebele (Zimbabwe)': 'Ndebele (Simbabwe)',
    'Ndonga': 'Ndonga',
    'Neapolitan Italian': 'Neapolitanisch Italienisch',
    'Nepali': 'Nepalesisch',
    'Newari': 'Newari',
    'Nias': 'Nias',
    'Niger-Kordofanian (Other)': 'Niger-Kordofanisch (Andere)',
    'Nilo-Saharan (Other)': 'Nilo-Saharanisch (Andere)',
    'Niuean': 'Niuéisch',
    'Nogai': 'Nogai',
    'North American Indian (Other)': 'Nordamerikanische Indianer (Andere)',
    'Northern Sami': 'Nördliche Sami',
    'Northern Sotho': 'Nördliche Sotho',
    'Norwegian (Bokmal)': 'Norwegisch (Bokmal)',
    'Norwegian (Nynorsk)': 'Norwegisch (Nynorsk)',
    'Norwegian': 'Norweger',
    'Nubian languages': 'Nubische Sprachen',
    'Nyamwezi': 'Njamwezi',
    'Nyanja': 'Nyanja',
    'Nyankole': 'Nyankole',
    'Occitan (post-1500)': 'Okzitanisch (nach 1500)',
    'Ojibwa': 'Ojibwa',
    'Old Norse': 'Altnordisch',
    'Old Persian (ca. 600-400 B.C.)': 'Altpersisch (ca. 600-400 v. Chr.)',
    'Oriya': 'Oriya',
    'Oromo': 'Oromo',
    'Osage': 'Osage',
    'Ossetic': 'Ossetisch',
    'Otomian languages': 'Otromische Sprachen',
    'Pahlavi': 'Pahlavisch',
    'Palauan': 'Palauisch',
    'Pali': 'Pali',
    'Pampanga': 'Pampanga',
    'Panjabi': 'Panjabi',
    'Papiamento': 'Papiamento',
    'Papuan (Other)': 'Papua (Andere)',
    'Persian': 'Persisch',
    'Philippine (Other)': 'Philippinisch (Andere)',
    'Phoenician': 'Phönizisch',
    'Polish': 'Polnisch',
    'Ponape': 'Ponape',
    'Portuguese': 'Portugiesisch',
    'Prakrit languages': 'Prakrit-Sprachen',
    'Provencal (to 1500)': 'Provenzalisch (bis 1500)',
    'Pushto': 'Pushto',
    'Quechua': 'Quechua',
    'Raeto-Romance': 'Rätoromanisch',
    'Rajasthani': 'Rajasthanisch',
    'Rapanui': 'Rapanui',
    'Rarotongan': 'Rarotonga',
    'Romance (Other)': 'Romanes (Andere)',
    'Romani': 'Rumänisch',
    'Romanian': 'Rumänisch',
    'Rundi': 'Rundi',
    'Russian': 'Russisch',
    'Salishan languages': 'Salitische Sprachen',
    'Samaritan Aramaic': 'Samaritanisches Aramäisch',
    'Sami': 'Samisch',
    'Samoan': 'Samoanisch',
    'Sango (Ubangi Creole)': 'Sango (Ubangi Kreolisch)',
    'Sanskrit': 'Sanskrit',
    'Santali': 'Santali',
    'Sardinian': 'Sardisch',
    'Sasak': 'Sasak',
    'Scots': 'Schottisch',
    'Scottish Gaelic': 'Schottisch-Gälisch',
    'Selkup': 'Selkup',
    'Semitic (Other)': 'Semitisch (Andere)',
    'Serbian': 'Serbisch',
    'Serer': 'Serer',
    'Shan': 'Shan',
    'Shona': 'Schona',
    'Sichuan Yi': 'Sichuan Yi',
    'Sidamo': 'Sidamo',
    'Siksika': 'Siksika',
    'Sindhi': 'Sindhi',
    'Sinhalese': 'Singhalesisch',
    'Sino-Tibetan (Other)': 'Sino-Tibetisch (Andere)',
    'Siouan (Other)': 'Siouanisch (Andere)',
    'Skolt Sami': 'Skolt Samisch',
    'Slave': 'Sklave',
    'Slavic (Other)': 'Slawisch (Andere)',
    'Slovak': 'Slowakisch',
    'Slovenian': 'Slowenisch',
    'Sogdian': 'Sogdisch',
    'Somali': 'Somalisch',
    'Songhai': 'Songhai',
    'Soninke': 'Soninke',
    'Sorbian languages': 'Sorbische Sprachen',
    'Sotho': 'Sotho',
    'South American Indian (Other)': 'Südamerikanische Indianer (Andere)',
    'Southern Sami': 'Südliche Sami',
    'Spanish': 'Spanisch',
    'Sukuma': 'Sukuma',
    'Sumerian': 'Sumerisch',
    'Sundanese': 'Sundanisch',
    'Susu': 'Susu',
    'Swahili': 'Suaheli',
    'Swazi': 'Suaheli',
    'Swedish': 'Schwedisch',
    'Syriac': 'Syrisch',
    'Tagalog': 'Tagalog',
    'Tahitian': 'Tahitisch',
    'Tai (Other)': 'Tai (Andere)',
    'Tajik': 'Tadschikisch',
    'Tamashek': 'Tamashek',
    'Tamil': 'Tamilisch',
    'Tatar': 'Tatarisch',
    'Telugu': 'Telugu',
    'Temne': 'Temne',
    'Terena': 'Terena',
    'Tetum': 'Tetum',
    'Thai': 'Thailändisch',
    'Tibetan': 'Tibetisch',
    'Tigre': 'Tigre',
    'Tigrinya': 'Tigrinya',
    'Tiv': 'Tiv',
    'Tlingit': 'Tlingitisch',
    'Tok Pisin': 'Tok Pisin',
    'Tokelauan': 'Tokelauisch',
    'Tonga (Nyasa)': 'Tonga (Nyasa)',
    'Tongan': 'Tonga',
    'Truk': 'Truk',
    'Tsonga': 'Tsonga',
    'Tswana': 'Tswana',
    'Tumbuka': 'Tumbuka',
    'Tupi languages': 'Tupi-Sprachen',
    'Turkish, Ottoman': 'Türkisch, Osmanisch',
    'Turkish': 'Türkisch',
    'Turkmen': 'Turkmenisch',
    'Tuvaluan': 'Tuvaluisch',
    'Tuvinian': 'Tuwinisch',
    'Twi': 'Twi',
    'Udmurt': 'Udmurtisch',
    'Ugaritic': 'Ugaritisch',
    'Uighur': 'Uigurisch',
    'Ukrainian': 'Ukrainisch',
    'Umbundu': 'Umbundu',
    'Undetermined': 'Unbestimmt',
    'Urdu': 'Urdu',
    'Uzbek': 'Usbekisch',
    'Vai': 'Vai',
    'Venda': 'Venda',
    'Vietnamese': 'Vietnamesisch',
    'Volapuk': 'Volapuk',
    'Votic': 'Votisch',
    'Wakashan languages': 'Wakaschanische Sprachen',
    'Walamo': 'Walamo',
    'Walloon': 'Wallonisch',
    'Waray': 'Waray',
    'Welsh': 'Walisisch',
    'Wolof': 'Wolof',
    'Xhosa': 'Xhosa',
    'Yakut': 'Jakutisch',
    'Yao (Africa)': 'Yao (Afrika)',
    'Yapese': 'Japsen',
    'Yiddish': 'Jiddisch',
    'Yoruba': 'Yoruba',
    'Yupik languages': 'Yupik-Sprachen',
    'Zande': 'Zande',
    'Zapotec': 'Zapotekisch',
    'Zenaga': 'Zenaga',
    'Zhuang': 'Zhuang',
    'Zulu': 'Zulu',
    'Zuni': 'Zuni',
};

/* ================================================================
   LANGUAGE VALUE → DISPLAY LABEL MAPPING (English)
   Maps backend language values to English display labels.
   ================================================================ */
const LANGUAGE_LABELS_EN = {
    'Abkhaz': 'Abkhaz',
    'Achinese': 'Achinese',
    'Acoli': 'Acoli',
    'Adygei': 'Adygei',
    'Afar': 'Afar',
    'Afrikaans': 'Afrikaans',
    'Afroasiatic (Other)': 'Afroasiatic (Other)',
    'Akan': 'Akan',
    'Akkadian': 'Akkadian',
    'Albanian': 'Albanian',
    'Aleut': 'Aleut',
    'Algonquian (Other)': 'Algonquian (Other)',
    'Altaic (Other)': 'Altaic (Other)',
    'Amharic': 'Amharic',
    'Apache languages': 'Apache languages',
    'Arabic': 'Arabic',
    'Aragonese Spanish': 'Aragonese Spanish',
    'Aramaic': 'Aramaic',
    'Arapaho': 'Arapaho',
    'Arawak': 'Arawak',
    'Armenian': 'Armenian',
    'Artificial (Other)': 'Artificial (Other)',
    'Assamese': 'Assamese',
    'Athapascan (Other)': 'Athapascan (Other)',
    'Australian languages': 'Australian languages',
    'Austronesian (Other)': 'Austronesian (Other)',
    'Avaric': 'Avaric',
    'Avestan': 'Avestan',
    'Awadhi': 'Awadhi',
    'Aymara': 'Aymara',
    'Azerbaijani': 'Azerbaijani',
    'Bable': 'Bable',
    'Balinese': 'Balinese',
    'Baltic (Other)': 'Baltic (Other)',
    'Baluchi': 'Baluchi',
    'Bambara': 'Bambara',
    'Bantu (Other)': 'Bantu (Other)',
    'Basa': 'Basa',
    'Bashkir': 'Bashkir',
    'Basque': 'Basque',
    'Batak': 'Batak',
    'Beja': 'Beja',
    'Belarusian': 'Belarusian',
    'Bemba': 'Bemba',
    'Bengali': 'Bengali',
    'Berber (Other)': 'Berber (Other)',
    'Bhojpuri': 'Bhojpuri',
    'Bihari': 'Bihari',
    'Bikol': 'Bikol',
    'Bislama': 'Bislama',
    'Bosnian': 'Bosnian',
    'Braj': 'Braj',
    'Breton': 'Breton',
    'Bugis': 'Bugis',
    'Bulgarian': 'Bulgarian',
    'Buriat': 'Buriat',
    'Burmese': 'Burmese',
    'Caddo': 'Caddo',
    'Carib': 'Carib',
    'Catalan': 'Catalan',
    'Caucasian (Other)': 'Caucasian (Other)',
    'Cebuano': 'Cebuano',
    'Celtic (Other)': 'Celtic (Other)',
    'Central American Indian (Other)': 'Central American Indian (Other)',
    'Chagatai': 'Chagatai',
    'Chamic languages': 'Chamic languages',
    'Chamorro': 'Chamorro',
    'Chechen': 'Chechen',
    'Cherokee': 'Cherokee',
    'Cheyenne': 'Cheyenne',
    'Chibcha': 'Chibcha',
    'Chinese': 'Chinese',
    'Chinook jargon': 'Chinook jargon',
    'Chipewyan': 'Chipewyan',
    'Choctaw': 'Choctaw',
    'Church Slavic': 'Church Slavic',
    'Chuvash': 'Chuvash',
    'Coptic': 'Coptic',
    'Cornish': 'Cornish',
    'Corsican': 'Corsican',
    'Cree': 'Cree',
    'Creek': 'Creek',
    'Creoles and Pidgins (Other)': 'Creoles and Pidgins (Other)',
    'Creoles and Pidgins, English-based (Other)': 'Creoles and Pidgins, English-based (Other)',
    'Creoles and Pidgins, French-based (Other)': 'Creoles and Pidgins, French-based (Other)',
    'Creoles and Pidgins, Portuguese-based (Other)': 'Creoles and Pidgins, Portuguese-based (Other)',
    'Crimean Tatar': 'Crimean Tatar',
    'Croatian': 'Croatian',
    'Cushitic (Other)': 'Cushitic (Other)',
    'Czech': 'Czech',
    'Dakota': 'Dakota',
    'Danish': 'Danish',
    'Dargwa': 'Dargwa',
    'Dayak': 'Dayak',
    'Delaware': 'Delaware',
    'Dinka': 'Dinka',
    'Divehi': 'Divehi',
    'Dogri': 'Dogri',
    'Dravidian (Other)': 'Dravidian (Other)',
    'Duala': 'Duala',
    'Dutch, Middle (ca. 1050-1350)': 'Dutch, Middle (ca. 1050-1350)',
    'Dutch': 'Dutch',
    'Dzongkha': 'Dzongkha',
    'Edo': 'Edo',
    'Efik': 'Efik',
    'Egyptian': 'Egyptian',
    'Elamite': 'Elamite',
    'English, Middle (1100-1500)': 'English, Middle (1100-1500)',
    'English, Old (ca. 450-1100)': 'English, Old (ca. 450-1100)',
    'English': 'English',
    'Eskimo languages': 'Eskimo languages',
    'Esperanto': 'Esperanto',
    'Estonian': 'Estonian',
    'Ethiopic': 'Ethiopic',
    'Ewe': 'Ewe',
    'Ewondo': 'Ewondo',
    'Fang': 'Fang',
    'Fanti': 'Fanti',
    'Faroese': 'Faroese',
    'Fijian': 'Fijian',
    'Finnish': 'Finnish',
    'Finno-Ugrian (Other)': 'Finno-Ugrian (Other)',
    'Fon': 'Fon',
    'French, Middle (ca. 1400-1600)': 'French, Middle (ca. 1400-1600)',
    'French, Old (ca. 842-1400)': 'French, Old (ca. 842-1400)',
    'French': 'French',
    'Frisian': 'Frisian',
    'Friulian': 'Friulian',
    'Fula': 'Fula',
    'Ga': 'Ga',
    'Galician': 'Galician',
    'Ganda': 'Ganda',
    'Gayo': 'Gayo',
    'Gbaya': 'Gbaya',
    'Georgian': 'Georgian',
    'German, Middle High (ca. 1050-1500)': 'German, Middle High (ca. 1050-1500)',
    'German, Old High (ca. 750-1050)': 'German, Old High (ca. 750-1050)',
    'German': 'German',
    'Germanic (Other)': 'Germanic (Other)',
    'Gilbertese': 'Gilbertese',
    'Gondi': 'Gondi',
    'Gothic': 'Gothic',
    'Grebo': 'Grebo',
    'Greek, Ancient (to 1453)': 'Greek, Ancient (to 1453)',
    'Greek, Modern (1453- )': 'Greek, Modern (1453-)',
    'Guarani': 'Guarani',
    'Gujarati': 'Gujarati',
    'Gwich-in': 'Gwich-in',
    'Haida': 'Haida',
    'Haitian French Creole': 'Haitian French Creole',
    'Hausa': 'Hausa',
    'Hawaiian': 'Hawaiian',
    'Hebrew': 'Hebrew',
    'Herero': 'Herero',
    'Hiligaynon': 'Hiligaynon',
    'Himachali': 'Himachali',
    'Hindi': 'Hindi',
    'Hiri Motu': 'Hiri Motu',
    'Hittite': 'Hittite',
    'Hmong': 'Hmong',
    'Hungarian': 'Hungarian',
    'Iban': 'Iban',
    'Icelandic': 'Icelandic',
    'Ido': 'Ido',
    'Igbo': 'Igbo',
    'Ijo': 'Ijo',
    'Iloko': 'Iloko',
    'Indic (Other)': 'Indic (Other)',
    'Indo-European (Other)': 'Indo-European (Other)',
    'Indonesian': 'Indonesian',
    'Ingush': 'Ingush',
    'Interlingua (International Auxiliary Language Association)': 'Interlingua (International Auxiliary Language Association)',
    'Interlingue': 'Interlingue',
    'Inuktitut': 'Inuktitut',
    'Inupiaq': 'Inupiaq',
    'Iranian (Other)': 'Iranian (Other)',
    'Irish, Middle (ca. 1100-1550)': 'Irish, Middle (ca. 1100-1550)',
    'Irish, Old (to 1100)': 'Irish, Old (to 1100)',
    'Irish': 'Irish',
    'Iroquoian (Other)': 'Iroquoian (Other)',
    'Italian': 'Italian',
    'Japanese': 'Japanese',
    'Javanese': 'Javanese',
    'Judeo-Arabic': 'Judeo-Arabic',
    'Judeo-Persian': 'Judeo-Persian',
    'Kabardian': 'Kabardian',
    'Kabyle': 'Kabyle',
    'Kachin': 'Kachin',
    'Kalatdlisut': 'Kalatdlisut',
    'Kalmyk': 'Kalmyk',
    'Kamba': 'Kamba',
    'Kannada': 'Kannada',
    'Kanuri': 'Kanuri',
    'Kara-Kalpak': 'Kara-Kalpak',
    'Karen': 'Karen',
    'Kashmiri': 'Kashmiri',
    'Kawi': 'Kawi',
    'Kazakh': 'Kazakh',
    'Khasi': 'Khasi',
    'Khmer': 'Khmer',
    'Khoisan (Other)': 'Khoisan (Other)',
    'Khotanese': 'Khotanese',
    'Kikuyu': 'Kikuyu',
    'Kimbundu': 'Kimbundu',
    'Kinyarwanda': 'Kinyarwanda',
    'Komi': 'Komi',
    'Kongo': 'Kongo',
    'Konkani': 'Konkani',
    'Korean': 'Korean',
    'Kpelle': 'Kpelle',
    'Kru': 'Kru',
    'Kuanyama': 'Kuanyama',
    'Kumyk': 'Kumyk',
    'Kurdish': 'Kurdish',
    'Kurukh': 'Kurukh',
    'Kusaie': 'Kusaie',
    'Kyrgyz': 'Kyrgyz',
    'Ladino': 'Ladino',
    'Lahnda': 'Lahnda',
    'Lamba': 'Lamba',
    'Lao': 'Lao',
    'Latin': 'Latin',
    'Latvian': 'Latvian',
    'Letzeburgesch': 'Letzeburgesch',
    'Lezgian': 'Lezgian',
    'Limburgish': 'Limburgish',
    'Lingala': 'Lingala',
    'Lithuanian': 'Lithuanian',
    'Low German': 'Low German',
    'Lozi': 'Lozi',
    'Luba-Katanga': 'Luba-Katanga',
    'Luba-Lulua': 'Luba-Lulua',
    'Lunda': 'Lunda',
    'Luo (Kenya and Tanzania)': 'Luo (Kenya and Tanzania)',
    'Lushai': 'Lushai',
    'Macedonian': 'Macedonian',
    'Madurese': 'Madurese',
    'Magahi': 'Magahi',
    'Maithili': 'Maithili',
    'Makasar': 'Makasar',
    'Malagasy': 'Malagasy',
    'Malay': 'Malay',
    'Malayalam': 'Malayalam',
    'Maltese': 'Maltese',
    'Manchu': 'Manchu',
    'Mandar': 'Mandar',
    'Mandingo': 'Mandingo',
    'Manipuri': 'Manipuri',
    'Manobo languages': 'Manobo languages',
    'Manx': 'Manx',
    'Maori': 'Maori',
    'Mapuche': 'Mapuche',
    'Marathi': 'Marathi',
    'Mari': 'Mari',
    'Marshallese': 'Marshallese',
    'Marwari': 'Marwari',
    'Masai': 'Masai',
    'Mayan languages': 'Mayan languages',
    'Mende': 'Mende',
    'Micmac': 'Micmac',
    'Minangkabau': 'Minangkabau',
    'Miscellaneous languages': 'Miscellaneous languages',
    'Mohawk': 'Mohawk',
    'Mon-Khmer (Other)': 'Mon-Khmer (Other)',
    'Mongo-Nkundu': 'Mongo-Nkundu',
    'Mongolian': 'Mongolian',
    'Moore': 'Moore',
    'Multiple languages': 'Multiple languages',
    'Munda (Other)': 'Munda (Other)',
    'Nahuatl': 'Nahuatl',
    'Nauru': 'Nauru',
    'Navajo': 'Navajo',
    'Ndebele (South Africa)': 'Ndebele (South Africa)',
    'Ndebele (Zimbabwe)': 'Ndebele (Zimbabwe)',
    'Ndonga': 'Ndonga',
    'Neapolitan Italian': 'Neapolitan Italian',
    'Nepali': 'Nepali',
    'Newari': 'Newari',
    'Nias': 'Nias',
    'Niger-Kordofanian (Other)': 'Niger-Kordofanian (Other)',
    'Nilo-Saharan (Other)': 'Nilo-Saharan (Other)',
    'Niuean': 'Niuean',
    'Nogai': 'Nogai',
    'North American Indian (Other)': 'North American Indian (Other)',
    'Northern Sami': 'Northern Sami',
    'Northern Sotho': 'Northern Sotho',
    'Norwegian (Bokmal)': 'Norwegian (Bokmal)',
    'Norwegian (Nynorsk)': 'Norwegian (Nynorsk)',
    'Norwegian': 'Norwegian',
    'Nubian languages': 'Nubian languages',
    'Nyamwezi': 'Nyamwezi',
    'Nyanja': 'Nyanja',
    'Nyankole': 'Nyankole',
    'Occitan (post-1500)': 'Occitan (post-1500)',
    'Ojibwa': 'Ojibwa',
    'Old Norse': 'Old Norse',
    'Old Persian (ca. 600-400 B.C.)': 'Old Persian (ca. 600-400 B.C.)',
    'Oriya': 'Oriya',
    'Oromo': 'Oromo',
    'Osage': 'Osage',
    'Ossetic': 'Ossetic',
    'Otomian languages': 'Otomian languages',
    'Pahlavi': 'Pahlavi',
    'Palauan': 'Palauan',
    'Pali': 'Pali',
    'Pampanga': 'Pampanga',
    'Panjabi': 'Panjabi',
    'Papiamento': 'Papiamento',
    'Papuan (Other)': 'Papuan (Other)',
    'Persian': 'Persian',
    'Philippine (Other)': 'Philippine (Other)',
    'Phoenician': 'Phoenician',
    'Polish': 'Polish',
    'Ponape': 'Ponape',
    'Portuguese': 'Portuguese',
    'Prakrit languages': 'Prakrit languages',
    'Provencal (to 1500)': 'Provencal (to 1500)',
    'Pushto': 'Pushto',
    'Quechua': 'Quechua',
    'Raeto-Romance': 'Raeto-Romance',
    'Rajasthani': 'Rajasthani',
    'Rapanui': 'Rapanui',
    'Rarotongan': 'Rarotongan',
    'Romance (Other)': 'Romance (Other)',
    'Romani': 'Romani',
    'Romanian': 'Romanian',
    'Rundi': 'Rundi',
    'Russian': 'Russian',
    'Salishan languages': 'Salishan languages',
    'Samaritan Aramaic': 'Samaritan Aramaic',
    'Sami': 'Sami',
    'Samoan': 'Samoan',
    'Sango (Ubangi Creole)': 'Sango (Ubangi Creole)',
    'Sanskrit': 'Sanskrit',
    'Santali': 'Santali',
    'Sardinian': 'Sardinian',
    'Sasak': 'Sasak',
    'Scots': 'Scots',
    'Scottish Gaelic': 'Scottish Gaelic',
    'Selkup': 'Selkup',
    'Semitic (Other)': 'Semitic (Other)',
    'Serbian': 'Serbian',
    'Serer': 'Serer',
    'Shan': 'Shan',
    'Shona': 'Shona',
    'Sichuan Yi': 'Sichuan Yi',
    'Sidamo': 'Sidamo',
    'Siksika': 'Siksika',
    'Sindhi': 'Sindhi',
    'Sinhalese': 'Sinhalese',
    'Sino-Tibetan (Other)': 'Sino-Tibetan (Other)',
    'Siouan (Other)': 'Siouan (Other)',
    'Skolt Sami': 'Skolt Sami',
    'Slave': 'Slave',
    'Slavic (Other)': 'Slavic (Other)',
    'Slovak': 'Slovak',
    'Slovenian': 'Slovenian',
    'Sogdian': 'Sogdian',
    'Somali': 'Somali',
    'Songhai': 'Songhai',
    'Soninke': 'Soninke',
    'Sorbian languages': 'Sorbian languages',
    'Sotho': 'Sotho',
    'South American Indian (Other)': 'South American Indian (Other)',
    'Southern Sami': 'Southern Sami',
    'Spanish': 'Spanish',
    'Sukuma': 'Sukuma',
    'Sumerian': 'Sumerian',
    'Sundanese': 'Sundanese',
    'Susu': 'Susu',
    'Swahili': 'Swahili',
    'Swazi': 'Swazi',
    'Swedish': 'Swedish',
    'Syriac': 'Syriac',
    'Tagalog': 'Tagalog',
    'Tahitian': 'Tahitian',
    'Tai (Other)': 'Tai (Other)',
    'Tajik': 'Tajik',
    'Tamashek': 'Tamashek',
    'Tamil': 'Tamil',
    'Tatar': 'Tatar',
    'Telugu': 'Telugu',
    'Temne': 'Temne',
    'Terena': 'Terena',
    'Tetum': 'Tetum',
    'Thai': 'Thai',
    'Tibetan': 'Tibetan',
    'Tigre': 'Tigre',
    'Tigrinya': 'Tigrinya',
    'Tiv': 'Tiv',
    'Tlingit': 'Tlingit',
    'Tok Pisin': 'Tok Pisin',
    'Tokelauan': 'Tokelauan',
    'Tonga (Nyasa)': 'Tonga (Nyasa)',
    'Tongan': 'Tongan',
    'Truk': 'Truk',
    'Tsonga': 'Tsonga',
    'Tswana': 'Tswana',
    'Tumbuka': 'Tumbuka',
    'Tupi languages': 'Tupi languages',
    'Turkish, Ottoman': 'Turkish, Ottoman',
    'Turkish': 'Turkish',
    'Turkmen': 'Turkmen',
    'Tuvaluan': 'Tuvaluan',
    'Tuvinian': 'Tuvinian',
    'Twi': 'Twi',
    'Udmurt': 'Udmurt',
    'Ugaritic': 'Ugaritic',
    'Uighur': 'Uighur',
    'Ukrainian': 'Ukrainian',
    'Umbundu': 'Umbundu',
    'Undetermined': 'Undetermined',
    'Urdu': 'Urdu',
    'Uzbek': 'Uzbek',
    'Vai': 'Vai',
    'Venda': 'Venda',
    'Vietnamese': 'Vietnamese',
    'Volapuk': 'Volapuk',
    'Votic': 'Votic',
    'Wakashan languages': 'Wakashan languages',
    'Walamo': 'Walamo',
    'Walloon': 'Walloon',
    'Waray': 'Waray',
    'Welsh': 'Welsh',
    'Wolof': 'Wolof',
    'Xhosa': 'Xhosa',
    'Yakut': 'Yakut',
    'Yao (Africa)': 'Yao (Africa)',
    'Yapese': 'Yapese',
    'Yiddish': 'Yiddish',
    'Yoruba': 'Yoruba',
    'Yupik languages': 'Yupik languages',
    'Zande': 'Zande',
    'Zapotec': 'Zapotec',
    'Zenaga': 'Zenaga',
    'Zhuang': 'Zhuang',
    'Zulu': 'Zulu',
    'Zuni': 'Zuni',
};
