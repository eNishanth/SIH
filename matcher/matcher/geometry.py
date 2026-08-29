"""
geometry.py
Small pure-python polygon toolkit — no shapely, no numpy.
Everything here works on a "ring": a list of [x, y] points (lon, lat degrees,
or already-projected meters — the functions don't care, as long as both
inputs to a comparison use the same units).

What's here:
    project_ring(ring, ref_lat)   -> ring in local meters (equirectangular approx)
    ring_area(ring)               -> shoelace area (always positive)
    ring_centroid(ring)           -> (x, y) centroid of the ring's vertices
    clip_polygon(subject, clip)   -> Sutherland-Hodgman intersection polygon
    intersection_area(a, b)       -> area of a ^ b
    iou(a, b)                     -> intersection-over-union of two rings
    planar_distance(p1, p2)       -> straight-line distance between two points

LIMITATION (documented, not hidden): Sutherland-Hodgman clipping is only
exact when `clip` is convex. Cadastral parcels and building footprints are
*usually* close enough to convex (rectangles, simple quads) that this is a
reasonable approximation for a v0 tool — but a slim, concave, L-shaped
parcel can give a slightly wrong intersection. Good enough to flag "this
pair looks off", not good enough for legal survey work.
"""
import math


def _outer_ring(coordinates):
    """Pull the exterior ring out of GeoJSON-style nested coordinates.

    Handles:
      Polygon:      [[[x,y], [x,y], ...], [hole...]]   -> returns coordinates[0]
      MultiPolygon: [[[[x,y], ...]], [[[x,y], ...]]]    -> returns first poly's outer ring
      Already-flat: [[x,y], [x,y], ...]                 -> returned as-is
    Holes are ignored (v0 doesn't subtract them out).
    """
    if not coordinates:
        return []
    c = coordinates
    # Drill down until we hit a list of [num, num] pairs.
    while c and isinstance(c[0], list) and c[0] and isinstance(c[0][0], list):
        c = c[0]
    return c


def project_ring(ring, ref_lat):
    """Equirectangular projection: lon/lat degrees -> local meters.

    Good enough for a single parcel/building footprint (tens of meters
    across). Not meant for anything spanning a large area.
    """
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(ref_lat))
    return [(lon * m_per_deg_lon, lat * m_per_deg_lat) for lon, lat in ring]


def ring_area(ring):
    """Shoelace formula. Returns 0 for degenerate rings (<3 points)."""
    if len(ring) < 3:
        return 0.0
    total = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def ring_centroid(ring):
    if not ring:
        return (0.0, 0.0)
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def _inside(p, a, b):
    """Is point p on the 'inside' (left) side of clip edge a->b?"""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0


def _edge_intersect(p1, p2, a, b):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = a
    x4, y4 = b
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-12:
        return p2  # parallel; degenerate, just return an endpoint
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def clip_polygon(subject, clip):
    """Sutherland-Hodgman: clip `subject` ring against convex `clip` ring."""
    if len(subject) < 3 or len(clip) < 3:
        return []
    output = subject
    cn = len(clip)
    for i in range(cn):
        a, b = clip[i], clip[(i + 1) % cn]
        if not output:
            break
        input_list = output
        output = []
        n = len(input_list)
        for j in range(n):
            cur = input_list[j]
            prev = input_list[j - 1]
            cur_in = _inside(cur, a, b)
            prev_in = _inside(prev, a, b)
            if cur_in:
                if not prev_in:
                    output.append(_edge_intersect(prev, cur, a, b))
                output.append(cur)
            elif prev_in:
                output.append(_edge_intersect(prev, cur, a, b))
    return output


def intersection_area(ring_a, ring_b):
    return ring_area(clip_polygon(ring_a, ring_b))


def iou(ring_a, ring_b):
    """Intersection-over-union. 0 if either ring is degenerate or disjoint."""
    area_a = ring_area(ring_a)
    area_b = ring_area(ring_b)
    if area_a == 0 or area_b == 0:
        return 0.0
    inter = intersection_area(ring_a, ring_b)
    union = area_a + area_b - inter
    if union <= 0:
        return 0.0
    return max(0.0, min(1.0, inter / union))


def planar_distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
