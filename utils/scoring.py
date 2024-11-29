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
        self.minimum_amenities = {
            'transport': 1,
            'family': 1,
            'services': 1,
            'nature': 0  # Nature is optional
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
        """Calculate overall location score and distances with improved missing amenities handling"""
        scores = {}
        distances = {}
        missing_amenities = []
        available_weight_total = 0
        
        # First pass: identify missing required amenities and calculate available weight
        for category, locations in amenities.items():
            if not locations and self.minimum_amenities[category] > 0:
                missing_amenities.append(category)
            else:
                available_weight_total += self.weights[category]

        # If we're missing any required amenities, return a zero score
        if missing_amenities:
            return {
                'total_score': 0,
                'category_scores': {cat: 0 for cat in amenities.keys()},
                'distances': {cat: float('inf') for cat in amenities.keys()},
                'combined_distance': float('inf'),
                'missing_required_amenities': missing_amenities
            }

        # Normalize remaining weights
        adjusted_weights = {
            cat: (self.weights[cat] / available_weight_total) 
            for cat in amenities.keys() 
            if cat not in missing_amenities
        }
        
        # Calculate scores and distances
        for category, locations in amenities.items():
            if locations:
                category_distances = [geodesic(location, amenity).kilometers 
                                   for amenity in locations]
                distances[category] = min(category_distances)
                scores[category] = self.calculate_distance_score(location, locations)
            else:
                distances[category] = float('inf')
                scores[category] = 0
            
        # Calculate weighted total score using adjusted weights
        total_score = sum(scores[category] * adjusted_weights.get(category, 0)
                         for category in scores.keys())
        
        combined_distance = self.get_combined_distance({
            k: v for k, v in distances.items() 
            if v != float('inf')
        })
                         
        return {
            'total_score': total_score,
            'category_scores': scores,
            'distances': distances,
            'combined_distance': combined_distance,
            'adjusted_weights': adjusted_weights,
            'missing_amenities': missing_amenities
        }
