const MAX_MERCATOR_LAT = 85.05112878;
const DEFAULT_CLUSTER_RADIUS_PX = 56;
const MAX_LABEL_LENGTH = 100;

/**
 * Validate numeric map coordinates while explicitly preserving 0 (INV-UI-01).
 */
export const isValidCoordinate = (val) =>
    typeof val === 'number' && !Number.isNaN(val) && Number.isFinite(val);

/**
 * Project WGS84 latitude/longitude into Web-Mercator world pixel coordinates at a zoom level.
 */
export const projectToWorldPixels = (lat, lng, zoom) => {
    const safeZoom = isValidCoordinate(zoom) ? zoom : 5;
    const clampedLat = Math.max(-MAX_MERCATOR_LAT, Math.min(MAX_MERCATOR_LAT, lat));
    const rad = (clampedLat * Math.PI) / 180;
    const scale = 256 * 2 ** safeZoom;
    const x = ((lng + 180) / 360) * scale;
    const sinLat = Math.sin(rad);
    const y = (0.5 - Math.log((1 + sinLat) / (1 - sinLat)) / (4 * Math.PI)) * scale;
    return { x, y };
};

/**
 * Build a concise human-readable geographic label from member findspot values.
 */
export const summarizeClusterLabel = (items) => {
    if (!Array.isArray(items) || items.length === 0) return 'Map Area';

    const seen = new Set();
    const uniqueSites = [];
    for (const item of items) {
        const raw = typeof item?.findspot === 'string' ? item.findspot.trim() : '';
        if (!raw) continue;
        const low = raw.toLowerCase();
        if (!seen.has(low)) {
            seen.add(low);
            uniqueSites.push(raw);
        }
    }

    if (uniqueSites.length === 0) return 'Map Area';
    if (uniqueSites.length === 1) return uniqueSites[0].slice(0, MAX_LABEL_LENGTH);
    if (uniqueSites.length === 2) {
        return `${uniqueSites[0]} & ${uniqueSites[1]}`.slice(0, MAX_LABEL_LENGTH);
    }

    const extraCount = uniqueSites.length - 2;
    const summary = `${uniqueSites[0]}, ${uniqueSites[1]} + ${extraCount} sites`;
    return summary.slice(0, MAX_LABEL_LENGTH);
};

/**
 * Fuse nearby map points based on Web-Mercator pixel distance at the active zoom level.
 */
export const clusterMapPoints = (points, zoom, radiusPx = DEFAULT_CLUSTER_RADIUS_PX) => {
    if (!Array.isArray(points) || points.length === 0) return [];

    const validPoints = points
        .filter((p) => p && isValidCoordinate(p.latitude) && isValidCoordinate(p.longitude))
        .slice()
        .sort((a, b) => Number(a.id) - Number(b.id));

    const clusters = [];

    for (const point of validPoints) {
        const ptPx = projectToWorldPixels(point.latitude, point.longitude, zoom);
        let matchedCluster = null;
        let bestDistSq = radiusPx * radiusPx;

        for (const cluster of clusters) {
            const dx = ptPx.x - cluster.px.x;
            const dy = ptPx.y - cluster.px.y;
            const distSq = dx * dx + dy * dy;
            if (distSq <= bestDistSq) {
                bestDistSq = distSq;
                matchedCluster = cluster;
            }
        }

        if (matchedCluster) {
            matchedCluster.items.push(point);
            const n = matchedCluster.items.length;
            matchedCluster.latitude = ((matchedCluster.latitude * (n - 1)) + point.latitude) / n;
            matchedCluster.longitude = ((matchedCluster.longitude * (n - 1)) + point.longitude) / n;
            matchedCluster.px = projectToWorldPixels(matchedCluster.latitude, matchedCluster.longitude, zoom);
        } else {
            clusters.push({
                latitude: point.latitude,
                longitude: point.longitude,
                px: ptPx,
                items: [point],
            });
        }
    }

    return clusters.map((cluster) => {
        const ids = cluster.items
            .map((item) => Number(item.id))
            .filter((n) => Number.isInteger(n) && n > 0)
            .sort((a, b) => a - b);

        return {
            id: `cluster-${ids.join('-')}`,
            latitude: cluster.latitude,
            longitude: cluster.longitude,
            items: cluster.items,
            ids,
            label: summarizeClusterLabel(cluster.items),
        };
    });
};

/**
 * Build a /search URL that activates a map-cluster artifact ID filter.
 */
export const buildClusterSearchUrl = (cluster) => {
    const params = new URLSearchParams();
    if (cluster?.ids?.length > 0) {
        params.set('ids', cluster.ids.join(','));
    }
    if (cluster?.label) {
        params.set('map_label', cluster.label);
    }
    const qs = params.toString();
    return qs ? `/search?${qs}` : '/search';
};
