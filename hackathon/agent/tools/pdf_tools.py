"""PDF processing tools for the fact checker agent."""

import PyPDF2
import requests
import tempfile
import os
from typing import Dict, List, Optional
import re


def extract_pdf_text(pdf_path: str) -> Dict[str, any]:
    """
    Extract text content from a PDF file or URL.
    
    Args:
        pdf_path: Path to the PDF file or URL
        
    Returns:
        Dictionary with:
        - text: Extracted text content
        - page_count: Number of pages
        - char_count: Number of characters extracted
        - error: Error message if failed
    """
    print(f"[PDF Text Extractor] Processing: {pdf_path}")
    
    # Check if pdf_path is a URL
    if pdf_path.startswith('http://') or pdf_path.startswith('https://'):
        try:
            print(f"[PDF Text Extractor] Downloading PDF from URL...")
            response = requests.get(pdf_path, timeout=30)
            response.raise_for_status()
            
            print(f"[PDF Text Extractor] Downloaded {len(response.content)} bytes")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(response.content)
                temp_pdf_path = tmp_file.name
            
            # Extract text from downloaded PDF
            result = _extract_from_file(temp_pdf_path)
            
            # Clean up temporary file
            try:
                os.unlink(temp_pdf_path)
            except:
                pass
                
            return result
                
        except Exception as e:
            print(f"[PDF Text Extractor] Error downloading PDF: {str(e)}")
            return {
                'error': f'Failed to download PDF from URL: {str(e)}',
                'text': None,
                'page_count': 0,
                'char_count': 0
            }
    else:
        # Extract text from local PDF
        return _extract_from_file(pdf_path)


def _extract_from_file(pdf_path: str) -> Dict[str, any]:
    """Helper function to extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            page_count = len(pdf_reader.pages)
            
            # Try to extract text from each page
            for page_num in range(page_count):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    print(f"[PDF Text Extractor] Error on page {page_num}: {str(page_error)}")
                    continue
            
            # Check if we got any text
            if text.strip():
                print(f"[PDF Text Extractor] Successfully extracted {len(text)} characters from {page_count} pages")
                return {
                    'text': text,
                    'page_count': page_count,
                    'char_count': len(text),
                    'error': None
                }
            else:
                return {
                    'error': 'No text could be extracted from PDF',
                    'text': None,
                    'page_count': page_count,
                    'char_count': 0
                }
                
    except Exception as e:
        print(f"[PDF Text Extractor] Error: {str(e)}")
        return {
            'error': f'Failed to extract text: {str(e)}',
            'text': None,
            'page_count': 0,
            'char_count': 0
        }


def extract_pdf_claims(text: str) -> Dict[str, List[str]]:
    """
    Extract claims, assumptions, and conclusions from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing:
        - assumptions: List of assumption statements
        - conclusions: List of conclusion statements
        - factual_claims: List of factual claims
        - causal_claims: List of causal claims
        - total_claims: Total number of claims found
    """
    print(f"[Claim Extractor] Analyzing {len(text)} characters of text")
    
    # Clean text
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    claims = {
        'assumptions': [],
        'conclusions': [],
        'factual_claims': [],
        'causal_claims': []
    }
    
    # Patterns for different types of claims
    assumption_patterns = [
        r'assum\w+', r'suppos\w+', r'hypothes\w+', r'presuppos\w+',
        r'premise', r'given that', r'based on the assumption'
    ]
    
    conclusion_patterns = [
        r'therefore', r'thus', r'hence', r'consequent\w+', r'as a result',
        r'we conclude', r'in conclusion', r'this shows', r'this demonstrates',
        r'this proves', r'we find that'
    ]
    
    causal_patterns = [
        r'caus\w+', r'leads? to', r'results? in', r'due to', r'because of',
        r'affects?', r'influences?', r'contributes? to'
    ]
    
    factual_patterns = [
        r'\d+%', r'\d+ (times|percent|people|studies|participants)',
        r'research shows', r'studies? (show|indicate|suggest|demonstrate)',
        r'according to', r'data (shows?|indicates?|suggests?)',
        r'evidence suggests?', r'(is|are|was|were) \d+'
    ]
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Check for assumptions
        if any(re.search(pattern, sentence_lower) for pattern in assumption_patterns):
            claims['assumptions'].append(sentence)
        
        # Check for conclusions
        elif any(re.search(pattern, sentence_lower) for pattern in conclusion_patterns):
            claims['conclusions'].append(sentence)
        
        # Check for causal claims
        elif any(re.search(pattern, sentence_lower) for pattern in causal_patterns):
            claims['causal_claims'].append(sentence)
        
        # Check for factual claims
        elif any(re.search(pattern, sentence_lower) for pattern in factual_patterns):
            claims['factual_claims'].append(sentence)
        
        # If it contains specific quantitative info, also consider it a factual claim
        elif re.search(r'\d+\.?\d*\s*(percent|%|times|fold|million|billion|thousand)', sentence_lower):
            if sentence not in claims['factual_claims']:
                claims['factual_claims'].append(sentence)
    
    # Remove duplicates while preserving order
    for claim_type in claims:
        claims[claim_type] = list(dict.fromkeys(claims[claim_type]))
    
    # Add total count
    claims['total_claims'] = sum(len(claims[k]) for k in ['assumptions', 'conclusions', 'factual_claims', 'causal_claims'])
    
    print(f"[Claim Extractor] Found {claims['total_claims']} claims")
    print(f"  - Assumptions: {len(claims['assumptions'])}")
    print(f"  - Conclusions: {len(claims['conclusions'])}")
    print(f"  - Factual claims: {len(claims['factual_claims'])}")
    print(f"  - Causal claims: {len(claims['causal_claims'])}")
    
    return claims


def analyze_claim_connections(claims: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Analyze connections between assumptions and conclusions.
    
    Args:
        claims: Dictionary of categorized claims from extract_pdf_claims
        
    Returns:
        List of connections between claims with:
        - type: 'assumption-conclusion' or 'causal-conclusion'
        - claim1: First claim
        - claim2: Second claim
        - common_keywords: List of shared keywords
        - strength: Connection strength
    """
    connections = []
    
    # Find which assumptions might support which conclusions
    for assumption in claims.get('assumptions', []):
        assumption_keywords = set(re.findall(r'\b\w{4,}\b', assumption.lower()))
        
        for conclusion in claims.get('conclusions', []):
            conclusion_keywords = set(re.findall(r'\b\w{4,}\b', conclusion.lower()))
            
            # Check for keyword overlap
            overlap = assumption_keywords & conclusion_keywords
            if len(overlap) >= 2:  # At least 2 common keywords
                connections.append({
                    'type': 'assumption-conclusion',
                    'claim1': assumption,
                    'claim2': conclusion,
                    'common_keywords': list(overlap),
                    'strength': 'potential'
                })
    
    # Find causal chains
    for causal_claim in claims.get('causal_claims', []):
        causal_keywords = set(re.findall(r'\b\w{4,}\b', causal_claim.lower()))
        
        for conclusion in claims.get('conclusions', []):
            conclusion_keywords = set(re.findall(r'\b\w{4,}\b', conclusion.lower()))
            
            overlap = causal_keywords & conclusion_keywords
            if len(overlap) >= 2:
                connections.append({
                    'type': 'causal-conclusion',
                    'claim1': causal_claim,
                    'claim2': conclusion,
                    'common_keywords': list(overlap),
                    'strength': 'causal'
                })
    
    print(f"[Connection Analyzer] Found {len(connections)} connections between claims")
    
    return connections


def calculate_veracity_score(claims: Dict[str, List[str]], fact_check_results: List[Dict]) -> Dict[str, any]:
    """
    Calculate overall veracity score based on claims and fact-checking results.
    
    Args:
        claims: Dictionary of categorized claims
        fact_check_results: List of fact-checking results
        
    Returns:
        Dictionary with:
        - credibility_score: Score from 1-10
        - assessment: Overall assessment text
        - explanation: Detailed explanation
        - verified_count: Number of verified claims
        - unverified_count: Number of unverified claims
    """
    total_claims = claims.get('total_claims', 0)
    
    if not fact_check_results:
        return {
            'credibility_score': 5,
            'assessment': 'Unable to verify - No claims were fact-checked',
            'explanation': 'No fact-checking was performed on the extracted claims',
            'verified_count': 0,
            'unverified_count': 0
        }
    
    high_confidence_verified = 0
    medium_confidence_verified = 0
    low_confidence_verified = 0
    unverified = 0
    
    for result in fact_check_results:
        confidence = result.get('verification_summary', {}).get('confidence', 'Low')
        assessment = result.get('verification_summary', {}).get('assessment', '')
        
        if confidence == 'High' and 'found' in assessment:
            high_confidence_verified += 1
        elif confidence == 'Medium':
            medium_confidence_verified += 1
        elif confidence == 'Low':
            low_confidence_verified += 1
        else:
            unverified += 1
    
    # Calculate score
    score = 5  # Base score
    
    # Add points for verified claims
    score += (high_confidence_verified / len(fact_check_results)) * 4
    score += (medium_confidence_verified / len(fact_check_results)) * 2
    
    # Subtract points for unverified claims
    score -= (unverified / len(fact_check_results)) * 2
    
    # Ensure score is between 1 and 10
    score = max(1, min(10, round(score)))
    
    # Generate assessment
    if score >= 8:
        assessment = "High credibility - Most claims are well-supported by evidence"
    elif score >= 6:
        assessment = "Moderate credibility - Some claims are supported, others need verification"
    elif score >= 4:
        assessment = "Low credibility - Many claims lack supporting evidence"
    else:
        assessment = "Very low credibility - Most claims cannot be verified"
    
    # Generate explanation
    explanation = f"Based on fact-checking {len(fact_check_results)} out of {total_claims} claims: "
    explanation += f"{high_confidence_verified} highly verified, "
    explanation += f"{medium_confidence_verified} partially verified, "
    explanation += f"{low_confidence_verified + unverified} unverified or low confidence"
    
    return {
        'credibility_score': score,
        'assessment': assessment,
        'explanation': explanation,
        'verified_count': high_confidence_verified + medium_confidence_verified,
        'unverified_count': low_confidence_verified + unverified
    }