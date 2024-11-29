import requests
from typing import Dict, List, Tuple
import time
from geopy.distance import geodesic

class OSMDataFetcher:
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        
    def create_query(self, lat: float, lon: float, radius: int, amenity: str) -> str:
        """Create Overpass API query for amenities"""
        if amenity == 'playground':
            return f"""
            [out:json];
            (
              node["amenity"="playground"](around:{radius},{lat},{lon});
              way["amenity"="playground"](around:{radius},{lat},{lon});
              relation["amenity"="playground"](around:{radius},{lat},{lon});
              node["leisure"="park"](around:{radius},{lat},{lon});
              way["leisure"="park"](around:{radius},{lat},{lon});
              node["leisure"="pitch"](around:{radius},{lat},{lon});
              way["leisure"="pitch"](around:{radius},{lat},{lon});
              node["leisure"="sports_centre"](around:{radius},{lat},{lon});
              way["leisure"="sports_centre"](around:{radius},{lat},{lon});
            );
            out center;
            """
        elif amenity == 'water':
            return f"""
            [out:json];
            (
                // Lakes and ponds larger than 50m
                way["natural"="water"]["way_area">2500](around:{radius},{lat},{lon});
                relation["natural"="water"]["way_area">2500](around:{radius},{lat},{lon});
                
                // Rivers wider than 50m
                way["waterway"="river"]["width">50](around:{radius},{lat},{lon});
                way["waterway"="river"]["width:minimum">50](around:{radius},{lat},{lon});
                
                // Coastline (always large)
                way["natural"="coastline"](around:{radius},{lat},{lon});
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
            'supermarket': []
        }
        
        # Fetch bus and train stations separately but combine them
        transport_types = ['bus_station', 'train_station']
        transport_locations = []
        
        for transport_type in transport_types:
            query = self.create_query(lat, lon, radius, transport_type)
            try:
                response = requests.post(self.base_url, data=query)
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get('elements', []):
                        if 'lat' in element and 'lon' in element:
                            transport_locations.append((element['lat'], element['lon'], transport_type))
                        elif 'center' in element:
                            transport_locations.append((element['center']['lat'], 
                                                     element['center']['lon'], 
                                                     transport_type))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {transport_type}: {str(e)}")

        # Find closest transport location for the target coordinates
        if transport_locations:
            amenities['transport'] = transport_locations

        # Fetch other amenities
        other_amenities = ['hospital', 'playground', 'water', 'supermarket']
        for amenity_type in other_amenities:
            query = self.create_query(lat, lon, radius, amenity_type)
            try:
                response = requests.post(self.base_url, data=query)
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get('elements', []):
                        if 'lat' in element and 'lon' in element:
                            amenities[amenity_type].append((element['lat'], element['lon'], amenity_type))
                        elif 'center' in element:
                            amenities[amenity_type].append((element['center']['lat'], 
                                                         element['center']['lon'],
                                                         amenity_type))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {amenity_type}: {str(e)}")
                
        return amenities
