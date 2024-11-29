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
    distances_text = []
    for amenity, dist in score_info['distances'].items():
        if dist == float('inf'):
            distances_text.append(f"{amenity.replace('_', ' ').title()}: Not found")
        else:
            if amenity == 'transport':
                transport_type = score_info['amenity_types']['transport']
                if transport_type:
                    distances_text.append(
                        f"Transport ({transport_type.replace('_', ' ').title()}): {dist:.2f}km"
                    )
            else:
                distances_text.append(f"{amenity.replace('_', ' ').title()}: {dist:.2f}km")
    
    popup_html = f"""
    <div style='min-width: 200px'>
        <b>Rank #{rank}</b><br>
        Score: {score_info['total_score']:.2f}<br>
        <b>Distances:</b><br>
        {'<br>'.join(distances_text)}
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
                        amenities: Dict[str, List[Tuple[float, float, str]]]) -> folium.Map:
    """Add amenity markers to map"""
    colors = {
        'transport': 'purple',
        'hospital': 'red',
        'playground': 'green',
        'water': 'lightblue',
        'supermarket': 'orange'
    }
    
    icons = {
        'transport': 'exchange',
        'hospital': 'plus',
        'playground': 'tree',
        'water': 'tint',
        'supermarket': 'shopping-cart'
    }
    
    for amenity_type, locations in amenities.items():
        for location in locations:
            lat, lon, specific_type = location
            popup_text = specific_type.replace('_', ' ').title() if amenity_type == 'transport' else amenity_type.replace('_', ' ').title()
            
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color=colors[amenity_type], 
                               icon=icons[amenity_type], 
                               prefix='fa'),
                popup=popup_text
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
