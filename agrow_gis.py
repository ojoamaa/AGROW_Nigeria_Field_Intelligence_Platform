"""AGROWNova administrative boundary maps. No farm GPS coordinates are inferred.

State focus uses the selected feature's own geographic extent, not Nigeria's.
Requires gis_data/NGA_ADM1.geojson and (for LGA) NGA_ADM2.geojson.
"""
import json
import math
from functools import lru_cache
from pathlib import Path
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'gis_data'


def canonical(value):
    s = ' '.join(str(value or '').casefold().replace('_', ' ').replace('-', ' ').split())
    aliases = {'fct': 'federal capital territory', 'abuja': 'federal capital territory',
               'federal capital territory abuja': 'federal capital territory',
               'abuja federal capital territory': 'federal capital territory',
               'nasarawa': 'nassarawa', 'akwa-ibom': 'akwa ibom'}
    return aliases.get(s, s)


@lru_cache(maxsize=2)
def load_layer(level):
    if level not in ('ADM1', 'ADM2'):
        raise ValueError('Invalid administrative level')
    path = DATA / f'NGA_{level}.geojson'
    if not path.is_file():
        return None
    with path.open(encoding='utf-8') as file:
        obj = json.load(file)
    if obj.get('type') != 'FeatureCollection' or not isinstance(obj.get('features'), list):
        raise ValueError(f'Invalid GeoJSON FeatureCollection: {path}')
    return obj


def feature_name(feature):
    p = feature.get('properties') or {}
    for key in ('shapeName', 'ADM2_EN', 'ADM1_EN', 'admin2Name', 'admin1Name', 'NAME_2', 'NAME_1', 'name', 'Name'):
        if p.get(key):
            return str(p[key])
    return ''


def _points(coords):
    if isinstance(coords, (list, tuple)):
        if len(coords) >= 2 and all(isinstance(v, (int, float)) for v in coords[:2]):
            if all(math.isfinite(v) for v in coords[:2]):
                yield (float(coords[0]), float(coords[1]))
        else:
            for item in coords:
                yield from _points(item)


def _bounds(features):
    points = (pt for f in features for pt in _points((f.get('geometry') or {}).get('coordinates', [])))
    xs, ys = [], []
    for x, y in points:
        xs.append(x); ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _rings(geometry):
    """Yield outer and inner rings from Polygon/MultiPolygon GeoJSON."""
    kind = (geometry or {}).get('type')
    coords = (geometry or {}).get('coordinates') or []
    polygons = [coords] if kind == 'Polygon' else coords if kind == 'MultiPolygon' else []
    for polygon in polygons:
        for ring in polygon:
            if len(ring) >= 4:
                yield ring



def _outer_rings(geometry):
    """Outer rings only; holes must not be considered label regions."""
    kind = (geometry or {}).get('type')
    coords = (geometry or {}).get('coordinates') or []
    polygons = [coords] if kind == 'Polygon' else coords if kind == 'MultiPolygon' else []
    for polygon in polygons:
        if polygon and len(polygon[0]) >= 4:
            yield polygon[0]


def _label_anchor(geometry):
    """Find a point inside the largest polygon using horizontal interior spans.

    This is more reliable for concave boundaries than a bounding-box centre.
    """
    candidates = []
    for ring in _outer_rings(geometry):
        pts = [(float(p[0]), float(p[1])) for p in ring]
        signed_twice_area = sum(
            x1 * y2 - x2 * y1
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1])
        )
        candidates.append((abs(signed_twice_area), pts))
    if not candidates:
        return None
    _, pts = max(candidates, key=lambda pair: pair[0])
    ys = [p[1] for p in pts]
    low, high = min(ys), max(ys)
    best = None
    for fraction in (0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8):
        y = low + (high - low) * fraction
        xs = []
        for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for left, right in zip(xs[::2], xs[1::2]):
            if best is None or right - left > best[0]:
                best = (right - left, (left + right) / 2, y)
    if best:
        return best[1], best[2]
    return pts[0]


def _short_label(name, level, focused):
    """Compact visible labels; full official names remain in hover text."""
    if canonical(name) == 'federal capital territory':
        return 'FCT' if not focused else 'FCT · ABUJA'
    if level == 'ADM1':
        return name.replace(' State', '').strip()
    return name


def _draw(features, counts=None, selection=None, height=510, title=None, level="ADM1", metrics=None):
    """Native Plotly vector geometry: no geo projection or external map tiles.

    Geographic coordinates are rendered directly with a fixed aspect ratio,
    which prevents the tiny-state projection issue.
    """
    import plotly.graph_objects as go
    fig = go.Figure()
    counts = counts or {}
    metrics = metrics or {}
    selected = canonical(selection)
    focused = len(features) == 1
    label_positions = []
    for feature in features:
        name = feature_name(feature)
        if not name:
            continue
        count = int(counts.get(canonical(name), 0))
        m = metrics.get(canonical(name), {})
        # State-level intelligence, not individual farm GPS evidence.
        hover = (
            f"<b>{name}</b><br>Registered farmers: {count:,}"
            f"<br>Declared land: {float(m.get('Land_Ha', 0)):,.1f} ha"
            f"<br>Measured land: {float(m.get('measured_land_ha', 0)):,.1f} ha"
            f"<br>Measurement coverage: {float(m.get('Measurement_Coverage_Pct', 0)):.1f}%"
            f"<br>LGAs: {int(m.get('LGAs', 0)):,}"
            f"<br>Commodities: {int(m.get('Commodities', 0)):,}"
            f"<br>Youth (18–35): {int(m.get('Youth', 0)):,} ({float(m.get('Youth_Pct', 0)):.1f}%)"
        )
        active = bool(selected and canonical(name) == selected)
        dimmed = bool(selected and not active)
        fill = '#176747' if active else '#E6EBE9' if dimmed else '#B6DCCB' if count else '#E7EEEC'
        outline = '#0D513A' if active else '#C2CECA' if dimmed else '#75978A'
        # A separate trace per polygon avoids unwanted connections across islands.
        for ring in _rings(feature.get('geometry')):
            fig.add_trace(go.Scatter(
                x=[p[0] for p in ring], y=[p[1] for p in ring],
                mode='lines', fill='toself', fillcolor=fill,
                line=dict(color=outline, width=2.6 if active else 1.05),
                name=name, hovertext=name, customdata=[count] * len(ring),
                hovertemplate=hover + '<extra></extra>',
                showlegend=False, selectedpoints=None,
            ))
        anchor = _label_anchor(feature.get('geometry'))
        if anchor is not None:
            label_positions.append((anchor, name, count, active, hover))
    # Invisible-but-hit-testable centre markers restore reliable hover/click selection.
    # Polygon line traces alone are only hoverable at boundaries.
    if label_positions:
        fig.add_trace(go.Scatter(
            x=[p[0][0] for p in label_positions],
            y=[p[0][1] for p in label_positions],
            mode='markers',
            marker=dict(size=22 if focused else 16, color='rgba(0,0,0,0.005)',
                        line=dict(width=0)),
            hovertext=[p[1] for p in label_positions],
            customdata=[[p[2], p[4]] for p in label_positions],
            hovertemplate='%{customdata[1]}<extra></extra>',
            showlegend=False, name='State selection targets',
        ))
        # Text layer: selection is bold; nonselected labels recede.
        for anchor, name, count, active, hover in label_positions:
            dimmed = bool(selected and not active)
            fig.add_trace(go.Scatter(
                x=[anchor[0]], y=[anchor[1]], mode='text',
                text=[('<b>' + _short_label(name, level, focused) + '</b>') if active
                      else _short_label(name, level, focused)],
                textposition='middle center',
                textfont=dict(family='Arial, sans-serif',
                              size=14 if active else 11 if focused else 9,
                              color='#FFFFFF' if active else '#9CAAA4' if dimmed else '#123E30'),
                hovertext=[name], customdata=[count],
                hovertemplate=hover + '<extra></extra>',
                showlegend=False, name=name, cliponaxis=True,
            ))
    bounds = _bounds(features)
    if not bounds:
        return None
    west, south, east, north = bounds
    dx = max(east - west, 0.04)
    dy = max(north - south, 0.04)
    # Geographical aspect correction: longitude degrees shrink with latitude.
    import math
    ratio = max(math.cos(math.radians((south+north)/2)), 0.3)
    fig.update_xaxes(visible=False, range=[west - dx*.12, east + dx*.12],
                     constrain='domain')
    fig.update_yaxes(visible=False, range=[south - dy*.12, north + dy*.12],
                     scaleanchor='x', scaleratio=1/ratio, constrain='domain')
    fig.update_layout(
        height=height, margin=dict(l=12, r=12, t=24, b=12),
        plot_bgcolor='#F4F8F6', paper_bgcolor='#FFFFFF',
        dragmode='pan', hovermode='closest', clickmode='event+select',
        font=dict(family='Arial, sans-serif', color='#173E31'),
        annotations=[dict(x=.01,y=1.02,xref='paper',yref='paper',showarrow=False,
                          text=title or 'ADMINISTRATIVE BOUNDARIES',
                          font=dict(size=11,color='#4C6B5D'),xanchor='left')],
    )
    return fig


def state_map(agg, selected=None):
    """Compatible interface: (figure, feature-ID map)."""
    layer = load_layer('ADM1')
    if not layer:
        return None, {}
    features = [f for f in layer['features'] if f.get('geometry') and feature_name(f)]
    if not features:
        return None, {}
    selection = canonical(selected)
    focused = selection not in ('', 'all nigeria', 'all programme states')
    matching = [f for f in features if canonical(feature_name(f)) == selection]
    # Keep all states in view; selected one is emphasized and others are muted.
    # This supports click-to-select and reset without changing map extent.
    counts = {}
    metrics = {}
    if agg is not None:
        for _, row in agg.iterrows():
            key = canonical(row['State'])
            counts[key] = int(row['Farmers'])
            metrics[key] = {field: row.get(field, 0) for field in ('Land_Ha', 'measured_land_ha', 'Measurement_Coverage_Pct', 'LGAs', 'Commodities', 'Youth', 'Youth_Pct')}
    figure = _draw(features, counts, selection if focused else None, metrics=metrics,
                   title='SELECTED STATE · CLICK ANOTHER STATE TO COMPARE' if focused else 'NIGERIA · STATE BOUNDARIES')
    ids = {str(i): feature_name(f) for i, f in enumerate(features)}
    return figure, ids


def lga_map(state, selected_lga=None):
    """Display LGA polygons only where parent-state attribution is reliable."""
    layer = load_layer('ADM2')
    if not layer:
        return None
    features = []
    for feature in layer['features']:
        props = feature.get('properties') or {}
        parent = next((props[key] for key in
                       ('ADM1_EN', 'admin1Name', 'NAME_1', 'state', 'State')
                       if props.get(key)), None)
        if parent and canonical(parent) == canonical(state) and feature.get('geometry'):
            features.append(feature)
    if not features:
        return None
    return _draw(features, selection=selected_lga, height=480,
                 title=f'{state.upper()} · LGA BOUNDARIES', level='ADM2')
