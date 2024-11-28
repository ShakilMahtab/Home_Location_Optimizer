import folium
from typing import Dict, List, Tuple
import branca.colormap as cm

def create_base_map(location: Tuple[float, float]) -> folium.Map:
    """Create base map centered on location"""
    return folium.Map(
        location=location,
        zoom_start=14,
        tiles='cartodbpositron'
    )

def add_ranked_location(m: folium.Map, location: Tuple[float, float], 
                       rank: int, score_info: Dict) -> None:
    """Add a ranked location marker to the map"""
    popup_html = f"""
    <div style='min-width: 200px'>
        <b>Rank #{rank}</b><br>
        Score: {score_info['total_score']:.2f}<br>
        <b>Distances:</b><br>
        {'<br>'.join(f"{cat.title()}: {dist:.2f}km" 
                     for cat, dist in score_info['distances'].items())}
    </div>
    """
    
    folium.Marker(
        location,
        popup=popup_html,
        icon=folium.DivIcon(
            html=f'<div style="font-size: 14px; background-color: white; '
                 f'border: 2px solid red; border-radius: 50%; padding: 2px 8px;">{rank}</div>'
        )
    ).add_to(m)

def add_amenities_to_map(m: folium.Map, 
                        amenities: Dict[str, List[Tuple[float, float]]]) -> folium.Map:
    """Add amenity markers to map"""
    colors = {
        'transport': 'blue',
        'family': 'green',
        'services': 'red',
        'nature': 'purple'
    }
    
    icons = {
        'transport': 'train',
        'family': 'home',
        'services': 'plus',
        'nature': 'tree'
    }
    
    for category, locations in amenities.items():
        for lat, lon in locations:
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color=colors[category], 
                               icon=icons[category], 
                               prefix='fa'),
                popup=category.title()
            ).add_to(m)
            
    return m

def create_heatmap(locations: List[Tuple[float, float]], 
                  scores: List[float]) -> folium.Map:
    """Create heatmap layer for scoring visualization"""
    location_center = locations[0]
    m = create_base_map(location_center)
    
    # Create gradient for heatmap
    gradient = {
        0.2: 'blue',
        0.4: 'cyan',
        0.6: 'lime',
        0.8: 'yellow',
        1.0: 'red'
    }
    
    heatmap_data = [[lat, lon, score] for (lat, lon), score 
                    in zip(locations, scores)]
    
    folium.plugins.HeatMap(
        heatmap_data,
        min_opacity=0.3,
        max_val=1.0,
        gradient=gradient,
        radius=25
    ).add_to(m)
    
    return m
