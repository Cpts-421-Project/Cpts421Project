import { useState, useEffect } from 'react';
import { Link, useInRouterContext } from 'react-router-dom';
import useTags from '../hooks/useTags';

const hasNumericFilter = (val) => val !== null && val !== undefined && val !== '';

const FilterSidebar = ({ filters, onFilterChange }) => {
    const inRouter = useInRouterContext();
    const { tags, loading: tagsLoading, error: tagsError } = useTags();
    const [localStartDate, setLocalStartDate] = useState(filters.startDate ?? '');
    const [localEndDate, setLocalEndDate] = useState(filters.endDate ?? '');
    const [tagSearch, setTagSearch] = useState('');

    // Keep local inputs in sync when filters are reset or preset from parent (preserving 0 CE)
    useEffect(() => {
        setLocalStartDate(filters.startDate ?? '');
        setLocalEndDate(filters.endDate ?? '');
    }, [filters.startDate, filters.endDate]);

    // Handle tag selection
    const handleTagChange = (tag) => {
        const currentTags = filters.selectedTags || [];
        const newTags = currentTags.includes(tag)
            ? currentTags.filter((t) => t !== tag)
            : [...currentTags, tag];
        onFilterChange({ ...filters, selectedTags: newTags });
    };

    // Handle date changes without dropping 0 CE
    const handleDateChange = (type, value) => {
        if (type === 'startDate') setLocalStartDate(value);
        if (type === 'endDate') setLocalEndDate(value);

        const parsed = value !== '' ? parseInt(value, 10) : null;
        onFilterChange({
            ...filters,
            [type]: Number.isNaN(parsed) ? null : parsed,
        });
    };

    const isFocusPeriodActive = filters.startDate === 0 && filters.endDate === 899;

    const handleToggleFocusPeriod = () => {
        if (isFocusPeriodActive) {
            onFilterChange({ ...filters, startDate: null, endDate: null });
        } else {
            onFilterChange({ ...filters, startDate: 0, endDate: 899 });
        }
    };

    // Reset all sidebar filters
    const handleClearAll = () => {
        setLocalStartDate('');
        setLocalEndDate('');
        setTagSearch('');
        onFilterChange({
            ...filters,
            selectedTags: [],
            selectedIds: [],
            mapClusterLabel: '',
            startDate: null,
            endDate: null,
            search: '',
        });
    };

    const hasStart = hasNumericFilter(filters.startDate);
    const hasEnd = hasNumericFilter(filters.endDate);
    const hasMapSelection = Boolean(filters.selectedIds && filters.selectedIds.length > 0);
    const hasActiveFilters = Boolean(
        (filters.selectedTags && filters.selectedTags.length > 0) ||
        hasMapSelection ||
        hasStart ||
        hasEnd ||
        filters.search
    );

    const filteredTags = tags.filter((t) =>
        t.toLowerCase().includes(tagSearch.trim().toLowerCase())
    );

    return (
        <aside className="w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto h-full hidden md:block">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                {hasActiveFilters && (
                    <button
                        type="button"
                        onClick={handleClearAll}
                        className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                    >
                        Clear All
                    </button>
                )}
            </div>

            {hasMapSelection && (
                <div className="mb-5 p-3 rounded-lg bg-emerald-50 border border-emerald-200 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                        <div>
                            <h3 className="text-xs font-semibold text-emerald-900 uppercase tracking-wide">
                                Map Selection
                            </h3>
                            <p className="text-sm font-medium text-emerald-950 mt-0.5">
                                {filters.mapClusterLabel || 'Selected Area'}
                            </p>
                            <p className="text-xs text-emerald-800">
                                {filters.selectedIds.length}{' '}
                                {filters.selectedIds.length === 1 ? 'artifact' : 'artifacts'}
                            </p>
                        </div>
                        <button
                            type="button"
                            aria-label="Clear map selection filter"
                            onClick={() =>
                                onFilterChange({
                                    ...filters,
                                    selectedIds: [],
                                    mapClusterLabel: '',
                                })
                            }
                            className="text-xs font-medium text-emerald-800 hover:text-emerald-950 underline"
                        >
                            Clear
                        </button>
                    </div>
                    {inRouter ? (
                        <Link
                            to="/map"
                            className="inline-block text-xs font-medium text-emerald-700 hover:text-emerald-900 underline"
                        >
                            Back to Map
                        </Link>
                    ) : (
                        <a
                            href="/map"
                            className="inline-block text-xs font-medium text-emerald-700 hover:text-emerald-900 underline"
                        >
                            Back to Map
                        </a>
                    )}
                </div>
            )}

            {/* Date Range Section */}
            <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-medium text-gray-700">Time Period (Year)</h3>
                    {(hasStart || hasEnd) && (
                        <button
                            type="button"
                            onClick={() => {
                                setLocalStartDate('');
                                setLocalEndDate('');
                                onFilterChange({ ...filters, startDate: null, endDate: null });
                            }}
                            className="text-xs text-gray-500 hover:text-gray-700"
                        >
                            Reset
                        </button>
                    )}
                </div>

                <button
                    type="button"
                    onClick={handleToggleFocusPeriod}
                    aria-pressed={isFocusPeriodActive}
                    className={`mb-2 w-full px-2.5 py-1.5 text-xs font-medium rounded border transition-colors text-left ${
                        isFocusPeriodActive
                            ? 'bg-blue-50 border-blue-400 text-blue-800'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                >
                    {isFocusPeriodActive ? '✓ 0–899 CE Focus Active' : 'Filter to 0–899 CE Focus'}
                </button>

                <div className="flex flex-col gap-2">
                    <input
                        type="number"
                        aria-label="Start Year"
                        placeholder="Start Year (e.g. 0)"
                        value={localStartDate}
                        onChange={(e) => handleDateChange('startDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <input
                        type="number"
                        aria-label="End Year"
                        placeholder="End Year (e.g. 899)"
                        value={localEndDate}
                        onChange={(e) => handleDateChange('endDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                </div>
                <p className="text-[11px] text-gray-500 mt-1">
                    Primary focus: 0–899 CE (negative = BCE)
                </p>
            </div>

            {/* Tags Section */}
            <div>
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-medium text-gray-700">
                        Tags {filters.selectedTags?.length > 0 && `(${filters.selectedTags.length})`}
                    </h3>
                    {filters.selectedTags?.length > 0 && (
                        <button
                            type="button"
                            onClick={() => onFilterChange({ ...filters, selectedTags: [] })}
                            className="text-xs text-gray-500 hover:text-gray-700"
                        >
                            Clear
                        </button>
                    )}
                </div>

                {tags.length > 6 && (
                    <input
                        type="text"
                        placeholder="Filter tags..."
                        value={tagSearch}
                        onChange={(e) => setTagSearch(e.target.value)}
                        className="mb-2 p-1.5 text-xs border border-gray-200 rounded w-full focus:outline-none focus:ring-1 focus:ring-blue-400"
                    />
                )}

                {tagsLoading ? (
                    <p className="text-sm text-gray-500">Loading tags...</p>
                ) : tagsError ? (
                    <p className="text-sm text-red-500">Error loading tags.</p>
                ) : (
                    <div className="space-y-1 max-h-80 overflow-y-auto">
                        {filteredTags.map((tag) => (
                            <label key={tag} className="flex items-center space-x-2 cursor-pointer hover:bg-gray-100 p-1 rounded">
                                <input
                                    type="checkbox"
                                    checked={(filters.selectedTags || []).includes(tag)}
                                    onChange={() => handleTagChange(tag)}
                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-700 truncate">{tag}</span>
                            </label>
                        ))}
                        {filteredTags.length === 0 && (
                            <p className="text-xs text-gray-400 italic">No matching tags</p>
                        )}
                    </div>
                )}
            </div>
        </aside>
    );
};

export default FilterSidebar;
