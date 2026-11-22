import api from '../services/api';

export const MAX_ACTIVITY_LOG = 20;

const TERMINAL_MILESTONES = new Set([
    'museum_started',
    'candidate_found',
    'museum_completed',
    'complete',
    'error',
]);

/**
 * Format elapsed seconds cleanly as M:SS (e.g., 0:04, 1:12).
 */
export function formatElapsedTime(totalSeconds) {
    const safeSeconds = Number.isFinite(totalSeconds) && totalSeconds > 0
        ? Math.floor(totalSeconds)
        : 0;
    const mins = Math.floor(safeSeconds / 60);
    const secs = safeSeconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Build the initial client-side progress model before the first NDJSON chunk arrives.
 */
export function createInitialProgressState(selectedMuseumIds, museumsCatalog = [], totalKeywords = 0) {
    const byId = new Map((museumsCatalog || []).map((m) => [m.id, m.name]));
    const museumList = (selectedMuseumIds || []).map((id) => ({
        museum_id: id,
        museum_name: byId.get(id) || id.toUpperCase(),
        status: 'queued',
        currentStage: 'Queued',
        fetched_count: 0,
        new_count: 0,
        duplicates_skipped: 0,
        error: null,
        progressFraction: 0,
    }));

    return {
        phase: 'connecting',
        percent: null,
        totalMuseums: museumList.length,
        completedMuseums: 0,
        totalKeywords,
        currentMuseumId: null,
        currentKeyword: null,
        statusMessage: 'Connecting to museum APIs...',
        totalChecked: 0,
        totalNew: 0,
        totalSkipped: 0,
        museums: museumList,
        activityLog: [],
    };
}

function computeOverallPercent(museums, phase) {
    if (phase === 'complete') return 100;
    if (!museums || museums.length === 0) return null;
    const sum = museums.reduce((acc, m) => acc + (m.progressFraction || 0), 0);
    const raw = Math.round((sum / museums.length) * 100);
    return Math.max(0, Math.min(99, raw));
}

function appendActivityLog(prevLog, event) {
    if (!event?.type || !TERMINAL_MILESTONES.has(event.type) || !event.message) {
        return prevLog;
    }
    const entry = {
        id: `${event.type}-${event.museum_id || 'all'}-${Date.now()}-${prevLog.length}`,
        type: event.type,
        museum_id: event.museum_id || null,
        message: event.message,
    };
    return [entry, ...prevLog].slice(0, MAX_ACTIVITY_LOG);
}

/**
 * Apply a single parsed NDJSON progress event to the live discovery UI state.
 */
export function reduceDiscoveryProgress(prev, event) {
    if (!prev || !event || typeof event !== 'object') {
        return prev;
    }

    let nextPhase = prev.phase;
    let nextMuseums = prev.museums.map((m) => ({ ...m }));
    let currentMuseumId = prev.currentMuseumId;
    let currentKeyword = prev.currentKeyword;
    const statusMessage = event.message || prev.statusMessage;
    const totalKeywords = event.total_keywords ?? prev.totalKeywords;

    const findMuseumIndex = (museumId) =>
        nextMuseums.findIndex((m) => m.museum_id === museumId);

    switch (event.type) {
        case 'search_started': {
            nextPhase = 'searching';
            if (Array.isArray(event.museums) && event.museums.length > 0) {
                const existingMap = new Map(nextMuseums.map((m) => [m.museum_id, m]));
                nextMuseums = event.museums.map((m) => ({
                    museum_id: m.museum_id,
                    museum_name: m.museum_name,
                    status: existingMap.get(m.museum_id)?.status || 'queued',
                    currentStage: existingMap.get(m.museum_id)?.currentStage || 'Queued',
                    fetched_count: existingMap.get(m.museum_id)?.fetched_count || 0,
                    new_count: existingMap.get(m.museum_id)?.new_count || 0,
                    duplicates_skipped: existingMap.get(m.museum_id)?.duplicates_skipped || 0,
                    error: existingMap.get(m.museum_id)?.error || null,
                    progressFraction: existingMap.get(m.museum_id)?.progressFraction || 0,
                }));
            }
            break;
        }
        case 'museum_started': {
            nextPhase = 'searching';
            currentMuseumId = event.museum_id;
            const idx = findMuseumIndex(event.museum_id);
            if (idx >= 0) {
                nextMuseums[idx].status = 'searching';
                nextMuseums[idx].currentStage = 'Starting query...';
                nextMuseums[idx].progressFraction = Math.max(nextMuseums[idx].progressFraction, 0.05);
            }
            break;
        }
        case 'keyword_searching': {
            nextPhase = 'searching';
            currentMuseumId = event.museum_id;
            currentKeyword = event.keyword || currentKeyword;
            const idx = findMuseumIndex(event.museum_id);
            if (idx >= 0) {
                const kwTotal = event.total_keywords || totalKeywords || 1;
                const kwRatio = Math.min(1, Math.max(0, (event.keyword_index || 0) / kwTotal));
                nextMuseums[idx].status = 'searching';
                nextMuseums[idx].currentStage = `Keyword "${event.keyword}" (${event.keyword_index}/${kwTotal})`;
                nextMuseums[idx].fetched_count = event.fetched_count ?? nextMuseums[idx].fetched_count;
                nextMuseums[idx].new_count = event.new_count ?? nextMuseums[idx].new_count;
                nextMuseums[idx].duplicates_skipped = event.duplicates_skipped ?? nextMuseums[idx].duplicates_skipped;
                // Reserve upper portion for record inspection when adapters enter detail phase
                nextMuseums[idx].progressFraction = Math.max(nextMuseums[idx].progressFraction, 0.08 + kwRatio * 0.55);
            }
            break;
        }
        case 'detail_fetching': {
            nextPhase = 'searching';
            currentMuseumId = event.museum_id;
            const idx = findMuseumIndex(event.museum_id);
            if (idx >= 0) {
                const detTotal = event.detail_total || 1;
                const detRatio = Math.min(1, Math.max(0, (event.detail_index || 0) / detTotal));
                nextMuseums[idx].status = 'searching';
                nextMuseums[idx].currentStage = `Inspecting record ${event.detail_index}/${detTotal}`;
                nextMuseums[idx].fetched_count = event.fetched_count ?? nextMuseums[idx].fetched_count;
                nextMuseums[idx].new_count = event.new_count ?? nextMuseums[idx].new_count;
                nextMuseums[idx].duplicates_skipped = event.duplicates_skipped ?? nextMuseums[idx].duplicates_skipped;
                nextMuseums[idx].progressFraction = Math.max(nextMuseums[idx].progressFraction, 0.65 + detRatio * 0.30);
            }
            break;
        }
        case 'candidate_found': {
            nextPhase = 'searching';
            currentMuseumId = event.museum_id;
            const idx = findMuseumIndex(event.museum_id);
            if (idx >= 0) {
                nextMuseums[idx].status = 'searching';
                nextMuseums[idx].fetched_count = event.fetched_count ?? nextMuseums[idx].fetched_count;
                nextMuseums[idx].new_count = event.new_count ?? nextMuseums[idx].new_count;
                nextMuseums[idx].duplicates_skipped = event.duplicates_skipped ?? nextMuseums[idx].duplicates_skipped;
                nextMuseums[idx].currentStage = `Found "${event.object_type}"`;
            }
            break;
        }
        case 'museum_completed': {
            const idx = findMuseumIndex(event.museum_id);
            if (idx >= 0) {
                nextMuseums[idx].status = event.error ? 'error' : 'done';
                nextMuseums[idx].fetched_count = event.fetched_count ?? nextMuseums[idx].fetched_count;
                nextMuseums[idx].new_count = event.new_count ?? nextMuseums[idx].new_count;
                nextMuseums[idx].duplicates_skipped = event.duplicates_skipped ?? nextMuseums[idx].duplicates_skipped;
                nextMuseums[idx].error = event.error || null;
                nextMuseums[idx].currentStage = event.error ? 'Error' : 'Complete';
                nextMuseums[idx].progressFraction = 1;
            }
            break;
        }
        case 'complete': {
            nextPhase = 'complete';
            nextMuseums = nextMuseums.map((m) => ({
                ...m,
                status: m.error ? 'error' : 'done',
                progressFraction: 1,
            }));
            break;
        }
        case 'error': {
            nextPhase = 'error';
            break;
        }
        default:
            break;
    }

    const totalChecked = nextMuseums.reduce((sum, m) => sum + (m.fetched_count || 0), 0);
    const totalNew = nextMuseums.reduce((sum, m) => sum + (m.new_count || 0), 0);
    const totalSkipped = nextMuseums.reduce((sum, m) => sum + (m.duplicates_skipped || 0), 0);
    const completedMuseums = nextMuseums.filter((m) => m.status === 'done' || m.status === 'error').length;
    const percent = event.type === 'search_started' && prev.percent === null
        ? 2
        : computeOverallPercent(nextMuseums, nextPhase);

    return {
        ...prev,
        phase: nextPhase,
        percent,
        totalMuseums: nextMuseums.length,
        completedMuseums,
        totalKeywords,
        currentMuseumId,
        currentKeyword,
        statusMessage,
        totalChecked,
        totalNew,
        totalSkipped,
        museums: nextMuseums,
        activityLog: appendActivityLog(prev.activityLog, event),
    };
}

/**
 * Stream discovery search progress via NDJSON, with graceful fallback to standard POST
 * if an older backend returns 404/405 for `/admin/discovery/search/stream`.
 */
export async function streamDiscoverySearch(payload, { onEvent, signal } = {}) {
    const baseUrl = (api.defaults?.baseURL || '/api').replace(/\/$/, '');
    const response = await fetch(`${baseUrl}/admin/discovery/search/stream`, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            Accept: 'application/x-ndjson',
        },
        body: JSON.stringify(payload),
        signal,
    });

    if (response.status === 404 || response.status === 405) {
        const fallbackResp = await api.post('/admin/discovery/search', payload, { signal });
        return fallbackResp.data;
    }

    if (response.status === 204) {
        return {
            candidates: [],
            total_new: 0,
            total_duplicates_skipped: 0,
            museum_reports: [],
        };
    }

    if (!response.ok) {
        let detail = `Discovery search failed (HTTP ${response.status}).`;
        try {
            const errJson = await response.json();
            if (errJson?.detail) {
                detail = typeof errJson.detail === 'string'
                    ? errJson.detail
                    : JSON.stringify(errJson.detail);
            }
        } catch {
            // Non-JSON error body; keep status-derived detail
        }
        throw new Error(detail);
    }

    const contentType = response.headers?.get?.('content-type') || '';
    if (contentType.includes('application/json')) {
        return await response.json();
    }

    if (!response.body || typeof response.body.getReader !== 'function') {
        const text = await response.text();
        let finalResult = null;
        for (const line of text.split('\n')) {
            const trimmed = line.trim();
            if (!trimmed) continue;
            const evt = JSON.parse(trimmed);
            onEvent?.(evt);
            if (evt.type === 'error') {
                throw new Error(evt.message || 'Discovery search failed.');
            }
            if (evt.type === 'complete') {
                finalResult = evt.result;
            }
        }
        if (!finalResult) {
            throw new Error('Discovery search stream ended unexpectedly before completion.');
        }
        return finalResult;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let finalResult = null;

    const processLine = (rawLine) => {
        const trimmed = rawLine.trim();
        if (!trimmed) return;
        const evt = JSON.parse(trimmed);
        onEvent?.(evt);
        if (evt.type === 'error') {
            throw new Error(evt.message || 'Discovery search failed.');
        }
        if (evt.type === 'complete') {
            finalResult = evt.result;
        }
    };

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                buffer += decoder.decode();
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            let newlineIdx;
            while ((newlineIdx = buffer.indexOf('\n')) !== -1) {
                const line = buffer.slice(0, newlineIdx);
                buffer = buffer.slice(newlineIdx + 1);
                processLine(line);
            }
        }

        if (buffer.trim()) {
            processLine(buffer);
        }
    } finally {
        reader.releaseLock?.();
    }

    if (!finalResult) {
        throw new Error('Discovery search stream ended unexpectedly before completion.');
    }

    return finalResult;
}
