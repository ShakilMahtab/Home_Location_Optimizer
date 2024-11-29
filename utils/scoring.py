from typing import Dict, List, Tuple
from geopy.distance import geodesic
import numpy as np

class LocationScorer:
    def __init__(self):
        self.weights = {
            'bus_station': 0.15,
            'train_station': 0.15,
            'hospital': 0.2,
            'playground': 0.15,
            'water': 0.15,
            'supermarket': 0.2
        }
        
    def calculate_distance_score(self, point: Tuple[float, float], 
                               amenities: List[Tuple[float, float]], 
                               max_distance: float = 2.0) -> float:
        """Calculate score based on distance to amenities"""
        if not amenities:
            return 0.0
            
        distances = [geodesic(point, amenity).kilometers for amenity in amenities]
        closest_distance = min(distances)
        
        if closest_distance > max_distance:
            return 0.0
            
        # Inverse distance scoring (closer = better)
        score = 1 - (closest_distance / max_distance)
        return max(0, min(1, score))
        
    def get_combined_distance(self, distances: Dict[str, float]) -> float:
        """Calculate the average distance to all amenities"""
        valid_distances = [d for d in distances.values() if d != float('inf')]
        if not valid_distances:
            return float('inf')
        return sum(valid_distances) / len(valid_distances)

    def score_location(self, location: Tuple[float, float], 
                      amenities: Dict[str, List[Tuple[float, float]]]) -> Dict:
        """Calculate scores and distances for individual amenities"""
        scores = {}
        distances = {}
        
        # Calculate scores and distances for each amenity
        for amenity_type, locations in amenities.items():
            if locations:
                amenity_distances = [geodesic(location, amenity).kilometers 
                                  for amenity in locations]
                distances[amenity_type] = min(amenity_distances)
                scores[amenity_type] = self.calculate_distance_score(location, locations)
            else:
                distances[amenity_type] = float('inf')
                scores[amenity_type] = 0
            
        # Calculate total score as weighted average of individual scores
        total_score = sum(scores[amenity] * self.weights[amenity]
                         for amenity in amenities.keys())
        
        combined_distance = self.get_combined_distance(distances)
                         
        return {
            'total_score': total_score,
            'individual_scores': scores,
            'distances': distances,
            'combined_distance': combined_distance
        }