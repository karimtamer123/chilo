from typing import List, Dict, Any, Optional, Tuple
import math
from db import get_chillers_by_criteria, get_available_ambients

class ChillerSelector:
    """Handles chiller selection and ranking logic."""
    
    def __init__(self):
        self.capacity_tolerance_levels = [0.10, 0.125, 0.15, 0.175, 0.20]
    
    def find_best_chillers(self, capacity_tons: float, ambient_f: int, 
                          ewt_c: Optional[float] = None, lwt_c: Optional[float] = None) -> Dict[str, Any]:
        """
        Find the best matching chillers for the given criteria.
        Returns a dictionary with:
        - best_option: The best matching chiller
        - alternatives: Up to 2 alternatives (above/below in capacity)
        - all_matches: All chillers within tolerance
        - search_info: Information about the search parameters used
        - fallback_available: Whether fallback ambients are available
        """
        
        # First, try to find chillers with the exact ambient
        candidates, tolerance_used, search_info = self._find_candidates_with_tolerance(
            capacity_tons, ambient_f, ewt_c, lwt_c
        )
        
        if not candidates:
            # Try fallback ambients
            fallback_results = self._try_fallback_ambients(capacity_tons, ewt_c, lwt_c)
            return {
                'best_option': None,
                'alternatives': [],
                'all_matches': [],
                'search_info': search_info,
                'fallback_available': fallback_results,
                'no_matches': True
            }
        
        # Rank the candidates
        ranked_candidates = self._rank_candidates(candidates, capacity_tons, ewt_c, lwt_c)
        
        if not ranked_candidates:
            return {
                'best_option': None,
                'alternatives': [],
                'all_matches': [],
                'search_info': search_info,
                'fallback_available': False,
                'no_matches': True
            }
        
        # Select best 3 options: closest to capacity, then closest above, closest below
        best_options = self._select_best_3_options(ranked_candidates, capacity_tons)
        
        return {
            'best_option': best_options[0] if best_options else None,
            'alternatives': best_options[1:3] if len(best_options) > 1 else [],
            'all_matches': ranked_candidates,
            'search_info': search_info,
            'fallback_available': False,
            'no_matches': False
        }
    
    def _find_candidates_with_tolerance(self, capacity_tons: float, ambient_f: int,
                                      ewt_c: Optional[float], lwt_c: Optional[float]) -> Tuple[List[Dict], float, Dict]:
        """Find candidates with progressive tolerance widening."""
        
        for tolerance in self.capacity_tolerance_levels:
            candidates = get_chillers_by_criteria(capacity_tons, ambient_f, ewt_c, lwt_c, tolerance)
            
            if candidates:
                cap_min = capacity_tons * (1 - tolerance)
                cap_max = capacity_tons * (1 + tolerance)
                
                search_info = {
                    'capacity_tons': capacity_tons,
                    'ambient_f': ambient_f,
                    'ewt_c': ewt_c,
                    'lwt_c': lwt_c,
                    'tolerance_used': tolerance,
                    'tolerance_percent': tolerance * 100,
                    'capacity_range': (cap_min, cap_max),
                    'candidates_found': len(candidates)
                }
                
                return candidates, tolerance, search_info
        
        # No candidates found even with maximum tolerance
        search_info = {
            'capacity_tons': capacity_tons,
            'ambient_f': ambient_f,
            'ewt_c': ewt_c,
            'lwt_c': lwt_c,
            'tolerance_used': self.capacity_tolerance_levels[-1],
            'tolerance_percent': self.capacity_tolerance_levels[-1] * 100,
            'capacity_range': (capacity_tons * 0.8, capacity_tons * 1.2),
            'candidates_found': 0
        }
        
        return [], self.capacity_tolerance_levels[-1], search_info
    
    def _try_fallback_ambients(self, capacity_tons: float, ewt_c: Optional[float], 
                              lwt_c: Optional[float]) -> List[Dict]:
        """Try to find candidates with fallback ambient temperatures."""
        
        available_ambients = get_available_ambients()
        if not available_ambients:
            return []
        
        fallback_results = []
        
        for ambient in available_ambients:
            candidates, tolerance, _ = self._find_candidates_with_tolerance(
                capacity_tons, ambient, ewt_c, lwt_c
            )
            if candidates:
                fallback_results.append({
                    'ambient_f': ambient,
                    'candidates': candidates,
                    'tolerance_used': tolerance,
                    'count': len(candidates)
                })
        
        return fallback_results
    
    def _rank_candidates(self, candidates: List[Dict], capacity_tons: float,
                        ewt_c: Optional[float], lwt_c: Optional[float]) -> List[Dict]:
        """Rank candidates by capacity delta, temperature score, and efficiency."""
        
        def calculate_ranking_score(chiller):
            # Capacity delta (lower is better)
            cap_delta = abs(chiller.get('capacity_tons', 0) - capacity_tons)
            
            # Temperature score (lower is better)
            temp_score = 0
            if ewt_c is not None and chiller.get('ewt_c') is not None:
                temp_score += abs(chiller['ewt_c'] - ewt_c)
            if lwt_c is not None and chiller.get('lwt_c') is not None:
                temp_score += abs(chiller['lwt_c'] - lwt_c)
            
            # Efficiency (lower is better, but handle nulls)
            efficiency = chiller.get('efficiency_kw_per_ton')
            if efficiency is None:
                efficiency = float('inf')
            
            # Waterflow (prefer higher, but handle nulls)
            waterflow = chiller.get('waterflow_usgpm')
            if waterflow is None:
                waterflow = 0  # Sort nulls last
            
            return (cap_delta, temp_score, efficiency, -waterflow)
        
        # Sort by ranking score
        ranked = sorted(candidates, key=calculate_ranking_score)
        
        # Add ranking metadata
        for i, chiller in enumerate(ranked):
            chiller['_rank'] = i + 1
            chiller['_cap_delta'] = abs(chiller.get('capacity_tons', 0) - capacity_tons)
            chiller['_temp_score'] = 0
            if ewt_c is not None and chiller.get('ewt_c') is not None:
                chiller['_temp_score'] += abs(chiller['ewt_c'] - ewt_c)
            if lwt_c is not None and chiller.get('lwt_c') is not None:
                chiller['_temp_score'] += abs(chiller['lwt_c'] - lwt_c)
        
        return ranked
    
    def _select_best_3_options(self, ranked_candidates: List[Dict], capacity_tons: float) -> List[Dict]:
        """Select the best 3 options: closest to capacity, closest above, closest below."""
        
        if not ranked_candidates:
            return []
        
        # The first candidate is already the best (closest to capacity)
        best_options = [ranked_candidates[0]]
        
        if len(ranked_candidates) <= 1:
            return best_options
        
        best_capacity = ranked_candidates[0].get('capacity_tons', 0)
        
        # Find candidates above and below the best capacity
        above_candidates = [c for c in ranked_candidates[1:] if c.get('capacity_tons', 0) > best_capacity]
        below_candidates = [c for c in ranked_candidates[1:] if c.get('capacity_tons', 0) < best_capacity]
        
        # Add closest above capacity
        if above_candidates:
            best_options.append(above_candidates[0])
        
        # Add closest below capacity
        if below_candidates:
            best_options.append(below_candidates[0])
        
        return best_options[:3]  # Maximum 3 options
    
    def get_search_summary(self, search_info: Dict) -> str:
        """Generate a human-readable search summary."""
        
        cap_min, cap_max = search_info['capacity_range']
        tolerance_pct = search_info['tolerance_percent']
        
        summary_parts = [
            f"Target capacity: {search_info['capacity_tons']:.1f} tons",
            f"Band: ±{tolerance_pct:.1f}% ({cap_min:.1f}–{cap_max:.1f})",
            f"Ambient: {search_info['ambient_f']}°F"
        ]
        
        if search_info['ewt_c'] is not None and search_info['lwt_c'] is not None:
            summary_parts.append(f"EWT/LWT: {search_info['ewt_c']:.1f}/{search_info['lwt_c']:.1f}°C")
        elif search_info['ewt_c'] is not None:
            summary_parts.append(f"EWT: {search_info['ewt_c']:.1f}°C")
        elif search_info['lwt_c'] is not None:
            summary_parts.append(f"LWT: {search_info['lwt_c']:.1f}°C")
        
        summary_parts.append(f"Found: {search_info['candidates_found']} matches")
        
        return " · ".join(summary_parts)
    
    def format_chiller_display(self, chiller: Dict) -> Dict[str, Any]:
        """Format chiller data for display."""
        
        # Main metrics
        capacity = chiller.get('capacity_tons')
        efficiency = chiller.get('efficiency_kw_per_ton')
        waterflow = chiller.get('waterflow_usgpm')
        
        # Temperature info
        ambient = chiller.get('ambient_f')
        ewt = chiller.get('ewt_c')
        lwt = chiller.get('lwt_c')
        
        temp_info = []
        if ambient is not None:
            temp_info.append(f"{ambient}°F")
        if ewt is not None:
            temp_info.append(f"EWT: {ewt:.1f}°C")
        if lwt is not None:
            temp_info.append(f"LWT: {lwt:.1f}°C")
        
        # Detailed info
        details = {
            'model': chiller.get('model', 'Unknown'),
            'manufacturer': chiller.get('manufacturer', 'Unknown'),
            'model_prefix': chiller.get('model_prefix', 'Unknown'),
            'folder_name': chiller.get('folder_name', 'Unknown'),
            'unit_kw': chiller.get('unit_kw'),
            'compressor_kw': chiller.get('compressor_kw'),
            'fan_kw': chiller.get('fan_kw'),
            'iplv_kw_per_ton': chiller.get('iplv_kw_per_ton'),
            'mca_amps': chiller.get('mca_amps'),
            'pressure_drop_psi': chiller.get('pressure_drop_psi'),
            'pressure_drop_ftwg': chiller.get('pressure_drop_ftwg'),
            'length_in': chiller.get('length_in'),
            'width_in': chiller.get('width_in'),
            'height_in': chiller.get('height_in'),
            'notes': chiller.get('notes'),
            'extras_json': chiller.get('extras_json')
        }
        
        return {
            'capacity_tons': capacity,
            'efficiency_kw_per_ton': efficiency,
            'waterflow_usgpm': waterflow,
            'temp_info': ' / '.join(temp_info) if temp_info else 'Unknown',
            'details': details,
            'id': chiller.get('id')
        }
