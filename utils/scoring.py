from typing import Dict, List, Tuple
from geopy.distance import geodesic
import numpy as np

class LocationScorer:
    def __init__(self):
        self.weights = {
            'transport': 0.3,
            'hospital': 0.2,
            'playground': 0.15,
            'water': 0.15,
            'supermarket': 0.2
        }
        
    def calculate_distance_score(self, point: Tuple[float, float], 
                               amenities: List[Tuple[float, float, str]], 
                               max_distance: float = 2.0) -> Tuple[float, str]:
        """Calculate score based on distance to amenities"""
        if not amenities:
            return 0.0, None
            
        # Calculate distances and keep track of amenity types
        distances_with_type = [(geodesic(point, (amenity[0], amenity[1])).kilometers, amenity[2]) 
                             for amenity in amenities]
        
        # Find the closest amenity and its type
        closest_distance, amenity_type = min(distances_with_type, key=lambda x: x[0])
        
        if closest_distance > max_distance:
            return 0.0, None
            
        # Inverse distance scoring (closer = better)
        score = 1 - (closest_distance / max_distance)
        return max(0, min(1, score)), amenity_type
        
    def get_combined_distance(self, distances: Dict[str, float]) -> float:
        """Calculate the average distance to all amenities"""
        valid_distances = [d for d in distances.values() if d != float('inf')]
        if not valid_distances:
            return float('inf')
        return sum(valid_distances) / len(valid_distances)

    def score_location(self, location: Tuple[float, float], 
                      amenities: Dict[str, List[Tuple[float, float, str]]]) -> Dict:
        """Calculate scores and distances for individual amenities"""
        scores = {}
        distances = {}
        amenity_types = {}
        
        # Calculate scores and distances for each amenity
        for amenity_type, locations in amenities.items():
            if locations:
                score, closest_type = self.calculate_distance_score(location, locations)
                distances[amenity_type] = min(geodesic(location, (loc[0], loc[1])).kilometers 
                                            for loc in locations)
                scores[amenity_type] = score
                amenity_types[amenity_type] = closest_type
            else:
                distances[amenity_type] = float('inf')
                scores[amenity_type] = 0
                amenity_types[amenity_type] = None
            
        # Calculate total score as weighted average of individual scores
        total_score = sum(scores[amenity] * self.weights[amenity]
                         for amenity in amenities.keys())
        
        combined_distance = self.get_combined_distance(distances)
                         
        return {
            'total_score': total_score,
            'individual_scores': scores,
            'distances': distances,
            'combined_distance': combined_distance,
            'amenity_types': amenity_types
        }
