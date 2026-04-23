"""Hybrid ranking system for grant/tender matching."""

import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TenderRanker:
    """Hybrid ranker combining TF-IDF similarity with business rules."""
    
    def __init__(self, tenders: List[Dict]):
        """Initialize ranker with tenders and build TF-IDF index."""
        self.tenders = tenders
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words=None,
            sublinear_tf=True
        )
        self._build_index()
    
    def _build_index(self):
        """Build TF-IDF index from tender texts."""
        tender_texts = [self._prepare_tender_text(t) for t in self.tenders]
        self.tfidf_matrix = self.vectorizer.fit_transform(tender_texts)
        self.feature_names = self.vectorizer.get_feature_names_out()
    
    def _prepare_tender_text(self, tender: Dict) -> str:
        """Prepare tender text for TF-IDF indexing."""
        parts = [
            tender.get('title', ''),
            tender.get('sector', ''),
            tender.get('text', '')[:3000]
        ]
        return ' '.join(parts).lower()
    
    def _prepare_profile_query(self, profile: Dict) -> str:
        """Prepare profile query for TF-IDF similarity."""
        needs = profile.get('needs_text', '')
        sector = profile.get('sector', '')
        # Repeat sector for emphasis
        return f"{needs} {sector} {sector} {needs[:500]}"
    
    def rank(self, profile: Dict, top_k: int = 5) -> List[Dict]:
        """Rank tenders for a given profile."""
        query = self._prepare_profile_query(profile)
        query_vec = self.vectorizer.transform([query])
        
        # Compute cosine similarities
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Score each tender
        scored_tenders = []
        for idx, tender in enumerate(self.tenders):
            score = self._compute_hybrid_score(profile, tender, similarities[idx])
            scored_tenders.append((score, idx))
        
        # Sort by score descending
        scored_tenders.sort(key=lambda x: x[0], reverse=True)
        
        # Build results
        results = []
        for rank_idx, (score, idx) in enumerate(scored_tenders[:top_k], 1):
            tender = self.tenders[idx].copy()
            tender['score'] = score
            tender['rank'] = rank_idx
            tender['breakdown'] = self._get_breakdown(profile, tender, similarities[idx])
            results.append(tender)
        
        return results
    
    def _compute_hybrid_score(self, profile: Dict, tender: Dict, tfidf_sim: float) -> float:
        """Compute weighted hybrid score."""
        # Weights
        w_tfidf = 0.45
        w_sector = 0.25
        w_budget = 0.20
        w_urgency = 0.10
        
        # Component scores
        sector_score = self._sector_match_score(profile, tender)
        budget_score = self._budget_compatibility_score(profile, tender)
        urgency_score = self._deadline_urgency_score(tender)
        
        # Weighted sum
        total = (w_tfidf * tfidf_sim + 
                 w_sector * sector_score + 
                 w_budget * budget_score + 
                 w_urgency * urgency_score)
        
        return total
    
    def _sector_match_score(self, profile: Dict, tender: Dict) -> float:
        """Score sector match: exact=1.0, related=0.3, none=0.0."""
        profile_sector = profile.get('sector', '').lower()
        tender_sector = tender.get('sector', '').lower()
        
        if profile_sector == tender_sector:
            return 1.0
        # Related sectors mapping (simplified)
        related_pairs = [
            ('agritech', 'wastetech'), ('cleantech', 'wastetech'),
            ('healthtech', 'edtech'), ('fintech', 'edtech')
        ]
        if (profile_sector, tender_sector) in related_pairs or (tender_sector, profile_sector) in related_pairs:
            return 0.3
        return 0.0
    
    def _budget_compatibility_score(self, profile: Dict, tender: Dict) -> float:
        """Score budget fit based on past funding."""
        profile_budget = profile.get('past_funding', 0)
        tender_budget = tender.get('budget')
        
        if not tender_budget or tender_budget <= 0:
            return 0.2  # Unknown budget = low confidence
        
        if profile_budget <= 0:
            return 0.5  # New business = neutral
        
        ratio = tender_budget / max(profile_budget, 1)
        
        if 0.5 <= ratio <= 2.0:
            return 1.0
        elif 0.25 <= ratio <= 3.0:
            return 0.6
        else:
            return 0.2
    
    def _deadline_urgency_score(self, tender: Dict) -> float:
        """Score deadline urgency: closer deadline = higher urgency."""
        deadline_str = tender.get('deadline', '')
        if not deadline_str or deadline_str == 'Not specified':
            return 0.3
        
        try:
            # Try to parse deadline
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                try:
                    deadline = datetime.strptime(deadline_str, fmt)
                    days_left = (deadline - datetime.now()).days
                    if days_left < 0:
                        return 0.0
                    elif days_left <= 7:
                        return 1.0
                    elif days_left <= 30:
                        return 0.8
                    elif days_left <= 90:
                        return 0.5
                    else:
                        return 0.3
                except ValueError:
                    continue
        except:
            pass
        return 0.3
    
    def _get_breakdown(self, profile: Dict, tender: Dict, tfidf_sim: float) -> Dict:
        """Get score breakdown for explainability."""
        return {
            'tfidf_similarity': round(tfidf_sim, 4),
            'sector_match': round(self._sector_match_score(profile, tender), 4),
            'budget_score': round(self._budget_compatibility_score(profile, tender), 4),
            'urgency_score': round(self._deadline_urgency_score(tender), 4),
        }


def get_top_disqualifier(profile: Dict, tender: Dict) -> str:
    """Return the single biggest disqualifier for a match."""
    disqualifiers = []
    
    # Check deadline
    deadline_str = tender.get('deadline', '')
    if deadline_str and deadline_str != 'Not specified':
        try:
            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    deadline = datetime.strptime(deadline_str, fmt)
                    if deadline < datetime.now():
                        disqualifiers.append(("Deadline passed", 100))
                    elif (deadline - datetime.now()).days <= 7:
                        disqualifiers.append(("Deadline very soon (<7 days)", 80))
                    break
                except:
                    continue
        except:
            pass
    
    # Check sector mismatch
    profile_sector = profile.get('sector', '')
    tender_sector = tender.get('sector', '')
    if profile_sector and tender_sector and profile_sector != tender_sector:
        disqualifiers.append((f"Sector mismatch (needs {profile_sector}, tender is {tender_sector})", 60))
    
    # Check budget mismatch
    profile_budget = profile.get('past_funding', 0)
    tender_budget = tender.get('budget')
    if profile_budget > 0 and tender_budget:
        ratio = tender_budget / profile_budget
        if ratio > 3:
            disqualifiers.append((f"Budget too large (${tender_budget:,} vs ${profile_budget:,} past)", 70))
        elif ratio < 0.25:
            disqualifiers.append((f"Budget too small (${tender_budget:,} vs ${profile_budget:,} past)", 50))
    
    if not disqualifiers:
        return "No major disqualifiers — good match!"
    
    # Return highest severity disqualifier
    disqualifiers.sort(key=lambda x: x[1], reverse=True)
    return disqualifiers[0][0]
