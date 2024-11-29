import streamlit as st
from streamlit_folium import folium_static
import numpy as np
from streamlit_folium import st_folium
from utils.data_fetcher import OSMDataFetcher
from utils.scoring import LocationScorer
from utils.map_utils import create_base_map, add_amenities_to_map, add_ranked_location
from geopy.geocoders import Nominatim

# Initialize services
geocoder = Nominatim(user_agent="location_optimizer")
data_fetcher = OSMDataFetcher()
scorer = LocationScorer()

# Page configuration
st.set_page_config(
    page_title="Location Optimizer",
    page_icon="🏠",
    layout="wide"
)

# Title and description
st.title("🏠 Location Optimizer")
st.markdown("""
Find the perfect location based on proximity to important amenities.
Use the sidebar to set your preferences and search for locations.
""")

# Sidebar filters
st.sidebar.header("Search Parameters")

# Location input
location_search = st.sidebar.text_input(
    "Search Location",
    "New York, NY"
)

# Search radius
radius = st.sidebar.slider(
    "Search Radius (km)",
    0.5, 5.0, 2.0,
    step=0.5
) * 1000  # Convert to meters

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Location Map")
    
    if location_search:
        location = geocoder.geocode(location_search)
        if location is None:
            st.error("Location not found. Please try a different search term.")
        else:
            center_lat, center_lon = location.latitude, location.longitude
            st.write(f"📍 Showing results for: {location.address}")
            
            # Fetch amenities
            amenities = data_fetcher.fetch_amenities(
                center_lat, 
                center_lon, 
                radius=int(radius)
            )
            
            # Generate potential locations in a grid
            grid_size = 10
            lat_step = radius / 111000  # Convert meters to approx. degrees
            lon_step = radius / (111000 * np.cos(np.radians(center_lat)))
            
            potential_locations = []
            for i in range(-grid_size, grid_size + 1):
                for j in range(-grid_size, grid_size + 1):
                    lat = center_lat + (i * lat_step)
                    lon = center_lon + (j * lon_step)
                    potential_locations.append((lat, lon))
            
            # Score all locations
            location_scores = []
            for loc in potential_locations:
                score_info = scorer.score_location(loc, amenities)
                location_scores.append((loc, score_info))
            
            # Sort locations by total score
            location_scores.sort(key=lambda x: (-x[1]['total_score'], x[1]['combined_distance']))
            
            # Create map with top 5 locations
            m = create_base_map((center_lat, center_lon))
            m = add_amenities_to_map(m, amenities)
            
            # Add ranked markers for top 5 locations
            top_locations = location_scores[:5]
            for rank, (location, score_info) in enumerate(top_locations, 1):
                add_ranked_location(m, location, rank, score_info)
            
            # Display map
            st_folium(m, width=800)
            
            # Display scores
            with col2:
                st.subheader("Top 5 Locations")
                
                for rank, (location, score_info) in enumerate(top_locations, 1):
                    with st.expander(f"Rank #{rank} - Score: {score_info['total_score']:.2f}"):
                        st.write("Distances to amenities:")
                        
                        # Display transport information
                        transport_distance = score_info['distances']['transport']
                        transport_type = score_info['amenity_types']['transport']
                        transport_score = score_info['individual_scores']['transport']
                        
                        if transport_distance == float('inf'):
                            st.write("Transport: Not found")
                        else:
                            st.write(f"Transport ({transport_type.replace('_', ' ').title()}): "
                                   f"{transport_distance:.2f}km (Score: {transport_score:.2f})")
                        
                        # Display other amenities
                        for amenity in ['hospital', 'playground', 'water', 'supermarket']:
                            distance = score_info['distances'][amenity]
                            if distance == float('inf'):
                                st.write(f"{amenity.replace('_', ' ').title()}: Not found")
                            else:
                                score = score_info['individual_scores'][amenity]
                                st.write(f"{amenity.replace('_', ' ').title()}: "
                                       f"{distance:.2f}km (Score: {score:.2f})")
                        
                        if score_info['combined_distance'] != float('inf'):
                            st.write(f"\nCombined distance: {score_info['combined_distance']:.2f}km")
    else:
        st.info("Enter a location to begin your search")
