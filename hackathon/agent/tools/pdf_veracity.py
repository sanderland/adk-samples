"""Simplified PDF veracity analysis tool for the fact checker agent."""

from typing import Dict
from .pdf_tools import extract_pdf_text, extract_pdf_claims, calculate_veracity_score
from .fact_checker import fact_check


def analyze_pdf_veracity_simple(pdf_url: str, num_claims_to_check: int = 5) -> str:
    """
    Analyze a PDF for veracity and return a formatted report.
    
    Args:
        pdf_url: URL or path to the PDF file
        num_claims_to_check: Number of claims to fact-check (default: 3)
        
    Returns:
        A formatted string report with the analysis results
    """
    # Step 1: Extract text
    print(f"[PDF Veracity] Starting analysis of: {pdf_url}")
    text_result = extract_pdf_text(pdf_url)
    
    if text_result.get('error'):
        return f"Error extracting PDF text: {text_result['error']}"
    
    # Step 2: Extract claims
    claims = extract_pdf_claims(text_result['text'])
    
    # Step 3: Prepare all claims with categories
    all_claims_categorized = []
    
    # Add all assumptions
    for claim in claims['assumptions']:
        all_claims_categorized.append({
            'category': 'Assumption',
            'claim': claim,
            'checked': False,
            'score': 'N/A',
            'confidence': 'N/A'
        })
    
    # Add all conclusions
    for claim in claims['conclusions']:
        all_claims_categorized.append({
            'category': 'Conclusion',
            'claim': claim,
            'checked': False,
            'score': 'N/A',
            'confidence': 'N/A'
        })
    
    # Add all factual claims
    for claim in claims['factual_claims']:
        all_claims_categorized.append({
            'category': 'Factual Claim',
            'claim': claim,
            'checked': False,
            'score': 'N/A',
            'confidence': 'N/A'
        })
    
    # Add all causal claims
    for claim in claims['causal_claims']:
        all_claims_categorized.append({
            'category': 'Causal Claim',
            'claim': claim,
            'checked': False,
            'score': 'N/A',
            'confidence': 'N/A'
        })
    
    # Step 4: Select and fact-check claims
    claims_to_check = []
    claims_to_check_indices = []
    
    # Prioritize factual claims
    for i, claim_info in enumerate(all_claims_categorized):
        if claim_info['category'] == 'Factual Claim' and len(claims_to_check) < num_claims_to_check//2:
            claims_to_check.append(claim_info['claim'])
            claims_to_check_indices.append(i)
    
    # Then conclusions
    for i, claim_info in enumerate(all_claims_categorized):
        if claim_info['category'] == 'Conclusion' and len(claims_to_check) < num_claims_to_check:
            claims_to_check.append(claim_info['claim'])
            claims_to_check_indices.append(i)
    
    # Then causal claims
    for i, claim_info in enumerate(all_claims_categorized):
        if claim_info['category'] == 'Causal Claim' and len(claims_to_check) < num_claims_to_check:
            claims_to_check.append(claim_info['claim'])
            claims_to_check_indices.append(i)
    
    # Fact-check selected claims
    fact_check_results = []
    for i, (claim, claim_idx) in enumerate(zip(claims_to_check, claims_to_check_indices)):
        print(f"[PDF Veracity] Fact-checking claim {i+1}/{len(claims_to_check)}")
        try:
            result = fact_check(claim, search_depth=2)
            fact_check_results.append(result)
            
            # Update claim info with results
            confidence = result.get('verification_summary', {}).get('confidence', 'Low')
            assessment = result.get('verification_summary', {}).get('assessment', '')
            
            # Assign individual score based on confidence
            if confidence == 'High' and 'found' in assessment:
                score = 9
            elif confidence == 'High':
                score = 8
            elif confidence == 'Medium':
                score = 6
            elif confidence == 'Low' and 'not found' not in assessment:
                score = 4
            else:
                score = 2
                
            all_claims_categorized[claim_idx]['checked'] = True
            all_claims_categorized[claim_idx]['score'] = score
            all_claims_categorized[claim_idx]['confidence'] = confidence
            
        except Exception as e:
            fact_check_results.append({
                'statement': claim,
                'error': str(e),
                'verification_summary': {
                    'confidence': 'Low',
                    'assessment': 'Error during fact-checking'
                }
            })
            all_claims_categorized[claim_idx]['checked'] = True
            all_claims_categorized[claim_idx]['score'] = 1
            all_claims_categorized[claim_idx]['confidence'] = 'Error'
    
    # Step 4: Calculate score
    score_result = calculate_veracity_score(claims, fact_check_results)
    
    # Format report
    report = f"""PDF Veracity Analysis Report
============================
PDF: {pdf_url}

SUMMARY
-------
Overall Credibility Score: {score_result['credibility_score']}/10
Assessment: {score_result['assessment']}

CLAIMS ANALYSIS
--------------
Total claims extracted: {claims['total_claims']}
- Assumptions: {len(claims['assumptions'])}
- Conclusions: {len(claims['conclusions'])}
- Factual claims: {len(claims['factual_claims'])}
- Causal claims: {len(claims['causal_claims'])}

Claims fact-checked: {len(fact_check_results)}
- Verified: {score_result['verified_count']}
- Unverified: {score_result['unverified_count']}

{score_result['explanation']}

ALL CLAIMS WITH INDIVIDUAL SCORES
=================================
"""
    
    # Group claims by category
    categories = ['Assumption', 'Conclusion', 'Factual Claim', 'Causal Claim']
    
    for category in categories:
        category_claims = [c for c in all_claims_categorized if c['category'] == category]
        if category_claims:
            report += f"\n{category.upper()}S:\n"
            report += "-" * (len(category) + 2) + "\n"
            
            for i, claim_info in enumerate(category_claims, 1):
                # Format claim text (truncate if too long)
                claim_text = claim_info['claim']
                if len(claim_text) > 150:
                    claim_text = claim_text[:147] + "..."
                
                report += f"\n{i}. {claim_text}\n"
                
                if claim_info['checked']:
                    report += f"   Score: {claim_info['score']}/10"
                    report += f"   (Confidence: {claim_info['confidence']})\n"
                else:
                    report += f"   Score: Not checked (insufficient resources)\n"
    
    # Add summary statistics
    report += "\n\nSUMMARY STATISTICS\n"
    report += "==================\n"
    checked_claims = [c for c in all_claims_categorized if c['checked']]
    if checked_claims:
        avg_score = sum(c['score'] for c in checked_claims) / len(checked_claims)
        report += f"Average score of checked claims: {avg_score:.1f}/10\n"
        report += f"Highest scoring claim: {max(c['score'] for c in checked_claims)}/10\n"
        report += f"Lowest scoring claim: {min(c['score'] for c in checked_claims)}/10\n"
        
    return report