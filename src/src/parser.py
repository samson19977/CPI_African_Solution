"""Multilingual document parser for tenders (EN/FR)."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import chardet
from pypdf import PdfReader
from bs4 import BeautifulSoup


def detect_language(text: str) -> str:
    """Detect if text is English or French."""
    en_markers = ['the', 'and', 'for', 'with', 'grant', 'tender', 'deadline', 'application', 'funding']
    fr_markers = ['le', 'la', 'les', 'et', 'pour', 'avec', 'subvention', 'offre', 'candidature', 'financement']
    
    text_lower = text.lower()[:1000]
    en_count = sum(1 for m in en_markers if m in text_lower)
    fr_count = sum(1 for m in fr_markers if m in text_lower)
    
    if fr_count > en_count:
        return 'fr'
    return 'en'


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from PDF file."""
    text = []
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    except Exception as e:
        print(f"  [WARN] PDF read error {filepath}: {e}")
    return '\n'.join(text)


def extract_text_from_html(filepath: str) -> str:
    """Extract text from HTML file."""
    with open(filepath, 'rb') as f:
        raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected['encoding'] or 'utf-8'
        content = raw.decode(encoding, errors='ignore')
    
    soup = BeautifulSoup(content, 'html.parser')
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator='\n')


def extract_text_from_txt(filepath: str) -> str:
    """Extract text from TXT file."""
    with open(filepath, 'rb') as f:
        raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected['encoding'] or 'utf-8'
        return raw.decode(encoding, errors='ignore')


def extract_sector(text: str) -> str:
    """Extract sector from tender text."""
    sectors = ['agritech', 'healthtech', 'cleantech', 'edtech', 'fintech', 'wastetech']
    text_lower = text.lower()
    for sector in sectors:
        if sector in text_lower:
            return sector
    return "unspecified"


def extract_budget(text: str) -> Optional[int]:
    """Extract budget amount from tender text."""
    patterns = [
        r'budget[:\s]*\$?(\d+(?:[,\s]\d+)*)\s*(?:USD|US\s?Dollars?)',
        r'Total available funding:\s*USD\s*(\d+(?:[,\s]\d+)*)',
        r'grant per applicant:\s*USD\s*(\d+(?:[,\s]\d+)*)',
        r'envelope:\s*USD\s*(\d+(?:[,\s]\d+)*)',
        r'up to\s*\$?(\d+(?:[,\s]\d+)*)',
        r'Budget\s*[\$]?(\d+[,.]?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '').replace(' ', '')
            try:
                return int(float(amount_str))
            except ValueError:
                continue
    return None


def extract_deadline(text: str) -> str:
    """Extract deadline date from tender text."""
    patterns = [
        r'deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'date limite[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Date de soumission[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'submission deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'Application deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Not specified"


def extract_region(text: str) -> str:
    """Extract region from tender text."""
    regions = ['East Africa', 'West Africa', 'Central Africa', 'Southern Africa']
    text_lower = text.lower()
    for region in regions:
        if region.lower() in text_lower:
            return region
    
    countries = ['rwanda', 'kenya', 'uganda', 'senegal', 'drc', 'ethiopia', 'tanzania', 'ghana', 'nigeria']
    for country in countries:
        if country in text_lower:
            return f"{country.title()}"
    return "Not specified"


def parse_tender(filepath: str) -> Dict[str, Any]:
    """Parse a single tender document."""
    ext = Path(filepath).suffix.lower()
    
    if ext == '.pdf':
        text = extract_text_from_pdf(filepath)
    elif ext == '.html':
        text = extract_text_from_html(filepath)
    else:  # .txt
        text = extract_text_from_txt(filepath)
    
    if not text or len(text.strip()) < 50:
        text = f"Tender document at {filepath}"
    
    # Extract tender ID from filename (e.g., T001_...)
    filename = Path(filepath).stem
    tender_id = filename.split('_')[0] if '_' in filename else filename
    
    return {
        'tender_id': tender_id,
        'filename': Path(filepath).name,
        'title': extract_title(text, filename),
        'language': detect_language(text),
        'text': text[:8000],
        'sector': extract_sector(text),
        'budget': extract_budget(text),
        'deadline': extract_deadline(text),
        'region': extract_region(text),
    }


def extract_title(text: str, fallback: str) -> str:
    """Extract title from tender text."""
    # Look for common title patterns
    lines = text.split('\n')
    for line in lines[:20]:
        line = line.strip()
        if len(line) > 10 and len(line) < 120:
            if any(keyword in line.lower() for keyword in ['grant', 'funding', 'call', 'tender', 'opportunity', 'subvention', 'appel']):
                return line[:80]
    return fallback.replace('_', ' ').title()


def load_tenders(tenders_dir: str) -> List[Dict[str, Any]]:
    """Load all tenders from directory."""
    tenders = []
    path = Path(tenders_dir)
    
    if not path.exists():
        raise FileNotFoundError(f"Tenders directory not found: {tenders_dir}")
    
    for filepath in path.iterdir():
        if filepath.suffix.lower() in ['.txt', '.html', '.pdf']:
            tender = parse_tender(str(filepath))
            tenders.append(tender)
    
    print(f"  Loaded {len(tenders)} tenders from {tenders_dir}")
    return tenders


def load_profiles(profiles_path: str) -> List[Dict[str, Any]]:
    """Load business profiles from JSON."""
    import json
    with open(profiles_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]
#####
