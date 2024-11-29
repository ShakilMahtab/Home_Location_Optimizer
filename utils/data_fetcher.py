import requests
from typing import Dict, List, Tuple
import time

class OSMDataFetcher:
    def __init__(self):
        self.base_url = "https://overpass-api.de/api/interpreter"
        
    def create_query(self, lat: float, lon: float, radius: int, amenity: str) -> str:
        """Create Overpass API query for amenities"""
        return f"""
        [out:json];
        (
          node["amenity"="{amenity}"](around:{radius},{lat},{lon});
          way["amenity"="{amenity}"](around:{radius},{lat},{lon});
          relation["amenity"="{amenity}"](around:{radius},{lat},{lon});
        );
        out center;
        """

    def fetch_amenities(self, lat: float, lon: float, radius: int = 1000) -> Dict[str, List[Tuple[float, float]]]:
        """Fetch nearby amenities from OpenStreetMap"""
        amenities = {
            'bus_station': [],
            'train_station': [],
            'hospital': [],
            'playground': [],
            'water': [],
            'supermarket': []
        }
        
        for amenity_type in amenities.keys():
            query = self.create_query(lat, lon, radius, amenity_type)
            try:
                response = requests.post(self.base_url, data=query)
                if response.status_code == 200:
                    data = response.json()
                    for element in data.get('elements', []):
                        if 'lat' in element and 'lon' in element:
                            amenities[amenity_type].append((element['lat'], element['lon']))
                        elif 'center' in element:
                            amenities[amenity_type].append((element['center']['lat'], 
                                                        element['center']['lon']))
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error fetching {amenity_type}: {str(e)}")
                
        return amenities
