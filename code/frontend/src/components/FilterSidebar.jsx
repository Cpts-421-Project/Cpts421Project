import { useState, useEffect } from 'react';
import useTags from '../hooks/useTags';

const FilterSidebar = ({ filters, onFilterChange }) => {
    const { tags, loading: tagsLoading, error: tagsError } = useTags();
    const [localStartDate, setLocalStartDate] = useState(filters.startDate || '');
    const [localEndDate, setLocalEndDate] = useState(filters.endDate || '');
    const [tagSearch, setTagSearch] = useState('');

    // Keep local inputs in sync when filters are reset from parent
    useEffect(() => {
        setLocalStartDate(filters.startDate || '');
        setLocalEndDate(filters.endDate || '');
    }, [filters.startDate, filters.endDate]);

    // Handle tag selection
    const handleTagChange = (tag) => {
        const currentTags = filters.selectedTags || [];
        let newTags;
        if (currentTags.includes(tag)) {
            newTags = currentTags.filter(t => t !== tag);
        } else {
            newTags = [...currentTags, tag];
        }
        onFilterChange({ ...filters, selectedTags: newTags });
    };

    // Handle date changes
    const handleDateChange = (type, value) => {
        if (type === 'startDate') setLocalStartDate(value);
        if (type === 'endDate') setLocalEndDate(value);

        onFilterChange({
            ...filters,
            [type]: value ? parseInt(value, 10) : null
        });
    };

    // Reset all sidebar filters
    const handleClearAll = () => {
        setLocalStartDate('');
        setLocalEndDate('');
        setTagSearch('');
        onFilterChange({
            ...filters,
            selectedTags: [],
            startDate: null,
            endDate: null,
            search: ''
        });
    };

    const hasActiveFilters = Boolean(
        (filters.selectedTags && filters.selectedTags.length > 0) ||
        filters.startDate ||
        filters.endDate ||
        filters.search
    );

    const filteredTags = tags.filter(t => 
        t.toLowerCase().includes(tagSearch.trim().toLowerCase())
    );

    return (
        <aside className="w-64 bg-gray-50 border-r border-gray-200 p-4 overflow-y-auto h-full hidden md:block">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
                {hasActiveFilters && (
                    <button
                        onClick={handleClearAll}
                        className="text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                    >
                        Clear All
                    </button>
                )}
            </div>

            {/* Date Range Section */}
            <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-medium text-gray-700">Time Period (Year)</h3>
                    {(filters.startDate || filters.endDate) && (
                        <button
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
                <div className="flex flex-col gap-2">
                    <input
                        type="number"
                        placeholder="Start Year (e.g. 200)"
                        value={localStartDate}
                        onChange={(e) => handleDateChange('startDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                    <input
                        type="number"
                        placeholder="End Year (e.g. 800)"
                        value={localEndDate}
                        onChange={(e) => handleDateChange('endDate', e.target.value)}
                        className="p-2 border border-gray-300 rounded text-sm w-full focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                </div>
            </div>

            {/* Tags Section */}
            <div>
                <div className="flex justify-between items-center mb-2">
                    <h3 className="text-sm font-medium text-gray-700">
                        Tags {filters.selectedTags?.length > 0 && `(${filters.selectedTags.length})`}
                    </h3>
                    {filters.selectedTags?.length > 0 && (
                        <button
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
                        {filteredTags.map(tag => (
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
