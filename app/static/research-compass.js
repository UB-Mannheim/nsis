/* ================================================================
   STATE
   Single source of truth for the research compass UI. (persisted to history)
   ================================================================ */
const STATE = {

    // Search context
    history: [], // Recent searches with snapshots for restoration
    query: '', // Current search query string

    // Options (facets, keywords, filters)
    options: [], // Active options from QE/QT pipeline results; toggleable by user
    initialOptions: [], // Deep copy of options after search pipeline initally completes; used by resetOptions

    // Pipeline results
    siMeta: null, // Search intent metadata (search intention)
    qeMeta: null, // Query expansion metadata (expanded keywords)
    qtMeta: null, // Query transformation metadata (filters, GND headings, BK notations, date ranges)

    // Explicit concept storage for logical tree construction
    qeConcepts: {
        positive: {},
        negative: {}
    }, // QE concepts: concept key -> terms
    qtConcepts: {
        positive: {},
        negative: {}
    }, // QT concepts: concept key -> terms (negative always empty for topicHeadings)

    // VuFind results
    vufindResults: [], // Preview titles from VuFind for result validation
    totalResults: null, // Total result count from VuFind for history restoration

    // Query quality assessment
    qualityScore: null, // Score 0–1 indicating URL match quality
    qualityAssessment: '', // Human-readable explanation of the quality score
    relevantIndices: [], // Indices (1-based) of relevant titles from query quality assessment

    // URL generation
    generatedUrl: '', // Fully constructed VuFind search URL from active options

};

/* ================================================================
   STATE_UI
   Transient UI state (not persisted to history)
   ================================================================ */
const STATE_UI = {
    // Fetch debounce
    fetchDebounce: null, // Timeout ID for the debounced fetch; cleared on new searches

    // Debounce timer animation state
    debounceTimerStart: null, // Timestamp when timer started; null when idle
    debounceTimerAnimation: null, // requestAnimationFrame ID for active timer

    // Request management
    abortController: null, // AbortController for cancelling in-flight API requests
    searchId: 0, // Monotonically increasing counter; incremented on each new search
    fetchId: 0, // Monotonically increasing counter; incremented on each debounced fetch
    activeFetchId: null, // The fetchId that was active when the current debounce was set

    // Pipeline progress
    siDone: false, // Whether SI step has completed (success or error)
    qtDone: false, // Whether QT step has completed (success or error)
    qeDone: false, // Whether QE step has completed (success or error)

    // Custom keyword addition state
    addingCustomKeyword: false, // Whether a custom keyword is being added (loading state)
    addingCustomTopic: false, // Whether a custom topic heading is being added (loading state)
    addingCustomBlkNumber: false, // Whether a custom BK number is being added (loading state)
};

/* ================================================================
   HELPERS
   ================================================================ */

/**
 * Shortcuts for document.querySelector and document.querySelectorAll
 */
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

/**
 * Converts a value to a safe string, returning empty string for null/undefined.
 * @param {*} value - The value to convert
 * @returns {string} String representation or empty string
 */
function safeStr(value) {
    return String(value == null ? '' : value);
}

/**
 * Escapes HTML special characters in text to prevent XSS.
 * @param {*} text - The text to escape
 * @returns {string} HTML-escaped string
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = safeStr(text);
    return div.innerHTML;
}

/**
 * Applies syntax highlighting to a VuFind search URL.
 * Each parameter group (lookforN[], typeN[], boolN[]) gets its own color.
 * @param {string} url - The encoded URL to highlight
 * @returns {string} HTML string with colored spans
 */
function highlightUrl(url) {
    if (!url) return '';

    try {
        const decoded = decodeURIComponent(url);

        // Color palette for different groups (muted colors)
        const colors = [
            'var(--url-color-base)', // Color A - base URL
            'var(--url-color-join)', // Color B - join parameter
            'var(--url-color-group-0)', // Color C - first search group
            'var(--url-color-group-1)', // Color D - second search group
            'var(--url-color-group-2)', // Color E - third search group
            'var(--url-color-group-3)', // Color F - fourth search group
            'var(--url-color-group-4)', // Color G - fifth search group
            'var(--url-color-group-5)', // Color H - sixth search group
            'var(--url-color-group-6)', // Color I - seventh search group
            'var(--url-color-filter)', // Color J - filter parameters
        ];

        // Split the URL at each parameter separator (? or &) while keeping the separators
        // This regex captures the separators as separate tokens
        const segments = decoded.split(/([?&])/);

        let colorIndex = 2; // Start with group colors after base
        const parts = [];

        // Process segments: [baseUrl, ?, param1, &, param2, &, param3, ...]
        let i = 0;
        while (i < segments.length) {
            const segment = segments[i];

            // Skip empty segments (before first ?)
            if (segment === '') {
                i++;
                continue;
            }

            // Determine the separator (if any)
            const isSeparator = segment === '?' || segment === '&';
            if (isSeparator) {
                // Check if next segment is a parameter - if so, combine separator with it
                const nextSegment = segments[i + 1];
                if (nextSegment && nextSegment.includes('=')) {
                    // Combine separator + param in one span
                    const paramMatch = nextSegment.match(/^([^=]+)=(.*)$/);
                    if (paramMatch) {
                        const [, paramName, paramValue] = paramMatch;
                        let spanClass = 'url-part url-filter';
                        let color = colors[colorIndex % colors.length];

                        // Determine color and class based on parameter name
                        if (paramName === 'join') {
                            spanClass = 'url-part url-join';
                            color = colors[1]; // Join color
                        } else if (paramName.match(/^(lookfor|type|bool)(\d+)\[\]$/)) {
                            spanClass = 'url-part url-group';
                            const groupMatch = paramName.match(/^(lookfor|type|bool)(\d+)/);
                            if (groupMatch) {
                                const groupIndex = parseInt(groupMatch[2]);
                                color = colors[2 + (groupIndex % 4)];
                            }
                        }

                        parts.push(
                            `<span class="${spanClass}" style="color:${color}">${segment}${escapeHtml(paramName)}=${escapeHtml(paramValue)}</span>`
                        );
                        i += 2;
                        colorIndex++;
                        continue;
                    }
                }
                // Not a parameter, add separator as-is
                parts.push(segment);
                i++;
                continue;
            }

            // This is a parameter segment (standalone, without preceding separator)
            const paramMatch = segment.match(/^([^=]+)=(.*)$/);
            if (!paramMatch) {
                // No = found, just add as-is
                parts.push(escapeHtml(segment));
                i++;
                continue;
            }

            const [, paramName, paramValue] = paramMatch;
            let spanClass = 'url-part url-filter';
            let color = colors[colorIndex % colors.length];

            // Determine color and class based on parameter name
            if (paramName === 'join') {
                spanClass = 'url-part url-join';
                color = colors[1]; // Join color
            } else if (paramName.match(/^(lookfor|type|bool)(\d+)\[\]$/)) {
                spanClass = 'url-part url-group';
                const groupMatch = paramName.match(/^(lookfor|type|bool)(\d+)/);
                if (groupMatch) {
                    const groupIndex = parseInt(groupMatch[2]);
                    color = colors[2 + (groupIndex % 4)];
                }
            }

            parts.push(
                `<span class="${spanClass}" style="color:${color}">${escapeHtml(paramName)}=${escapeHtml(paramValue)}</span>`
            );
            colorIndex++;
            i++;
        }

        return parts.join('');
    } catch (e) {
        // Fallback: return decoded URL without highlighting
        return escapeHtml(decodeURIComponent(url));
    }
}

/* ================================================================
   LOCALSTORAGE HELPERS
   ================================================================ */
/**
 * Loads the search history from localStorage.
 * @returns {Array} Parsed history array or empty array on error
 */
function loadHistoryFromStorage() {
    try {
        const rawData = localStorage.getItem(CONFIG.LOCAL_STORAGE_KEY);
        return rawData ? JSON.parse(rawData) : [];
    } catch (error) {
        console.warn('Failed to load history from localStorage:', error);
        return [];
    }
}

/**
 * Saves the search history to localStorage.
 * @param {Array} history - History array to persist
 */
function saveHistoryToStorage(history) {
    try {
        localStorage.setItem(CONFIG.LOCAL_STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
        console.warn('Failed to save history to localStorage:', error);
    }
}

/* ================================================================
   HTTP CLIENT
   ================================================================ */
/**
 * Makes an API request to the backend.
 * @param {string} endpoint - API endpoint path
 * @param {Object} requestBody - Request payload
 * @param {AbortSignal} [signal] - Abort signal for cancellation
 * @returns {Promise<Object>} Parsed JSON response
 * @throws {Error} If response is not ok
 */
async function fetchAPI(endpoint, requestBody, signal = null) {
    const url = `${CONFIG.API_BASE_URL}${endpoint}`;
    const fetchOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody),
        signal,
    };

    const response = await fetch(url, fetchOptions);
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API error ${response.status}: ${errorText}`);
    }
    return response.json();
}

/* ================================================================
   SEARCH PIPELINE
   Executes registered steps sequentially (queryExpansion → queryTransformation).
   Each step updates the UI independently when it resolves or rejects.
   ================================================================ */
const Pipeline = (() => {
    /** @type {Map<string, {indicatorId:string|null, execute:Function, onSuccess:Function, onError?:Function}>} */
    const steps = new Map();

    /**
     * Registers a named pipeline step. Call before first search.
     * @param {string} stepName - Name of the step
     * @param {Object} config - Step configuration
     * @param {string} [config.indicatorId] - DOM element ID for loading indicator
     * @param {Function} config.execute - Async function that executes the step
     * @param {Function} config.onSuccess - Callback on successful execution
     * @param {Function} [config.onError] - Callback on error
     */
    function register(stepName, {
        indicatorId = null,
        execute,
        onSuccess,
        onError = null
    }) {
        steps.set(stepName, {
            indicatorId,
            execute,
            onSuccess,
            onError
        });
    }

    /**
     * Runs every registered step sequentially (QE first, then QT).
     * Each step updates the UI the moment it resolves or rejects.
     * Returns when ALL steps are done.
     * @param {string} query - Search query
     * @param {AbortSignal} signal - Abort signal for cancellation
     * @param {number} searchId - Current search ID to detect stale searches
     */
    async function run(query, signal, searchId) {
        // Set all indicators to loading immediately (QT spinner visible from start)
        for (const [stepName, step] of steps) {
            if (step.indicatorId) setPipeline(step.indicatorId, 'loading');
        }

        let remaining = steps.size;

        // Run steps sequentially for proper ordering (QE before QT)
        for (const [stepName, step] of steps) {
            // Skip if already aborted
            if (signal?.aborted) return;

            try {
                const result = await step.execute(query, signal);
                if (step.indicatorId) setPipeline(step.indicatorId, 'done');
                step.onSuccess(result);
            } catch (error) {
                // Ignore abort errors - they're expected when cancelling
                if (error.name === 'AbortError') return;
                if (step.indicatorId) setPipeline(step.indicatorId, 'error');
                if (step.onError) step.onError(error);
            } finally {
                remaining--;
                if (remaining <= 0) onAllDone(searchId);
            }
        }
    }

    /**
     * Called once when every step has settled (success or error).
     * @param {number} searchId - Search ID to verify this callback is still current
     */
    function onAllDone(searchId) {
        // Only process if this is the current search (ignore stale callbacks from aborted searches)
        if (searchId !== STATE_UI.searchId) return;
        // Snapshot options for "reset" only once all steps have contributed
        STATE.initialOptions = JSON.parse(JSON.stringify(STATE.options));
        hideOptionsLoading();
        resetBtn();
    }

    return {
        register,
        run
    };
})();

/* ── Shared state for search intent ─────────────────── */
let currentSearchIntent = null;

/* ── Register pipeline steps ──────────────────────────── */
Pipeline.register('searchIntent', {
    indicatorId: 'pipelineSI',
    execute: async (query, signal) => {
        const result = await fetchAPI('/search-intent', { query }, signal);
        currentSearchIntent = result.searchIntent;
        return result;
    },
    onSuccess: (result) => {
        STATE_UI.siDone = true;
        STATE.siMeta = result;
    },
    onError: () => {
        STATE_UI.siDone = true;
        currentSearchIntent = null;
    },
});

Pipeline.register('queryExpansion', {
    indicatorId: 'pipelineQE',
    execute: (query, signal) => fetchAPI('/query-expansion', {
        query,
        search_intent: currentSearchIntent
    }, signal),
    onSuccess: (result) => onQE(result),
    onError: () => {
        STATE_UI.qeDone = true;
    },
});

Pipeline.register('queryTransformation', {
    indicatorId: 'pipelineQT',
    execute: (query, signal) => fetchAPI('/query-transformation', {
        query,
        search_intent: currentSearchIntent
    }, signal),
    onSuccess: (result) => onQT(result.metadata),
    onError: () => {
        STATE_UI.qtDone = true;
    },
});

/* ================================================================
    SEARCH
     Entry point for search. Delegates to Pipeline for execution.
     ================================================================ */
/**
 * Initiates a new search with the given query.
 * Cancels any in-flight requests, resets state, and runs the pipeline.
 * @param {string} query - Search query string
 */
async function doSearch(query) {
    query = safeStr(query).trim();
    if (!query) return;

    // Increment search ID and cancel any in-flight requests from previous searches
    STATE_UI.searchId++;
    if (STATE_UI.abortController) {
        STATE_UI.abortController.abort();
    }
    STATE_UI.abortController = new AbortController();

    // Clear any pending debounced fetch
    if (STATE_UI.fetchDebounce) {
        clearTimeout(STATE_UI.fetchDebounce);
        STATE_UI.fetchDebounce = null;
        stopDebounceTimer();
    }

    // Add to history immediately before API calls
    addHistory(query);

    // Reset all state variables to initial values before pipeline runs
    STATE.query = query;
    STATE.options = [];
    STATE.initialOptions = [];
    STATE.qeConcepts = {
        positive: {},
        negative: {}
    };
    STATE.qtConcepts = {
        positive: {},
        negative: {}
    };
    renderOptions();
    showOptionsLoading();
    STATE_UI.siDone = false;
    STATE.siMeta = null;
    currentSearchIntent = null;
    STATE.qtMeta = null;
    STATE_UI.qtDone = false;
    STATE.qeMeta = null;
    STATE_UI.qeDone = false;
    STATE.vufindResults = [];
    STATE.totalResults = null;
    STATE.qualityScore = null;
    STATE.qualityAssessment = '';
    STATE.generatedUrl = '';
    renderQualityScore();

    // Reset subtitle count display immediately to avoid showing stale data
    const subtitleCountEl = $('#subtitleCountNumber');
    if (subtitleCountEl) subtitleCountEl.textContent = '';
    const subtitle = $('#resultsSubtitle');
    if (subtitle) subtitle.classList.remove('visible');

    // Reset UI
    $('#debugPanel').style.display = CONFIG.SHOW_DEBUG_PANEL ? 'block' : 'none';
    $('#controlsContainer').style.display = 'none';
    $('#generatedUrl').textContent = getStrings().waitingForResults;

    renderVufindResults(true);

    const btn = $('#searchBtn');
    btn.disabled = true;
    btn.innerHTML = `<div class="spinner"></div> ${getStrings().searchInProgress}`;

    // Run all pipeline steps — each updates UI independently
    await Pipeline.run(query, STATE_UI.abortController.signal, STATE_UI.searchId);
}

/**
 * Resets search button to default state (enabled with original label).
 */
function resetBtn() {
    const searchButton = $('#searchBtn');
    if (searchButton) {
        searchButton.disabled = false;
        searchButton.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> ${getStrings().searchBtn}`;
    }
}

/**
 * Updates pipeline indicator state (loading/done/error).
 * @param {string} elementId - DOM element ID
 * @param {string} state - New state ('loading', 'done', 'error')
 */
function setPipeline(elementId, state) {
    const element = $('#' + elementId);
    if (element) {
        element.classList.remove('loading', 'done', 'error');
        element.classList.add(state);
    }
}

/* ================================================================
    DEBOUNCE TIMER
    Visual timer showing the debounce countdown.
    ================================================================ */
/**
 * Starts the debounce countdown animation.
 */
function startDebounceTimer() {
    const timer = $('#debounceTimer');
    const timerBar = $('#debounceTimerBar');
    const timerText = $('#debounceTimerText');
    if (!timer || !timerBar || !timerText) return;

    STATE_UI.debounceTimerStart = Date.now();
    timer.classList.add('active');
    timerBar.style.transform = 'scaleX(1)';

    // Cancel any existing animation frame
    if (STATE_UI.debounceTimerAnimation) {
        cancelAnimationFrame(STATE_UI.debounceTimerAnimation);
    }

    const duration = CONFIG.FETCH_DEBOUNCE_MS;

    // Animates the timer bar and text countdown using requestAnimationFrame
    function updateTimer() {
        if (!STATE_UI.debounceTimerStart) return;

        const elapsed = Date.now() - STATE_UI.debounceTimerStart;
        const remaining = Math.max(0, duration - elapsed);
        const progress = remaining / duration;

        timerBar.style.transform = `scaleX(${progress})`;
        timerText.textContent = `${Math.max(0, remaining / 1000).toFixed(1)}s`;

        if (remaining > 0) {
            STATE_UI.debounceTimerAnimation = requestAnimationFrame(updateTimer);
        }
    }

    STATE_UI.debounceTimerAnimation = requestAnimationFrame(updateTimer);
}

/**
 * Stops the debounce countdown animation and resets the timer display.
 */
function stopDebounceTimer() {
    const timer = $('#debounceTimer');
    const timerBar = $('#debounceTimerBar');
    const timerText = $('#debounceTimerText');
    if (!timer || !timerBar || !timerText) return;

    if (STATE_UI.debounceTimerAnimation) {
        cancelAnimationFrame(STATE_UI.debounceTimerAnimation);
        STATE_UI.debounceTimerAnimation = null;
    }

    STATE_UI.debounceTimerStart = null;
    timer.classList.remove('active');
    timerBar.style.transform = 'scaleX(1)';
    timerText.textContent = `${(CONFIG.FETCH_DEBOUNCE_MS / 1000).toFixed(1)}s`;
}

/* ================================================================
    HANDLE QT RESPONSE
    ================================================================ */
/**
 * Handles the query transformation response, updating STATE and extracting options.
 * @param {Object} metadata - QT metadata containing filters, GND headings, BK notations, date range
 */
function onQT(metadata) {
    STATE_UI.qtDone = true;
    STATE.qtMeta = metadata;

    // Build STATE.qtConcepts from gndHeadingsConcepts
    STATE.qtConcepts.positive = {};
    STATE.qtConcepts.negative = {};
    const gndHeadingsConcepts = metadata?.gndHeadingsConcepts || {};
    Object.entries(gndHeadingsConcepts).forEach(([conceptKey, headings]) => {
        STATE.qtConcepts.positive[conceptKey] = [];
        headings.forEach(gndHeading => {
            const heading = safeStr(gndHeading.heading);
            if (heading && !STATE.qtConcepts.positive[conceptKey].includes(heading)) {
                STATE.qtConcepts.positive[conceptKey].push(heading);
            }
        });
    });

    if (metadata) {
        try {
            extractOptionsFromMeta(metadata);
        } catch (error) {
            console.error('extractOptionsFromMeta error', error);
        }
    }

    renderOptions();
    rebuildUrl({
        skipFetch: true
    });
}

/**
 * Pushes an option onto STATE.options.
 * Handles both raw string values and objects with label/filterValue properties.
 * @param {string} optionId - Unique option identifier
 * @param {string} category - Option category (e.g., 'format', 'keyword')
 * @param {string|Object} item - Raw value or object with label/filterValue
 * @param {string} paramType - Param type ('filter', 'search_subject', 'date_from', 'date_to')
 * @param {string} [conceptKey] - Optional concept key for logical tree grouping
 */
function pushOption(optionId, category, item, paramType, conceptKey = undefined) {
    const label = typeof item === 'object' ? safeStr(item.label) : safeStr(item);
    const filterValue = typeof item === 'object' ? safeStr(item.filterValue) : safeStr(item);
    if (!label) return;
    STATE.options.push({
        id: optionId,
        source: 'qt',
        category,
        value: filterValue,
        filterValue: filterValue,
        label,
        active: false,
        paramType,
        conceptKey
    });
}

/**
 * Extracts search options from QT metadata and pushes them to STATE.options.
 * @param {Object} metadata - QT metadata object
 */
function extractOptionsFromMeta(metadata) {
    const filters = metadata.filters || {};

    // Media form (format) facets
    (filters.mediaForms || []).forEach((mediaForm, index) => {
        pushOption(`qt_fmt_${index}`, 'format', mediaForm, 'filter');
    });

    // Content genre (format_details) facets
    (filters.contentGenres || []).forEach((genre, index) => {
        pushOption(`qt_genre_${index}`, 'format_details', genre, 'filter');
    });

    // Language facets
    (filters.languages || []).forEach((language, index) => {
        pushOption(`qt_lang_${index}`, 'language', language, 'filter');
    });

    // Author name facets
    (filters.authorNames || []).forEach((authorName, index) => {
        pushOption(`qt_auth_${index}`, 'author_facet', authorName, 'filter');
    });

    // GND subject headings - using gndHeadingsConcepts for grouped access
    const gndHeadingsConcepts = metadata?.gndHeadingsConcepts || {};
    let gndIndex = 0;
    Object.entries(gndHeadingsConcepts).forEach(([conceptKey, headings]) => {
        headings.forEach(gndHeading => {
            const heading = safeStr(gndHeading.heading);
            if (!heading) return;
            pushOption(`qt_gnd_${gndIndex}`, 'topic_facet', heading, 'search_subject', conceptKey);
            gndIndex++;
        });
    });

    // BK classification notations
    (metadata.bkNotations || []).forEach((bkNotation, index) => {
        const notation = safeStr(bkNotation.notation);
        if (!notation) return;
        const label = `${safeStr(bkNotation.label || notation)}`;
        pushOption(`qt_bk_${index}`, 'bklnumber', {
            label,
            filterValue: notation
        }, 'filter');
    });

    // Date range filters
    const dateRange = metadata.dateRange || {};
    const strings = getStrings();
    if (dateRange.from != null) {
        pushOption('qt_date_from', 'date', {
            label: `${strings.dateFromLabel} ${dateRange.from}`,
            filterValue: String(dateRange.from)
        }, 'date_from');
    }
    if (dateRange.to != null) {
        pushOption('qt_date_to', 'date', {
            label: `${strings.dateToLabel} ${dateRange.to}`,
            filterValue: String(dateRange.to)
        }, 'date_to');
    }
}

/* ================================================================
    HANDLE QE RESPONSE
    ================================================================ */
/**
 * Handles the query expansion response, extracting keywords and updating STATE.
 * @param {Object} result - QE result containing positiveKeywordConcepts and negativeKeywordConcepts
 */
function onQE(result) {
    STATE_UI.qeDone = true;
    STATE.qeMeta = result;

    // Store concepts explicitly in STATE
    STATE.qeConcepts.positive = result?.positiveKeywordConcepts || {};
    STATE.qeConcepts.negative = result?.negativeKeywordConcepts || {};

    // Handle positiveKeywordConcepts
    if (result && result.positiveKeywordConcepts && typeof result.positiveKeywordConcepts === 'object') {
        let idx = 0;
        Object.entries(result.positiveKeywordConcepts).forEach(([concept, relatedTerms]) => {
            if (Array.isArray(relatedTerms)) {
                relatedTerms.forEach((term) => {
                    const termStr = safeStr(term).trim();
                    if (!termStr) return;
                    STATE.options.push({
                        id: `qe_pos_${idx++}`,
                        source: 'qe',
                        category: 'keyword',
                        value: termStr,
                        filterValue: termStr,
                        label: termStr,
                        active: false,
                        paramType: 'keyword',
                        negated: false,
                        conceptKey: concept
                    });
                });
            }
        });
    }

    // Handle negativeKeywordConcepts
    if (result && result.negativeKeywordConcepts && typeof result.negativeKeywordConcepts === 'object') {
        let idx = 0;
        Object.entries(result.negativeKeywordConcepts).forEach(([concept, relatedTerms]) => {
            if (Array.isArray(relatedTerms)) {
                relatedTerms.forEach((term) => {
                    const termStr = safeStr(term).trim();
                    if (!termStr) return;
                    STATE.options.push({
                        id: `qe_neg_${idx++}`,
                        source: 'qe',
                        category: 'keyword',
                        value: termStr,
                        filterValue: termStr,
                        label: termStr,
                        active: false,
                        paramType: 'keyword',
                        negated: true,
                        conceptKey: concept
                    });
                });
            }
        });
    }

    // Auto-toggle all keyword options to trigger rebuildUrl with keywords
    STATE.options
        .filter(option => option.paramType === 'keyword')
        .forEach(option => {
            option.active = true;
            const element = document.querySelector(`[data-oid="${option.id}"]`);
            if (element) element.classList.add('active');
        });

    renderOptions();
    rebuildUrl({
        skipFetch: false,
        immediate: true
    });
}

/* ================================================================
   VUFIND DATA
   Fetches result count and preview titles from VuFind API.
   ================================================================ */
/**
 * Fetches result count and preview titles from VuFind API.
 * @param {string} searchUrl - VuFind search URL
 * @param {AbortSignal} [signal] - Abort signal for cancellation
 * @param {number} [fetchId] - Fetch ID for stale fetch detection
 * @returns {Promise<Object>} VuFind search response data
 */
async function fetchVufindData(searchUrl, signal = null, fetchId = null) {
    // Show loading state immediately so the UI feels responsive
    showCountLoading();
    renderVufindResults(true);

    try {
        const responseData = await fetchAPI('/perform-vufind-search', {
            url: searchUrl,
            limit: 10
        }, signal);
        onVuFindSearch(responseData, fetchId);
        // After VuFind data is fetched, run query quality assessment
        // using the already-fetched titles to avoid redundant API calls
        return responseData;
    } catch (error) {
        // Ignore abort errors - they're expected when cancelling
        if (error.name === 'AbortError') return null;
        // Clear results on error to prevent stale data from previous searches
        STATE.vufindResults = [];
        hideCountLoading();
        renderVufindResults(false);
        throw error;
    }
}

/**
 * Handles the VuFind search response, updating STATE with results.
 * @param {Object} searchData - VuFind search response
 * @param {number} [fetchId] - Fetch ID for stale fetch detection
 */
function onVuFindSearch(searchData, fetchId = null) {
    // Skip rendering if a newer fetch has started since this one was triggered
    // Compare against activeFetchId (which is set to currentFetchId when debounce fires)
    if (fetchId !== null && STATE_UI.activeFetchId !== fetchId) {
        return;
    }

    hideCountLoading();
    const subtitle = $('#resultsSubtitle');
    if (subtitle) subtitle.classList.add('visible');
    if (searchData.totalResults != null) {
        STATE.totalResults = searchData.totalResults;
        const subtitleEl = $('#subtitleCountNumber');
        if (subtitleEl) subtitleEl.textContent = new Intl.NumberFormat('de-DE').format(searchData.totalResults);
    }
    STATE.vufindResults = searchData.titles || [];
    renderVufindResults(false);
}

/**
 * Shows loading state for result count.
 */
function showCountLoading() {
    const subtitleCount = $('#subtitleCountNumber');
    if (subtitleCount) subtitleCount.parentElement.classList.add('loading');
}

/**
 * Hides loading state for result count.
 */
function hideCountLoading() {
    const subtitleCount = $('#subtitleCountNumber');
    if (subtitleCount) subtitleCount.parentElement.classList.remove('loading');
}

/* ================================================================
   QUALITY ASSESSMENT
   Assesses query-result match quality using query quality analysis.
   ================================================================ */
/**
 * Fetches query quality assessment from the backend.
 * @param {string} searchUrl - VuFind search URL
 * @param {Array} resultTitles - Pre-fetched result titles
 * @param {number} [fetchId] - Fetch ID for stale fetch detection
 */
function fetchQueryQuality(searchUrl, resultTitles, fetchId = null) {
    // Show loading state
    showQualityLoading();

    fetchAPI('/query-judge-quality', {
        query: STATE.query,
        url: searchUrl,
        titles: resultTitles, // Pass pre-fetched titles to avoid redundant VuFind call
        output_language: CONFIG.UI_LANGUAGE
    }).then(data => onQueryQuality(data, fetchId)).catch(() => {
        hideQualityLoading();
    });
}

/**
 * Handles the query quality assessment response.
 * @param {Object} qualityData - Quality assessment data
 * @param {number} [fetchId] - Fetch ID for stale fetch detection
 */
function onQueryQuality(qualityData, fetchId = null) {
    // Skip if this fetch is stale
    if (fetchId !== null && STATE_UI.activeFetchId !== fetchId) {
        return;
    }

    hideQualityLoading();
    STATE.qualityScore = qualityData.qualityScore;
    STATE.qualityAssessment = qualityData.assessment || '';
    STATE.relevantIndices = qualityData.relevantIndices || [];
    renderQualityScore();
    highlightRelevantTitles(); // Toggle classes on existing elements
    // Save quality score to history after async quality assessment resolves
    updateHistorySnapshot(STATE.query, createStateSnapshot());
}

/**
 * Renders the quality score display based on STATE.qualityScore.
 */
function renderQualityScore() {
    const subtitleScoreEl = $('#subtitleQualityScore');
    const qualityAssessmentContainer = $('#qualityAssessmentContainer');
    const qualityAssessmentText = $('#qualityAssessmentText');

    const score = STATE.qualityScore;
    if (score === null) {
        if (subtitleScoreEl) {
            subtitleScoreEl.textContent = '--';
            subtitleScoreEl.className = 'quality-score';
        }
        // Hide quality assessment when loading or no score
        if (qualityAssessmentContainer) {
            qualityAssessmentContainer.classList.remove('visible');
        }
        return;
    }

    const formattedScore = (score * 100).toFixed(0) + '%';
    if (subtitleScoreEl) {
        subtitleScoreEl.textContent = formattedScore;
        subtitleScoreEl.className = 'quality-score';
    }

    // Show/hide quality assessment text
    if (qualityAssessmentContainer && qualityAssessmentText) {
        if (STATE.qualityAssessment && STATE.qualityAssessment.trim() !== '') {
            qualityAssessmentText.innerHTML = '<strong>' + getStrings().qualityScore + '</strong> ' + escapeHtml(STATE.qualityAssessment);
            qualityAssessmentContainer.classList.add('visible');
        } else {
            qualityAssessmentContainer.classList.remove('visible');
        }
    }
}

/**
 * Shows loading state for quality score.
 */
function showQualityLoading() {
    const subtitleQuality = $('.subtitle-quality');
    if (subtitleQuality) subtitleQuality.classList.add('loading');
}

/**
 * Hides loading state for quality score.
 */
function hideQualityLoading() {
    const subtitleQuality = $('.subtitle-quality');
    if (subtitleQuality) subtitleQuality.classList.remove('loading');
}

/* ================================================================
   RENDER VUFIND RESULTS
   Renders preview results in the results section.
   ================================================================ */
/**
 * Renders preview results in the results section.
 * @param {boolean} isLoading - Whether to show loading spinner
 */
function renderVufindResults(isLoading) {
    const container = $('#vufindResultsList');
    const spinner = $('#resultsSpinner');
    const emptyEl = $('#emptyVufind');

    if (isLoading) {
        if (spinner) spinner.style.display = 'flex';
        if (emptyEl) emptyEl.style.display = 'none';
        if (container) container.innerHTML = '';
        return;
    }

    if (spinner) spinner.style.display = 'none';

    if (!STATE.vufindResults || STATE.vufindResults.length === 0) {
        if (emptyEl) {
            emptyEl.style.display = 'block';
            emptyEl.textContent = getStrings().noResultsFound;
        }
        if (container) container.innerHTML = '';
        return;
    }

    if (emptyEl) emptyEl.style.display = 'none';

    container.innerHTML = STATE.vufindResults.map((result, resultIndex) => {
        const title = escapeHtml(safeStr(result.title) || getStrings().noTitle);
        let resultUrl = safeStr(result.url);
        // Prepend VUFIND_BASE_URL to relative URLs (API returns /Record/...)
        if (resultUrl.startsWith('/')) {
            resultUrl = CONFIG.VUFIND_BASE_URL + resultUrl;
        }
        const year = result.year ? escapeHtml(result.year) : '';
        let format = result.format ? escapeHtml(result.format) : '';
        // Apply media form mapping for display
        const mediaFormLabels = getMediaFormLabels();
        if (mediaFormLabels[format]) {
            format = mediaFormLabels[format];
        }
        // Get author (first author from the authors array), truncated if too long
        const author = (result.authors && result.authors.length > 0) ? result.authors[0] : '';
        const authorDisplay = author.length > 35 ? author.substring(0, 32) + '…' : author;
        const metaParts = [authorDisplay, year, format].filter(Boolean);
        const metaHtml = metaParts.length ?
            `<div class="vufind-result-meta">${metaParts.map(metaPart => `<span>${escapeHtml(metaPart)}</span>`).join('<span>·</span>')}</div>` :
            '';

        const isRelevant = STATE.relevantIndices.includes(resultIndex + 1);
        const indexClass = isRelevant ? 'vufind-result-index relevant' : 'vufind-result-index';
        return `
            <a class="vufind-result-item fade-in" href="${escapeHtml(resultUrl)}" target="_blank"
               aria-label="${title}" style="animation-delay:${resultIndex * 30}ms">
                <div class="${indexClass}">${resultIndex + 1}</div>
                <div>
                    <div class="vufind-result-title">${title}</div>
                    ${metaHtml}
                </div>
            </a>`;
    }).join('');
}

/* ================================================================
    HIGHLIGHT RELEVANT TITLES
    Toggles 'relevant' class on vufind-result-index elements based on STATE.relevantIndices.
    ================================================================ */
/**
 * Toggles 'relevant' class on result index badges based on STATE.relevantIndices.
 */
function highlightRelevantTitles() {
    const container = $('#vufindResultsList');
    if (!container) return;
    const indices = container.querySelectorAll('.vufind-result-index');
    indices.forEach((indexEl, i) => {
        const resultIndex = i + 1;
        const isRelevant = STATE.relevantIndices.includes(resultIndex);
        if (isRelevant) {
            indexEl.classList.add('relevant');
        } else {
            indexEl.classList.remove('relevant');
        }
    });
}

/* ================================================================
   URL BUILDER
   Constructs the VuFind search URL from active options.
   ================================================================ */
/**
 * Rebuilds the VuFind search URL from active options and triggers data fetch.
 * @param {Object} options - Configuration options
 * @param {boolean} [options.skipFetch] - Skip VuFind data fetch
 * @param {boolean} [options.immediate] - Execute fetch immediately without debounce
 */
async function rebuildUrl({
    skipFetch = false,
    immediate = false
} = {}) {
    // Cancel any pending debounced request
    if (STATE_UI.fetchDebounce) {
        clearTimeout(STATE_UI.fetchDebounce);
        STATE_UI.fetchDebounce = null;
        stopDebounceTimer();
    }

    const url = buildUrl();
    STATE.generatedUrl = url;
    $('#generatedUrl').innerHTML = highlightUrl(url);
    const openInVuFind = $('#openInVuFind');
    if (openInVuFind) openInVuFind.href = url;
    updateControlsBar();

    // Update history snapshot on every rebuildUrl call
    updateHistorySnapshot(STATE.query, createStateSnapshot());

    if (skipFetch) return;

    // Reset quality score when initiating new fetch
    STATE.qualityScore = null;
    STATE.qualityAssessment = '';
    STATE.relevantIndices = [];
    renderQualityScore();

    // Define the fetch sequence to be used by both paths
    const executeFetch = async (fetchIdAtTrigger) => {
        // Capture the fetchId at the moment this fetch was triggered
        const myFetchId = fetchIdAtTrigger;
        try {
            const vufindData = await fetchVufindData(url, STATE_UI.abortController.signal, myFetchId);
            // Skip quality fetch if aborted
            if (vufindData === null) return;
            fetchQueryQuality(url, vufindData?.titles || [], myFetchId);
            // Update history snapshot after VuFind fetch completes
            updateHistorySnapshot(STATE.query, createStateSnapshot());
        } finally {
            stopDebounceTimer();
        }
    };

    if (immediate) {
        // Set activeFetchId for immediate fetches to prevent stale check from skipping results
        STATE_UI.activeFetchId = STATE_UI.fetchId;
        await executeFetch(STATE_UI.fetchId);
    } else {
        // Show loading state IMMEDIATELY before waiting for debounce
        showCountLoading();
        renderVufindResults(true);

        // Increment fetchId to invalidate any pending fetch from a previous toggle
        STATE_UI.fetchId++;
        const currentFetchId = STATE_UI.fetchId;

        startDebounceTimer();
        STATE_UI.fetchDebounce = setTimeout(async () => {
            // Skip if aborted or if a newer toggle happened (stale fetch)
            if (STATE_UI.abortController?.signal?.aborted) return;
            if (currentFetchId !== STATE_UI.fetchId) {
                return;
            }

            // Store fetchId that this fetch was triggered for (for stale check in onVuFindSearch)
            STATE_UI.activeFetchId = currentFetchId;
            await executeFetch(currentFetchId);
        }, CONFIG.FETCH_DEBOUNCE_MS);
    }
}

/**
 * Constructs the VuFind search URL from active STATE.options.
 * Options for VuFind URL construction are defined by
 * const VUFIND_PARAMS in research-compass-settings.js
 * @returns {string} Full VuFind search URL
 */
function buildUrl() {
    const active = STATE.options.filter(option => option.active);
    const params = new URLSearchParams();

    const subjects = active.filter(option => option.paramType === 'search_subject');
    const keywords = active.filter(option => option.paramType === 'keyword');

    let startIndex = 0;

    if (keywords.length > 0) {
        const qeLt = STATE.qeMeta && STATE.qeMeta.logicalTree;
        if (qeLt) {
            const ltParams = buildLTParams(qeLt, keywords, VUFIND_PARAMS.SEARCH_TYPE_ALL_FIELDS, startIndex);
            ltParams.forEach(([paramKey, paramValue]) => params.append(paramKey, paramValue));
            ltParams.forEach(([paramKey]) => {
                const indexMatch = paramKey.match(/^lookfor(\d+)/);
                if (indexMatch) startIndex = Math.max(startIndex, +indexMatch[1] + 1);
            });
        } else {
            const combined = keywords.map(keyword => keyword.value).join(' ');
            if (subjects.length > 0) {
                params.append(`${VUFIND_PARAMS.PARAM_LOOKFOR}${startIndex}`, combined);
                params.append(`${VUFIND_PARAMS.PARAM_TYPE}${startIndex}`, VUFIND_PARAMS.SEARCH_TYPE_ALL_FIELDS);
                if (!params.has(VUFIND_PARAMS.PARAM_JOIN)) params.append(VUFIND_PARAMS.PARAM_JOIN, VUFIND_PARAMS.BOOL_AND);
            } else {
                params.append(VUFIND_PARAMS.PARAM_LOOKFOR, combined);
                params.append(VUFIND_PARAMS.PARAM_TYPE, VUFIND_PARAMS.SEARCH_TYPE_ALL_FIELDS);
            }
        }
    }

    if (subjects.length > 0) {
        const qtLt = STATE.qtMeta && STATE.qtMeta.logicalTree;
        if (qtLt) {
            const ltParams = buildLTParams(qtLt, subjects, VUFIND_PARAMS.SEARCH_TYPE_SUBJECT, startIndex);
            ltParams.forEach(([paramKey, paramValue]) => params.append(paramKey, paramValue));
            ltParams.forEach(([paramKey]) => {
                const indexMatch = paramKey.match(/^lookfor(\d+)/);
                if (indexMatch) startIndex = Math.max(startIndex, +indexMatch[1] + 1);
            });
        } else {
            subjects.forEach((subject, subjectIndex) => {
                params.append(`${VUFIND_PARAMS.PARAM_LOOKFOR}${startIndex}`, `"${subject.value}"`);
                params.append(`${VUFIND_PARAMS.PARAM_TYPE}${startIndex}`, VUFIND_PARAMS.SEARCH_TYPE_SUBJECT);
                startIndex++;
            });
            if (subjects.length > 1 && !params.has(VUFIND_PARAMS.PARAM_JOIN)) params.append(VUFIND_PARAMS.PARAM_JOIN, VUFIND_PARAMS.BOOL_OR);
        }
    }

    // Only add default AllFields search if no filters are active
    // (filters should work independently without requiring a text search)
    const activeFilters = active.filter(option => option.paramType === 'filter' || option.paramType === 'date_from' ||
        option.paramType === 'date_to');
    if (subjects.length === 0 && keywords.length === 0 && activeFilters.length === 0) {
        params.append(VUFIND_PARAMS.PARAM_LOOKFOR, STATE.query);
        params.append(VUFIND_PARAMS.PARAM_TYPE, VUFIND_PARAMS.SEARCH_TYPE_ALL_FIELDS);
    }

    const formatMap = {
        format: filterValue => `${VUFIND_PARAMS.FILTER_FORMAT}:"${filterValue}"`,
        format_details: filterValue => `${VUFIND_PARAMS.FILTER_FORMAT_DETAILS}:"${filterValue}"`,
        language: filterValue => `${VUFIND_PARAMS.FILTER_LANGUAGE}:"${filterValue}"`,
        author_facet: filterValue => `${VUFIND_PARAMS.FILTER_AUTHOR}:"${filterValue}"`,
        bklnumber: filterValue => `${VUFIND_PARAMS.FILTER_BK}:"${filterValue}"`,
    };

    active.forEach(activeOption => {
        if (activeOption.paramType === 'filter' && formatMap[activeOption.category]) {
            params.append(VUFIND_PARAMS.PARAM_FILTER_ARRAY, formatMap[activeOption.category](activeOption.filterValue));
        }
    });

    const dateFrom = active.find(option => option.paramType === 'date_from');
    const dateTo = active.find(option => option.paramType === 'date_to');
    if (dateFrom || dateTo) {
        params.append(VUFIND_PARAMS.PARAM_DATERANGE_ARRAY, VUFIND_PARAMS.PARAM_PUBLISH_DATE);
        if (dateFrom) params.append(VUFIND_PARAMS.PARAM_PUBLISH_DATE_FROM, dateFrom.value);
        if (dateTo) params.append(VUFIND_PARAMS.PARAM_PUBLISH_DATE_TO, dateTo.value);
    }

    // Ensure join=AND appears first in the URL (both logical trees add join=AND at top level)
    const joinValues = params.getAll(VUFIND_PARAMS.PARAM_JOIN);
    if (joinValues.length >= 1) {
        params.delete(VUFIND_PARAMS.PARAM_JOIN);
        // Reconstruct URL with join=AND at the start, after SEARCH_PATH?
        const remainingParams = params.toString();
        return CONFIG.VUFIND_BASE_URL + VUFIND_PARAMS.SEARCH_PATH + '?' + VUFIND_PARAMS.PARAM_JOIN + '=' + VUFIND_PARAMS.BOOL_AND + (remainingParams ? '&' + remainingParams : '');
    }

    const finalUrl = CONFIG.VUFIND_BASE_URL + VUFIND_PARAMS.SEARCH_PATH + '?' + params.toString();
    return finalUrl;
}

/**
 * Builds URL parameters from a logical tree structure for VuFind.
 * @param {Object} tree - Logical tree object with root property
 * @param {Array} activeSubjects - Active subject options
 * @param {string} searchType - Search type (from VUFIND_PARAMS.SEARCH_TYPE_*)
 * @param {number} [startIndex] - Starting index for lookfor parameters
 * @returns {Array} Array of [paramKey, paramValue] tuples
 */
function buildLTParams(tree, activeSubjects, searchType, startIndex = 0) {
    const output = [];
    const root = tree.root || tree;
    if (!root) {
        return output;
    }

    const aliveSubjects = new Set(activeSubjects.map(subject => subject.value));

    // Recursively serializes a logical tree node into a query string.
    // Handles 'term' nodes (quoted if containing spaces) and 'group' nodes (AND/OR joined).
    function serializeNode(node) {
        if (node.type === 'term') {
            if (!aliveSubjects.has(node.value)) {
                return null;
            }
            const result = node.value.includes(' ') ? `"${node.value}"` : node.value;
            return result;
        }
        if (node.type === 'group') {
            const parts = (node.items || []).map(serializeNode).filter(Boolean);
            if (!parts.length) {
                return null;
            }
            if (parts.length === 1) {
                return parts[0];
            }
            const result = '(' + parts.join(` ${node.operator} `) + ')';
            return result;
        }
        return null;
    }

    if (root.type === 'term') {
        if (aliveSubjects.has(root.value)) {
            output.push(
                [`${VUFIND_PARAMS.PARAM_LOOKFOR}${startIndex}[]`, root.value],
                [`${VUFIND_PARAMS.PARAM_TYPE}${startIndex}[]`, searchType],
                [`${VUFIND_PARAMS.PARAM_BOOL}${startIndex}[]`, VUFIND_PARAMS.BOOL_AND],
                [VUFIND_PARAMS.PARAM_JOIN, VUFIND_PARAMS.BOOL_AND]
            );
        }
    } else if (root.type === 'group') {
        let currentIndex = startIndex;
        const items = root.items || [];

        for (let i = 0; i < items.length; i++) {
            const item = items[i];
            const queryStr = serializeNode(item);
            if (queryStr) {
                output.push(
                    [`${VUFIND_PARAMS.PARAM_LOOKFOR}${currentIndex}[]`, queryStr],
                    [`${VUFIND_PARAMS.PARAM_TYPE}${currentIndex}[]`, searchType]
                );
                let boolOp = item.operator || VUFIND_PARAMS.BOOL_AND;
                output.push([`${VUFIND_PARAMS.PARAM_BOOL}${currentIndex}[]`, boolOp]);
                currentIndex++;
            }
        }
        if (currentIndex > startIndex) {
            output.push([VUFIND_PARAMS.PARAM_JOIN, root.operator]);
        }
    }

    return output;
}

/* ================================================================
   RENDER OPTIONS
   Displays search options (keywords, facets, filters) in the UI.
   ================================================================ */
/**
 * Shows loading state for options.
 */
function showOptionsLoading() {
    const spinner = $('#optionsSpinner');
    if (spinner) spinner.style.display = 'flex';
    const emptyOption = document.querySelector('#optionsGrid .empty-option');
    if (emptyOption) emptyOption.style.display = 'none';
}

/**
 * Hides loading state for options.
 */
function hideOptionsLoading() {
    const spinner = $('#optionsSpinner');
    if (spinner) spinner.style.display = 'none';
}

/**
 * Renders all search options in the options grid.
 */
function renderOptions() {
    const grid = $('#optionsGrid');
    if (!grid) return;
    grid.innerHTML = '';

    if (STATE.options.length === 0) {
        grid.innerHTML = `<div class="empty-option">${getStrings().noSearchOptionsAvailable}</div>`;
        hideOptionsLoading();
        return;
    }

    // Group options by category for card-based layout
    const groups = {};
    STATE.options.forEach(option => {
        (groups[option.category] = groups[option.category] || []).push(option);
    });

    // Iterate categories in defined order, creating a card for each with options and optional placeholder
    OPTIONS_ORDER.forEach(category => {
        const items = groups[category] || [];
        const hasItems = items.length > 0;
        // Categories that support custom item addition via placeholder
        const hasPlaceholder = STATE_UI.qtDone && ['keyword', 'topic_facet', 'bklnumber'].includes(category);

        // Skip categories with no items and no placeholder support
        if (!hasItems && !hasPlaceholder) return;

        try {
            const optionsConfig = getOptionsConfig();
            const categoryConfig = optionsConfig[category] || {
                label: category,
                icon: 'fa-filter'
            };

            const card = document.createElement('div');
            card.className = 'option-card fade-in';
            card.innerHTML = `
                <div class="option-card-header">
                    <i class="fa-solid ${categoryConfig.icon} option-icon"></i>
                    ${escapeHtml(categoryConfig.label)}
                </div>
                <div class="option-card-body">
                    ${items.map(renderItem).join('')}
                    ${category === 'keyword' ? renderPlaceholderItem({ isLoading: STATE_UI.addingCustomKeyword, action: 'add-custom-keyword', category: 'keyword', placeholder: getStrings().customKeywordPlaceholder }) : ''}
                    ${category === 'topic_facet' ? renderPlaceholderItem({ isLoading: STATE_UI.addingCustomTopic, action: 'add-custom-topic', category: 'topic_facet', placeholder: getStrings().customTopicPlaceholder }) : ''}
                    ${category === 'bklnumber' ? renderPlaceholderItem({ isLoading: STATE_UI.addingCustomBlkNumber, action: 'add-custom-blk-number', category: 'bklnumber', placeholder: getStrings().customBlkNumberPlaceholder }) : ''}
                </div>
            `;
            grid.appendChild(card);

            // Attach tooltip to the header if tooltip text exists
            const header = card.querySelector('.option-card-header');
            if (header && categoryConfig.tooltip) {
                createTooltip(header, () => categoryConfig.tooltip);
            }
        } catch (error) {
            console.error(`renderOptions error for category "${category}":`, error.message);
        }
    });

    updateControlsBar();
}

/**
 * Renders a single option item HTML.
 * @param {Object} option - Option object with label, category, active, etc.
 * @returns {string} HTML string for the option item
 */
function renderItem(option) {
    let label = safeStr(option.label).replace(/^"|"$/g, '');
    const categoryLabels = getCategoryLabels();
    const mediaFormLabels = getMediaFormLabels();
    const languageLabels = getLanguageLabels();

    // Apply media form mapping for format category items
    if (option.category === 'format' && mediaFormLabels[label]) {
        label = mediaFormLabels[label];
    }
    // Apply language mapping for language category items
    if (option.category === 'language' && languageLabels[label]) {
        label = languageLabels[label];
    }
    const classes = ['option-item'];
    if (option.active) classes.push('active');

    const negatedBadge = option.negated ?
        `<span class="option-negated-badge">${getStrings().negatedBadge}</span>` :
        '';

    return `
        <button type="button" class="${classes.join(' ')}"
                data-oid="${option.id}" aria-pressed="${option.active}">
            <span class="option-checkbox"><i class="fa-solid fa-check"></i></span>
            <span class="option-item-text">${escapeHtml(label)}</span>
            ${negatedBadge}
            <span class="option-item-type">${categoryLabels[option.category] || option.category}</span>
            <span class="option-remove-btn" data-remove-oid="${option.id}" role="img" aria-label="${getStrings().removeOption}">
                <i class="fa-solid fa-xmark"></i>
            </span>
        </button>`;
}

/**
 * Renders a placeholder item for adding custom options.
 * @param {Object} config - Configuration object
 * @param {boolean} [config.isLoading] - Loading state
 * @param {string} [config.action] - Action type
 * @param {string} [config.category] - Category
 * @param {string} [config.placeholder] - Placeholder text
 * @returns {string} HTML string for placeholder item
 */
function renderPlaceholderItem(config = {}) {
    const {
        isLoading = false, action = 'add-custom-keyword', category = 'keyword', placeholder = getStrings().customKeywordPlaceholder
    } = config;
    const iconHtml = isLoading ?
        '<div class="option-placeholder-spinner"></div>' :
        '<div class="option-placeholder-icon"><i class="fa-solid fa-plus"></i></div>';
    return `
        <div class="option-item placeholder-item ${isLoading ? 'loading' : ''}" data-action="${action}" data-category="${category}">
            ${iconHtml}
            <input type="text" class="placeholder-input" placeholder="${isLoading ? getStrings().processingPlaceholder : placeholder}" ${isLoading ? 'disabled' : ''} maxlength="200" />
        </div>`;
}

/* ================================================================
   SHARED HELPER FOR CUSTOM KEYWORD/TOPIC HEADING HANDLERS
   ================================================================ */

/**
 * Inserts a new option into STATE.options before the placeholder item.
 * @param {Array} options - STATE.options array
 * @param {Object} newOption - Option to insert
 * @param {string} placeholderCategory - Category to find placeholder by
 * @returns {number} Index where option was inserted (or -1 if not inserted)
 */
function insertOptionBeforePlaceholder(options, newOption, placeholderCategory) {
    const placeholderIndex = options.findIndex(o => o.id?.startsWith('placeholder-') && o.category ===
        placeholderCategory);
    if (placeholderIndex === -1) {
        options.push(newOption);
    } else {
        options.splice(placeholderIndex, 0, newOption);
    }
    return placeholderIndex;
}

/* ================================================================
    CUSTOM KEYWORD HANDLER
    ================================================================ */
/**
 * Adds a custom keyword to the search options.
 * @param {string} keyword - Keyword to add
 */
async function addCustomKeyword(keyword) {
    keyword = safeStr(keyword).trim();
    if (!keyword) return;
    if (!STATE.query) return;

    // Check if keyword already exists (only check keyword category, not topic_facet or bklnumber)
    if (STATE.options.some(option => option.category === 'keyword' && option.value.toLowerCase() === keyword
            .toLowerCase())) {
        const placeholderItem = document.querySelector('[data-action="add-custom-keyword"]');
        // Show a temporary tooltip indicating that the keyword already exists
        showTemporaryTooltip(placeholderItem, getStrings().keywordDuplicate);
        return;
    }

    // Show loading state immediately
    STATE_UI.addingCustomKeyword = true;
    renderOptions();

    // Call LLM to decide concept mapping (only with positive concepts since custom keywords are positive)
    let conceptKey = keyword;
    try {
        const mappingResult = await fetchAPI('/add-keyword-to-concepts', {
            keyword: keyword,
            existing_concepts: STATE.qeConcepts.positive
        });
        conceptKey = mappingResult.conceptKey;

        // Replace qeConcepts.positive with server's authoritative state
        if (mappingResult.updated_concepts) {
            STATE.qeConcepts.positive = mappingResult.updated_concepts;
        }
    } catch (error) {
        console.warn('Failed to map keyword, using as new concept:', error);
    }

    // Add keyword to STATE.options (before placeholder, so it appears above)
    const newOption = {
        id: `custom_kw_${Date.now()}`,
        source: 'custom',
        category: 'keyword',
        value: keyword,
        filterValue: keyword,
        label: keyword,
        active: true,
        paramType: 'keyword',
        negated: false,
        conceptKey: conceptKey
    };

    // Insert before placeholder using helper
    insertOptionBeforePlaceholder(STATE.options, newOption, 'keyword');

    // Call /build-logical-tree to update qeMeta with the new keyword
    if (Object.keys(STATE.qeConcepts.positive).length > 0 || Object.keys(STATE.qeConcepts.negative).length > 0) {
        try {
            const result = await fetchAPI('/build-logical-tree', {
                query: STATE.query,
                positive_keywords: STATE.qeConcepts.positive,
                negative_keywords: STATE.qeConcepts.negative
            });
            if (result && result.logicalTree) {
                STATE.qeMeta = STATE.qeMeta || {};
                STATE.qeMeta.logicalTree = result.logicalTree;
            }
        } catch (error) {
            console.warn('Failed to analyze logical tree for custom keyword:', error);
        }
    }

    // Hide loading state
    STATE_UI.addingCustomKeyword = false;
    renderOptions();
    rebuildUrl({
        immediate: true
    });
}


/* ================================================================
    CUSTOM TOPIC HEADING HANDLER
    ================================================================ */
/**
 * Adds a custom topic heading (GND subject) to the search options.
 * @param {string} term - Topic term to search and add
 */
async function addCustomTopicHeading(term) {
    term = safeStr(term).trim();
    if (!term) return;
    if (!STATE.query) return;

    // Show loading state
    STATE_UI.addingCustomTopic = true;
    renderOptions();

    // Call /lookup-vocabulary to resolve the term to a GND heading
    // Search both gnd-saz (subject headings) and gnd-geo (geographical entities)
    let vocabResults = [];
    try {
        const [gndSazResult, gndGeoResult] = await Promise.all([
            fetchAPI('/lookup-vocabulary', {
                term: term,
                vocabulary: 'gnd-saz',
                limit: 10
            }),
            fetchAPI('/lookup-vocabulary', {
                term: term,
                vocabulary: 'gnd-geo',
                limit: 10
            })
        ]);
        // Combine results from both GND databases
        if (gndSazResult && gndSazResult.results) {
            vocabResults = vocabResults.concat(gndSazResult.results);
        }
        if (gndGeoResult && gndGeoResult.results) {
            vocabResults = vocabResults.concat(gndGeoResult.results);
        }
    } catch (error) {
        console.warn('Failed to lookup vocabulary:', error);
    }

    // Show popup for selection (or empty message if no results)
    return new Promise((resolve) => {
        showVocabularySelectionPopup(vocabResults, async (selectedResults) => {
            // User confirmed selection - add selected items
            const itemsToAdd = selectedResults.length > 0 ? selectedResults : vocabResults
                .slice(0, 1);

            if (itemsToAdd.length === 0) {
                // No results and user didn't select anything - just reset state
                STATE_UI.addingCustomTopic = false;
                renderOptions();
                resolve();
                return;
            }

            // Use existing concepts from STATE for LLM concept mapping
            // Call LLM to decide concept mapping for each selected topic
            const topicConceptKeys = [];
            for (const vocabItem of itemsToAdd) {
                const resolvedTerm = vocabItem.label || term;
                const resolvedLabel = vocabItem.label || term;
                let conceptKey = resolvedTerm;
                try {
                    const mappingResult = await fetchAPI('/add-keyword-to-concepts', {
                        keyword: resolvedTerm,
                        existing_concepts: STATE.qtConcepts.positive
                    });
                    conceptKey = mappingResult.conceptKey;

                    // Replace qtConcepts.positive with server's authoritative state
                    if (mappingResult.updated_concepts) {
                        STATE.qtConcepts.positive = mappingResult.updated_concepts;
                    }
                } catch (error) {
                    console.warn('Failed to map topic, using as new concept:', error);
                }
                topicConceptKeys.push({
                    resolvedTerm,
                    resolvedLabel,
                    conceptKey
                });
            }

            // Add each selected topic heading with conceptKey
            topicConceptKeys.forEach((topicData, idx) => {
                // Check for duplicate before adding - use only 'value' for duplicate detection
                const isDuplicate = STATE.options.some(opt =>
                    opt.category === 'topic_facet' &&
                    opt.value === topicData.resolvedTerm
                );

                if (isDuplicate) {
                    return;
                }

                const newOption = {
                    id: `custom_topic_${Date.now()}_${idx}`,
                    source: 'custom',
                    category: 'topic_facet',
                    value: topicData.resolvedTerm,
                    filterValue: topicData.resolvedTerm,
                    label: topicData.resolvedLabel,
                    active: true,
                    paramType: 'search_subject',
                    conceptKey: topicData.conceptKey
                };

                // Insert before placeholder using helper (handles index calculation correctly)
                insertOptionBeforePlaceholder(STATE.options, newOption, 'topic_facet');
            });

            // Call /build-logical-tree to update qtMeta with the new topic headings
            if (Object.keys(STATE.qtConcepts.positive).length > 0) {
                try {
                    const result = await fetchAPI('/build-logical-tree', {
                        query: STATE.query,
                        positive_keywords: STATE.qtConcepts.positive,
                        negative_keywords: STATE.qtConcepts.negative
                    });

                    if (result && result.logicalTree) {
                        STATE.qtMeta = STATE.qtMeta || {};
                        STATE.qtMeta.logicalTree = result.logicalTree;
                    }
                } catch (error) {
                    console.warn('Failed to analyze logical tree for custom topic:', error);
                }
            }

            // Hide loading state
            STATE_UI.addingCustomTopic = false;
            renderOptions();
            rebuildUrl({
                immediate: true
            });
            resolve();
        }, () => {
            // Popup was dismissed - reset loading state
            STATE_UI.addingCustomTopic = false;
            renderOptions();
            resolve();
        });
    });
}


/* ================================================================
    CUSTOM BK NUMBER HANDLER
    ================================================================ */
/**
 * Adds a custom BK classification number to the search options.
 * @param {string} term - BK notation term to search and add
 */
async function addCustomBlkNumber(term) {
    term = safeStr(term).trim();
    if (!term) return;
    if (!STATE.query) return;

    // Show loading state
    STATE_UI.addingCustomBlkNumber = true;
    renderOptions();

    // Call /lookup-vocabulary to resolve the term to a BK notation
    let vocabResults = [];
    try {
        const vocabResult = await fetchAPI('/lookup-vocabulary', {
            term: term,
            vocabulary: 'bk',
            limit: 10
        });
        if (vocabResult && vocabResult.results) {
            vocabResults = vocabResult.results;
        }
    } catch (error) {
        console.warn('Failed to lookup vocabulary:', error);
    }

    // Show popup for selection (or empty message if no results)
    return new Promise((resolve) => {
        showVocabularySelectionPopup(vocabResults, async (selectedResults) => {
            // User confirmed selection - add selected items
            const itemsToAdd = selectedResults.length > 0 ? selectedResults : vocabResults
                .slice(0, 1);

            if (itemsToAdd.length === 0) {
                // No results and user didn't select anything - just reset state
                STATE_UI.addingCustomBlkNumber = false;
                renderOptions();
                resolve();
                return;
            }

            // Find placeholder position
            const placeholderIndex = STATE.options.findIndex(o => o.id?.startsWith(
                'placeholder-') && o.category === 'bklnumber');

            // Add each selected BK number
            itemsToAdd.forEach((vocabItem, idx) => {
                const notation = vocabItem.notation || '';
                const label = vocabItem.label || term;
                const resolvedLabel = notation ? `${label}` : label;
                const resolvedTerm = notation || label;

                const newOption = {
                    id: `custom_blk_${Date.now()}_${idx}`,
                    source: 'custom',
                    category: 'bklnumber',
                    value: resolvedTerm,
                    filterValue: resolvedTerm,
                    label: resolvedLabel,
                    active: true,
                    paramType: 'filter',
                };

                if (placeholderIndex === -1) {
                    STATE.options.push(newOption);
                } else {
                    STATE.options.splice(placeholderIndex + idx, 0, newOption);
                }
            });

            // Hide loading state
            STATE_UI.addingCustomBlkNumber = false;
            renderOptions();
            rebuildUrl({
                immediate: true
            });
            resolve();
        }, () => {
            // Popup was dismissed - reset loading state
            STATE_UI.addingCustomBlkNumber = false;
            renderOptions();
            resolve();
        });
    });
}

/* ================================================================
   VOCABULARY SELECTION POPUP
   Generic popup for selecting vocabulary results.
   ================================================================ */
/**
 * Shows a popup for selecting vocabulary results.
 * @param {Array} vocabResults - Array of VocabularyResult objects with label property
 * @param {Function} onSelect - Callback(selectedItems) called when user confirms selection
 * @param {Function} onDismiss - Optional callback called when popup is dismissed without selection
 * @returns {Function} dismiss function to close popup programmatically
 */
function showVocabularySelectionPopup(vocabResults, onSelect, onDismiss) {
    const overlay = $('#vocabPopupOverlay');
    if (!overlay) return () => {};

    const selectedItems = new Set();
    let dismissed = false;

    // Renders the vocabulary items as selectable buttons in the popup body
    function renderPopupBody() {
        const body = overlay.querySelector('.vocab-popup-body');
        if (!vocabResults || vocabResults.length === 0) {
            body.innerHTML = `<div class="vocab-popup-empty">${getStrings().vocabEmptyResults}</div>`;
            return;
        }

        body.innerHTML = vocabResults.map((result, index) => {
            const label = escapeHtml(safeStr(result.label || ''));
            const isSelected = selectedItems.has(index);
            return `
                <button type="button" class="vocab-popup-item ${isSelected ? 'selected' : ''}" data-action="toggle-item" data-index="${index}" aria-pressed="${isSelected}">
                    <span class="option-checkbox"><i class="fa-solid fa-check"></i></span>
                    <span class="vocab-popup-item-text">${label}</span>
                </button>`;
        }).join('');
    }

    // Closes the popup and removes event listeners
    function dismiss() {
        if (dismissed) return;
        dismissed = true;
        overlay.classList.remove('visible');
        overlay.removeEventListener('click', handleOverlayClick);
        document.removeEventListener('keydown', handleKeydown);
    }

    // Single delegated event handler for all popup interactions (close, select-all, deselect-all, apply, toggle-item)
    function handleOverlayClick(event) {
        // Close on overlay click (outside popup)
        if (event.target === overlay) {
            dismiss();
            onDismiss?.();
            return;
        }

        // Handle button actions via data-action attributes
        const action = event.target.closest('[data-action]')?.dataset.action;
        switch (action) {
            case 'close':
                dismiss();
                onDismiss?.();
                break;
            case 'select-all':
                vocabResults.forEach((_, index) => selectedItems.add(index));
                renderPopupBody();
                break;
            case 'deselect-all':
                selectedItems.clear();
                renderPopupBody();
                break;
            case 'apply':
                dismiss();
                onSelect?.(Array.from(selectedItems).map(index => vocabResults[index]));
                break;
            case 'toggle-item': {
                const item = event.target.closest('.vocab-popup-item');
                if (item) {
                    const index = parseInt(item.dataset.index, 10);
                    if (selectedItems.has(index)) {
                        selectedItems.delete(index);
                    } else {
                        selectedItems.add(index);
                    }
                    renderPopupBody();
                }
                break;
            }
        }
    }

    // Closes popup when Escape key is pressed
    function handleKeydown(event) {
        if (event.key === 'Escape') {
            dismiss();
            onDismiss?.();
        }
    }

    overlay.addEventListener('click', handleOverlayClick);
    document.addEventListener('keydown', handleKeydown);
    overlay.classList.add('visible');
    renderPopupBody();

    return dismiss;
}


/* ================================================================
   INTERACTION HANDLERS
   Handles user interactions with options, controls, and history.
   ================================================================ */
/**
 * Toggles an option's active state and triggers URL rebuild.
 * @param {string} optionId - Option ID to toggle
 */
function toggleOpt(optionId) {
    const option = STATE.options.find(currentOption => currentOption.id === optionId);
    if (!option) return;
    option.active = !option.active;

    const element = document.querySelector(`[data-oid="${optionId}"]`);
    if (element) element.classList.toggle('active', option.active);

    /* Instant URL rebuild + result count fetch on every toggle */
    rebuildUrl();
}

/* ================================================================
   REMOVE OPTION
   Permanently removes an option from STATE.options.
   If the option is active, it is first toggled off.
   For keywords and topics, the logical tree is rebuilt.
   ================================================================ */
/**
 * Removes an option from STATE.options and rebuilds URL.
 * @param {string} optionId - Option ID to remove
 */
function removeOption(optionId) {
    const optionIndex = STATE.options.findIndex(opt => opt.id === optionId);
    if (optionIndex === -1) return;

    const option = STATE.options[optionIndex];

    // If the option is active, first toggle it off
    // This ensures the UI state is consistent and the debounced fetch is properly triggered
    if (option.active) {
        option.active = false;
    }

    // Remove from STATE.options first (so rebuildLogicalTree sees the correct state)
    STATE.options.splice(optionIndex, 1);

    // For keyword/topic_facet, need to update logical tree
    if (option.paramType === 'keyword' || option.paramType === 'search_subject') {
        // Rebuild logical tree without this option
        rebuildLogicalTree(option);
    }

    // Re-render and rebuild URL
    renderOptions();
    rebuildUrl({
        immediate: true
    });
}

/* ================================================================
   REBUILD LOGICAL TREE
   Rebuilds the logical tree after an option removal.
   Used to keep the logical tree in sync with STATE.options.
   ================================================================ */
/**
 * Rebuilds the logical tree after an option removal.
 * @param {Object} removedOption - The option that was removed
 */
async function rebuildLogicalTree(removedOption) {
    // Check if this is a topic heading (vs keyword)
    const isTopicHeading = removedOption.paramType === 'search_subject';
    const isKeyword = removedOption.paramType === 'keyword';

    // Determine which concept store to update
    const concepts = isKeyword ? STATE.qeConcepts : STATE.qtConcepts;

    // Rebuild positive/negative concepts from remaining STATE.options
    const positiveConcepts = {};
    const negativeConcepts = {};

    // Iterate remaining options and group by conceptKey for logical tree reconstruction
    STATE.options.forEach(opt => {
        if (opt.category !== removedOption.category) return;
        if (opt.paramType !== 'keyword' && opt.paramType !== 'search_subject') return;

        const conceptKey = opt.conceptKey || opt.value;
        const targetDict = opt.negated ? negativeConcepts : positiveConcepts;

        if (!targetDict[conceptKey]) {
            targetDict[conceptKey] = [];
        }
        if (!targetDict[conceptKey].includes(opt.value)) {
            targetDict[conceptKey].push(opt.value);
        }
    });

    // Update STATE concepts with rebuilt values
    concepts.positive = positiveConcepts;
    concepts.negative = negativeConcepts;

    // Call /build-logical-tree to update the logical tree
    // Skip API call if no concepts remain - avoids unnecessary 422 error
    if (Object.keys(positiveConcepts).length === 0 && Object.keys(negativeConcepts).length === 0) {
        return;
    }

    try {
        const result = await fetchAPI('/build-logical-tree', {
            query: STATE.query,
            positive_keywords: positiveConcepts,
            negative_keywords: negativeConcepts
        });
        if (result && result.logicalTree) {
            if (isKeyword) {
                STATE.qeMeta = STATE.qeMeta || {};
                STATE.qeMeta.logicalTree = result.logicalTree;
            } else if (isTopicHeading) {
                STATE.qtMeta = STATE.qtMeta || {};
                STATE.qtMeta.logicalTree = result.logicalTree;
            }
        }
    } catch (error) {
        console.warn('Failed to rebuild logical tree after removal:', error);
    }
}

/**
 * Updates the controls bar visibility and active count badge.
 */
function updateControlsBar() {
    const activeCount = STATE.options.filter(option => option.active).length;
    const controlsContainer = $('#controlsContainer');
    const controlsBadge = $('#controlsBadge');
    if (STATE.options.length > 0) {
        if (controlsContainer) controlsContainer.style.display = 'flex';
    } else {
        if (controlsContainer) controlsContainer.style.display = 'none';
    }
    if (controlsBadge) controlsBadge.textContent = activeCount;
}

/**
 * Resets options to their initial state (after the search pipeline completed).
 */
function resetOptions() {
    STATE.options = JSON.parse(JSON.stringify(STATE.initialOptions));
    renderOptions();
    rebuildUrl({
        immediate: true
    });
}

/* ================================================================
   SEARCH HISTORY
   Manages and renders the search history list.
   ================================================================ */
/**
 * Creates a serializable snapshot of the current search state.
 * Excludes runtime-only fields like fetchDebounce, timers, and history itself.
 */
function createStateSnapshot() {
    return {
        query: STATE.query,
        options: JSON.parse(JSON.stringify(STATE.options)),
        initialOptions: JSON.parse(JSON.stringify(STATE.initialOptions)),
        siMeta: STATE.siMeta,
        qtMeta: STATE.qtMeta,
        qeMeta: STATE.qeMeta,
        qeConcepts: JSON.parse(JSON.stringify(STATE.qeConcepts)),
        qtConcepts: JSON.parse(JSON.stringify(STATE.qtConcepts)),
        vufindResults: JSON.parse(JSON.stringify(STATE.vufindResults)),
        totalResults: STATE.totalResults,
        qualityScore: STATE.qualityScore,
        qualityAssessment: STATE.qualityAssessment,
        relevantIndices: JSON.parse(JSON.stringify(STATE.relevantIndices)),
        generatedUrl: STATE.generatedUrl,
    };
}

/**
 * Restores the UI from a history snapshot without re-triggering API calls.
 */
function restoreFromSnapshot(snapshot) {
    if (!snapshot) return;

    // Abort any in-flight requests before restoring state
    if (STATE_UI.abortController) {
        STATE_UI.abortController.abort();
    }
    STATE_UI.abortController = new AbortController();

    // Clear any pending debounced fetch
    if (STATE_UI.fetchDebounce) {
        clearTimeout(STATE_UI.fetchDebounce);
        STATE_UI.fetchDebounce = null;
        stopDebounceTimer();
    }

    // Restore core state
    STATE.query = snapshot.query || '';
    STATE.options = JSON.parse(JSON.stringify(snapshot.options || []));
    STATE.initialOptions = JSON.parse(JSON.stringify(snapshot.initialOptions || []));
    STATE.siMeta = snapshot.siMeta || null;
    STATE.qtMeta = snapshot.qtMeta || null;
    STATE.qeMeta = snapshot.qeMeta || null;
    STATE.qeConcepts = JSON.parse(JSON.stringify(snapshot.qeConcepts || {
        positive: {},
        negative: {}
    }));
    STATE.qtConcepts = JSON.parse(JSON.stringify(snapshot.qtConcepts || {
        positive: {},
        negative: {}
    }));
    STATE.vufindResults = JSON.parse(JSON.stringify(snapshot.vufindResults || []));
    STATE.totalResults = snapshot.totalResults;
    STATE.qualityScore = snapshot.qualityScore;
    STATE.qualityAssessment = snapshot.qualityAssessment || '';
    STATE.relevantIndices = JSON.parse(JSON.stringify(snapshot.relevantIndices || []));
    STATE.generatedUrl = snapshot.generatedUrl || '';

    // Restore search input
    $('#searchInput').value = STATE.query;
    // Show/hide clear button based on restored input content
    const clearBtn = $('#searchClearBtn');
    if (clearBtn) {
        clearBtn.style.display = STATE.query && STATE.query.length > 0 ? 'flex' : 'none';
    }

    // Restore results panel visibility
    const debugPanel = $('#debugPanel');
    if (debugPanel) debugPanel.style.display = CONFIG.SHOW_DEBUG_PANEL ? 'block' : 'none';

    // Restore pipeline indicators to neutral state since siDone/qeDone/qtDone are not persisted
    setPipeline('pipelineSI', 'false');
    setPipeline('pipelineQE', 'false');
    setPipeline('pipelineQT', 'false');

    // Restore URL box
    $('#generatedUrl').innerHTML = STATE.generatedUrl ? highlightUrl(STATE.generatedUrl) : getStrings().waitingForResults;
    const openInVuFind = $('#openInVuFind');
    if (openInVuFind) openInVuFind.href = STATE.generatedUrl;

    // Restore options
    renderOptions();
    updateControlsBar();

    // Restore quality score
    renderQualityScore();

    // Restore VuFind results
    renderVufindResults(false);

    // Restore subtitle count number
    if (STATE.totalResults != null) {
        const subtitleCountEl = $('#subtitleCountNumber');
        if (subtitleCountEl) subtitleCountEl.textContent = new Intl.NumberFormat('de-DE').format(STATE.totalResults);
    }

    // Show results subtitle if we have a total result count (including 0 results)
    const subtitle = $('#resultsSubtitle');
    if (subtitle && STATE.totalResults != null) {
        subtitle.classList.add('visible');
    }
}

/**
 * Adds a query to the search history.
 * @param {string} query - Search query
 */
function addHistory(query) {
    STATE.history = STATE.history.filter(historyEntry => historyEntry.query !== query);
    STATE.history.unshift({
        query,
        timestamp: new Date()
    });
    STATE.history = STATE.history.slice(0, CONFIG.MAX_HISTORY);
    saveHistoryToStorage(STATE.history);
    renderHistory();
}

/**
 * Updates the history entry snapshot for a query.
 * @param {string} query - Search query
 * @param {Object} snapshot - State snapshot to save
 */
function updateHistorySnapshot(query, snapshot) {
    const entry = STATE.history.find(historyEntry => historyEntry.query === query);
    if (entry) {
        entry.snapshot = snapshot;
        saveHistoryToStorage(STATE.history);
    }
}

/**
 * Clears all search history.
 */
function clearHistory() {
    STATE.history = [];
    saveHistoryToStorage(STATE.history);
    renderHistory();
}

/**
 * Renders the search history list in the UI.
 */
function renderHistory() {
    const historyList = $('#historyList');
    if (!historyList) return;
    if (!STATE.history.length) {
        historyList.innerHTML = `<div class="empty-history">${getStrings().emptyHistory}</div>`;
        return;
    }
    historyList.innerHTML = STATE.history.map((historyEntry, historyIndex) =>
        `<button type="button" class="history-item" data-index="${historyIndex}" aria-label="${escapeHtml(historyEntry.query)}">
            <span class="history-text">${escapeHtml(historyEntry.query)}</span>
         </button>`
    ).join('');
    historyList.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', () => {
            const historyEntry = STATE.history[+item.dataset.index];
            restoreFromSnapshot(historyEntry.snapshot);
        });
    });
}


/* ================================================================
   TOOLTIP SYSTEM
   Manages and renders tooltips across the UI.
   ================================================================ */

/**
 * Creates a tooltip on a trigger element with dynamic content.
 * @param {string|Element} triggerSelector - CSS selector or DOM element
 * @param {Function} getContent - Function that returns tooltip content
 */
function createTooltip(triggerSelector, getContent) {
    /* Generic tooltip creator for any element with hover (desktop) and tap (mobile) support.

       Usage:
         createTooltip('.my-trigger', () => STATE.someStateValue);  // CSS selector string
         createTooltip(someElement, () => 'Static content');         // or DOM element directly
    */
    const trigger = typeof triggerSelector === 'string' ? $(triggerSelector) : triggerSelector;
    if (!trigger) return;

    // Add question mark icon inside the trigger element (always at right-end)
    const icon = document.createElement('span');
    icon.className = 'tooltip-icon';
    icon.innerHTML = '<i class="fa-regular fa-circle-question"></i>';
    icon.style.cssText = 'margin-left: 8px; padding: 2px; display: inline-flex; align-items: center;';
    const iconWrapper = document.createElement('span');
    iconWrapper.style.cssText = 'margin-left: auto;';
    iconWrapper.appendChild(icon);
    trigger.style.display = 'flex';
    trigger.style.alignItems = 'center';
    trigger.appendChild(iconWrapper);

    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    document.body.appendChild(tooltip);

    let visible = false;

    // Positions and displays the tooltip below or above the trigger element
    function show() {
        const content = getContent();
        if (!content) return;
        tooltip.textContent = content;
        tooltip.style.display = 'block';
        const rect = iconWrapper.getBoundingClientRect();
        const tRect = tooltip.getBoundingClientRect();
        let left = rect.left + (rect.width / 2) - (tRect.width / 2);
        let top = rect.bottom + 8;
        if (top + tRect.height > window.innerHeight - 10) {
            top = rect.top - tRect.height - 8;
        }
        // Ensure tooltip doesn't touch right viewport edge
        const maxLeft = window.innerWidth - tRect.width - 20;
        tooltip.style.left = Math.min(Math.max(20, left), maxLeft) + 'px';
        tooltip.style.top = top + 'px';
        visible = true;
    }

    function hide() {
        tooltip.style.display = 'none';
        visible = false;
    }

    // Desktop: hover
    iconWrapper.addEventListener('mouseenter', show);
    iconWrapper.addEventListener('mouseleave', hide);

    // Mobile: tap to toggle
    iconWrapper.addEventListener('click', () => {
        visible ? hide() : show();
    });
}

/* ================================================================
   TEMPORARY TOOLTIP
   Shows a temporary tooltip with custom styling, auto-hides after delay.
   ================================================================ */
/**
 * Shows a temporary tooltip that auto-hides after a duration.
 * @param {Element} targetElement - DOM element to attach tooltip to
 * @param {string} message - Tooltip message text
 * @param {number} [duration] - Auto-hide delay in ms (default 3000)
 */
function showTemporaryTooltip(targetElement, message, duration = 3000) {
    if (!targetElement) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip tooltip-temporary';
    tooltip.textContent = message;
    document.body.appendChild(tooltip);

    const rect = targetElement.getBoundingClientRect();
    const tRect = tooltip.getBoundingClientRect();
    let left = rect.left + (rect.width / 2) - (tRect.width / 2);
    let top = rect.bottom + 4;
    if (top + tRect.height > window.innerHeight - 10) {
        top = rect.top - tRect.height - 4;
    }
    const maxLeft = window.innerWidth - tRect.width - 20;
    tooltip.style.left = Math.min(Math.max(20, left), maxLeft) + 'px';
    tooltip.style.top = top + 'px';

    setTimeout(() => {
        tooltip.style.display = 'none';
        tooltip.remove();
    }, duration);
}


/* ================================================================
   COMPASS ANIMATION
   Smooth, organic compass needle sway with randomness.
   ================================================================ */
const compassAnim = (() => {
    let animId = null;
    let startTime = null;
    let config = { angle: 0, speed: 0, target: 0 };

    const getRand = (min, max) => Math.random() * (max - min) + min;

    function pickNextTarget() {
        // Ensure minimum 30 degree movement from current position
        const minMove = 30;
        let newTarget;
        do {
            newTarget = getRand(-100, 100);
        } while (Math.abs(newTarget - config.angle) < minMove);
        config.target = newTarget;
        config.speed = getRand(0.4, 0.9);
    }

    function animate(timestamp) {
        if (!startTime) startTime = timestamp;
        const elapsed = (timestamp - startTime) / 1000;

        // Smooth easing toward target angle
        const diff = config.target - config.angle;
        config.angle += diff * 0.04 * config.speed;

        // Gentle oscillation overlay for natural feel
        const wobble = Math.sin(elapsed * 0.7) * 2 + Math.sin(elapsed * 1.3) * 1;

        const compass = document.querySelector('.compass-svg');
        if (compass) {
            compass.style.transform = `rotate(${config.angle + wobble}deg)`;
        }

        // Check if close enough to target, then pick new target
        if (Math.abs(diff) < 0.5) {
            pickNextTarget();
        }

        animId = requestAnimationFrame(animate);
    }

    function start() {
        pickNextTarget();
        animId = requestAnimationFrame(animate);
    }

    function stop() {
        if (animId) {
            cancelAnimationFrame(animId);
            animId = null;
        }
    }

    return { start, stop };
})();

/* ================================================================
   UPDATE UI ELEMENTS
   Updates UI elements that are dynamically rendered via JavaScript
   (not via data-i18n attributes) when language is switched.
   ================================================================ */

/**
 * Updates the search button text to reflect the current language.
 * Called after language switch since the button text is set dynamically via JavaScript.
 */
function updateSearchBtn() {
    const searchBtn = $('#searchBtn');
    if (!searchBtn) return;

    // Only update if the button is in its default state (not showing loading spinner)
    const isLoading = searchBtn.querySelector('.spinner') !== null;
    if (!isLoading) {
        searchBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> ${getStrings().searchBtn}`;
    }
}

/* ================================================================
   UPDATE OPTION LABELS
   Updates the UI labels for options when language is switched.
   ================================================================ */

/**
 * Updates all option labels in the UI to reflect the current language.
 * Called after language switch to update labels without re-rendering options.
 */
function updateOptionLabels() {
    const lang = getLanguage();
    const categoryLabels = getCategoryLabels(lang);
    const mediaFormLabels = getMediaFormLabels(lang);
    const languageLabels = getLanguageLabels(lang);

    // Update option card headers (category labels)
    document.querySelectorAll('.option-card').forEach(card => {
        const header = card.querySelector('.option-card-header');
        if (!header) return;

        // Get category from card - check for data attribute or find by icon class
        const iconEl = header.querySelector('.option-icon');
        if (!iconEl) return;

        // Determine category by icon class
        let category = null;
        const iconClass = iconEl.className;
        if (iconClass.includes(UI_ELEMENTS.keywordIcon.replace('fa-', ''))) category = 'keyword';
        else if (iconClass.includes(UI_ELEMENTS.topicIcon.replace('fa-', ''))) category = 'topic_facet';
        else if (iconClass.includes(UI_ELEMENTS.bklIcon.replace('fa-', ''))) category = 'bklnumber';
        else if (iconClass.includes(UI_ELEMENTS.formatIcon.replace('fa-', ''))) category = 'format';
        else if (iconClass.includes(UI_ELEMENTS.formatDetailsIcon.replace('fa-', ''))) category = 'format_details';
        else if (iconClass.includes(UI_ELEMENTS.languageIcon.replace('fa-', ''))) category = 'language';
        else if (iconClass.includes(UI_ELEMENTS.authorIcon.replace('fa-', ''))) category = 'author_facet';
        else if (iconClass.includes(UI_ELEMENTS.dateIcon.replace('fa-', ''))) category = 'date';

        if (category && categoryLabels[category]) {
            const iconHtml = `<i class="fa-solid ${iconEl.className.replace('option-icon', '').trim()} option-icon"></i>`;
            header.innerHTML = iconHtml + ' ' + escapeHtml(categoryLabels[category]);
        }
    });

    // Update item labels and badges
    document.querySelectorAll('#optionsGrid .option-item:not(.placeholder-item)').forEach(item => {
        const optionId = item.dataset.oid;
        const option = STATE.options.find(o => o.id === optionId);
        if (!option) return;

        let newLabel = option.label;

        // Apply media form mapping for format category items
        if (option.category === 'format' && mediaFormLabels[option.label]) {
            newLabel = mediaFormLabels[option.label];
        }

        // Apply language mapping for language category items
        if (option.category === 'language' && languageLabels[option.label]) {
            newLabel = languageLabels[option.label];
        }

        // Update text content
        const textEl = item.querySelector('.option-item-text');
        if (textEl) textEl.textContent = newLabel;

        // Update badge
        const badgeEl = item.querySelector('.option-item-type');
        if (badgeEl && categoryLabels[option.category]) {
            badgeEl.textContent = categoryLabels[option.category];
        }
    });

    // Update empty-option text when there are no options
    const emptyOption = document.querySelector('#optionsGrid .empty-option');
    if (emptyOption) {
        emptyOption.textContent = getStrings().noSearchOptionsAvailable;
    }

    // Update placeholder input placeholders for custom keyword, topic, and BK number inputs
    const customKeywordInput = document.querySelector('[data-action="add-custom-keyword"] .placeholder-input');
    if (customKeywordInput && !customKeywordInput.disabled) {
        customKeywordInput.placeholder = getStrings().customKeywordPlaceholder;
    }

    const customTopicInput = document.querySelector('[data-action="add-custom-topic"] .placeholder-input');
    if (customTopicInput && !customTopicInput.disabled) {
        customTopicInput.placeholder = getStrings().customTopicPlaceholder;
    }

    const customBlkNumberInput = document.querySelector('[data-action="add-custom-blk-number"] .placeholder-input');
    if (customBlkNumberInput && !customBlkNumberInput.disabled) {
        customBlkNumberInput.placeholder = getStrings().customBlkNumberPlaceholder;
    }
}

/* ================================================================
   INITIALIZATION
   Sets up event listeners on page load. Handles search input, option
   interactions, keyboard shortcuts, tooltips, and UI popups.
   ================================================================ */
document.addEventListener('DOMContentLoaded', () => {    // Check if welcome popup was previously dismissed (by checking if research-compass-settings key exists)
    const wasDismissed = localStorage.getItem('research-compass-settings') !== null;
    if (!wasDismissed) {
        const welcomePopup = document.getElementById('welcomePopup');
        if (welcomePopup) {
            welcomePopup.classList.add('visible');
            compassAnim.start();
        }
    }

    // Helper to dismiss and persist the welcome popup dismissal
    function dismissWelcomePopup() {
        const welcomePopup = document.getElementById('welcomePopup');
        if (welcomePopup) {
            welcomePopup.classList.remove('visible');
        }
        // Set research-compass-settings to indicate popup was dismissed
        localStorage.setItem('research-compass-settings', JSON.stringify({ welcomeDismissed: true }));
    }

    // Welcome popup close handler
    const welcomePopup = document.getElementById('welcomePopup');
    const welcomePopupClose = document.getElementById('welcomePopupClose');
    if (welcomePopupClose && welcomePopup) {
        welcomePopupClose.addEventListener('click', dismissWelcomePopup);
    }
    if (welcomePopup) {
        welcomePopup.addEventListener('click', (e) => {
            if (e.target === welcomePopup) {
                dismissWelcomePopup();
            }
        });
    }
    if (welcomePopup) {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && welcomePopup.classList.contains('visible')) {
                dismissWelcomePopup();
            }
        });
    }

    // Apply debug panel visibility from config
    const debugPanel = $('#debugPanel');
    if (debugPanel) debugPanel.style.display = CONFIG.SHOW_DEBUG_PANEL ? 'block' : 'none';

    // Toggle debug panel with Ctrl-Alt-D
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'd') {
            CONFIG.SHOW_DEBUG_PANEL = !CONFIG.SHOW_DEBUG_PANEL;
            if (debugPanel) {
                debugPanel.style.display = CONFIG.SHOW_DEBUG_PANEL ? 'block' : 'none';
            }
        }
    });

    // Load history from localStorage
    STATE.history = loadHistoryFromStorage();
    renderHistory();

    $('#searchBtn').addEventListener('click', () => doSearch($('#searchInput').value));
    $('#searchInput').addEventListener('keypress', keyEvent => {
        if (keyEvent.key === 'Enter') doSearch($('#searchInput').value);
    });
    $('#searchInput').addEventListener('input', (e) => {
        // Show/hide clear button based on input content
        const clearBtn = $('#searchClearBtn');
        if (clearBtn) {
            clearBtn.style.display = e.target.value.length > 0 ? 'flex' : 'none';
        }
    });
    $('#searchClearBtn').addEventListener('click', () => {
        const searchInput = $('#searchInput');
        if (searchInput) {
            searchInput.value = '';
            searchInput.focus();
            STATE.query = '';
            const clearBtn = $('#searchClearBtn');
            if (clearBtn) clearBtn.style.display = 'none';
        }
    });
    $('#resetBtn').addEventListener('click', resetOptions);
    $('#clearHistoryBtn').addEventListener('click', clearHistory);
    $$('.search-example-item').forEach(button => button.addEventListener('click', () => {
        $('#searchInput').value = button.dataset.query;
        const clearBtn = $('#searchClearBtn');
        if (clearBtn) clearBtn.style.display = button.dataset.query && button.dataset.query.length >
            0 ? 'flex' : 'none';
        doSearch(button.dataset.query);
    }));

    // Delegated click handler for option grid: handles placeholder inputs,
    // custom keyword/topic/BK number addition, remove buttons, and option toggles
    $('#optionsGrid').addEventListener('click', clickEvent => {
        const item = clickEvent.target.closest('.option-item');
        if (!item) return;

        // Handle placeholder items - clicking on input should not trigger any action
        if (clickEvent.target.classList.contains('placeholder-input')) {
            return;
        }

        // Handle placeholder item for adding custom keyword
        if (item.dataset.action === 'add-custom-keyword') {
            const input = item.querySelector('.placeholder-input');
            if (!input || input.disabled) return;

            // Click on + icon submits the keyword
            if (clickEvent.target.closest('.option-placeholder-icon')) {
                const keyword = input.value.trim();
                if (keyword) addCustomKeyword(keyword);
                return;
            }

            // Click elsewhere in placeholder focuses input
            input.focus();
            return;
        }

        // Handle placeholder item for adding custom topic heading
        if (item.dataset.action === 'add-custom-topic') {
            const input = item.querySelector('.placeholder-input');
            if (!input || input.disabled) return;

            // Click on + icon submits the topic heading
            if (clickEvent.target.closest('.option-placeholder-icon')) {
                const term = input.value.trim();
                if (term) addCustomTopicHeading(term);
                return;
            }

            // Click elsewhere in placeholder focuses input
            input.focus();
            return;
        }

        // Handle placeholder item for adding custom BK number
        if (item.dataset.action === 'add-custom-blk-number') {
            const input = item.querySelector('.placeholder-input');
            if (!input || input.disabled) return;

            // Click on + icon submits the BK number
            if (clickEvent.target.closest('.option-placeholder-icon')) {
                const term = input.value.trim();
                if (term) addCustomBlkNumber(term);
                return;
            }

            // Click elsewhere in placeholder focuses input
            input.focus();
            return;
        }

        // Handle remove button click
        const removeBtn = clickEvent.target.closest('.option-remove-btn');
        if (removeBtn) {
            clickEvent.stopPropagation();
            const optionId = removeBtn.dataset.removeOid;
            if (optionId) removeOption(optionId);
            return;
        }

        if (item.dataset.oid) {
            toggleOpt(item.dataset.oid);
        }
    });

    // Keyboard handler for option-item buttons (Delete/Backspace to remove)
    $('#optionsGrid').addEventListener('keydown', keyEvent => {
        const item = keyEvent.target.closest('.option-item');
        if (!item) return;

        // Skip placeholder items
        if (item.dataset.action?.startsWith('add-custom-')) {
            return;
        }

        // Handle Delete/Backspace to remove option
        if (keyEvent.key === 'Delete' || keyEvent.key === 'Backspace') {
            const optionId = item.dataset.oid;
            if (optionId) {
                keyEvent.preventDefault();
                removeOption(optionId);
            }
        }
    });

    // Handle Enter key on placeholder input
    $('#optionsGrid').addEventListener('keypress', keyEvent => {
        if (keyEvent.key === 'Enter') {
            const input = keyEvent.target.closest('.placeholder-input');
            if (input) {
                const value = input.value.trim();
                if (!value) return;

                const item = input.closest('.option-item');
                if (item && item.dataset.action === 'add-custom-topic') {
                    addCustomTopicHeading(value);
                } else if (item && item.dataset.action === 'add-custom-keyword') {
                    addCustomKeyword(value);
                } else if (item && item.dataset.action === 'add-custom-blk-number') {
                    addCustomBlkNumber(value);
                }
            }
        }
    });

    // Quality assessment tooltip - shows prefix only (full assessment is in speech bubble)
    createTooltip('.subtitle-quality', () => getStrings().qualityTooltip);

    // Search examples sidebar header tooltip
    createTooltip('#searchExamplesHeader', () => getStrings().searchExamplesTooltip);

    // Tooltips for search options are added / rendered dynamically in the relevant code section

    // Show options section with placeholder on first load
    renderOptions();

    // About popup handlers
    const aboutLink = document.getElementById('aboutLink');
    const aboutPopup = document.getElementById('aboutPopup');
    const aboutPopupClose = document.getElementById('aboutPopupClose');

    if (aboutLink && aboutPopup) {
        aboutLink.addEventListener('click', (e) => {
            e.preventDefault();
            aboutPopup.classList.add('visible');
        });
    }

    // Close about popup when close button is clicked
    if (aboutPopupClose && aboutPopup) {
        aboutPopupClose.addEventListener('click', () => {
            aboutPopup.classList.remove('visible');
        });
    }

    // Close about popup when clicking outside the popup content (on the overlay)
    if (aboutPopup) {
        aboutPopup.addEventListener('click', (e) => {
            if (e.target === aboutPopup) {
                aboutPopup.classList.remove('visible');
            }
        });
    }

    // Close about popup when Escape key is pressed
    if (aboutPopup) {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && aboutPopup.classList.contains('visible')) {
                aboutPopup.classList.remove('visible');
            }
        });
    }

    // Accessibility report popup handlers
    const accessibilityReportLink = document.getElementById('reportAccessibilityIssueLink');
    const accessibilityReportPopup = document.getElementById('accessibilityReportPopup');
    const accessibilityReportPopupClose = document.getElementById('accessibilityReportPopupClose');

    if (accessibilityReportLink && accessibilityReportPopup) {
        accessibilityReportLink.addEventListener('click', (e) => {
            e.preventDefault();
            accessibilityReportPopup.classList.add('visible');
        });
    }

    // Close accessibility report popup when close button is clicked
    if (accessibilityReportPopupClose && accessibilityReportPopup) {
        accessibilityReportPopupClose.addEventListener('click', () => {
            accessibilityReportPopup.classList.remove('visible');
        });
    }

    // Close accessibility report popup when clicking outside the popup content (on the overlay)
    if (accessibilityReportPopup) {
        accessibilityReportPopup.addEventListener('click', (e) => {
            if (e.target === accessibilityReportPopup) {
                accessibilityReportPopup.classList.remove('visible');
            }
        });
    }

    // Close accessibility report popup when Escape key is pressed
    if (accessibilityReportPopup) {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && accessibilityReportPopup.classList.contains('visible')) {
                accessibilityReportPopup.classList.remove('visible');
            }
        });
    }

    // Language switcher click handlers
    const langDeLink = document.getElementById('langDe');
    const langEnLink = document.getElementById('langEn');

    if (langDeLink) {
        langDeLink.addEventListener('click', (e) => {
            e.preventDefault();
            saveLanguage('de');
            initUI('de');
            updateOptionLabels();
            updateSearchBtn();
        });
    }

    if (langEnLink) {
        langEnLink.addEventListener('click', (e) => {
            e.preventDefault();
            saveLanguage('en');
            initUI('en');
            updateOptionLabels();
            updateSearchBtn();
        });
    }

    // Logo click handler - reloads the page
    const logo = document.querySelector('.logo');
    if (logo) {
        logo.addEventListener('click', () => {
            window.location.reload();
        });
    }

    // Initialize UI (called at end of DOMContentLoaded to ensure all DOM elements exist)
    initUI();
});
