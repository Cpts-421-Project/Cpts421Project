import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import ImageLightbox from '../components/ImageLightbox';
import ReviewShortcutKey from '../components/ReviewShortcutKey';

const MUSEUM_PROVENANCE_URL_RE = /(metmuseum\.org|clevelandart\.org|artic\.edu|vam\.ac\.uk)/i;
const MUSEUM_SOURCE_ID_RE = /^(Met Object ID|CMA |AIC |V&A )/i;

const hasMuseumProvenance = (obj) => {
    if (!obj) return false;
    if (obj.external_url && MUSEUM_PROVENANCE_URL_RE.test(obj.external_url)) {
        return true;
    }
    if (obj.present_location && /cleveland museum of art/i.test(obj.present_location)) {
        return true;
    }
    return Array.isArray(obj.images) && obj.images.some(
        (img) => img?.source_identifier && MUSEUM_SOURCE_ID_RE.test(img.source_identifier)
    );
};

const hasMissingImageUrl = (obj) => {
    if (!obj) return false;
    if (!Array.isArray(obj.images) || obj.images.length === 0) return true;
    return obj.images.some((img) => !(img?.file_url && img.file_url.trim() !== ''));
};

const getImageRenderKey = (objectId, img, idx) =>
    `${objectId}-${img?.id ?? idx}-${img?.file_url || 'empty'}`;

const hasNumericValue = (val) => val !== null && val !== undefined && val !== '';

const isSafeHttpsUrl = (value) => {
    if (typeof value !== 'string') return '';
    const trimmed = value.trim();
    if (!trimmed.toLowerCase().startsWith('https://')) return '';
    try {
        const parsed = new URL(trimmed);
        return parsed.protocol === 'https:' ? trimmed : '';
    } catch {
        return '';
    }
};

const formatDimensions = (obj) => {
    if (!obj) return '';
    if (typeof obj.dimensions_display === 'string' && obj.dimensions_display.trim()) {
        return obj.dimensions_display.trim();
    }
    const parts = [
        hasNumericValue(obj.height) ? `H ${obj.height}` : null,
        hasNumericValue(obj.width) ? `W ${obj.width}` : null,
        hasNumericValue(obj.depth) ? `D ${obj.depth}` : null,
    ].filter(Boolean);
    if (parts.length === 0) return '';
    return `${parts.join(' × ')} ${obj.unit || 'cm'}`;
};

const formatInscriptionSummary = (obj) => {
    if (!obj) return '';
    const texts = [obj.inscription_1, obj.inscription_2]
        .map((item) => (typeof item === 'string' ? item.trim() : ''))
        .filter(Boolean);
    if (texts.length > 0) {
        return texts.join(' / ');
    }
    if (obj.inscription_present === true) return 'Yes';
    if (obj.inscription_present === false) return 'No';
    return '';
};

const ReviewPage = () => {
    const navigate = useNavigate();
    const { isAdmin } = useAuth();

    const [pendingArtifacts, setPendingArtifacts] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [queueVersion, setQueueVersion] = useState(0);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);
    const [fetchError, setFetchError] = useState('');
    const [actionError, setActionError] = useState('');
    const [recoveringImages, setRecoveringImages] = useState(false);
    const [failedImageKeys, setFailedImageKeys] = useState({});
    const [lightboxOpen, setLightboxOpen] = useState(false);
    const [lightboxIndex, setLightboxIndex] = useState(0);
    const [shortcutsOpen, setShortcutsOpen] = useState(false);

    const mainRef = useRef(null);
    const attemptedRecoveryRef = useRef(new Set());

    // Form fields for currently viewed artifact
    const [formData, setFormData] = useState(null);

    // Undo stack for session
    const [undoStack, setUndoStack] = useState([]);

    const fetchPending = useCallback(async () => {
        try {
            setLoading(true);
            setFetchError('');
            const response = await api.get('/objects/pending');
            setPendingArtifacts(Array.isArray(response.data) ? response.data : []);
            setCurrentIndex(0);
            setFailedImageKeys({});
            attemptedRecoveryRef.current = new Set();
            setQueueVersion((v) => v + 1);
        } catch (err) {
            console.error('Failed to fetch pending artifacts', err);
            setFetchError(err.response?.data?.detail || 'Failed to load pending artifacts.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!isAdmin) {
            navigate('/login');
            return;
        }
        fetchPending();
    }, [isAdmin, navigate, fetchPending]);

    const currentObj = currentIndex < pendingArtifacts.length ? pendingArtifacts[currentIndex] : null;
    const currentObjId = currentObj?.id ?? null;

    useEffect(() => {
        mainRef.current?.scrollTo?.({ top: 0 });
        if (currentObj) {
            setFormData({
                object_type: currentObj.object_type || '',
                material: currentObj.material || '',
                findspot: currentObj.findspot || '',
                present_location: currentObj.present_location || '',
                date_display: currentObj.date_display || '',
                date_start: currentObj.date_start ?? 0,
                date_end: currentObj.date_end ?? 0,
                inventory_number: currentObj.inventory_number || '',
                description: currentObj.description || '',
                latitude: currentObj.latitude ?? '',
                longitude: currentObj.longitude ?? ''
            });
        } else {
            setFormData(null);
        }
        // Only re-initialize form fields when switching items or reloading the queue,
        // so background image recovery does not overwrite in-progress edits.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentObjId, queueVersion]);

    const recoverImagesForObject = useCallback(async (obj) => {
        if (!obj?.id) return;
        setRecoveringImages(true);
        setActionError('');
        try {
            const response = await api.post(`/objects/${obj.id}/recover-images`);
            const updatedObj = response?.data;
            if (updatedObj && updatedObj.id) {
                setPendingArtifacts((prev) =>
                    prev.map((item) => (item.id === updatedObj.id ? updatedObj : item))
                );
                setFailedImageKeys((prev) => {
                    const next = { ...prev };
                    const prefix = `${updatedObj.id}-`;
                    Object.keys(next).forEach((key) => {
                        if (key.startsWith(prefix)) {
                            delete next[key];
                        }
                    });
                    return next;
                });
            }
        } catch (err) {
            console.error('Failed to recover museum images', err);
            setActionError(err.response?.data?.detail || 'Failed to recover images from museum API.');
        } finally {
            setRecoveringImages(false);
        }
    }, []);

    useEffect(() => {
        setLightboxOpen(false);
        setLightboxIndex(0);

        if (!currentObj) return;
        if (
            hasMissingImageUrl(currentObj) &&
            hasMuseumProvenance(currentObj) &&
            !attemptedRecoveryRef.current.has(currentObj.id)
        ) {
            attemptedRecoveryRef.current.add(currentObj.id);
            recoverImagesForObject(currentObj);
        }
    }, [currentObjId, currentObj, recoverImagesForObject]);

    const processAction = useCallback(async (action) => {
        if (processing || !formData || currentIndex >= pendingArtifacts.length) return;

        const targetObj = pendingArtifacts[currentIndex];
        setProcessing(true);
        setActionError('');

        try {
            if (action === 'skip') {
                setCurrentIndex((prev) => prev + 1);
            } else {
                const parsedStart = parseInt(formData.date_start, 10);
                const parsedEnd = parseInt(formData.date_end, 10);
                const payload = {
                    ...formData,
                    present_location: formData.present_location?.trim() || null,
                    date_start: Number.isNaN(parsedStart) ? 0 : parsedStart,
                    date_end: Number.isNaN(parsedEnd) ? 0 : parsedEnd,
                    latitude: formData.latitude !== '' && formData.latitude !== null ? parseFloat(formData.latitude) : null,
                    longitude: formData.longitude !== '' && formData.longitude !== null ? parseFloat(formData.longitude) : null,
                };

                await api.put(`/objects/${targetObj.id}`, payload);

                const status = action === 'accept' ? 'accepted' : 'rejected';
                await api.patch(`/objects/${targetObj.id}/review`, { status });

                if (action === 'deny') {
                    setUndoStack((prev) => {
                        const newStack = [{ id: targetObj.id, title: payload.object_type || `Item #${targetObj.id}` }, ...prev];
                        return newStack.slice(0, 3);
                    });
                }

                setCurrentIndex((prev) => prev + 1);
            }
        } catch (err) {
            console.error(`Failed to execute ${action}`, err);
            setActionError(err.response?.data?.detail || `Failed to ${action} artifact. Please try again.`);
        } finally {
            setProcessing(false);
        }
    }, [processing, formData, currentIndex, pendingArtifacts]);

    const handleUndo = useCallback(async (item) => {
        if (processing || !item) return;
        setProcessing(true);
        setActionError('');
        try {
            await api.patch(`/objects/${item.id}/review`, { status: 'pending' });
            setUndoStack((prev) => prev.filter((u) => u.id !== item.id));
            await fetchPending();
        } catch (error) {
            console.error('Failed to undo', error);
            setActionError(error.response?.data?.detail || 'Failed to undo. The item might be permanently deleted.');
        } finally {
            setProcessing(false);
        }
    }, [processing, fetchPending]);

    const isComplete = currentIndex >= pendingArtifacts.length;
    const currentImages = currentObj?.images || [];

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.ctrlKey || e.metaKey || e.altKey) {
                return;
            }
            if (e.isComposing || e.keyCode === 229 || e.repeat) {
                return;
            }

            const target = e.target;
            if (
                ['INPUT', 'TEXTAREA', 'SELECT'].includes(target?.tagName) ||
                target?.isContentEditable
            ) {
                if (e.key === 'Escape') {
                    target.blur?.();
                }
                return;
            }

            if (lightboxOpen) {
                return;
            }

            if (e.key === '?') {
                e.preventDefault();
                setShortcutsOpen((prev) => !prev);
                return;
            }

            if (shortcutsOpen) {
                return;
            }

            if (
                typeof target?.closest === 'function' &&
                target.closest('button, a, summary') &&
                (e.code === 'Space' || e.code === 'Enter')
            ) {
                return;
            }

            const key = (e.key || '').toLowerCase();

            if (key === 'u') {
                if (undoStack.length > 0 && !processing) {
                    e.preventDefault();
                    handleUndo(undoStack[0]);
                }
                return;
            }

            if (e.key === 'ArrowLeft' || key === 'p') {
                if (currentIndex > 0 && !processing) {
                    e.preventDefault();
                    setCurrentIndex((prev) => Math.max(0, prev - 1));
                }
                return;
            }

            if (isComplete) {
                return;
            }

            if (e.code === 'Space' || key === 'a') {
                e.preventDefault();
                processAction('accept');
            } else if (e.code === 'Delete' || e.code === 'Backspace' || key === 'd') {
                e.preventDefault();
                processAction('deny');
            } else if (e.code === 'Enter' || key === 's' || e.key === 'ArrowRight') {
                e.preventDefault();
                processAction('skip');
            } else if (key === 'z' && currentImages.length > 0) {
                e.preventDefault();
                const firstValidIdx = currentImages.findIndex((img, idx) => {
                    const url = (img?.file_url || '').trim();
                    return url !== '' && !failedImageKeys[getImageRenderKey(currentObj.id, img, idx)];
                });
                setLightboxIndex(firstValidIdx >= 0 ? firstValidIdx : 0);
                setLightboxOpen(true);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [
        processAction,
        handleUndo,
        lightboxOpen,
        shortcutsOpen,
        undoStack,
        processing,
        currentIndex,
        isComplete,
        currentImages,
        currentObj,
        failedImageKeys,
    ]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData((prev) => ({ ...prev, [name]: value }));
    };

    const handleImageError = (imgKey) => {
        setFailedImageKeys((prev) => (prev[imgKey] ? prev : { ...prev, [imgKey]: true }));
    };

    if (loading || (!isComplete && !formData)) {
        return (
            <main ref={mainRef} className="flex-1 min-h-0 overflow-y-auto bg-gray-50 p-8">
                Loading pending artifacts...
            </main>
        );
    }

    const hasRecoverableFailure = Boolean(
        currentObj &&
        hasMuseumProvenance(currentObj) &&
        (
            hasMissingImageUrl(currentObj) ||
            currentImages.some((img, idx) => Boolean(failedImageKeys[getImageRenderKey(currentObj.id, img, idx)]))
        )
    );

    const safeExternalUrl = isSafeHttpsUrl(currentObj?.external_url);
    const dimensionsSummary = formatDimensions(currentObj);
    const inscriptionSummary = formatInscriptionSummary(currentObj);
    const hasCoords = hasNumericValue(currentObj?.latitude) && hasNumericValue(currentObj?.longitude);
    const coordsSummary = hasCoords ? `${currentObj.latitude}, ${currentObj.longitude}` : '';
    const factRows = [
        { label: 'Production Site', value: currentObj?.production_location },
        { label: 'Group / Hoard', value: currentObj?.object_group },
        { label: 'Date Basis', value: currentObj?.date_basis },
        { label: 'Dimensions', value: dimensionsSummary },
        { label: 'Weight', value: currentObj?.weight },
        { label: 'Completeness', value: currentObj?.completeness },
        { label: 'Inscriptions', value: inscriptionSummary },
        { label: 'Coordinates', value: coordsSummary },
    ].filter((row) => typeof row.value === 'string' && row.value.trim() !== '');
    const tagsList = Array.isArray(currentObj?.tags) ? currentObj.tags.filter(Boolean) : [];
    const bibliographyList = Array.isArray(currentObj?.bibliography) ? currentObj.bibliography.filter(Boolean) : [];
    const hasCaptionFact = Boolean(currentObj?.assembled_caption && currentObj.assembled_caption.trim());
    const hasPublicationsFact = Boolean(currentObj?.publications && currentObj.publications.trim());
    const hasAdditionalFacts = Boolean(
        currentObj &&
        (
            hasCaptionFact ||
            factRows.length > 0 ||
            tagsList.length > 0 ||
            hasPublicationsFact ||
            bibliographyList.length > 0 ||
            Boolean(safeExternalUrl)
        )
    );

    return (
        <main ref={mainRef} className="flex-1 min-h-0 overflow-y-auto bg-gray-50 py-8 px-4">
            <div className="w-full max-w-4xl mx-auto pb-8">
                <div className="w-full flex justify-between items-end mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Review Queue</h1>
                        {!isComplete && (
                            <p className="text-gray-500 mt-2">
                                Item {currentIndex + 1} of {pendingArtifacts.length}
                            </p>
                        )}
                    </div>

                    {/* Undo Stack UI */}
                    {undoStack.length > 0 && (
                        <div className="bg-white p-3 rounded shadow-sm border text-sm">
                            <strong className="text-gray-700 block mb-2">Recently Denied:</strong>
                            <ul className="space-y-1">
                                {undoStack.map((item) => (
                                    <li key={item.id} className="flex items-center justify-between gap-4">
                                        <span className="truncate w-32">{item.title}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleUndo(item)}
                                            className="text-blue-600 hover:text-blue-800 font-semibold"
                                            disabled={processing}
                                        >
                                            Undo
                                        </button>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {fetchError && (
                    <div
                        role="alert"
                        className="w-full mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800 flex items-center justify-between gap-4"
                    >
                        <span>{fetchError}</span>
                        <button
                            type="button"
                            onClick={fetchPending}
                            className="px-3 py-1 text-xs font-semibold text-red-800 bg-white border border-red-300 rounded hover:bg-red-100"
                        >
                            Retry
                        </button>
                    </div>
                )}

                {actionError && (
                    <div
                        role="alert"
                        className="w-full mb-4 p-4 rounded-lg bg-red-50 border border-red-200 text-sm text-red-800"
                    >
                        {actionError}
                    </div>
                )}

                <ReviewShortcutKey
                    isOpen={shortcutsOpen}
                    onOpen={() => setShortcutsOpen(true)}
                    onClose={() => setShortcutsOpen(false)}
                    canUndo={undoStack.length > 0}
                    canGoPrev={currentIndex > 0}
                    canZoom={!isComplete && currentImages.length > 0}
                />

                {isComplete ? (
                    <div className="bg-white p-12 text-center rounded shadow w-full border">
                        <h2 className="text-2xl font-bold text-gray-700 mb-4">Queue Empty!</h2>
                        <p className="text-gray-500">You have reviewed all pending artifacts.</p>
                        <button
                            type="button"
                            onClick={fetchPending}
                            className="mt-6 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Refresh Queue
                        </button>
                    </div>
                ) : (
                    <div className="bg-white shadow rounded-lg w-full overflow-hidden border">
                        {/* Visualizer & Images */}
                        <div className="bg-gray-100 p-4 border-b space-y-3">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                                <span className="text-xs font-semibold uppercase tracking-wider text-gray-600">
                                    Artifact Images ({currentImages.length})
                                </span>
                                <div className="flex items-center gap-3">
                                    {recoveringImages && (
                                        <span role="status" className="text-xs font-medium text-blue-700">
                                            Fetching museum images...
                                        </span>
                                    )}
                                    {hasRecoverableFailure && !recoveringImages && (
                                        <button
                                            type="button"
                                            onClick={() => recoverImagesForObject(currentObj)}
                                            className="px-3 py-1 text-xs font-medium text-blue-700 bg-white border border-blue-200 rounded hover:bg-blue-50"
                                        >
                                            Retry Image Fetch
                                        </button>
                                    )}
                                </div>
                            </div>

                            {currentImages.length > 0 ? (
                                <div className="flex gap-4 overflow-x-auto pb-2">
                                    {currentImages.map((img, idx) => {
                                        const imgKey = getImageRenderKey(currentObj.id, img, idx);
                                        const rawUrl = (img?.file_url || '').trim();
                                        const hasUrl = rawUrl !== '';
                                        const isFailed = Boolean(failedImageKeys[imgKey]);
                                        const canDisplay = hasUrl && !isFailed;
                                        const typeLabel = [img.image_type, img.view_type].filter(Boolean).join(' · ') || 'Artifact image';

                                        return (
                                            <div
                                                key={imgKey}
                                                className="min-w-[14rem] max-w-xs bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm flex-shrink-0 flex flex-col"
                                            >
                                                {canDisplay ? (
                                                    <button
                                                        type="button"
                                                        onClick={() => {
                                                            setLightboxIndex(idx);
                                                            setLightboxOpen(true);
                                                        }}
                                                        aria-label={`Inspect ${currentObj.object_type || 'artifact'} image ${idx + 1}`}
                                                        className="block w-full bg-gray-100 cursor-zoom-in focus:outline-none focus:ring-2 focus:ring-blue-500"
                                                    >
                                                        <img
                                                            src={rawUrl}
                                                            alt={`${currentObj.object_type || 'Artifact'} - ${img.view_type || `View ${idx + 1}`}`}
                                                            referrerPolicy="no-referrer"
                                                            onError={() => handleImageError(imgKey)}
                                                            className="w-full h-52 object-contain bg-gray-100"
                                                        />
                                                    </button>
                                                ) : (
                                                    <div className="w-full h-52 bg-gray-50 flex flex-col items-center justify-center p-4 text-center space-y-2">
                                                        <img
                                                            src="/placeholder-artifact.svg"
                                                            alt={hasUrl ? 'Image unavailable' : 'Image pending upload'}
                                                            className="w-32 h-24 object-contain opacity-85"
                                                        />
                                                        <span className="text-xs font-medium text-gray-600">
                                                            {hasUrl ? 'Image Unavailable' : 'Image Pending Upload'}
                                                        </span>
                                                    </div>
                                                )}

                                                <div className="px-3 py-2 border-t border-gray-100 text-xs flex items-center justify-between gap-2 bg-white">
                                                    <div className="min-w-0">
                                                        <p className="font-medium text-gray-800 truncate">
                                                            {img.db_identifier && <span className="mr-1.5 text-gray-900">{img.db_identifier}</span>}
                                                            {typeLabel}
                                                        </p>
                                                        {img.source_identifier && (
                                                            <p className="text-[11px] text-gray-500 truncate">{img.source_identifier}</p>
                                                        )}
                                                    </div>
                                                    {canDisplay && (
                                                        <span className="text-[11px] font-medium text-blue-600 flex-shrink-0">
                                                            Zoom
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="h-48 bg-white rounded-lg border border-gray-200 flex flex-col items-center justify-center p-4 text-center space-y-2">
                                    <img
                                        src="/placeholder-artifact.svg"
                                        alt="Image pending upload"
                                        className="w-32 h-24 object-contain opacity-85"
                                    />
                                    <p className="text-sm font-medium text-gray-600">Image Pending Upload</p>
                                </div>
                            )}
                        </div>

                        {/* Editor Form */}
                        <div className="p-6">
                            <form className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Type</label>
                                        <input type="text" name="object_type" value={formData.object_type} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Inventory Number</label>
                                        <input type="text" name="inventory_number" value={formData.inventory_number} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Material</label>
                                        <input type="text" name="material" value={formData.material} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Findspot</label>
                                        <input type="text" name="findspot" value={formData.findspot} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="block text-sm font-medium text-gray-700">Present Location (Collection)</label>
                                        <input type="text" name="present_location" value={formData.present_location} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">Date Display</label>
                                        <input type="text" name="date_display" value={formData.date_display} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                    </div>

                                    <div className="grid grid-cols-2 gap-2">
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700">Start Year</label>
                                            <input type="number" name="date_start" value={formData.date_start} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700">End Year</label>
                                            <input type="number" name="date_end" value={formData.date_end} onChange={handleChange} className="mt-1 w-full p-2 border rounded" />
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700">Description</label>
                                    <textarea name="description" value={formData.description} onChange={handleChange} rows="3" className="mt-1 w-full p-2 border rounded"></textarea>
                                </div>
                            </form>
                        </div>

                        {/* Additional Recorded Facts */}
                        {hasAdditionalFacts && (
                            <section
                                aria-labelledby="review-recorded-facts-heading"
                                className="border-t border-gray-200 px-6 py-5 bg-slate-50/60 space-y-4"
                            >
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                    <h2
                                        id="review-recorded-facts-heading"
                                        className="text-xs font-semibold uppercase tracking-wider text-gray-600"
                                    >
                                        Additional Recorded Facts
                                    </h2>
                                    {safeExternalUrl && (
                                        <a
                                            href={safeExternalUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-xs font-medium text-blue-700 hover:text-blue-900 underline"
                                        >
                                            View Source Museum Record
                                        </a>
                                    )}
                                </div>

                                {hasCaptionFact && (
                                    <div className="rounded-md bg-white border border-slate-200 p-3">
                                        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1">
                                            Assembled Caption
                                        </p>
                                        <p className="text-sm text-slate-900 leading-relaxed">
                                            {currentObj.assembled_caption}
                                        </p>
                                    </div>
                                )}

                                {factRows.length > 0 && (
                                    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5 text-sm">
                                        {factRows.map((row) => (
                                            <div key={row.label}>
                                                <dt className="text-xs font-medium text-gray-500">{row.label}</dt>
                                                <dd className="text-gray-900 break-words">{row.value}</dd>
                                            </div>
                                        ))}
                                    </dl>
                                )}

                                {tagsList.length > 0 && (
                                    <div>
                                        <p className="text-xs font-medium text-gray-500 mb-1.5">Tags</p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {tagsList.map((tag) => (
                                                <span
                                                    key={tag}
                                                    className="inline-block px-2.5 py-0.5 text-xs font-medium bg-blue-50 text-blue-700 rounded-full border border-blue-200"
                                                >
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {hasPublicationsFact && (
                                    <div>
                                        <p className="text-xs font-medium text-gray-500 mb-1">
                                            Image Discussions &amp; Publications
                                        </p>
                                        <p className="text-sm text-gray-800 leading-relaxed">{currentObj.publications}</p>
                                    </div>
                                )}

                                {bibliographyList.length > 0 && (
                                    <div>
                                        <p className="text-xs font-medium text-gray-500 mb-1">
                                            Image Sources (Chicago Style)
                                        </p>
                                        <ul className="list-disc pl-5 space-y-1 text-xs text-gray-700">
                                            {bibliographyList.map((ref, idx) => (
                                                <li key={idx}>{ref}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </section>
                        )}

                        {/* Action Bar */}
                        <div className="bg-gray-50 border-t p-4 flex flex-wrap justify-between items-center gap-4 px-6">
                            <p className="text-gray-500 text-xs sm:text-sm">
                                Press{' '}
                                <kbd className="px-1.5 py-0.5 text-[11px] font-mono font-semibold bg-white text-gray-800 border border-gray-300 rounded">
                                    ?
                                </kbd>{' '}
                                for all shortcuts ·{' '}
                                <kbd className="px-1.5 py-0.5 text-[11px] font-mono font-semibold bg-white text-gray-800 border border-gray-300 rounded">
                                    Esc
                                </kbd>{' '}
                                to exit text field
                            </p>

                            <div className="flex flex-wrap gap-3">
                                <button
                                    type="button"
                                    onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
                                    disabled={processing || currentIndex === 0}
                                    aria-keyshortcuts="ArrowLeft p"
                                    className="px-4 py-2 border hover:bg-gray-100 text-gray-700 rounded font-medium disabled:opacity-50 inline-flex items-center gap-1.5"
                                >
                                    <span>Previous</span>
                                    <kbd aria-hidden="true" className="px-1 py-0.5 text-[10px] font-mono bg-white text-gray-500 border border-gray-300 rounded">
                                        ←
                                    </kbd>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => processAction('deny')}
                                    disabled={processing}
                                    aria-keyshortcuts="d Delete Backspace"
                                    className="px-5 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded font-medium disabled:opacity-50 inline-flex items-center gap-1.5"
                                >
                                    <span>Deny</span>
                                    <kbd aria-hidden="true" className="px-1 py-0.5 text-[10px] font-mono bg-red-50 text-red-700 border border-red-200 rounded">
                                        D
                                    </kbd>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => processAction('skip')}
                                    disabled={processing}
                                    aria-keyshortcuts="s Enter ArrowRight"
                                    className="px-5 py-2 border hover:bg-gray-100 text-gray-700 rounded font-medium disabled:opacity-50 inline-flex items-center gap-1.5"
                                >
                                    <span>Skip</span>
                                    <kbd aria-hidden="true" className="px-1 py-0.5 text-[10px] font-mono bg-white text-gray-500 border border-gray-300 rounded">
                                        S
                                    </kbd>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => processAction('accept')}
                                    disabled={processing}
                                    aria-keyshortcuts="a Space"
                                    className="px-5 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium disabled:opacity-50 inline-flex items-center gap-1.5"
                                >
                                    <span>Accept</span>
                                    <kbd aria-hidden="true" className="px-1 py-0.5 text-[10px] font-mono bg-green-700 text-green-50 border border-green-500 rounded">
                                        A
                                    </kbd>
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                <ImageLightbox
                    isOpen={lightboxOpen}
                    images={currentImages}
                    activeIndex={lightboxIndex}
                    objectTitle={currentObj?.object_type || 'Artifact Image'}
                    onClose={() => setLightboxOpen(false)}
                    onSelectIndex={setLightboxIndex}
                />
            </div>
        </main>
    );
};

export default ReviewPage;
