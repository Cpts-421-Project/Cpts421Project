import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import useMapData from '../hooks/useMapData';
import L from 'leaflet';
import { clusterMapPoints, buildClusterSearchUrl } from '../utils/mapClustering';

// Fix for default marker icon in React-Leaflet
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

const createClusterIcon = (count) => {
    const safeCount = Number(count) || 0;
    const tierClass =
        safeCount >= 10
            ? 'map-cluster-badge--lg'
            : safeCount >= 5
                ? 'map-cluster-badge--md'
                : 'map-cluster-badge--sm';
    const size = safeCount >= 10 ? 52 : safeCount >= 5 ? 44 : 36;
    const anchor = size / 2;

    return L.divIcon({
        html: `<span class="map-cluster-badge ${tierClass}">${safeCount}</span>`,
        className: 'map-cluster-icon',
        iconSize: [size, size],
        iconAnchor: [anchor, anchor],
    });
};

const ZoomWatcher = ({ onZoomChange }) => {
    useMapEvents({
        zoomend: (e) => {
            onZoomChange(e.target.getZoom());
        },
    });
    return null;
};

const MapVisualizer = () => {
    const navigate = useNavigate();
    const { mapData, loading, error } = useMapData();
    const defaultCenter = [34.0, 18.0];
    const defaultZoom = 5;
    const [zoom, setZoom] = useState(defaultZoom);

    const clusters = useMemo(() => clusterMapPoints(mapData, zoom), [mapData, zoom]);

    if (loading) return <div className="h-64 flex items-center justify-center bg-gray-100 rounded">Loading Map...</div>;
    if (error) return <div className="h-64 flex items-center justify-center bg-red-50 text-red-500 rounded">Error loading map.</div>;

    return (
        <div className="h-full w-full rounded-lg overflow-hidden border border-gray-300 shadow-sm z-0">
            <MapContainer center={defaultCenter} zoom={defaultZoom} style={{ height: '100%', width: '100%' }}>
                <ZoomWatcher onZoomChange={setZoom} />
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {clusters.map((cluster) => {
                    if (cluster.items.length > 1) {
                        const searchUrl = buildClusterSearchUrl(cluster);
                        return (
                            <Marker
                                key={cluster.id}
                                position={[cluster.latitude, cluster.longitude]}
                                icon={createClusterIcon(cluster.items.length)}
                                keyboard={true}
                                alt={`${cluster.items.length} artifacts in ${cluster.label} — click to view in Search`}
                                eventHandlers={{
                                    click: () => navigate(searchUrl),
                                }}
                            >
                                <Tooltip direction="top" offset={[0, -20]}>
                                    <div className="space-y-0.5 text-xs">
                                        <div className="font-semibold text-gray-900">{cluster.items.length} artifacts</div>
                                        <div className="text-gray-600">{cluster.label}</div>
                                        <div className="font-medium text-blue-700">Click to view all in Search</div>
                                    </div>
                                </Tooltip>
                            </Marker>
                        );
                    }

                    const item = cluster.items[0];
                    const singleSearchUrl = buildClusterSearchUrl(cluster);
                    return (
                        <Marker
                            key={cluster.id}
                            position={[item.latitude, item.longitude]}
                            keyboard={true}
                            alt={item.name}
                        >
                            <Popup>
                                <div className="space-y-1 text-xs">
                                    <strong className="block text-sm text-gray-900">{item.name}</strong>
                                    {item.findspot && <p className="text-gray-600">{item.findspot}</p>}
                                    <div className="flex items-center gap-3 pt-1">
                                        <Link to={`/objects/${item.id}`} className="text-blue-600 hover:underline font-medium">
                                            View Details
                                        </Link>
                                        <Link to={singleSearchUrl} className="text-emerald-700 hover:underline font-medium">
                                            Filter in Search
                                        </Link>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
};

export default MapVisualizer;
