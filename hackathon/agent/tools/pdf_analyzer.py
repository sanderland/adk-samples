import PyPDF2
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import requests
import tempfile
from .fact_checker import fact_check


def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text or None if failed
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Try to extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    # Skip problematic pages
                    continue
            
            # Check if we got any text
            if text.strip():
                return text
            else:
                return None
                
    except Exception as e:
        # Log the error for debugging
        print(f"Error extracting PDF text: {str(e)}")
        return None


def extract_claims(text: str) -> Dict[str, List[str]]:
    """
    Extract claims, assumptions, and conclusions from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing categorized claims
    """
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
        r'assum\w+',
        r'suppos\w+',
        r'hypothes\w+',
        r'presuppos\w+',
        r'premise',
        r'given that',
        r'based on the assumption'
    ]
    
    conclusion_patterns = [
        r'therefore',
        r'thus',
        r'hence',
        r'consequent\w+',
        r'as a result',
        r'we conclude',
        r'in conclusion',
        r'this shows',
        r'this demonstrates',
        r'this proves',
        r'we find that'
    ]
    
    causal_patterns = [
        r'caus\w+',
        r'leads? to',
        r'results? in',
        r'due to',
        r'because of',
        r'affects?',
        r'influences?',
        r'contributes? to'
    ]
    
    factual_patterns = [
        r'\d+%',
        r'\d+ (times|percent|people|studies|participants)',
        r'research shows',
        r'studies? (show|indicate|suggest|demonstrate)',
        r'according to',
        r'data (shows?|indicates?|suggests?)',
        r'evidence suggests?',
        r'(is|are|was|were) \d+'
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
    
    return claims


def analyze_claim_connections(claims: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """
    Analyze connections between assumptions and conclusions.
    
    Args:
        claims: Dictionary of categorized claims
        
    Returns:
        List of connections between claims
    """
    connections = []
    
    # Find which assumptions might support which conclusions
    for assumption in claims['assumptions']:
        assumption_keywords = set(re.findall(r'\b\w{4,}\b', assumption.lower()))
        
        for conclusion in claims['conclusions']:
            conclusion_keywords = set(re.findall(r'\b\w{4,}\b', conclusion.lower()))
            
            # Check for keyword overlap
            overlap = assumption_keywords & conclusion_keywords
            if len(overlap) >= 2:  # At least 2 common keywords
                connections.append({
                    'assumption': assumption,
                    'conclusion': conclusion,
                    'common_keywords': list(overlap),
                    'connection_strength': 'potential'
                })
    
    # Find causal chains
    for causal_claim in claims['causal_claims']:
        causal_keywords = set(re.findall(r'\b\w{4,}\b', causal_claim.lower()))
        
        for conclusion in claims['conclusions']:
            conclusion_keywords = set(re.findall(r'\b\w{4,}\b', conclusion.lower()))
            
            overlap = causal_keywords & conclusion_keywords
            if len(overlap) >= 2:
                connections.append({
                    'causal_claim': causal_claim,
                    'conclusion': conclusion,
                    'common_keywords': list(overlap),
                    'connection_strength': 'causal'
                })
    
    return connections


def calculate_credibility_score(fact_check_results: List[Dict], total_claims: int) -> Tuple[int, str]:
    """
    Calculate overall credibility score based on fact-checking results.
    
    Args:
        fact_check_results: List of fact-checking results
        total_claims: Total number of claims analyzed
        
    Returns:
        Tuple of (score out of 10, explanation)
    """
    if not fact_check_results:
        return 5, "No claims could be verified"
    
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
    
    # Generate explanation
    explanation = f"Based on fact-checking {len(fact_check_results)} out of {total_claims} claims: "
    explanation += f"{high_confidence_verified} highly verified, "
    explanation += f"{medium_confidence_verified} partially verified, "
    explanation += f"{low_confidence_verified + unverified} unverified or low confidence"
    
    return score, explanation


def analyze_pdf_veracity(pdf_path: str, max_claims_to_check: int = 3) -> Dict[str, any]:
    """
    Analyze a PDF document for veracity by extracting claims and fact-checking them.
    
    Args:
        pdf_path: Path to the PDF file to analyze (can be local path or URL)
        max_claims_to_check: Maximum number of claims to fact-check (default: 10)
        
    Returns:
        Dictionary containing:
        - pdf_path: Path to the analyzed PDF
        - extracted_claims: Categorized claims from the PDF
        - claim_connections: Connections between assumptions and conclusions
        - fact_check_results: Results of fact-checking individual claims
        - credibility_score: Overall credibility rating (1-10)
        - summary: Overall assessment of the document's veracity
    """
    
    print(f"[PDF Analyzer] Starting analysis of: {pdf_path}")
    
    # Check if pdf_path is a URL
    if pdf_path.startswith('http://') or pdf_path.startswith('https://'):
        try:
            print(f"[PDF Analyzer] Downloading PDF from URL...")
            # Download PDF to temporary file
            response = requests.get(pdf_path, timeout=30)
            response.raise_for_status()
            
            print(f"[PDF Analyzer] Downloaded {len(response.content)} bytes")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(response.content)
                temp_pdf_path = tmp_file.name
            
            # Extract text from downloaded PDF
            text = extract_text_from_pdf(temp_pdf_path)
            
            # Clean up temporary file
            try:
                os.unlink(temp_pdf_path)
            except:
                pass
                
        except Exception as e:
            print(f"[PDF Analyzer] Error downloading PDF: {str(e)}")
            return {
                'pdf_path': pdf_path,
                'error': f'Failed to download PDF from URL: {str(e)}'
            }
    else:
        # Extract text from local PDF
        text = extract_text_from_pdf(pdf_path)
    
    if not text:
        print(f"[PDF Analyzer] Failed to extract text from PDF")
        return {
            'pdf_path': pdf_path,
            'error': 'Failed to extract text from PDF'
        }
    
    print(f"[PDF Analyzer] Extracted {len(text)} characters of text")
    
    # Extract claims
    claims = extract_claims(text)
    print(f"[PDF Analyzer] Extracted claims - Assumptions: {len(claims['assumptions'])}, Conclusions: {len(claims['conclusions'])}, Factual: {len(claims['factual_claims'])}, Causal: {len(claims['causal_claims'])}")
    
    # Analyze connections
    connections = analyze_claim_connections(claims)
    print(f"[PDF Analyzer] Found {len(connections)} claim connections")
    
    # Select claims to fact-check (prioritize factual claims and conclusions)
    claims_to_check = []
    
    # First add factual claims
    claims_to_check.extend(claims['factual_claims'][:max_claims_to_check//2])
    
    # Then add conclusions
    remaining_slots = max_claims_to_check - len(claims_to_check)
    claims_to_check.extend(claims['conclusions'][:remaining_slots//2])
    
    # Then add causal claims
    remaining_slots = max_claims_to_check - len(claims_to_check)
    claims_to_check.extend(claims['causal_claims'][:remaining_slots])
    
    print(f"[PDF Analyzer] Selected {len(claims_to_check[:max_claims_to_check])} claims to fact-check")
    
    # Fact-check selected claims
    fact_check_results = []
    for i, claim in enumerate(claims_to_check[:max_claims_to_check]):
        try:
            print(f"[PDF Analyzer] Fact-checking claim {i+1}/{min(len(claims_to_check), max_claims_to_check)}: {claim[:100]}...")
            result = fact_check(claim, search_depth=2)
            fact_check_results.append(result)
        except Exception as e:
            print(f"[PDF Analyzer] Error fact-checking claim {i+1}: {str(e)}")
            fact_check_results.append({
                'statement': claim,
                'error': str(e),
                'verification_summary': {
                    'confidence': 'Low',
                    'assessment': 'Error during fact-checking'
                }
            })
    
    # Calculate credibility score
    total_claims = sum(len(claims[k]) for k in claims)
    credibility_score, score_explanation = calculate_credibility_score(fact_check_results, total_claims)
    
    # Generate summary
    summary = {
        'total_claims_extracted': total_claims,
        'claims_fact_checked': len(fact_check_results),
        'credibility_score': credibility_score,
        'score_explanation': score_explanation,
        'key_findings': []
    }
    
    # Add key findings
    if claims['assumptions']:
        summary['key_findings'].append(f"Document makes {len(claims['assumptions'])} explicit assumptions")
    
    if claims['conclusions']:
        summary['key_findings'].append(f"Document draws {len(claims['conclusions'])} conclusions")
    
    if connections:
        summary['key_findings'].append(f"Found {len(connections)} connections between claims")
    
    # Assess overall veracity
    if credibility_score >= 8:
        summary['overall_assessment'] = "High credibility - Most claims are well-supported by evidence"
    elif credibility_score >= 6:
        summary['overall_assessment'] = "Moderate credibility - Some claims are supported, others need verification"
    elif credibility_score >= 4:
        summary['overall_assessment'] = "Low credibility - Many claims lack supporting evidence"
    else:
        summary['overall_assessment'] = "Very low credibility - Most claims cannot be verified"
    
    print(f"[PDF Analyzer] Analysis complete. Credibility score: {credibility_score}/10")
    
    # Return a simplified structure for the agent
    return {
        'pdf_path': pdf_path,
        'credibility_score': credibility_score,
        'total_claims': total_claims,
        'claims_verified': len(fact_check_results),
        'assessment': summary['overall_assessment'],
        'key_findings': summary['key_findings'],
        'details': {
            'extracted_claims': claims,
            'claim_connections': connections,
            'fact_check_results': fact_check_results
        }
    }