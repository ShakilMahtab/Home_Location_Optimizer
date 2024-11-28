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
        
    def score_location(self, location: Tuple[float, float], 
                      amenities: Dict[str, List[Tuple[float, float]]]) -> Dict:
        """Calculate overall location score"""
        scores = {}
        
        for category, locations in amenities.items():
            scores[category] = self.calculate_distance_score(location, locations)
            
        # Calculate weighted total score
        total_score = sum(scores[category] * self.weights[category] 
                         for category in scores.keys())
                         
        return {
            'total_score': total_score,
            'category_scores': scores
        }
