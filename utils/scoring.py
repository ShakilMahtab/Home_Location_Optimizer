from typing import Dict, List, Tuple
from geopy.distance import geodesic
import numpy as np

class LocationScorer:
    def __init__(self):
        self.weights = {
            'transport': 0.3,
            'family': 0.25,
            'services': 0.25,
            'nature': 0.2
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
        if not distances:
            return float('inf')
        return sum(distances.values()) / len(distances)

    def score_location(self, location: Tuple[float, float], 
                      amenities: Dict[str, List[Tuple[float, float]]]) -> Dict:
        """Calculate overall location score and distances"""
        scores = {}
        distances = {}
        
        for category, locations in amenities.items():
            if locations:
                category_distances = [geodesic(location, amenity).kilometers 
                                   for amenity in locations]
                distances[category] = min(category_distances)
                scores[category] = self.calculate_distance_score(location, locations)
            else:
                distances[category] = float('inf')
                scores[category] = 0
            
        # Calculate weighted total score
        total_score = sum(scores[category] * self.weights[category] 
                         for category in scores.keys())
        
        combined_distance = self.get_combined_distance(distances)
                         
        return {
            'total_score': total_score,
            'category_scores': scores,
            'distances': distances,
            'combined_distance': combined_distance
        }
