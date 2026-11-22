import MapVisualizer from '../components/MapVisualizer';

const MapPage = () => {
    return (
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto h-full flex flex-col">
                <div className="mb-4">
                    <h1 className="text-xl font-semibold text-gray-800">Geographic Distribution</h1>
                    <p className="text-xs text-gray-600 mt-1">
                        Nearby artifacts fuse together when zoomed out or sharing a site. Click any fused cluster to view all of its artifacts in Search.
                    </p>
                </div>
                <div className="flex-1 min-h-[500px]">
                    <MapVisualizer />
                </div>
            </div>
        </main>
    );
};

export default MapPage;
