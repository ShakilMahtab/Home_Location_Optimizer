import requests
import os
import googlemaps
from typing import Dict, List, Tuple
import time
from geopy.distance import geodesic

class GooglePlacesFetcher:
    def __init__(self):
        self.gmaps = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])
        self.type_mapping = {
            'transport': ['transit_station', 'bus_station', 'train_station', 'subway_station'],
            'hospital': ['hospital'],
            'playground': ['park'],
            'water': [],  # Natural features not well-supported in Places API
            'supermarket': ['supermarket', 'grocery_or_supermarket'],
            'school': ['school', 'primary_school', 'secondary_school']
        }
        
    def fetch_places(self, lat: float, lon: float, radius: int, amenity_type: str) -> List[Tuple[float, float, str]]:
        """Fetch places from Google Places API"""
        results = []
        place_types = self.type_mapping.get(amenity_type, [])
        
        if not place_types:  # Skip if no mapping exists
            return results
            
        for place_type in place_types:
            try:
                places = self.gmaps.places_nearby(
                    location=(lat, lon),
                    radius=radius,
                    type=place_type
                )
                
                for place in places.get('results', []):
                    location = place['geometry']['location']
                    name = place.get('name', place_type)
                    results.append((
                        location['lat'],
                        location['lng'],
                        f"{name} ({place_type})"
                    ))
                
                # Handle pagination if necessary
                while 'next_page_token' in places:
                    time.sleep(2)  # Required delay between requests
                    places = self.gmaps.places_nearby(
                        location=(lat, lon),
                        radius=radius,
                        type=place_type,
                        page_token=places['next_page_token']
                    )
                    for place in places.get('results', []):
                        location = place['geometry']['location']
                        name = place.get('name', place_type)
                        results.append((
                            location['lat'],
                            location['lng'],
                            f"{name} ({place_type})"
                        ))
                
            except Exception as e:
                print(f"Error fetching from Google Places API for {place_type}: {str(e)}")
                continue
            
            time.sleep(2)  # Rate limiting between different place types
            
        return results

class OSMDataFetcher:
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        self.google_fetcher = GooglePlacesFetcher()
        
    def create_query(self, lat: float, lon: float, radius: int, amenity: str) -> str:
        """Create Overpass API query for amenities"""
        if amenity == 'playground':
            return f"""
            [out:json];
            (
                // Sports grounds and pitches larger than 100m
                way["leisure"="pitch"]["way_area">10000](around:{radius},{lat},{lon});
                relation["leisure"="pitch"]["way_area">10000](around:{radius},{lat},{lon});
                way["leisure"="sports_centre"]["way_area">10000](around:{radius},{lat},{lon});
                relation["leisure"="sports_centre"]["way_area">10000](around:{radius},{lat},{lon});
                
                // Parks larger than 100m
                way["leisure"="park"]["way_area">10000](around:{radius},{lat},{lon});
                relation["leisure"="park"]["way_area">10000](around:{radius},{lat},{lon});
            );
            out center;
            """
        elif amenity == 'water':
            return f'''
            [out:json];
            (
                // Rivers and waterways without size restriction
                way["waterway"="river"](around:{radius},{lat},{lon});
                relation["waterway"="river"](around:{radius},{lat},{lon});
                way["waterway"="canal"](around:{radius},{lat},{lon});
                
                // River banks and edges
                way["natural"="water"]["water"="river"](around:{radius},{lat},{lon});
                way["waterway"="riverbank"](around:{radius},{lat},{lon});
                
                // Lakes and large water bodies
                way["natural"="water"]["water"="lake"](around:{radius},{lat},{lon});
                relation["natural"="water"]["water"="lake"](around:{radius},{lat},{lon});
                
                // Ocean and coastal features
                way["natural"="coastline"](around:{radius},{lat},{lon});
                way["natural"="bay"](around:{radius},{lat},{lon});
                way["water"="ocean"](around:{radius},{lat},{lon});
            );
            out center;
            '''
        elif amenity == 'school':
            return f"""
            [out:json];
            (
                // Schools and educational institutions
                way["amenity"="school"](around:{radius},{lat},{lon});
                relation["amenity"="school"](around:{radius},{lat},{lon});
                way["building"="school"](around:{radius},{lat},{lon});
                relation["building"="school"](around:{radius},{lat},{lon});
            );
            out center;
            """
        else:
            return f"""
            [out:json];
            (
              node["amenity"="{amenity}"](around:{radius},{lat},{lon});
              way["amenity"="{amenity}"](around:{radius},{lat},{lon});
              relation["amenity"="{amenity}"](around:{radius},{lat},{lon});
            );
            out center;
            """

    def fetch_amenities(self, lat: float, lon: float, radius: int = 1000) -> Dict[str, List[Tuple[float, float, str]]]:
        """Fetch nearby amenities from both OpenStreetMap and Google Places"""
        amenities = {
            'transport': [],
            'hospital': [],
            'playground': [],
            'water': [],
            'supermarket': [],
            'school': []
        }
        
        # Fetch from Google Places API first
        for amenity_type in amenities.keys():
            google_results = self.google_fetcher.fetch_places(lat, lon, radius, amenity_type)
            amenities[amenity_type].extend(google_results)
        
        # Fetch transport locations from OSM
        transport_types = ['bus_station', 'train_station']
        for transport_type in transport_types:
            query = self.create_query(lat, lon, radius, transport_type)
            try:
                response = requests.post(self.base_url, data=query)
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get('elements', []):
                        if 'lat' in element and 'lon' in element:
                            amenities['transport'].append((element['lat'], element['lon'], transport_type))
                        elif 'center' in element:
                            amenities['transport'].append((
                                element['center']['lat'],
                                element['center']['lon'],
                                transport_type
                            ))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {transport_type} from OSM: {str(e)}")

        # Fetch other amenities from OSM
        other_amenities = ['hospital', 'playground', 'water', 'supermarket', 'school']
        for amenity_type in other_amenities:
            query = self.create_query(lat, lon, radius, amenity_type)
            try:
                response = requests.post(self.base_url, data=query)
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get('elements', []):
                        if 'lat' in element and 'lon' in element:
                            amenities[amenity_type].append((
                                element['lat'],
                                element['lon'],
                                f"OSM {amenity_type}"
                            ))
                        elif 'center' in element:
                            amenities[amenity_type].append((
                                element['center']['lat'],
                                element['center']['lon'],
                                f"OSM {amenity_type}"
                            ))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {amenity_type} from OSM: {str(e)}")
        
        # Remove duplicates based on proximity (within 50 meters)
        for amenity_type in amenities:
            unique_locations = []
            for loc in amenities[amenity_type]:
                is_duplicate = False
                for existing_loc in unique_locations:
                    distance = geodesic((loc[0], loc[1]), (existing_loc[0], existing_loc[1])).meters
                    if distance < 50:  # Consider locations within 50m as duplicates
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_locations.append(loc)
            amenities[amenity_type] = unique_locations
                
        return amenities
