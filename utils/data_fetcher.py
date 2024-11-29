import requests
from typing import Dict, List, Tuple
import time
from geopy.distance import geodesic

class OSMDataFetcher:
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        
    def create_query(self, lat: float, lon: float, radius: int, amenity: str) -> str:
        """Create Overpass API query for amenities"""
        if amenity == 'transport':
            return f"""
            [out:json];
            (
                // Bus stations and stops
                node["highway"="bus_stop"](around:{radius},{lat},{lon});
                way["highway"="bus_stop"](around:{radius},{lat},{lon});
                node["amenity"="bus_station"](around:{radius},{lat},{lon});
                way["amenity"="bus_station"](around:{radius},{lat},{lon});
                
                // Train and subway stations
                node["railway"="station"](around:{radius},{lat},{lon});
                way["railway"="station"](around:{radius},{lat},{lon});
                node["railway"="subway_station"](around:{radius},{lat},{lon});
                way["railway"="subway_station"](around:{radius},{lat},{lon});
            );
            out center;
            """
        elif amenity == 'playground':
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
                node["amenity"="school"](around:{radius},{lat},{lon});
                way["amenity"="school"](around:{radius},{lat},{lon});
                relation["amenity"="school"](around:{radius},{lat},{lon});
                node["amenity"="university"](around:{radius},{lat},{lon});
                way["amenity"="university"](around:{radius},{lat},{lon});
                node["amenity"="college"](around:{radius},{lat},{lon});
                way["amenity"="college"](around:{radius},{lat},{lon});
            );
            out center;
            """
        elif amenity == 'hospital':
            return f"""
            [out:json];
            (
                // Hospitals and medical centers
                node["amenity"="hospital"](around:{radius},{lat},{lon});
                way["amenity"="hospital"](around:{radius},{lat},{lon});
                relation["amenity"="hospital"](around:{radius},{lat},{lon});
                node["amenity"="clinic"](around:{radius},{lat},{lon});
                way["amenity"="clinic"](around:{radius},{lat},{lon});
            );
            out center;
            """
        elif amenity == 'supermarket':
            return f"""
            [out:json];
            (
                // Supermarkets and grocery stores
                node["shop"="supermarket"](around:{radius},{lat},{lon});
                way["shop"="supermarket"](around:{radius},{lat},{lon});
                relation["shop"="supermarket"](around:{radius},{lat},{lon});
                node["shop"="grocery"](around:{radius},{lat},{lon});
                way["shop"="grocery"](around:{radius},{lat},{lon});
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
        """Fetch nearby amenities from OpenStreetMap"""
        amenities = {
            'transport': [],
            'hospital': [],
            'playground': [],
            'water': [],
            'supermarket': [],
            'school': []
        }
        
        # Fetch amenities from OSM
        for amenity_type in amenities.keys():
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