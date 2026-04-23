"""Multilingual summarizer for match explanations (≤80 words)."""

from typing import Dict, Optional
from datetime import datetime


def generate_summary(profile: Dict, match: Dict, language: str = 'en') -> str:
    """Generate a concise match summary (≤80 words)."""
    
    if language == 'fr':
        return _generate_french_summary(profile, match)
    return _generate_english_summary(profile, match)


def _generate_english_summary(profile: Dict, match: Dict) -> str:
    """Generate English summary."""
    score = match.get('score', 0)
    tender_title = match.get('title', 'Untitled')
    sector = match.get('sector', 'various')
    budget = match.get('budget')
    deadline = match.get('deadline', 'Not specified')
    region = match.get('region', '')
    
    # Build summary parts
    parts = []
    
    # Opening
    if score > 0.6:
        parts.append(f"✅ Strong match: {tender_title}")
    else:
        parts.append(f"📌 Potential match: {tender_title}")
    
    # Why it matches
    parts.append(f"Your {profile.get('sector', '')} expertise aligns with this {sector} opportunity.")
    
    # Budget
    if budget:
        parts.append(f"Budget ${budget:,} fits your scale.")
    
    # Deadline
    if deadline and deadline != 'Not specified':
        parts.append(f"Apply by {deadline}.")
    
    # Region
    if region and region != 'Not specified':
        parts.append(f"Operates in {region}.")
    
    # Join and truncate to 80 words
    summary = ' '.join(parts)
    words = summary.split()
    if len(words) > 80:
        summary = ' '.join(words[:77]) + '...'
    
    return summary


def _generate_french_summary(profile: Dict, match: Dict) -> str:
    """Generate French summary with natural cooperative leader language."""
    score = match.get('score', 0)
    tender_title = match.get('title', 'Sans titre')
    sector = match.get('sector', 'divers')
    budget = match.get('budget')
    deadline = match.get('deadline', 'Non spécifiée')
    region = match.get('region', '')
    
    parts = []
    
    # Opening - using "coopérative" which is more natural in African French context
    if score > 0.6:
        parts.append(f"✅ Bonne correspondance : {tender_title}")
    else:
        parts.append(f"📌 Correspondance possible : {tender_title}")
    
    # Why it matches - using "votre coopérative" instead of "votre organisation"
    parts.append(f"Votre coopérative dans le secteur {profile.get('sector', '')} correspond à cette offre {sector}.")
    
    # Budget
    if budget:
        parts.append(f"Budget de ${budget:,} adapté à votre taille.")
    
    # Deadline
    if deadline and deadline != 'Non spécifiée':
        parts.append(f"Postulez avant le {deadline}.")
    
    # Region
    if region and region != 'Non spécifiée':
        parts.append(f"Opère en {region}.")
    
    summary = ' '.join(parts)
    words = summary.split()
    if len(words) > 80:
        summary = ' '.join(words[:77]) + '...'
    
    return summary


def generate_summary_md(profile: Dict, matches: list, language: str = 'en') -> str:
    """Generate markdown summary for a profile."""
    lines = []
    lines.append(f"# Tender Matches for {profile.get('name', profile.get('id', 'Unknown'))}")
    lines.append("")
    lines.append(f"**Sector:** {profile.get('sector', 'N/A')} | **Country:** {profile.get('country', 'N/A')}")
    lines.append(f"**Employees:** {profile.get('employees', 'N/A')} | **Past Funding:** ${profile.get('past_funding', 0):,}")
    lines.append(f"**Needs:** {profile.get('needs_text', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for match in matches:
        lines.append(f"## {match['rank']}. {match.get('title', 'Untitled')}")
        lines.append("")
        lines.append(f"- **Score:** {match.get('score', 0):.4f}")
        lines.append(f"- **Tender ID:** {match.get('tender_id', 'N/A')}")
        lines.append(f"- **Sector:** {match.get('sector', 'N/A')}")
        lines.append(f"- **Budget:** ${match.get('budget', 0):,}" if match.get('budget') else "- **Budget:** Not specified")
        lines.append(f"- **Deadline:** {match.get('deadline', 'Not specified')}")
        lines.append(f"- **Region:** {match.get('region', 'Not specified')}")
        lines.append("")
        lines.append("### Why this match?")
        lines.append("")
        summary = generate_summary(profile, match, language)
        lines.append(f"> {summary}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return '\n'.join(lines)


def generate_individual_summary_md(profile: Dict, match: Dict, rank: int, language: str = 'en', disqualifier: str = "") -> str:
    """Generate individual markdown file for (profile, tender) pair."""
    lines = []
    lines.append(f"# Match: {profile.get('name', profile.get('id', 'Unknown'))} → {match.get('title', 'Untitled')}")
    lines.append("")
    lines.append(f"**Rank:** #{rank} | **Score:** {match.get('score', 0):.4f}")
    lines.append("")
    lines.append("## Profile Details")
    lines.append(f"- **ID:** {profile.get('id', 'N/A')}")
    lines.append(f"- **Sector:** {profile.get('sector', 'N/A')}")
    lines.append(f"- **Country:** {profile.get('country', 'N/A')}")
    lines.append(f"- **Employees:** {profile.get('employees', 'N/A')}")
    lines.append(f"- **Past Funding:** ${profile.get('past_funding', 0):,}")
    lines.append(f"- **Needs:** {profile.get('needs_text', 'N/A')}")
    lines.append("")
    lines.append("## Tender Details")
    lines.append(f"- **ID:** {match.get('tender_id', 'N/A')}")
    lines.append(f"- **Sector:** {match.get('sector', 'N/A')}")
    lines.append(f"- **Budget:** ${match.get('budget', 0):,}" if match.get('budget') else "- **Budget:** Not specified")
    lines.append(f"- **Deadline:** {match.get('deadline', 'Not specified')}")
    lines.append(f"- **Region:** {match.get('region', 'Not specified')}")
    lines.append(f"- **Language:** {match.get('language', 'en').upper()}")
    lines.append("")
    lines.append("## Match Summary")
    lines.append("")
    summary = generate_summary(profile, match, language)
    lines.append(f"> {summary}")
    lines.append("")
    if disqualifier:
        lines.append("## ⚠ Biggest Disqualifier")
        lines.append("")
        lines.append(f"> {disqualifier}")
    
    return '\n'.join(lines)
