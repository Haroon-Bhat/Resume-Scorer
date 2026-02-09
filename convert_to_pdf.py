"""
Convert JSONL resumes to PDF format
Extracts 500 resumes and creates individual PDF files
"""

import json
import os
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
except ImportError:
    print("Installing reportlab...")
    os.system("pip install reportlab")
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch


def create_resume_pdf(resume_data: dict, output_path: str):
    """Create a PDF file from resume data"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title - Name
    name = resume_data.get('Name', 'Unknown')
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12
    )
    story.append(Paragraph(name, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Contact Info
    email = resume_data.get('Email', '')
    phone = resume_data.get('Phone', '')[:20] if resume_data.get('Phone') else ''
    location = resume_data.get('Location', '')
    
    contact_style = styles['Normal']
    if email:
        story.append(Paragraph(f"<b>Email:</b> {email}", contact_style))
    if location:
        story.append(Paragraph(f"<b>Location:</b> {location}", contact_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Category/Title
    category = resume_data.get('Category', '')
    if category:
        story.append(Paragraph(f"<b>Role:</b> {category}", styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
    
    # Summary
    summary = resume_data.get('Summary', '')
    if summary:
        story.append(Paragraph("<b>Summary</b>", styles['Heading2']))
        # Truncate and clean summary
        clean_summary = summary[:500].replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(clean_summary, contact_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Skills
    skills = resume_data.get('Skills', '')
    if skills:
        story.append(Paragraph("<b>Skills</b>", styles['Heading2']))
        story.append(Paragraph(skills.replace('<', '&lt;').replace('>', '&gt;'), contact_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Experience
    experience = resume_data.get('Experience', '')
    if experience:
        story.append(Paragraph("<b>Experience</b>", styles['Heading2']))
        # Truncate experience to fit in PDF
        clean_exp = experience[:1500].replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(clean_exp, contact_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Education
    education = resume_data.get('Education', '')
    if education:
        story.append(Paragraph("<b>Education</b>", styles['Heading2']))
        story.append(Paragraph(education.replace('<', '&lt;').replace('>', '&gt;'), contact_style))
    
    doc.build(story)


def convert_jsonl_to_pdfs(jsonl_path: str, output_dir: str, limit: int = 500):
    """Convert JSONL resumes to PDF files"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Converting {limit} resumes to PDF...")
    print(f"Output directory: {output_path.absolute()}")
    
    converted = 0
    errors = 0
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if converted >= limit:
                break
                
            line = line.strip()
            if not line:
                continue
            
            try:
                resume = json.loads(line)
                resume_id = resume.get('ResumeID', f'RESUME_{line_num}')
                name = resume.get('Name', 'Unknown').replace(' ', '_')
                
                # Create safe filename
                filename = f"{resume_id}_{name}.pdf"
                filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
                
                pdf_path = output_path / filename
                create_resume_pdf(resume, str(pdf_path))
                
                converted += 1
                if converted % 50 == 0:
                    print(f"  Converted {converted}/{limit} resumes...")
                    
            except Exception as e:
                errors += 1
                print(f"  Error on line {line_num}: {e}")
                continue
    
    print(f"\n✓ Successfully converted {converted} resumes to PDF")
    if errors:
        print(f"✗ {errors} errors encountered")
    print(f"📁 PDFs saved to: {output_path.absolute()}")


if __name__ == "__main__":
    jsonl_file = "resumes_dataset.jsonl"
    output_folder = "resumes_pdf"
    
    convert_jsonl_to_pdfs(jsonl_file, output_folder, limit=500)