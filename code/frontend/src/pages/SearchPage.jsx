import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import FilterSidebar from '../components/FilterSidebar';
import ArtifactGrid from '../components/ArtifactGrid';
import useArtifacts from '../hooks/useArtifacts';

const SearchPage = () => {
    const [searchParams, setSearchParams] = useSearchParams();

    // Initialize filters from URL parameters if present
    const [filters, setFilters] = useState(() => {
        const initialSearch = searchParams.get('search') || searchParams.get('q') || '';
        const initialTag = searchParams.get('tag') || searchParams.get('tags') || '';
        const start = searchParams.get('date_start');
        const end = searchParams.get('date_end');

        return {
            search: initialSearch,
            selectedTags: initialTag ? [initialTag] : [],
            startDate: start ? parseInt(start, 10) : null,
            endDate: end ? parseInt(end, 10) : null,
        };
    });

    const { artifacts, loading, error } = useArtifacts(filters);

    // Sync URL when filters change
    useEffect(() => {
        const params = new URLSearchParams();
        if (filters.search) params.set('search', filters.search);
        if (filters.selectedTags && filters.selectedTags.length > 0) {
            filters.selectedTags.forEach(t => params.append('tag', t));
        }
        if (filters.startDate) params.set('date_start', filters.startDate.toString());
        if (filters.endDate) params.set('date_end', filters.endDate.toString());

        setSearchParams(params, { replace: true });
    }, [filters, setSearchParams]);

    const handleRemoveTag = (tagToRemove) => {
        setFilters(prev => ({
            ...prev,
            selectedTags: prev.selectedTags.filter(t => t !== tagToRemove)
        }));
    };

    const handleClearAll = () => {
        setFilters({
            search: '',
            selectedTags: [],
            startDate: null,
            endDate: null
        });
    };

    const hasActiveFilters = Boolean(
        filters.search ||
        (filters.selectedTags && filters.selectedTags.length > 0) ||
        filters.startDate ||
        filters.endDate
    );

    return (
        <div className="flex flex-1 overflow-hidden h-full">
            <FilterSidebar filters={filters} onFilterChange={setFilters} />

            <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
                <div className="max-w-7xl mx-auto space-y-6">
                    {/* Search Input Bar */}
                    <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                        <div className="w-full md:w-2/3 relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                                </svg>
                            </div>
                            <input
                                type="text"
                                placeholder="Search by name, description, material, findspot, or tag..."
                                className="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 text-sm"
                                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                                value={filters.search}
                            />
                            {filters.search && (
                                <button
                                    onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
                                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                                    title="Clear search"
                                >
                                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Active Filter Pills Bar */}
                    {hasActiveFilters && (
                        <div className="flex flex-wrap items-center gap-2 pt-1 pb-2">
                            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active:</span>

                            {filters.search && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                                    Search: "{filters.search}"
                                    <button
                                        onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
                                        className="hover:text-blue-900 focus:outline-none"
                                    >
                                        &times;
                                    </button>
                                </span>
                            )}

                            {filters.selectedTags.map(tag => (
                                <span
                                    key={tag}
                                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 border border-indigo-200"
                                >
                                    Tag: {tag}
                                    <button
                                        onClick={() => handleRemoveTag(tag)}
                                        className="hover:text-indigo-900 focus:outline-none"
                                    >
                                        &times;
                                    </button>
                                </span>
                            ))}

                            {(filters.startDate || filters.endDate) && (
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 border border-amber-200">
                                    Years: {filters.startDate || 'Any'} – {filters.endDate || 'Any'}
                                    <button
                                        onClick={() => setFilters(prev => ({ ...prev, startDate: null, endDate: null }))}
                                        className="hover:text-amber-900 focus:outline-none"
                                    >
                                        &times;
                                    </button>
                                </span>
                            )}

                            <button
                                onClick={handleClearAll}
                                className="text-xs text-red-600 hover:text-red-800 font-medium ml-2 underline"
                            >
                                Reset all
                            </button>
                        </div>
                    )}

                    {/* Results Section */}
                    <section>
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-semibold text-gray-800">
                                Search Results ({artifacts ? artifacts.length : 0})
                            </h2>
                        </div>

                        {!loading && !error && (!artifacts || artifacts.length === 0) ? (
                            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center space-y-4">
                                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <h3 className="text-lg font-medium text-gray-900">No artifacts found</h3>
                                <p className="text-sm text-gray-500 max-w-sm mx-auto">
                                    We couldn't find any artifacts matching your current search terms and filters.
                                </p>
                                {hasActiveFilters && (
                                    <button
                                        onClick={handleClearAll}
                                        className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-sm"
                                    >
                                        Clear all filters
                                    </button>
                                )}
                            </div>
                        ) : (
                            <ArtifactGrid artifacts={artifacts} loading={loading} error={error} />
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
};

export default SearchPage;
