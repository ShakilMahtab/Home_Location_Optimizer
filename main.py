import streamlit as st
import folium
from streamlit_folium import folium_static
from utils.data_fetcher import OSMDataFetcher
from utils.scoring import LocationScorer
from utils.map_utils import create_base_map, add_amenities_to_map
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
Find the perfect location based on your preferences for amenities and services.
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
            
            # Create map
            m = create_base_map((center_lat, center_lon))
            m = add_amenities_to_map(m, amenities)
            
            # Calculate score
            score_result = scorer.score_location(
                (center_lat, center_lon),
                amenities
            )
            
            # Display map
            folium_static(m)
            
            # Display scores
            with col2:
                st.subheader("Location Score")
                
                # Total score
                st.metric(
                    "Overall Score",
                    f"{score_result['total_score']:.2f}/1.00"
                )
                
                # Detailed breakdown
                st.subheader("Nearby Amenities")
                for category, locations in amenities.items():
                    st.write(f"{category.title()}: {len(locations)} found")
    else:
        st.info("Enter a location to begin your search")