import requests
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import time
from io import BytesIO
import PyPDF2
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()


def search_arxiv(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search arXiv for papers related to the query.
    
    Args:
        query: Search query for arXiv
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing paper metadata
    """
    base_url = "http://export.arxiv.org/api/query?"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    url = base_url + "&".join([f"{k}={v}" for k, v in params.items()])
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return []
    
    root = ET.fromstring(response.content)
    
    # Define namespace
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    papers = []
    for entry in root.findall('atom:entry', namespace):
        paper = {
            'title': entry.find('atom:title', namespace).text.strip(),
            'summary': entry.find('atom:summary', namespace).text.strip(),
            'authors': [author.find('atom:name', namespace).text 
                       for author in entry.findall('atom:author', namespace)],
            'pdf_url': None,
            'arxiv_id': None
        }
        
        # Get PDF URL and arXiv ID
        for link in entry.findall('atom:link', namespace):
            if link.get('type') == 'application/pdf':
                paper['pdf_url'] = link.get('href')
            
        # Extract arXiv ID from the entry ID
        entry_id = entry.find('atom:id', namespace).text
        arxiv_id_match = re.search(r'arxiv.org/abs/(\d+\.\d+)', entry_id)
        if arxiv_id_match:
            paper['arxiv_id'] = arxiv_id_match.group(1)
        
        papers.append(paper)
    
    return papers


def download_and_parse_pdf(pdf_url: str) -> Optional[str]:
    """
    Download PDF from arXiv and extract text content.
    
    Args:
        pdf_url: URL of the PDF to download
        
    Returns:
        Extracted text from the PDF or None if failed
    """
    try:
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        
        return text
    except Exception as e:
        return None


def fact_check(statement: str, search_depth: int = 3) -> Dict[str, any]:
    """
    Fact-check a statement by searching for information and cross-referencing with arXiv papers.
    
    Args:
        statement: The statement to fact-check
        search_depth: Number of arXiv papers to analyze (default: 3)
        
    Returns:
        Dictionary containing:
        - statement: The original statement
        - web_search_results: General web search results
        - arxiv_papers: List of relevant arXiv papers with analysis
        - verification_summary: Overall assessment of the statement's veracity
    """
    
    # Initialize Tavily client for web search
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        return {
            "statement": statement,
            "error": "TAVILY_API_KEY not found in environment variables"
        }
    
    tavily_client = TavilyClient(api_key=tavily_api_key)
    
    # Perform web search
    try:
        web_results = tavily_client.search(statement, max_results=5)
        web_search_summary = []
        for result in web_results.get('results', []):
            web_search_summary.append({
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'snippet': result.get('snippet', '')
            })
    except Exception as e:
        web_search_summary = f"Web search failed: {str(e)}"
    
    # Search arXiv for related papers
    arxiv_papers = search_arxiv(statement, max_results=search_depth)
    
    # Analyze each paper
    paper_analyses = []
    for paper in arxiv_papers[:search_depth]:
        analysis = {
            'title': paper['title'],
            'authors': paper['authors'],
            'arxiv_id': paper['arxiv_id'],
            'abstract': paper['summary'][:500] + '...' if len(paper['summary']) > 500 else paper['summary'],
            'relevance': 'Potentially relevant based on title/abstract'
        }
        
        # Download and analyze PDF if available
        if paper['pdf_url']:
            pdf_text = download_and_parse_pdf(paper['pdf_url'])
            if pdf_text:
                # Check if statement appears in the paper
                statement_lower = statement.lower()
                pdf_text_lower = pdf_text.lower()
                
                if statement_lower in pdf_text_lower:
                    analysis['found_in_paper'] = True
                    analysis['relevance'] = 'Statement found directly in paper'
                else:
                    # Look for key terms from the statement
                    key_terms = [term for term in statement_lower.split() 
                               if len(term) > 4]  # Only consider words longer than 4 chars
                    matches = sum(1 for term in key_terms if term in pdf_text_lower)
                    
                    if matches > len(key_terms) * 0.6:  # If 60% of key terms match
                        analysis['found_in_paper'] = False
                        analysis['relevance'] = f'High relevance - {matches}/{len(key_terms)} key terms found'
                    else:
                        analysis['found_in_paper'] = False
                        analysis['relevance'] = f'Low relevance - {matches}/{len(key_terms)} key terms found'
            else:
                analysis['pdf_parse_error'] = 'Failed to download or parse PDF'
        
        paper_analyses.append(analysis)
        
        # Add small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Generate verification summary
    verification_summary = {
        'statement': statement,
        'confidence': 'Low',
        'assessment': 'Unable to verify'
    }
    
    # Check if we found supporting evidence
    direct_matches = [p for p in paper_analyses if p.get('found_in_paper', False)]
    high_relevance = [p for p in paper_analyses if 'High relevance' in p.get('relevance', '')]
    
    if direct_matches:
        verification_summary['confidence'] = 'High'
        verification_summary['assessment'] = f'Statement found in {len(direct_matches)} arXiv paper(s)'
        verification_summary['supporting_papers'] = [p['arxiv_id'] for p in direct_matches]
    elif high_relevance:
        verification_summary['confidence'] = 'Medium'
        verification_summary['assessment'] = f'Related content found in {len(high_relevance)} arXiv paper(s)'
        verification_summary['supporting_papers'] = [p['arxiv_id'] for p in high_relevance]
    
    return {
        'statement': statement,
        'web_search_results': web_search_summary,
        'arxiv_papers': paper_analyses,
        'verification_summary': verification_summary
    }