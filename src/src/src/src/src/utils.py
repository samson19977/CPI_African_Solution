"""Utility functions for data loading, metrics, and formatting."""

import json
from typing import Dict, List, Set


def ensure_dir(path: str):
    """Ensure directory exists."""
    from pathlib import Path
    Path(path).mkdir(parents=True, exist_ok=True)


def get_profile_language(profile: Dict) -> str:
    """Get profile's preferred language."""
    langs = profile.get('languages', ['en'])
    if 'fr' in langs:
        return 'fr'
    return 'en'


def format_budget(budget: int) -> str:
    """Format budget as K/M string."""
    if budget >= 1_000_000:
        return f"${budget/1_000_000:.1f}M"
    elif budget >= 1_000:
        return f"${budget/1_000:.0f}K"
    return f"${budget}"


def print_banner(text: str, width: int = 60):
    """Print a banner with the given text."""
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width + "\n")


def load_gold_matches(gold_path: str = "data/gold_matches.csv") -> Dict[str, List[str]]:
    """Load gold standard matches from CSV."""
    import csv
    matches = {}
    try:
        with open(gold_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                profile_id = row.get('profile_id', row.get('profile_id', ''))
                tender_id = row.get('tender_id', row.get('tender_id', ''))
                if profile_id and tender_id:
                    matches.setdefault(profile_id, []).append(tender_id)
    except FileNotFoundError:
        raise FileNotFoundError(f"Gold matches file not found: {gold_path}")
    return matches


def compute_mrr(gold: Dict[str, List[str]], predictions: Dict[str, List[str]], k: int = 5) -> float:
    """Compute Mean Reciprocal Rank at K."""
    reciprocal_ranks = []
    for profile_id, gold_tenders in gold.items():
        pred_tenders = predictions.get(profile_id, [])[:k]
        found_rank = None
        for rank, pred in enumerate(pred_tenders, 1):
            if pred in gold_tenders:
                found_rank = rank
                break
        if found_rank:
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def compute_recall(gold: Dict[str, List[str]], predictions: Dict[str, List[str]], k: int = 5) -> float:
    """Compute Recall at K."""
    recalls = []
    for profile_id, gold_tenders in gold.items():
        pred_tenders = predictions.get(profile_id, [])[:k]
        gold_set = set(gold_tenders)
        pred_set = set(pred_tenders)
        if gold_set:
            recall = len(pred_set & gold_set) / len(gold_set)
            recalls.append(recall)
    return sum(recalls) / len(recalls) if recalls else 0.0


def save_json(data: Dict, filepath: str):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
