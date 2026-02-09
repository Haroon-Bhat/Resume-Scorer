"""
Resume Screening System - Streamlit Web Interface
Upload resumes and job description, get top matching candidates
"""

import streamlit as st
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
import io
import zipfile

from parsers import ResumeParser, JDParser
from extractors import KeywordExtractor
from matcher import ResumeScorer


# Page configuration
st.set_page_config(
    page_title="Resume Screening System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 0.5rem;
        padding-top: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .stProgress > div > div > div > div {
        background-color: #3498db;
    }
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        color: #34495e;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        border-left: 4px solid #3498db;
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        font-weight: 500;
        border-radius: 6px;
        border: none;
        padding: 0.6rem 2rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        border: none;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_components():
    """Load and cache the parsing components"""
    config_path = Path(__file__).parent / 'data' / 'config.json'
    taxonomy_path = Path(__file__).parent / 'data' / 'skills_taxonomy.json'
    
    resume_parser = ResumeParser()
    jd_parser = JDParser()
    extractor = KeywordExtractor(str(taxonomy_path))
    scorer = ResumeScorer(str(config_path) if config_path.exists() else None)
    
    return resume_parser, jd_parser, extractor, scorer


def parse_jd_text(jd_text, jd_parser):
    """Parse job description from text"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as tmp:
        tmp.write(jd_text)
        tmp_path = tmp.name
    
    try:
        jd_data = jd_parser.parse_file(tmp_path)
        return jd_data
    finally:
        Path(tmp_path).unlink()


def process_resumes(resume_files, jd_data, top_n, min_score, resume_parser, extractor, scorer):
    """Process uploaded resumes and return scored results"""
    
    # Create temporary directory for resumes
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files to temp directory
        st.info(f"Uploading {len(resume_files)} resume files...")
        progress_bar = st.progress(0)
        
        temp_files = []
        file_mapping = {}  # Map file path to original uploaded file
        for idx, uploaded_file in enumerate(resume_files):
            # Save file
            file_path = Path(temp_dir) / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            temp_files.append(file_path)
            file_mapping[str(file_path)] = uploaded_file
            progress_bar.progress((idx + 1) / len(resume_files))
        
        # Parse resumes
        st.info("Parsing resume files...")
        resumes = []
        parse_progress = st.progress(0)
        
        for idx, file_path in enumerate(temp_files):
            try:
                resume = resume_parser.parse_file(str(file_path))
                resume['filename'] = file_path.name  # Add filename to resume data
                resume['file_object'] = file_mapping[str(file_path)]  # Add original file object
                resumes.append(resume)
            except Exception as e:
                st.warning(f"Could not parse {file_path.name}: {str(e)}")
            parse_progress.progress((idx + 1) / len(temp_files))
        
        if not resumes:
            st.error("No resumes could be parsed successfully")
            return None
        
        # Score resumes
        st.info(f"Analyzing and scoring {len(resumes)} resumes...")
        scored_resumes = []
        score_progress = st.progress(0)
        
        for idx, resume in enumerate(resumes):
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
            score_progress.progress((idx + 1) / len(resumes))
        
        # Filter by minimum score
        if min_score is not None:
            scored_resumes = [r for r in scored_resumes if r['score']['total_score'] >= min_score]
        
        # Sort by score
        ranked_resumes = sorted(scored_resumes, key=lambda x: x['score']['total_score'], reverse=True)
        
        # Get top N
        top_resumes = ranked_resumes[:top_n]
        
        return top_resumes
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_results_dataframe(results):
    """Convert results to pandas DataFrame"""
    data = []
    
    for rank, result in enumerate(results, 1):
        resume = result['resume']
        score = result['score']
        
        # data.append({
        #     'Rank': rank,
        #     'Resume File': resume.get('filename', 'Unknown'),
        #     'Candidate Name': resume.get('name', 'Unknown'),
        #     'Email': resume.get('email', ''),
        #     'Phone': resume.get('phone', ''),
        #     'Total Score (%)': f"{score['total_score']:.1f}",
        #     'Required Skills (%)': f"{score.get('required_skills_score', 0):.1f}",
        #     'Preferred Skills (%)': f"{score['preferred_skills_score']:.1f}",
        #     'Experience (%)': f"{score['experience_score']:.1f}",
        #     'Keyword Match (%)': f"{score['keyword_score']:.1f}",
        #     'Experience (Years)': score['resume_experience'],
        #     'Matched Skills': ', '.join(score['matched_required_skills'][:10]),
        #     'Missing Skills': ', '.join(score['missing_required_skills'][:10])
        # })
        data.append({
    'Rank': rank,
    'Resume File': resume.get('filename', 'Unknown'),
    'Candidate Name': resume.get('name', 'Unknown'),
    'Email': resume.get('email', ''),
    'Phone': resume.get('phone', ''),
    'Total Score (%)': f"{score.get('total_score', 0):.1f}",
    'Required Skills (%)': f"{score.get('required_skills_score', 0):.1f}",
    'Preferred Skills (%)': f"{score.get('preferred_skills_score', 0):.1f}",
    'Experience (%)': f"{score.get('experience_score', 0):.1f}",
    'Keyword Match (%)': f"{score.get('keyword_score', 0):.1f}",
    'Experience (Years)': score.get('resume_experience', 0),
    'Matched Skills': ', '.join(score.get('matched_required_skills', [])[:10]),
    'Missing Skills': ', '.join(score.get('missing_required_skills', [])[:10])
})

    
    return pd.DataFrame(data)


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">Haroon\'s Resume Scoring System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Matching resumes to job descriptions</p>', unsafe_allow_html=True)
    
    # Load components
    with st.spinner("Loading system components..."):
        resume_parser, jd_parser, extractor, scorer = load_components()
    
    # Sidebar - Configuration
    st.sidebar.header("Configuration")
    
    top_n = st.sidebar.number_input(
        "Top N Matches",
        min_value=1,
        max_value=100,
        value=10,
        help="Number of top matching resumes to return"
    )
    
    min_score = st.sidebar.number_input(
        "Minimum Score (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        help="Filter resumes below this score (optional)"
    )
    
    if min_score == 0.0:
        min_score = None
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Scoring Weights")
    st.sidebar.markdown("**Required Skills**: 50%")
    st.sidebar.markdown("**Preferred Skills**: 25%")
    st.sidebar.markdown("**Experience**: 15%")
    st.sidebar.markdown("**Keywords**: 10%")
    
    # Main content - Two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<h3 class="section-header">Job Description</h3>', unsafe_allow_html=True)
        jd_input_method = st.radio(
            "Input Method:",
            ["Paste Text", "Upload File"],
            horizontal=True
        )
        
        jd_data = None
        
        if jd_input_method == "Paste Text":
            jd_text = st.text_area(
                "Paste Job Description:",
                height=400,
                placeholder="""Example:
Senior Python Developer

Required Skills:
- 5+ years of Python experience
- Django or Flask
- PostgreSQL
- Docker
- Git

Preferred Skills:
- AWS
- Kubernetes
- React
"""
            )
            
            if jd_text:
                try:
                    jd_data = parse_jd_text(jd_text, jd_parser)
                    with st.expander("Job Description Parsed Successfully", expanded=False):
                        st.write(f"**Required Skills:** {len(jd_data['required_skills'])} skills identified")
                        if jd_data['required_skills']:
                            st.write(f"Sample: {', '.join(list(jd_data['required_skills'])[:5])}")
                        st.write(f"**Preferred Skills:** {len(jd_data['preferred_skills'])} skills identified")
                        if jd_data['preferred_skills']:
                            st.write(f"Sample: {', '.join(list(jd_data['preferred_skills'])[:5])}")
                        st.write(f"**Minimum Experience:** {jd_data['min_experience']} years")
                except Exception as e:
                    st.error(f"Error parsing job description: {str(e)}")
        
        else:
            jd_file = st.file_uploader(
                "Upload Job Description File:",
                type=['txt', 'pdf', 'docx', 'doc'],
                help="Supported formats: TXT, PDF, DOCX, DOC"
            )
            
            if jd_file:
                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(jd_file.name).suffix) as tmp:
                    tmp.write(jd_file.getbuffer())
                    tmp_path = tmp.name
                
                try:
                    jd_data = jd_parser.parse_file(tmp_path)
                    with st.expander("Job Description Parsed Successfully", expanded=False):
                        st.write(f"**Required Skills:** {len(jd_data['required_skills'])} skills identified")
                        if jd_data['required_skills']:
                            st.write(f"Sample: {', '.join(list(jd_data['required_skills'])[:5])}")
                        st.write(f"**Preferred Skills:** {len(jd_data['preferred_skills'])} skills identified")
                        if jd_data['preferred_skills']:
                            st.write(f"Sample: {', '.join(list(jd_data['preferred_skills'])[:5])}")
                        st.write(f"**Minimum Experience:** {jd_data['min_experience']} years")
                except Exception as e:
                    st.error(f"Error parsing job description: {str(e)}")
                finally:
                    Path(tmp_path).unlink()
    
    with col2:
        st.markdown('<h3 class="section-header">Resume Files</h3>', unsafe_allow_html=True)
        resume_files = st.file_uploader(
            "Upload Resume Files:",
            type=['txt', 'pdf', 'docx', 'doc'],
            accept_multiple_files=True,
            help="Upload multiple resumes (500-1000 supported). Formats: TXT, PDF, DOCX, DOC"
        )
        
        if resume_files:
            st.success(f"{len(resume_files)} resume files uploaded")
            
            # Show file list in expander
            with st.expander("View Uploaded Files", expanded=False):
                for idx, file in enumerate(resume_files[:20], 1):
                    st.text(f"{idx}. {file.name}")
                if len(resume_files) > 20:
                    st.text(f"... and {len(resume_files) - 20} more files")
    
    # Process button
    st.markdown("---")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        process_button = st.button("Start Screening Process", type="primary", use_container_width=True)
    
    # Process resumes when button is clicked
    if process_button:
        if not jd_data:
            st.error("Please provide a job description first")
        elif not resume_files:
            st.error("Please upload resume files")
        else:
            st.markdown("---")
            st.markdown('<h3 class="section-header">Processing</h3>', unsafe_allow_html=True)
            
            start_time = datetime.now()
            
            # Process resumes
            results = process_resumes(
                resume_files, jd_data, top_n, min_score,
                resume_parser, extractor, scorer
            )
            
            if results:
                processing_time = (datetime.now() - start_time).total_seconds()
                
                st.success(f"Screening completed successfully in {processing_time:.2f} seconds")
                st.markdown("---")
                
                # Display results
                st.markdown('<h3 class="section-header">Top Matching Candidates</h3>', unsafe_allow_html=True)
                
                # Create DataFrame
                df = create_results_dataframe(results)
                
                # Display summary metrics
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Total Resumes Processed", len(resume_files))
                with col_m2:
                    st.metric("Top Matches Returned", len(results))
                with col_m3:
                    avg_score = sum([r['score']['total_score'] for r in results]) / len(results)
                    st.metric("Average Match Score", f"{avg_score:.1f}%")
                with col_m4:
                    top_score = results[0]['score']['total_score'] if results else 0
                    st.metric("Highest Match Score", f"{top_score:.1f}%")
                
                # Display table
                st.dataframe(df, use_container_width=True, height=400)
                
                # Download buttons
                st.markdown("---")
                st.markdown("### Export Options")
                col_d1, col_d2, col_d3 = st.columns([1, 1, 1])
                
                with col_d1:
                    # Download CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Results (CSV)",
                        data=csv,
                        file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_d2:
                    # Download JSON
                    json_data = df.to_json(orient='records', indent=2)
                    st.download_button(
                        label="Download Results (JSON)",
                        data=json_data,
                        file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                with col_d3:
                    # Download all matched resumes as ZIP
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for idx, result in enumerate(results, 1):
                            if 'file_object' in result['resume']:
                                file_obj = result['resume']['file_object']
                                filename = result['resume'].get('filename', f'resume_{idx}.pdf')
                                # Add rank prefix to filename
                                ranked_filename = f"{idx:02d}_{filename}"
                                zip_file.writestr(ranked_filename, file_obj.getvalue())
                    
                    st.download_button(
                        label="Download All Resumes (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"top_resumes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                
                # Detailed view with individual resume downloads
                st.markdown("---")
                st.markdown('<h3 class="section-header">Detailed Candidate Profiles</h3>', unsafe_allow_html=True)
                
                for idx, result in enumerate(results[:10], 1):  # Show top 10 in detail
                    resume_filename = result['resume'].get('filename', 'Unknown')
                    candidate_name = result['resume'].get('name', 'Unknown')
                    
                    with st.expander(f"Rank #{idx} - {resume_filename} - Match Score: {result['score']['total_score']:.1f}%"):
                        col_detail1, col_detail2 = st.columns(2)
                        
                        with col_detail1:
                            st.markdown("**Candidate Information**")
                            st.write(f"Resume File: {resume_filename}")
                            st.write(f"Name: {candidate_name}")
                            st.write(f"Email: {result['resume'].get('email', 'N/A')}")
                            st.write(f"Phone: {result['resume'].get('phone', 'N/A')}")
                            st.write(f"Experience: {result['experience']} years")
                        
                        with col_detail2:
                            st.markdown("**Score Breakdown**")
                            st.write(f"Required Skills Match: {result['score']['required_skills_score']:.1f}%")
                            st.write(f"Preferred Skills Match: {result['score']['preferred_skills_score']:.1f}%")
                            st.write(f"Experience Match: {result['score']['experience_score']:.1f}%")
                            st.write(f"Keyword Match: {result['score']['keyword_score']:.1f}%")
                        
                        st.markdown("**Skills Matched**")
                        if result['score']['matched_required_skills']:
                            st.write(", ".join(result['score']['matched_required_skills']))
                        else:
                            st.write("No matching skills found")
                        
                        st.markdown("**Skills Missing**")
                        if result['score']['missing_required_skills']:
                            st.write(", ".join(result['score']['missing_required_skills']))
                        else:
                            st.write("No missing skills")
                        
                        # Download individual resume button
                        if 'file_object' in result['resume']:
                            file_obj = result['resume']['file_object']
                            st.download_button(
                                label=f"Download Resume File",
                                data=file_obj.getvalue(),
                                file_name=resume_filename,
                                mime="application/octet-stream",
                                key=f"download_{idx}"
                            )


if __name__ == "__main__":
    main()

