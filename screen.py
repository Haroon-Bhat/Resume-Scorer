"""
Simple Resume Screening - Single Folder Input
Upload resumes and JD in one folder, get top matches automatically
"""

import argparse
import sys
from pathlib import Path

from parsers import ResumeParser, JDParser
from extractors import KeywordExtractor
from matcher import ResumeScorer
import csv
import json
from datetime import datetime


def find_jd_file(folder_path):
    """Automatically find the job description file in the folder"""
    folder = Path(folder_path)
    
    # Look for common JD file names
    jd_keywords = ['job', 'jd', 'description', 'opening', 'position', 'role', 'vacancy']
    
    for file in folder.iterdir():
        if file.is_file():
            filename_lower = file.stem.lower()
            # Check if filename contains JD-related keywords
            if any(keyword in filename_lower for keyword in jd_keywords):
                if file.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
                    return file
    
    # If no JD-specific name found, look for any PDF/DOCX that's not in common resume patterns
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
            filename_lower = file.stem.lower()
            # Skip if it looks like a resume
            if not any(word in filename_lower for word in ['resume', 'cv', 'candidate']):
                return file
    
    return None


def screen_resumes(input_folder, top_n=10, min_score=None, output_format='csv'):
    """
    Screen resumes in a single folder containing both JD and resumes
    
    Args:
        input_folder: Path to folder containing JD and resume files
        top_n: Number of top matches to return
        min_score: Minimum score threshold
        output_format: Output format ('csv' or 'json')
    """
    
    print(f"\n{'='*60}")
    print("RESUME SCREENING SYSTEM - SIMPLE MODE")
    print(f"{'='*60}\n")
    
    input_path = Path(input_folder)
    
    if not input_path.exists():
        print(f"✗ Error: Folder not found: {input_folder}")
        return
    
    if not input_path.is_dir():
        print(f"✗ Error: Not a directory: {input_folder}")
        return
    
    # Initialize components
    config_path = Path(__file__).parent / 'data' / 'config.json'
    taxonomy_path = Path(__file__).parent / 'data' / 'skills_taxonomy.json'
    
    resume_parser = ResumeParser()
    jd_parser = JDParser()
    extractor = KeywordExtractor(str(taxonomy_path))
    scorer = ResumeScorer(str(config_path) if config_path.exists() else None)
    
    # Step 1: Find JD file
    print(f"Scanning folder: {input_folder}")
    jd_file = find_jd_file(input_folder)
    
    if not jd_file:
        print("✗ Error: Could not find job description file")
        print("   Tip: Name your JD file with keywords like 'job', 'jd', 'description', or 'position'")
        return
    
    print(f"✓ Found JD: {jd_file.name}\n")
    
    # Step 2: Parse JD
    print("Parsing Job Description...")
    try:
        jd_data = jd_parser.parse_file(str(jd_file))
        print(f"✓ Required Skills: {len(jd_data['required_skills'])}")
        print(f"✓ Preferred Skills: {len(jd_data['preferred_skills'])}")
        print(f"✓ Min Experience: {jd_data['min_experience']} years\n")
    except Exception as e:
        print(f"✗ Error parsing JD: {e}")
        return
    
    # Step 3: Find and parse all resume files (excluding JD)
    print("Scanning for resumes...")
    resumes = []
    resume_count = 0
    
    for file in input_path.iterdir():
        if file.is_file() and file != jd_file:
            if file.suffix.lower() in ['.pdf', '.docx', '.doc', '.txt']:
                try:
                    resume = resume_parser.parse_file(str(file))
                    resumes.append(resume)
                    resume_count += 1
                except Exception as e:
                    print(f"  Warning: Could not parse {file.name}: {e}")
    
    if not resumes:
        print("✗ Error: No resume files found")
        print("   Supported formats: PDF, DOCX, DOC, TXT")
        return
    
    print(f"✓ Loaded {resume_count} resumes\n")
    
    # Step 4: Extract & Score
    print("Scoring resumes...")
    scored_resumes = []
    
    for idx, resume in enumerate(resumes, 1):
        if idx % 10 == 0:
            print(f"  Processed {idx}/{resume_count} resumes...")
        
        # Extract from resume
        resume_skills = extractor.extract_skills(resume['text'])
        resume_experience = extractor.extract_experience_years(resume['text'])
        resume_keywords = extractor.extract_keywords(resume['text'])
        
        # Score the resume
        score = scorer.score_resume(
            resume_skills, resume_experience, resume_keywords, jd_data
        )
        
        scored_resumes.append({
            'resume': resume,
            'score': score,
            'skills': list(resume_skills),
            'experience': resume_experience
        })
    
    print(f"✓ Scored {resume_count} resumes\n")
    
    # Step 5: Rank & Filter
    print("Ranking results...")
    
    # Apply minimum score filter if specified
    if min_score is not None:
        scored_resumes = [r for r in scored_resumes if r['score']['total_score'] >= min_score]
        print(f"✓ Filtered to {len(scored_resumes)} resumes above {min_score}% threshold")
    
    # Sort by score
    ranked_resumes = sorted(scored_resumes, key=lambda x: x['score']['total_score'], reverse=True)
    
    # Get top N
    top_resumes = ranked_resumes[:top_n]
    print(f"✓ Selected top {len(top_resumes)} matches\n")
    
    # Step 6: Save Results
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = input_path.name
    
    if output_format == 'csv':
        output_path = output_dir / f'results_{folder_name}_{timestamp}.csv'
        save_csv(top_resumes, output_path)
    else:
        output_path = output_dir / f'results_{folder_name}_{timestamp}.json'
        save_json(top_resumes, output_path)
    
    print(f"✓ Results saved to: {output_path}\n")
    
    # Display Summary
    display_summary(top_resumes)


def save_csv(results, output_path):
    """Save results to CSV file"""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'Rank', 'File Name', 'Total Score (%)',
            'Required Skills (%)', 'Preferred Skills (%)', 'Experience (%)',
            'Keyword Match (%)', 'Experience (Years)', 'Matched Skills',
            'Missing Skills'
        ])
        
        # Data rows
        for rank, result in enumerate(results, 1):
            resume = result['resume']
            score = result['score']
            
            # writer.writerow([
            #     rank,
            #     resume.get('file_name', 'Unknown'),
            #     score['total_score'],
            #     score['required_skills_score'],
            #     score['preferred_skills_score'],
            #     score['experience_score'],
            #     score['keyword_score'],
            #     score['resume_experience'],
            #     ', '.join(score['matched_required_skills'][:10]),
            #     ', '.join(score['missing_required_skills'][:10])
            # ])
            writer.writerow([
    rank,
    resume.get('file_name', 'Unknown'),
    score.get('total_score', 0.0),
    score.get('required_skills_score', 0.0),
    score.get('preferred_skills_score', 0.0),
    score.get('experience_score', 0.0),
    score.get('keyword_score', 0.0),
    score.get('resume_experience', 0),
    ', '.join(score.get('matched_required_skills', [])[:10]),
    ', '.join(score.get('missing_required_skills', [])[:10])
])


def save_json(results, output_path):
    """Save results to JSON file"""
    output_data = []
    
    for rank, result in enumerate(results, 1):
        resume = result['resume']
        score = result['score']
        
        output_data.append({
            'rank': rank,
            'file_name': resume.get('file_name', 'Unknown'),
            'total_score': score['total_score'],
            'scores': {
                'required_skills': score['required_skills_score'],
                'preferred_skills': score['preferred_skills_score'],
                'experience': score['experience_score'],
                'keyword_match': score['keyword_score']
            },
            'experience_years': score['resume_experience'],
            'matched_required_skills': score['matched_required_skills'],
            'matched_preferred_skills': score['matched_preferred_skills'],
            'missing_required_skills': score['missing_required_skills']
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)


def display_summary(results):
    """Display summary of top results"""
    print(f"{'='*60}")
    print("TOP MATCHING RESUMES")
    print(f"{'='*60}\n")
    
    for rank, result in enumerate(results[:5], 1):  # Show top 5
        resume = result['resume']
        score = result['score']
        
        # print(f"#{rank} - {resume.get('file_name', 'Unknown')}")
        # print(f"     Score: {score['total_score']:.1f}%")
        # # print(f"     Experience: {score['resume_experience']} years")
        # print(f"     Experience: {score.get('resume_experience', 0)} years")

        # print(f"     Matched Skills: {', '.join(score['matched_required_skills'][:5])}")
        # if score['missing_required_skills']:
        #     print(f"     Missing: {', '.join(score['missing_required_skills'][:3])}")
        # print()
        print(f"#{rank} - {resume.get('file_name', 'Unknown')}")
        print(f"     Score: {score.get('total_score', 0.0):.1f}%")
        print(f"     Experience: {score.get('resume_experience', 0)} years")

        print(f"     Matched Skills: {', '.join(score.get('matched_required_skills', [])[:5])}")
        if score.get('missing_required_skills'):  # Safe check
                print(f"     Missing: {', '.join(score.get('missing_required_skills', [])[:3])}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Resume Screening System - Simple Mode (Single Folder Input)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - screen all resumes in folder
  python screen.py --folder input_folder --top 10

  # With minimum score threshold
  python screen.py --folder my_resumes --top 15 --min-score 70

  # Output as JSON
  python screen.py --folder candidates --top 20 --format json

Folder Structure:
  input_folder/
    ├── job_description.pdf    (JD file - name should contain 'job', 'jd', or 'description')
    ├── resume_001.pdf         (Resume files)
    ├── resume_002.docx
    ├── candidate_003.pdf
    └── ...
        """
    )
    
    parser.add_argument(
        '--folder',
        required=True,
        help='Path to folder containing JD and resume files'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Number of top matches to return (default: 10)'
    )
    
    parser.add_argument(
        '--min-score',
        type=float,
        default=None,
        help='Minimum score threshold 0-100 (default: no threshold)'
    )
    
    parser.add_argument(
        '--format',
        choices=['csv', 'json'],
        default='csv',
        help='Output format (default: csv)'
    )
    
    args = parser.parse_args()
    
    # Run screening
    try:
        screen_resumes(
            input_folder=args.folder,
            top_n=args.top,
            min_score=args.min_score,
            output_format=args.format
        )
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError during screening: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()