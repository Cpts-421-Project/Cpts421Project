import { useState, useEffect, useId } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';

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

const hasNumericValue = (val) => val !== null && val !== undefined && val !== '';
const getCandidateKey = (cand) => `${cand.museum_id}:${cand.source_record_id}`;

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

    const [museums, setMuseums] = useState([]);
    const [loadingMuseums, setLoadingMuseums] = useState(true);
    const [selectedMuseums, setSelectedMuseums] = useState(['met', 'cma', 'aic', 'vam']);
    const [keywords, setKeywords] = useState(DEFAULT_KEYWORDS);
    const [keywordInput, setKeywordInput] = useState('');
    const [savingKeyword, setSavingKeyword] = useState(false);
    const [keywordStatus, setKeywordStatus] = useState('');
    const [dateStart, setDateStart] = useState(0);
    const [dateEnd, setDateEnd] = useState(899);
    const [limitPerMuseum, setLimitPerMuseum] = useState(10);

    const [validationErrors, setValidationErrors] = useState({});
    const [apiError, setApiError] = useState('');
    const [searching, setSearching] = useState(false);
    const [importing, setImporting] = useState(false);

    const [searchResult, setSearchResult] = useState(null);
    const [selectedKeys, setSelectedKeys] = useState([]);
    const [importResult, setImportResult] = useState(null);

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
                setKeywordStatus(`Removed "${kwToRemove}" from saved keywords.`);
            }
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Failed to remove keyword.');
        }
    };

    const handleResetDefaults = () => {
        const defaultKeywords = museums[0]?.default_keywords?.length ? museums[0].default_keywords : DEFAULT_KEYWORDS;
        const defaultStart = museums[0]?.default_date_start ?? 0;
        const defaultEnd = museums[0]?.default_date_end ?? 899;
        const defaultLimit = museums[0]?.default_limit ?? 10;

        setSelectedMuseums(museums.length > 0 ? museums.map((m) => m.id) : ['met', 'cma', 'aic', 'vam']);
        setKeywords([...defaultKeywords]);
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

    const handleDiscover = async (e) => {
        e.preventDefault();
        setApiError('');
        setImportResult(null);

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
        setSearching(true);

        try {
            const response = await api.post('/admin/discovery/search', {
                museums: selectedMuseums,
                keywords: effectiveKeywords,
                date_start: Number(dateStart),
                date_end: Number(dateEnd),
                limit_per_museum: Number(limitPerMuseum) || 10,
            });
            const data = response.data;
            setSearchResult(data);
            setSelectedKeys((data.candidates || []).map(getCandidateKey));
        } catch (err) {
            setApiError(err.response?.data?.detail || err.message || 'Discovery search failed.');
        } finally {
            setSearching(false);
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

    const candidates = searchResult?.candidates || [];
    const selectedCount = candidates.filter((c) => selectedKeys.includes(getCandidateKey(c))).length;

    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Discover Artifacts from Predefined Museums</h1>
                        <p className="text-sm text-gray-600 mt-1">
                            Search curated open-access collections using editable keywords and date ranges. Existing database pieces are skipped automatically, and new discoveries stage in the Review Queue.
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
                                <button
                                    type="button"
                                    onClick={() => {
                                        setDateStart(0);
                                        setDateEnd(899);
                                        setValidationErrors((prev) => ({ ...prev, dates: undefined }));
                                    }}
                                    className="text-xs font-medium text-blue-600 hover:text-blue-800"
                                >
                                    0–899 CE Focus
                                </button>
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
                                className="px-6 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-blue-300 transition shadow-sm"
                            >
                                {searching ? 'Searching Museums...' : 'Discover New Artifacts'}
                            </button>
                        </div>
                    </form>
                </search>

                {/* Results Panel */}
                {searchResult && (
                    <section role="status" aria-live="polite" className="space-y-4">
                        <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
                            <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                    <h2 className="text-lg font-semibold text-gray-900">
                                        Discovered Candidates ({candidates.length} new)
                                    </h2>
                                    <p className="text-xs text-gray-500">
                                        {searchResult.total_duplicates_skipped} existing/duplicate item(s) automatically skipped.
                                    </p>
                                </div>

                                {candidates.length > 0 && (
                                    <div className="flex flex-wrap items-center gap-2">
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
                                            : `${rep.new_count} new · ${rep.duplicates_skipped} skipped (${rep.fetched_count} checked)`}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {candidates.length === 0 ? (
                            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center text-sm text-gray-500">
                                No new artifacts found outside existing database records for these filters. Try adjusting keywords or expanding the date range.
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {candidates.map((cand) => {
                                    const key = getCandidateKey(cand);
                                    const isChecked = selectedKeys.includes(key);
                                    const previewUrl = cand.images?.[0]?.file_url || '/placeholder-artifact.svg';
                                    const dimsSummary = formatDimensionsSummary(cand);

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
                                                    referrerPolicy="no-referrer"
                                                    onError={(e) => {
                                                        e.target.onerror = null;
                                                        e.target.src = '/placeholder-artifact.svg';
                                                    }}
                                                    className="w-24 h-24 object-cover rounded border border-gray-200 bg-gray-100 flex-shrink-0"
                                                />
                                                <div className="min-w-0 flex-1 space-y-1">
                                                    <label htmlFor={`cand-${key}`} className="block font-semibold text-gray-900 text-sm cursor-pointer">
                                                        {cand.object_type}
                                                    </label>
                                                    <p className="text-xs text-gray-600">{cand.present_location}</p>
                                                    <div className="flex flex-wrap gap-1.5 text-[11px]">
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
