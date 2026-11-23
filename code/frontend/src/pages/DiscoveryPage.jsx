import { useState, useEffect, useId, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
    createInitialProgressState,
    formatElapsedTime,
    reduceDiscoveryProgress,
    streamDiscoverySearch,
} from '../utils/discoveryStream';

const DEFAULT_KEYWORDS = [
    'craftsman',
    'glass',
    'potter',
    'workshop',
    'weaver',
    'blacksmith',
    'scribe',
    'sculptor',
    'ancient worker',
    'baker',
    'brewer',
    'farmer',
    'butcher',
    'carpenter',
    'apprentice',
    'glass maker',
    'vitrearii',
    'jeweler',
    'carpenters',
    'craft',
    'ergateri',
    'slave',
    'furnace',
    'kiln',
    'oven',
    'cutter',
    'tailor',
    'carver',
    'smith',
    'mold',
    'glassblower',
    'builder',
    'construction',
    'scene',
    'work',
    'saw',
    'tool',
    'bow',
    'drill',
    'midwife',
    'physician',
    'serf',
    'pesant',
    'hephaestus',
    'sow',
    'driver',
    'carvan',
    'smelt',
    'work scene',
    'Daedalus',
    'Icarus',
    'Vulcan',
    'cobbler',
    'maker',
    'painter',
    'shop',
    'merchant',
    'producer',
    'product',
    'press',
    'grain',
    'Pygmalion',
];

const DEFAULT_WORKER_PRESETS = [
    {
        id: 'all_ancient_workers',
        name: 'All Ancient Workers',
        description: 'High-precision worker roles, workshops, tomb models, and labor scenes across trades.',
        keywords: [
            'work scene',
            'potter',
            'weaver',
            'blacksmith',
            'scribe',
            'baker',
            'farmer',
            'carpenter',
            'sculptor',
            'shoemaker',
            'fisherman',
            'shepherd',
            'merchant',
            'slave',
            'physician',
            'glassblower',
            'ushabti',
            'hephaestus',
        ],
        recommended_date_start: -3000,
        recommended_date_end: 899,
    },
    {
        id: 'artisans_workshops',
        name: 'Artisans & Workshops',
        description: 'Potters, smiths, weavers, sculptors, shoemakers, glassblowers, and ancient workshop scenes.',
        keywords: [
            'potter',
            'blacksmith',
            'weaver',
            'sculptor',
            'carpenter',
            'shoemaker',
            'cobbler',
            'jeweler',
            'glassblower',
            'vitrearii',
            'fuller',
            'tanner',
            'stonemason',
            'carver',
            'woodworker',
            'metalworker',
            'workshop',
            'ergasterion',
            'hephaestus',
            'vulcan',
        ],
        recommended_date_start: -2500,
        recommended_date_end: 899,
    },
    {
        id: 'agriculture_food',
        name: 'Agriculture & Food Production',
        description: 'Farmers, harvesters, bakers, brewers, butchers, shepherds, and rural estate labor.',
        keywords: [
            'farmer',
            'baker',
            'brewer',
            'butcher',
            'shepherd',
            'fisherman',
            'harvester',
            'plowman',
            'winemaker',
            'miller',
            'herdsman',
            'peasant',
            'bakery',
            'brewery',
            'olive harvest',
            'vintage',
            'grain harvest',
        ],
        recommended_date_start: -3000,
        recommended_date_end: 899,
    },
    {
        id: 'scribes_trade_maritime',
        name: 'Scribes, Medicine & Trade',
        description: 'Scribes, physicians, midwives, merchants, sailors, shipwrights, and market scenes.',
        keywords: [
            'scribe',
            'merchant',
            'trader',
            'physician',
            'midwife',
            'doctor',
            'sailor',
            'rower',
            'shipwright',
            'boatbuilder',
            'banker',
            'shopkeeper',
            'caravan',
            'barber',
            'weighing',
        ],
        recommended_date_start: -3000,
        recommended_date_end: 899,
    },
    {
        id: 'enslaved_monumental',
        name: 'Enslaved Labor & Monumental Work',
        description: 'Enslaved workers, servants, porters, miners, brickmakers, builders, and funerary ushabti figures.',
        keywords: [
            'slave',
            'enslaved',
            'servant',
            'attendant',
            'porter',
            'bearer',
            'miner',
            'brickmaker',
            'builder',
            'laborer',
            'serf',
            'captive',
            'ushabti',
            'shabti',
            'apprentice',
        ],
        recommended_date_start: -3000,
        recommended_date_end: 899,
    },
];

const ERA_PRESETS = [
    { id: 'focus_0_899', label: '0–899 CE Focus', start: 0, end: 899 },
    { id: 'ancient_world', label: 'Ancient World (3000 BCE–500 CE)', start: -3000, end: 500 },
    { id: 'classical_antiquity', label: 'Classical Antiquity (800 BCE–500 CE)', start: -800, end: 500 },
    { id: 'ancient_early_medieval', label: 'Ancient–Early Medieval (3000 BCE–899 CE)', start: -3000, end: 899 },
];

const hasNumericValue = (val) => val !== null && val !== undefined && val !== '';
const getCandidateKey = (cand) => `${cand.museum_id}:${cand.source_record_id}`;

const getWorkerBadgeMeta = (cand) => {
    const score = cand.worker_relevance_score ?? 0;
    const confidence = cand.worker_confidence || 'none';
    if (score === 0 && confidence === 'none') return null;
    if (confidence === 'high') {
        return {
            label: `★ High Worker Match (${score}%)`,
            className: 'bg-emerald-100 text-emerald-900 border-emerald-300',
        };
    }
    if (confidence === 'medium') {
        return {
            label: `● Worker Match (${score}%)`,
            className: 'bg-amber-100 text-amber-900 border-amber-300',
        };
    }
    return {
        label: `○ Low Match (${score}%)`,
        className: 'bg-slate-100 text-slate-700 border-slate-300',
    };
};

const formatDimensionsSummary = (cand) => {
    if (cand.dimensions_display) return cand.dimensions_display;
    const dims = [cand.height, cand.width, cand.depth].filter((v) => v !== null && v !== undefined);
    if (dims.length === 0) return null;
    return `${dims.join(' × ')} ${cand.unit || 'cm'}`;
};

const DiscoveryPage = () => {
    const navigate = useNavigate();
    const { isAdmin } = useAuth();
    const formHeadingId = useId();
    const progressBarId = useId();
    const workerModeId = useId();
    const broadModeId = useId();
    const strictFilterId = useId();
    const abortControllerRef = useRef(null);

    const [museums, setMuseums] = useState([]);
    const [loadingMuseums, setLoadingMuseums] = useState(true);
    const [selectedMuseums, setSelectedMuseums] = useState(['met', 'cma', 'aic', 'vam', 'bm']);
    const [keywords, setKeywords] = useState(DEFAULT_KEYWORDS);
    const [presets, setPresets] = useState(DEFAULT_WORKER_PRESETS);
    const [activePresetId, setActivePresetId] = useState(null);
    const [searchMode, setSearchMode] = useState('worker_depictions');
    const [strictWorkerFilter, setStrictWorkerFilter] = useState(false);
    const [confidenceFilter, setConfidenceFilter] = useState('all');
    const [keywordInput, setKeywordInput] = useState('');
    const [savingKeyword, setSavingKeyword] = useState(false);
    const [keywordStatus, setKeywordStatus] = useState('');
    const [dateStart, setDateStart] = useState(0);
    const [dateEnd, setDateEnd] = useState(899);
    const [limitPerMuseum, setLimitPerMuseum] = useState(10);

    const [validationErrors, setValidationErrors] = useState({});
    const [apiError, setApiError] = useState('');
    const [searching, setSearching] = useState(false);
    const [searchProgress, setSearchProgress] = useState(null);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const [searchAnnouncement, setSearchAnnouncement] = useState('');
    const [importing, setImporting] = useState(false);

    const [searchResult, setSearchResult] = useState(null);
    const [selectedKeys, setSelectedKeys] = useState([]);
    const [importResult, setImportResult] = useState(null);
    const [rejectingKeys, setRejectingKeys] = useState({});
    const [rejectedBanner, setRejectedBanner] = useState(null);
    const [undoingReject, setUndoingReject] = useState(false);

    useEffect(() => () => {
        abortControllerRef.current?.abort();
    }, []);

    useEffect(() => {
        if (!searching) return undefined;
        setElapsedSeconds(0);
        const timerId = setInterval(() => {
            setElapsedSeconds((prev) => prev + 1);
        }, 1000);
        return () => clearInterval(timerId);
    }, [searching]);

    useEffect(() => {
        if (!isAdmin) {
            navigate('/login');
            return;
        }

        const loadMuseums = async () => {
            try {
                setLoadingMuseums(true);
                const response = await api.get('/admin/discovery/museums');
                const list = Array.isArray(response.data) ? response.data : [];
                setMuseums(list);
                if (list.length > 0) {
                    setSelectedMuseums(list.map((m) => m.id));
                    if (Array.isArray(list[0].default_keywords) && list[0].default_keywords.length > 0) {
                        setKeywords(list[0].default_keywords);
                    }
                    if (list[0].default_date_start !== undefined && list[0].default_date_start !== null) {
                        setDateStart(list[0].default_date_start);
                    }
                    if (list[0].default_date_end !== undefined && list[0].default_date_end !== null) {
                        setDateEnd(list[0].default_date_end);
                    }
                    if (list[0].default_limit) {
                        setLimitPerMuseum(list[0].default_limit);
                    }
                }
            } catch (err) {
                setApiError(err.response?.data?.detail || 'Failed to load predefined museums.');
            } finally {
                setLoadingMuseums(false);
            }

            try {
                const presetResponse = await api.get('/admin/discovery/presets');
                if (Array.isArray(presetResponse?.data) && presetResponse.data.length > 0) {
                    setPresets(presetResponse.data);
                }
            } catch {
                // Non-fatal: built-in worker presets remain available when offline or unmocked.
            }
        };

        loadMuseums();
    }, [isAdmin, navigate]);

    const validateForm = (nextMuseums = selectedMuseums, nextKeywords = keywords, nextStart = dateStart, nextEnd = dateEnd) => {
        const errs = {};
        if (!nextMuseums || nextMuseums.length === 0) {
            errs.museums = 'Select at least one predefined museum.';
        }
        if (!nextKeywords || nextKeywords.length === 0) {
            errs.keywords = 'Add at least one search keyword.';
        }
        if (!hasNumericValue(nextStart) || !hasNumericValue(nextEnd) || Number.isNaN(Number(nextStart)) || Number.isNaN(Number(nextEnd))) {
            errs.dates = 'Enter valid integer start and end years.';
        } else if (Number(nextStart) > Number(nextEnd)) {
            errs.dates = 'Start Year must be less than or equal to End Year.';
        }
        return errs;
    };

    const syncSavedKeywords = (nextList) => {
        setKeywords(nextList);
        setMuseums((prev) => prev.map((m) => ({ ...m, default_keywords: nextList })));
    };

    const handleToggleMuseum = (museumId) => {
        const next = selectedMuseums.includes(museumId)
            ? selectedMuseums.filter((id) => id !== museumId)
            : [...selectedMuseums, museumId];
        setSelectedMuseums(next);
        if (next.length > 0 && validationErrors.museums) {
            setValidationErrors((prev) => ({ ...prev, museums: undefined }));
        }
    };

    const handleAddKeyword = async () => {
        const trimmed = keywordInput.replace(/\s+/g, ' ').trim();
        if (!trimmed) return keywords;

        if (keywords.some((kw) => kw.toLowerCase() === trimmed.toLowerCase())) {
            setKeywordInput('');
            setKeywordStatus(`Keyword "${trimmed}" is already saved.`);
            return keywords;
        }

        setSavingKeyword(true);
        setApiError('');
        setKeywordStatus('');

        try {
            const response = await api.post('/admin/discovery/keywords', { keyword: trimmed });
            const nextKeywords = Array.isArray(response?.data?.keywords)
                ? response.data.keywords
                : [...keywords, trimmed];
            syncSavedKeywords(nextKeywords);
            setActivePresetId(null);
            setKeywordInput('');
            setKeywordStatus(`Saved "${trimmed}" for future searches.`);
            if (validationErrors.keywords) {
                setValidationErrors((prev) => ({ ...prev, keywords: undefined }));
            }
            return nextKeywords;
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Failed to save keyword.');
            return null;
        } finally {
            setSavingKeyword(false);
        }
    };

    const handleKeywordKeyDown = (e) => {
        if (e.nativeEvent?.isComposing || e.isComposing || e.keyCode === 229) return;
        if (e.key === 'Enter') {
            e.preventDefault();
            handleAddKeyword();
        }
    };

    const handleRemoveKeyword = async (kwToRemove) => {
        setApiError('');
        setKeywordStatus('');
        try {
            const response = await api.delete('/admin/discovery/keywords', {
                params: { keyword: kwToRemove },
            });
            if (response?.status === 204 || !response || response.status < 300) {
                const nextKeywords = keywords.filter((kw) => kw !== kwToRemove);
                syncSavedKeywords(nextKeywords);
                setActivePresetId(null);
                setKeywordStatus(`Removed "${kwToRemove}" from saved keywords.`);
            }
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Failed to remove keyword.');
        }
    };

    const handleApplyPreset = (preset) => {
        setActivePresetId(preset.id);
        setKeywords([...(preset.keywords || [])]);
        setKeywordStatus(`Loaded "${preset.name}" preset (${preset.keywords?.length || 0} keywords) for this search (saved list unchanged).`);
        if (validationErrors.keywords) {
            setValidationErrors((prev) => ({ ...prev, keywords: undefined }));
        }
    };

    const handleUseAllSavedKeywords = () => {
        const saved = museums[0]?.default_keywords?.length ? museums[0].default_keywords : DEFAULT_KEYWORDS;
        setActivePresetId(null);
        setKeywords([...saved]);
        setKeywordStatus('Using all saved discovery keywords.');
        if (validationErrors.keywords) {
            setValidationErrors((prev) => ({ ...prev, keywords: undefined }));
        }
    };

    const handleResetDefaults = () => {
        const defaultKeywords = museums[0]?.default_keywords?.length ? museums[0].default_keywords : DEFAULT_KEYWORDS;
        const defaultStart = museums[0]?.default_date_start ?? 0;
        const defaultEnd = museums[0]?.default_date_end ?? 899;
        const defaultLimit = museums[0]?.default_limit ?? 10;

        setSelectedMuseums(museums.length > 0 ? museums.map((m) => m.id) : ['met', 'cma', 'aic', 'vam', 'bm']);
        setKeywords([...defaultKeywords]);
        setActivePresetId(null);
        setSearchMode('worker_depictions');
        setStrictWorkerFilter(false);
        setConfidenceFilter('all');
        setKeywordInput('');
        setKeywordStatus('');
        setDateStart(defaultStart);
        setDateEnd(defaultEnd);
        setLimitPerMuseum(defaultLimit);
        setValidationErrors({});
        setApiError('');
    };

    const handleDateBlur = () => {
        const errs = validateForm(selectedMuseums, keywords, dateStart, dateEnd);
        setValidationErrors((prev) => ({ ...prev, dates: errs.dates }));
    };

    const handleCancelSearch = () => {
        abortControllerRef.current?.abort();
    };

    const handleDiscover = async (e) => {
        e.preventDefault();
        setApiError('');
        setImportResult(null);
        setSearchAnnouncement('');

        let effectiveKeywords = keywords;
        if (keywordInput.trim()) {
            const added = await handleAddKeyword();
            if (added === null) return;
            effectiveKeywords = added;
        }

        const errs = validateForm(selectedMuseums, effectiveKeywords, dateStart, dateEnd);
        if (Object.keys(errs).length > 0) {
            setValidationErrors(errs);
            return;
        }
        setValidationErrors({});

        abortControllerRef.current?.abort();
        const controller = new AbortController();
        abortControllerRef.current = controller;

        setSearchResult(null);
        setSelectedKeys([]);
        setConfidenceFilter('all');
        setRejectedBanner(null);
        setRejectingKeys({});
        setSearching(true);
        setSearchProgress(createInitialProgressState(selectedMuseums, museums, effectiveKeywords.length));

        try {
            const data = await streamDiscoverySearch(
                {
                    museums: selectedMuseums,
                    keywords: effectiveKeywords,
                    date_start: Number(dateStart),
                    date_end: Number(dateEnd),
                    limit_per_museum: Number(limitPerMuseum) || 10,
                    search_mode: searchMode,
                    min_worker_score: strictWorkerFilter ? 65 : 35,
                    save_keywords: activePresetId === null,
                },
                {
                    signal: controller.signal,
                    onEvent: (evt) => {
                        setSearchProgress((prev) => reduceDiscoveryProgress(prev, evt));
                    },
                }
            );
            if (controller.signal.aborted) return;
            setSearchResult(data);
            setSelectedKeys((data.candidates || []).map(getCandidateKey));
            const filteredCount = data.total_filtered_non_worker ?? 0;
            const filteredSuffix = filteredCount > 0 ? `, ${filteredCount} non-worker item(s) filtered` : '';
            setSearchAnnouncement(
                `Discovery complete: ${data.total_new ?? 0} new artifact(s) found, ${data.total_duplicates_skipped ?? 0} duplicate(s) skipped${filteredSuffix}.`
            );
        } catch (err) {
            if (err?.name === 'AbortError' || err?.code === 'ERR_CANCELED' || controller.signal.aborted) {
                setSearchAnnouncement('Discovery search cancelled.');
            } else {
                setApiError(err.response?.data?.detail || err.message || 'Discovery search failed.');
            }
        } finally {
            if (abortControllerRef.current === controller) {
                abortControllerRef.current = null;
            }
            setSearching(false);
            setSearchProgress(null);
        }
    };

    const handleToggleCandidate = (key) => {
        setSelectedKeys((prev) =>
            prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
        );
    };

    const handleImportSelected = async () => {
        if (!searchResult?.candidates) return;
        const selectedCandidates = searchResult.candidates.filter((c) =>
            selectedKeys.includes(getCandidateKey(c))
        );
        if (selectedCandidates.length === 0) return;

        setImporting(true);
        setApiError('');

        try {
            const response = await api.post('/admin/discovery/import', {
                candidates: selectedCandidates,
            });
            const resData = response.data;
            setImportResult(resData);

            const skippedSet = new Set((resData.skipped_inventory_numbers || []).map((s) => s.toLowerCase()));
            const importedKeys = new Set(selectedCandidates.map(getCandidateKey));

            setSearchResult((prev) => {
                if (!prev) return prev;
                const remaining = (prev.candidates || []).filter((c) => {
                    const key = getCandidateKey(c);
                    const invMatch = c.inventory_number && skippedSet.has(c.inventory_number.toLowerCase());
                    return !importedKeys.has(key) && !invMatch;
                });
                return { ...prev, candidates: remaining, total_new: remaining.length };
            });
            setSelectedKeys((prev) => prev.filter((k) => !importedKeys.has(k)));
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Import failed.');
        } finally {
            setImporting(false);
        }
    };

    const handleRejectCandidate = async (cand) => {
        const key = getCandidateKey(cand);
        if (rejectingKeys[key] || importing || undoingReject) return;

        setRejectingKeys((prev) => ({ ...prev, [key]: true }));
        setApiError('');
        setRejectedBanner(null);

        try {
            const response = await api.post('/admin/discovery/reject', {
                candidates: [
                    {
                        museum_id: cand.museum_id,
                        source_record_id: String(cand.source_record_id ?? ''),
                        inventory_number: cand.inventory_number || null,
                        external_url: cand.external_url || null,
                        object_type: cand.object_type || null,
                        present_location: cand.present_location || null,
                        date_display: cand.date_display || null,
                    },
                ],
            });
            const savedItem = response?.data?.rejected_items?.[0] || null;
            setSearchResult((prev) => {
                if (!prev) return prev;
                const remaining = (prev.candidates || []).filter((c) => getCandidateKey(c) !== key);
                return { ...prev, candidates: remaining, total_new: remaining.length };
            });
            setSelectedKeys((prev) => prev.filter((k) => k !== key));
            setRejectedBanner({
                id: savedItem?.id ?? null,
                candidate: cand,
                title: cand.object_type || 'artifact',
            });
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Failed to reject artifact.');
        } finally {
            setRejectingKeys((prev) => {
                const next = { ...prev };
                delete next[key];
                return next;
            });
        }
    };

    const handleUndoReject = async () => {
        if (!rejectedBanner?.id || undoingReject) return;

        setUndoingReject(true);
        setApiError('');
        try {
            const response = await api.delete(`/admin/discovery/rejected/${rejectedBanner.id}`);
            if (response?.status === 204 || !response || response.status < 300) {
                const restored = rejectedBanner.candidate;
                const key = getCandidateKey(restored);
                setSearchResult((prev) => {
                    if (!prev) return prev;
                    const existing = prev.candidates || [];
                    if (existing.some((c) => getCandidateKey(c) === key)) {
                        return prev;
                    }
                    const nextCandidates = [restored, ...existing];
                    return { ...prev, candidates: nextCandidates, total_new: nextCandidates.length };
                });
                setSelectedKeys((prev) => (prev.includes(key) ? prev : [key, ...prev]));
                setRejectedBanner(null);
            }
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Failed to undo rejection.');
        } finally {
            setUndoingReject(false);
        }
    };

    const candidates = searchResult?.candidates || [];
    const hasScoredWorkers = candidates.some(
        (c) => (c.worker_relevance_score ?? 0) > 0 || (c.worker_confidence && c.worker_confidence !== 'none')
    );
    const highConfidenceCandidates = candidates.filter((c) => c.worker_confidence === 'high');
    const displayedCandidates = confidenceFilter === 'high' ? highConfidenceCandidates : candidates;
    const selectedCount = candidates.filter((c) => selectedKeys.includes(getCandidateKey(c))).length;

    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Discover Artifacts from Predefined Museums</h1>
                        <p className="text-sm text-gray-600 mt-1">
                            Search curated open-access collections using editable keywords and date ranges. Existing database pieces and previously rejected items are skipped automatically, and new discoveries stage in the Review Queue.
                        </p>
                    </div>
                    <Link
                        to="/admin/review"
                        className="px-4 py-2 text-sm font-medium text-purple-700 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100"
                    >
                        Review Queue
                    </Link>
                </div>

                {apiError && (
                    <div role="alert" className="p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800">
                        {apiError}
                    </div>
                )}

                {importResult && (
                    <div role="status" aria-live="polite" className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-sm text-emerald-900 space-y-2">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-semibold">
                                Imported {importResult.imported_count} new artifact(s) to Review Queue
                                {importResult.duplicates_skipped > 0 && ` · ${importResult.duplicates_skipped} duplicate(s) skipped`}
                                {importResult.failed_count > 0 && ` · ${importResult.failed_count} failed`}
                            </p>
                            <Link
                                to="/admin/review"
                                className="px-3 py-1 text-xs font-semibold text-white bg-emerald-700 rounded hover:bg-emerald-800"
                            >
                                Open Review Queue
                            </Link>
                        </div>
                        {importResult.imported_objects?.length > 0 && (
                            <ul className="list-disc pl-5 space-y-1 text-xs">
                                {importResult.imported_objects.map((item) => (
                                    <li key={item.id}>
                                        <Link to={`/objects/${item.id}`} className="font-medium text-emerald-800 underline hover:text-emerald-950">
                                            {item.object_type}
                                        </Link>
                                        {item.inventory_number && ` (${item.inventory_number})`}
                                        {item.present_location && ` — ${item.present_location}`}
                                    </li>
                                ))}
                            </ul>
                        )}
                        {importResult.errors?.length > 0 && (
                            <p className="text-xs text-red-700">{importResult.errors.join(' | ')}</p>
                        )}
                    </div>
                )}

                <search>
                    <form
                        onSubmit={handleDiscover}
                        aria-labelledby={formHeadingId}
                        noValidate
                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6"
                    >
                        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-3">
                            <h2 id={formHeadingId} className="text-lg font-semibold text-gray-800">
                                Discovery Parameters
                            </h2>
                            <button
                                type="button"
                                onClick={handleResetDefaults}
                                className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
                            >
                                Reset Defaults
                            </button>
                        </div>

                        {/* Discovery Focus Mode */}
                        <fieldset className="space-y-3">
                            <legend className="text-sm font-semibold text-gray-800">
                                Discovery Focus Mode
                            </legend>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div
                                    className={`p-3 rounded-lg border transition-colors ${
                                        searchMode === 'worker_depictions'
                                            ? 'border-blue-400 bg-blue-50/40'
                                            : 'border-gray-200 bg-white'
                                    }`}
                                >
                                    <div className="flex items-start gap-2.5">
                                        <input
                                            id={workerModeId}
                                            name="search_mode"
                                            type="radio"
                                            value="worker_depictions"
                                            checked={searchMode === 'worker_depictions'}
                                            onChange={() => setSearchMode('worker_depictions')}
                                            className="mt-1 border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <label htmlFor={workerModeId} className="cursor-pointer">
                                            <span className="block text-sm font-semibold text-gray-900">
                                                Ancient Workers Depictions (Recommended)
                                            </span>
                                            <span className="block text-xs text-gray-500 mt-0.5">
                                                Prioritizes depicted worker roles, workshop scenes, AAT subject tags, and figurative scenes while filtering out plain vessels and tools.
                                            </span>
                                        </label>
                                    </div>
                                </div>
                                <div
                                    className={`p-3 rounded-lg border transition-colors ${
                                        searchMode === 'broad'
                                            ? 'border-blue-400 bg-blue-50/40'
                                            : 'border-gray-200 bg-white'
                                    }`}
                                >
                                    <div className="flex items-start gap-2.5">
                                        <input
                                            id={broadModeId}
                                            name="search_mode"
                                            type="radio"
                                            value="broad"
                                            checked={searchMode === 'broad'}
                                            onChange={() => setSearchMode('broad')}
                                            className="mt-1 border-gray-300 text-blue-600 focus:ring-blue-500"
                                        />
                                        <label htmlFor={broadModeId} className="cursor-pointer">
                                            <span className="block text-sm font-semibold text-gray-900">
                                                Broad Keyword Search
                                            </span>
                                            <span className="block text-xs text-gray-500 mt-0.5">
                                                Returns all matching museum hits for every keyword without filtering out non-depiction artifacts.
                                            </span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                            {searchMode === 'worker_depictions' && (
                                <div className="flex items-center gap-2 pt-1">
                                    <input
                                        id={strictFilterId}
                                        name="strict_worker_filter"
                                        type="checkbox"
                                        checked={strictWorkerFilter}
                                        onChange={(e) => setStrictWorkerFilter(e.target.checked)}
                                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor={strictFilterId} className="text-xs font-medium text-gray-700 cursor-pointer">
                                        Strict: High-confidence worker depictions only (65+)
                                    </label>
                                </div>
                            )}
                        </fieldset>

                        {/* Predefined Museums */}
                        <fieldset className="space-y-3" aria-describedby={validationErrors.museums ? 'museums-error' : undefined}>
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <legend className="text-sm font-semibold text-gray-800">
                                    Predefined Museums
                                </legend>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setSelectedMuseums(museums.map((m) => m.id));
                                            setValidationErrors((prev) => ({ ...prev, museums: undefined }));
                                        }}
                                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                                    >
                                        Select All
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setSelectedMuseums([])}
                                        className="text-xs text-gray-500 hover:text-gray-700 font-medium"
                                    >
                                        Deselect All
                                    </button>
                                </div>
                            </div>

                            {loadingMuseums ? (
                                <p className="text-sm text-gray-500">Loading predefined museums...</p>
                            ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {museums.map((museum) => {
                                        const checkboxId = `museum-${museum.id}`;
                                        const checked = selectedMuseums.includes(museum.id);
                                        return (
                                            <div
                                                key={museum.id}
                                                className={`p-3 rounded-lg border transition-colors ${
                                                    checked ? 'border-blue-400 bg-blue-50/40' : 'border-gray-200 bg-white'
                                                }`}
                                            >
                                                <div className="flex items-start gap-2.5">
                                                    <input
                                                        id={checkboxId}
                                                        name="museums"
                                                        type="checkbox"
                                                        value={museum.id}
                                                        checked={checked}
                                                        onChange={() => handleToggleMuseum(museum.id)}
                                                        className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                    />
                                                    <label htmlFor={checkboxId} className="cursor-pointer">
                                                        <span className="block text-sm font-semibold text-gray-900">
                                                            {museum.name}
                                                        </span>
                                                        <span className="block text-xs text-gray-500 mt-0.5">
                                                            {museum.description}
                                                        </span>
                                                    </label>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {validationErrors.museums && (
                                <p id="museums-error" className="text-xs text-red-600" role="alert">
                                    {validationErrors.museums}
                                </p>
                            )}
                        </fieldset>

                        {/* Editable Keywords */}
                        <fieldset
                            className="space-y-3"
                            aria-describedby={
                                [
                                    'keyword-help',
                                    keywordStatus ? 'keyword-status' : null,
                                    validationErrors.keywords ? 'keywords-error' : null,
                                ]
                                    .filter(Boolean)
                                    .join(' ')
                            }
                        >
                            <legend className="text-sm font-semibold text-gray-800">
                                Search Keywords ({keywords.length})
                            </legend>

                            <div className="space-y-1.5">
                                <p className="text-xs font-medium text-gray-700">Curated Ancient Worker Presets</p>
                                <div className="flex flex-wrap gap-1.5">
                                    {presets.map((preset) => {
                                        const isActive = activePresetId === preset.id;
                                        return (
                                            <button
                                                key={preset.id}
                                                type="button"
                                                aria-pressed={isActive}
                                                title={preset.description}
                                                onClick={() => handleApplyPreset(preset)}
                                                className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                                                    isActive
                                                        ? 'bg-indigo-600 text-white border-indigo-600'
                                                        : 'bg-indigo-50 text-indigo-800 border-indigo-200 hover:bg-indigo-100'
                                                }`}
                                            >
                                                {preset.name}
                                            </button>
                                        );
                                    })}
                                    <button
                                        type="button"
                                        aria-pressed={activePresetId === null}
                                        onClick={handleUseAllSavedKeywords}
                                        className={`px-2.5 py-1 rounded-md text-xs font-medium border transition ${
                                            activePresetId === null
                                                ? 'bg-slate-700 text-white border-slate-700'
                                                : 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200'
                                        }`}
                                    >
                                        All Saved Keywords
                                    </button>
                                </div>
                            </div>

                            <div className="flex flex-col sm:flex-row gap-2 sm:items-end">
                                <div className="flex-1">
                                    <label htmlFor="keyword-input" className="block text-xs font-medium text-gray-700 mb-1">
                                        Add keyword
                                    </label>
                                    <input
                                        id="keyword-input"
                                        name="keyword"
                                        type="text"
                                        maxLength={80}
                                        autoCorrect="off"
                                        autoCapitalize="none"
                                        spellCheck={false}
                                        enterKeyHint="done"
                                        value={keywordInput}
                                        aria-describedby="keyword-help"
                                        onChange={(e) => setKeywordInput(e.target.value)}
                                        onKeyDown={handleKeywordKeyDown}
                                        placeholder="e.g. gold-glass, amphora, potter"
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <button
                                    type="button"
                                    disabled={savingKeyword}
                                    onClick={handleAddKeyword}
                                    className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-60"
                                >
                                    {savingKeyword ? 'Saving...' : 'Add Keyword'}
                                </button>
                            </div>

                            <p id="keyword-help" className="text-xs text-gray-500">
                                Added keywords are saved automatically for future searches (up to 80 characters).
                            </p>

                            {keywordStatus && (
                                <p id="keyword-status" role="status" aria-live="polite" className="text-xs text-emerald-700">
                                    {keywordStatus}
                                </p>
                            )}

                            <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 rounded-md border border-gray-100 bg-gray-50/50">
                                {keywords.map((kw) => (
                                    <span
                                        key={kw}
                                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-800 border border-slate-200"
                                    >
                                        <span>{kw}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveKeyword(kw)}
                                            aria-label={`Remove keyword ${kw}`}
                                            className="text-slate-500 hover:text-red-600 font-bold"
                                        >
                                            &times;
                                        </button>
                                    </span>
                                ))}
                            </div>

                            {validationErrors.keywords && (
                                <p id="keywords-error" className="text-xs text-red-600" role="alert">
                                    {validationErrors.keywords}
                                </p>
                            )}
                        </fieldset>

                        {/* Date Range & Limit */}
                        <fieldset className="space-y-3" aria-describedby={validationErrors.dates ? 'dates-error' : undefined}>
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <legend className="text-sm font-semibold text-gray-800">
                                    Date Range &amp; Fetch Limit
                                </legend>
                                <div className="flex flex-wrap gap-2">
                                    {ERA_PRESETS.map((era) => {
                                        const isActiveEra = Number(dateStart) === era.start && Number(dateEnd) === era.end;
                                        return (
                                            <button
                                                key={era.id}
                                                type="button"
                                                onClick={() => {
                                                    setDateStart(era.start);
                                                    setDateEnd(era.end);
                                                    setValidationErrors((prev) => ({ ...prev, dates: undefined }));
                                                }}
                                                className={`text-xs font-medium px-2 py-0.5 rounded border ${
                                                    isActiveEra
                                                        ? 'bg-blue-50 text-blue-700 border-blue-200'
                                                        : 'text-blue-600 hover:text-blue-800 border-transparent hover:bg-blue-50/50'
                                                }`}
                                            >
                                                {era.label}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <div>
                                    <label htmlFor="discovery-date-start" className="block text-xs font-medium text-gray-700 mb-1">
                                        Start Year (negative = BCE)
                                    </label>
                                    <input
                                        id="discovery-date-start"
                                        name="date_start"
                                        type="number"
                                        value={dateStart ?? ''}
                                        aria-invalid={Boolean(validationErrors.dates)}
                                        onBlur={handleDateBlur}
                                        onChange={(e) => {
                                            const raw = e.target.value;
                                            const parsed = raw !== '' ? parseInt(raw, 10) : '';
                                            setDateStart(Number.isNaN(parsed) ? '' : parsed);
                                            if (validationErrors.dates) {
                                                setValidationErrors((prev) => ({ ...prev, dates: undefined }));
                                            }
                                        }}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="discovery-date-end" className="block text-xs font-medium text-gray-700 mb-1">
                                        End Year (negative = BCE)
                                    </label>
                                    <input
                                        id="discovery-date-end"
                                        name="date_end"
                                        type="number"
                                        value={dateEnd ?? ''}
                                        aria-invalid={Boolean(validationErrors.dates)}
                                        onBlur={handleDateBlur}
                                        onChange={(e) => {
                                            const raw = e.target.value;
                                            const parsed = raw !== '' ? parseInt(raw, 10) : '';
                                            setDateEnd(Number.isNaN(parsed) ? '' : parsed);
                                            if (validationErrors.dates) {
                                                setValidationErrors((prev) => ({ ...prev, dates: undefined }));
                                            }
                                        }}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>

                                <div>
                                    <label htmlFor="discovery-limit" className="block text-xs font-medium text-gray-700 mb-1">
                                        Max New Pieces per Museum (1–25)
                                    </label>
                                    <input
                                        id="discovery-limit"
                                        name="limit_per_museum"
                                        type="number"
                                        min="1"
                                        max="25"
                                        value={limitPerMuseum ?? ''}
                                        onChange={(e) => {
                                            const raw = e.target.value;
                                            const parsed = raw !== '' ? parseInt(raw, 10) : '';
                                            setLimitPerMuseum(Number.isNaN(parsed) ? '' : parsed);
                                        }}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                            </div>

                            {validationErrors.dates && (
                                <p id="dates-error" className="text-xs text-red-600" role="alert">
                                    {validationErrors.dates}
                                </p>
                            )}
                        </fieldset>

                        <div className="flex justify-end pt-2 border-t border-gray-100">
                            <button
                                type="submit"
                                disabled={searching}
                                className="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition shadow-sm"
                            >
                                {searching && (
                                    <span aria-hidden="true" className="w-2 h-2 rounded-full bg-white motion-safe:animate-pulse" />
                                )}
                                {searching ? 'Searching Museums...' : 'Discover New Artifacts'}
                            </button>
                        </div>
                    </form>
                </search>

                {searchAnnouncement && !searching && !searchResult && (
                    <div role="status" aria-live="polite" className="p-4 rounded-lg bg-slate-100 border border-slate-200 text-sm text-slate-800">
                        {searchAnnouncement}
                    </div>
                )}

                {/* Live Discovery Progress Panel */}
                {searching && searchProgress && (
                    <section
                        aria-labelledby={`${progressBarId}-heading`}
                        className="bg-white rounded-lg shadow-sm border border-blue-200 p-5 space-y-4"
                    >
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 pb-3">
                            <div className="flex items-center gap-3">
                                <progress aria-label="Museum discovery in progress" className="loading-spinner loading-spinner--sm" />
                                <div>
                                    <h2 id={`${progressBarId}-heading`} className="text-base font-semibold text-gray-900">
                                        Live Discovery Progress
                                    </h2>
                                    <p className="text-xs text-gray-600">
                                        Scanning {searchProgress.totalMuseums} museum(s) across {searchProgress.totalKeywords} keyword(s)
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-slate-100 text-slate-700 border border-slate-200">
                                    {formatElapsedTime(elapsedSeconds)}
                                </span>
                                <button
                                    type="button"
                                    onClick={handleCancelSearch}
                                    className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded-md hover:bg-red-100"
                                >
                                    Cancel Search
                                </button>
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                                <label htmlFor={progressBarId} className="font-medium text-gray-700">
                                    {searchProgress.statusMessage}
                                </label>
                                <span className="font-semibold text-blue-700 tabular-nums">
                                    {searchProgress.percent !== null ? `${searchProgress.percent}%` : 'Connecting...'}
                                </span>
                            </div>
                            <progress
                                id={progressBarId}
                                max={100}
                                {...(searchProgress.percent !== null ? { value: searchProgress.percent } : {})}
                                className="discovery-progress w-full"
                            />
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="p-2.5 rounded-md bg-slate-50 border border-slate-200">
                                <p className="text-[11px] uppercase tracking-wider text-gray-500">Museums</p>
                                <p className="text-base font-semibold text-gray-900 tabular-nums">
                                    {searchProgress.completedMuseums}/{searchProgress.totalMuseums}
                                </p>
                            </div>
                            <div className="p-2.5 rounded-md bg-slate-50 border border-slate-200">
                                <p className="text-[11px] uppercase tracking-wider text-gray-500">Checked</p>
                                <p className="text-base font-semibold text-gray-900 tabular-nums">
                                    {searchProgress.totalChecked}
                                </p>
                            </div>
                            <div className="p-2.5 rounded-md bg-emerald-50 border border-emerald-200">
                                <p className="text-[11px] uppercase tracking-wider text-emerald-700">New Found</p>
                                <p className="text-base font-semibold text-emerald-900 tabular-nums">
                                    {searchProgress.totalNew}
                                </p>
                            </div>
                            <div className="p-2.5 rounded-md bg-amber-50 border border-amber-200">
                                <p className="text-[11px] uppercase tracking-wider text-amber-700">Duplicates Skipped</p>
                                <p className="text-base font-semibold text-amber-900 tabular-nums">
                                    {searchProgress.totalSkipped}
                                    {searchProgress.totalRejectedSkipped > 0 && (
                                        <span className="ml-1 text-xs font-normal text-amber-700">
                                            ({searchProgress.totalRejectedSkipped} rejected)
                                        </span>
                                    )}
                                    {searchProgress.totalFilteredNonWorker > 0 && (
                                        <span className="ml-1 text-xs font-normal text-amber-800">
                                            · {searchProgress.totalFilteredNonWorker} non-worker filtered
                                        </span>
                                    )}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                            {searchProgress.museums.map((m) => {
                                const statusStyles = {
                                    queued: 'bg-gray-100 text-gray-700 border-gray-200',
                                    searching: 'bg-blue-100 text-blue-800 border-blue-200',
                                    done: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                                    error: 'bg-red-100 text-red-800 border-red-200',
                                };
                                const statusLabels = {
                                    queued: 'Queued',
                                    searching: 'Searching',
                                    done: 'Complete',
                                    error: 'Error',
                                };
                                return (
                                    <div
                                        key={m.museum_id}
                                        className={`p-3 rounded-md border text-xs space-y-1 ${
                                            m.status === 'searching'
                                                ? 'border-blue-300 bg-blue-50/40'
                                                : 'border-gray-200 bg-gray-50/60'
                                        }`}
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="font-semibold text-gray-900 truncate">{m.museum_name}</span>
                                            <span className={`px-2 py-0.5 rounded-full text-[11px] font-medium border ${statusStyles[m.status] || statusStyles.queued}`}>
                                                {statusLabels[m.status] || 'Queued'}
                                            </span>
                                        </div>
                                        <p className="text-gray-600 truncate">
                                            {m.currentStage} · {m.new_count} new · {m.duplicates_skipped} skipped
                                            {m.filtered_non_worker > 0 ? ` · ${m.filtered_non_worker} filtered` : ''} ({m.fetched_count} checked)
                                        </p>
                                    </div>
                                );
                            })}
                        </div>

                        {searchProgress.activityLog.length > 0 && (
                            <div className="border-t border-gray-100 pt-3 space-y-1.5">
                                <p className="text-xs font-semibold text-gray-700">Live Activity Feed</p>
                                <ul className="max-h-36 overflow-y-auto space-y-1 text-xs text-gray-600 bg-slate-50 rounded-md p-2.5 border border-slate-200">
                                    {searchProgress.activityLog.map((entry) => (
                                        <li key={entry.id} className="truncate">
                                            {entry.message}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </section>
                )}

                {/* Results Panel */}
                {rejectedBanner && (
                    <div
                        role="status"
                        aria-live="polite"
                        className="p-3.5 rounded-lg bg-slate-100 border border-slate-300 text-sm text-slate-900 flex flex-wrap items-center justify-between gap-3"
                    >
                        <span>
                            Rejected &ldquo;{rejectedBanner.title}&rdquo;. It will be skipped in future searches.
                        </span>
                        {rejectedBanner.id !== null && rejectedBanner.id !== undefined && (
                            <button
                                type="button"
                                disabled={undoingReject}
                                onClick={handleUndoReject}
                                className="px-3 py-1.5 text-xs font-semibold text-blue-700 bg-white border border-blue-200 rounded hover:bg-blue-50 disabled:opacity-50"
                            >
                                {undoingReject ? 'Undoing...' : 'Undo'}
                            </button>
                        )}
                    </div>
                )}

                {searchResult && (
                    <section aria-label="Discovered candidates" className="space-y-4">
                        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <h2 className="text-lg font-semibold text-gray-900">
                                        Discovered Candidates ({candidates.length} new)
                                    </h2>
                                    <p className="text-xs text-gray-500">
                                        {searchResult.total_duplicates_skipped} existing/duplicate item(s) automatically skipped
                                        {searchResult.total_rejected_skipped > 0
                                            ? ` (${searchResult.total_rejected_skipped} previously rejected)`
                                            : ''}
                                        {(searchResult.total_filtered_non_worker ?? 0) > 0
                                            ? ` · ${searchResult.total_filtered_non_worker} non-worker item(s) filtered.`
                                            : '.'}
                                    </p>
                                </div>

                                {candidates.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-2">
                                        {hasScoredWorkers && (
                                            <div className="flex flex-wrap items-center gap-1.5 mr-2">
                                                <button
                                                    type="button"
                                                    aria-pressed={confidenceFilter === 'all'}
                                                    onClick={() => setConfidenceFilter('all')}
                                                    className={`px-2.5 py-1 text-xs font-medium rounded border ${
                                                        confidenceFilter === 'all'
                                                            ? 'bg-blue-600 text-white border-blue-600'
                                                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                                    }`}
                                                >
                                                    All Results ({candidates.length})
                                                </button>
                                                <button
                                                    type="button"
                                                    aria-pressed={confidenceFilter === 'high'}
                                                    onClick={() => setConfidenceFilter('high')}
                                                    className={`px-2.5 py-1 text-xs font-medium rounded border ${
                                                        confidenceFilter === 'high'
                                                            ? 'bg-emerald-700 text-white border-emerald-700'
                                                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                                    }`}
                                                >
                                                    High Confidence Only ({highConfidenceCandidates.length})
                                                </button>
                                                <button
                                                    type="button"
                                                    disabled={highConfidenceCandidates.length === 0}
                                                    onClick={() => setSelectedKeys(highConfidenceCandidates.map(getCandidateKey))}
                                                    className="px-2.5 py-1 text-xs font-medium text-emerald-800 bg-emerald-50 border border-emerald-200 rounded hover:bg-emerald-100 disabled:opacity-50"
                                                >
                                                    Select High-Confidence
                                                </button>
                                            </div>
                                        )}
                                        <button
                                            type="button"
                                            onClick={() => setSelectedKeys(candidates.map(getCandidateKey))}
                                            className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
                                        >
                                            Select All
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setSelectedKeys([])}
                                            className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
                                        >
                                            Clear Selection
                                        </button>
                                        <button
                                            type="button"
                                            disabled={importing || selectedCount === 0}
                                            onClick={handleImportSelected}
                                            className="px-4 py-2 text-sm font-semibold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 disabled:bg-emerald-300 transition shadow-sm"
                                        >
                                            {importing
                                                ? 'Importing to Review Queue...'
                                                : `Import Selected to Review Queue (${selectedCount})`}
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* Per-museum reports */}
                            <div className="flex flex-wrap gap-2">
                                {(searchResult.museum_reports || []).map((rep) => (
                                    <div
                                        key={rep.museum_id}
                                        className={`px-3 py-1.5 rounded-md text-xs border ${
                                            rep.error
                                                ? 'bg-amber-50 border-amber-300 text-amber-900'
                                                : 'bg-slate-50 border-slate-200 text-slate-700'
                                        }`}
                                    >
                                        <strong>{rep.museum_name}:</strong>{' '}
                                        {rep.error
                                            ? rep.error
                                            : `${rep.new_count} new · ${rep.duplicates_skipped} skipped${rep.rejected_skipped > 0 ? ` (${rep.rejected_skipped} rejected)` : ''}${(rep.filtered_non_worker ?? 0) > 0 ? ` · ${rep.filtered_non_worker} filtered` : ''} (${rep.fetched_count} checked)`}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {candidates.length === 0 ? (
                            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-sm text-gray-500 space-y-2">
                                <p>
                                    No new artifacts found outside existing database records for these filters. Try adjusting keywords or expanding the date range.
                                </p>
                                {(searchResult.total_filtered_non_worker ?? 0) > 0 && (
                                    <p className="text-xs text-amber-800">
                                        {searchResult.total_filtered_non_worker} record(s) matched your keywords but scored below the worker depiction threshold. Try widening the date range to Ancient World (3000 BCE–500 CE), disabling Strict mode, or switching to Broad Keyword Search.
                                    </p>
                                )}
                            </div>
                        ) : displayedCandidates.length === 0 ? (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 text-center text-sm text-gray-500">
                                No high-confidence worker depictions matched the current results. Click &ldquo;All Results&rdquo; to inspect medium-confidence candidates.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {displayedCandidates.map((cand) => {
                                    const key = getCandidateKey(cand);
                                    const isChecked = selectedKeys.includes(key);
                                    const isRejecting = Boolean(rejectingKeys[key]);
                                    const previewUrl = cand.images?.[0]?.file_url || '/placeholder-artifact.svg';
                                    const dimsSummary = formatDimensionsSummary(cand);
                                    const workerBadge = getWorkerBadgeMeta(cand);

                                    return (
                                        <article
                                            key={key}
                                            className={`bg-white rounded-lg border p-4 shadow-sm flex flex-col gap-3 ${
                                                isChecked ? 'border-blue-400 ring-1 ring-blue-100' : 'border-gray-200 opacity-85'
                                            }`}
                                        >
                                            <div className="flex items-start gap-3">
                                                <input
                                                    id={`cand-${key}`}
                                                    type="checkbox"
                                                    checked={isChecked}
                                                    onChange={() => handleToggleCandidate(key)}
                                                    aria-label={`Select ${cand.object_type}`}
                                                    className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                                />
                                                <img
                                                    src={previewUrl}
                                                    alt={cand.object_type}
                                                    width={96}
                                                    height={96}
                                                    loading="lazy"
                                                    referrerPolicy="no-referrer"
                                                    onError={(e) => {
                                                        e.target.onerror = null;
                                                        e.target.src = '/placeholder-artifact.svg';
                                                    }}
                                                    className="w-24 h-24 object-cover rounded border border-gray-200 bg-gray-100 flex-shrink-0"
                                                />
                                                <div className="min-w-0 flex-1 space-y-1">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <label htmlFor={`cand-${key}`} className="block font-semibold text-gray-900 text-sm cursor-pointer">
                                                            {cand.object_type}
                                                        </label>
                                                        <button
                                                            type="button"
                                                            disabled={isRejecting || importing}
                                                            onClick={() => handleRejectCandidate(cand)}
                                                            aria-label={`Reject ${cand.object_type}`}
                                                            className="px-2.5 py-1.5 text-xs font-medium text-red-700 bg-red-50 border border-red-200 rounded hover:bg-red-100 disabled:opacity-50 flex-shrink-0"
                                                        >
                                                            {isRejecting ? 'Rejecting...' : 'Reject'}
                                                        </button>
                                                    </div>
                                                    <p className="text-xs text-gray-600">{cand.present_location}</p>
                                                    <div className="flex flex-wrap gap-1.5 text-[11px]">
                                                        {workerBadge && (
                                                            <span className={`px-2 py-0.5 rounded font-semibold border ${workerBadge.className}`}>
                                                                {workerBadge.label}
                                                            </span>
                                                        )}
                                                        {cand.matched_keyword && (
                                                            <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200">
                                                                Matched: &ldquo;{cand.matched_keyword}&rdquo;
                                                            </span>
                                                        )}
                                                        <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">
                                                            {cand.date_display}
                                                        </span>
                                                        {cand.inventory_number && (
                                                            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                                                                inv. {cand.inventory_number}
                                                            </span>
                                                        )}
                                                        <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">
                                                            {cand.filled_fields_count} fields populated
                                                        </span>
                                                    </div>
                                                    {cand.worker_signals?.length > 0 && (
                                                        <div className="flex flex-wrap gap-1 pt-0.5">
                                                            {cand.worker_signals.slice(0, 3).map((sig) => (
                                                                <span
                                                                    key={sig}
                                                                    className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-50/70 text-emerald-800 border border-emerald-200/80"
                                                                >
                                                                    {sig}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-gray-600 border-t border-gray-100 pt-2">
                                                {(cand.findspot || cand.production_location) && (
                                                    <div className="col-span-2 truncate">
                                                        <dt className="inline font-medium text-gray-700">Location: </dt>
                                                        <dd className="inline">{cand.findspot || cand.production_location}</dd>
                                                    </div>
                                                )}
                                                {cand.material && (
                                                    <div className="truncate">
                                                        <dt className="inline font-medium text-gray-700">Medium: </dt>
                                                        <dd className="inline">{cand.material}</dd>
                                                    </div>
                                                )}
                                                {dimsSummary && (
                                                    <div className="truncate">
                                                        <dt className="inline font-medium text-gray-700">Dims: </dt>
                                                        <dd className="inline">{dimsSummary}</dd>
                                                    </div>
                                                )}
                                                {cand.inscription_1 && (
                                                    <div className="col-span-2 truncate">
                                                        <dt className="inline font-medium text-gray-700">Inscription: </dt>
                                                        <dd className="inline">{cand.inscription_1}</dd>
                                                    </div>
                                                )}
                                                {cand.publications && (
                                                    <div className="col-span-2 truncate">
                                                        <dt className="inline font-medium text-gray-700">Publications: </dt>
                                                        <dd className="inline">{cand.publications}</dd>
                                                    </div>
                                                )}
                                            </dl>

                                            {cand.assembled_caption && (
                                                <p className="text-xs text-slate-700 bg-slate-50 p-2 rounded border border-slate-100 line-clamp-2">
                                                    {cand.assembled_caption}
                                                </p>
                                            )}

                                            {cand.description && (
                                                <details className="text-xs text-gray-600 bg-gray-50/80 rounded border border-gray-100 px-2.5 py-1.5">
                                                    <summary className="cursor-pointer font-medium text-gray-700 select-none">
                                                        Catalog notes
                                                    </summary>
                                                    <p className="mt-1.5 leading-relaxed text-gray-700">{cand.description}</p>
                                                </details>
                                            )}

                                            {cand.tags?.length > 0 && (
                                                <div className="flex flex-wrap gap-1">
                                                    {cand.tags.slice(0, 5).map((tag) => (
                                                        <span key={tag} className="px-2 py-0.5 text-[11px] bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100">
                                                            {tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </article>
                                    );
                                })}
                            </div>
                        )}
                    </section>
                )}
            </div>
        </main>
    );
};

export default DiscoveryPage;
