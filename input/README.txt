HOW TO USE THIS FOLDER
======================

1. PUT YOUR FILES HERE:
   - Your resumes (PDF, DOCX, or TXT files)
   - Your job description (PDF, DOCX, or TXT file)

2. IMPORTANT: Your JD filename must contain one of these words:
   - "job"
   - "jd" 
   - "description"
   - "position"
   
   Examples: job_description.pdf, jd.docx, senior_java_jd.txt

3. RUN THIS COMMAND:
   python screen.py --folder input --top 10
   
   Change "10" to however many top matches you want (5, 10, 20, etc.)

4. RESULTS:
   Check the output/ folder for your results CSV file!

EXAMPLE:
--------
input/
├── job_description.pdf          ← Your JD
├── john_smith_resume.pdf        ← Your resumes
├── sarah_johnson_resume.docx
├── mike_chen_resume.txt
└── ... (add as many resumes as you want)

Then run: python screen.py --folder input --top 10
