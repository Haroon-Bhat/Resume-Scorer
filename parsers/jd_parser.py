"""
Job Description Parser Module
Extracts requirements, skills, and keywords from job descriptions
"""

import re
from pathlib import Path
from typing import Dict, List, Set
import PyPDF2
from docx import Document


class JDParser:
    """Parse job descriptions and extract requirements - Handles multiple JD formats"""

    def __init__(self):
        # Keywords that indicate REQUIRED skills section
        self.required_keywords = [
            'required', 'must have', 'mandatory', 'essential',
            'required skills', 'requirements', 'must possess',
            'key requirements', 'core skills', 'minimum qualifications',
            'basic qualifications', 'what you need', 'what we need',
            'you must have', 'you should have', 'necessary skills',
            'technical requirements', 'hard requirements', 'non-negotiable',
            'qualifications required', 'skills required', 'expected skills',
            'we are looking for', 'we expect', 'you will need'
        ]

        # Keywords that indicate PREFERRED/NICE-TO-HAVE skills section
        self.preferred_keywords = [
            'preferred', 'nice to have', 'desired', 'plus',
            'preferred skills', 'bonus', 'advantage', 'good to have',
            'additional skills', 'preferred qualifications', 'a plus',
            'ideal candidate', 'would be nice', 'beneficial',
            'extra credit', 'not required but', 'optional',
            'added advantage', 'brownie points', 'icing on the cake',
            'it would be great if', 'even better if', 'extra skills'
        ]

        # Patterns to extract years of experience (handles many formats)
        self.experience_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?).*?(?:experience|exp)',
            r'(?:experience|exp).*?(\d+)\+?\s*(?:years?|yrs?)',
            r'minimum\s+(\d+)\s+(?:years?|yrs?)',
            r'at\s+least\s+(\d+)\s+(?:years?|yrs?)',
            r'(\d+)\s*-\s*\d+\s*(?:years?|yrs?)',  # Range: 3-5 years
            r'(\d+)\s*to\s*\d+\s*(?:years?|yrs?)',  # Range: 3 to 5 years
            r'over\s+(\d+)\s+(?:years?|yrs?)',  # Over 5 years
            r'more\s+than\s+(\d+)\s+(?:years?|yrs?)',  # More than 5 years
            r'(\d+)\+\s*(?:years?|yrs?)',  # 5+ years
            r'around\s+(\d+)\s+(?:years?|yrs?)',  # Around 5 years
        ]
    
    def parse_file(self, file_path: str) -> Dict:
        """
        Parse job description from file (supports TXT, PDF, DOCX)
        
        Args:
            file_path: Path to the JD file
            
        Returns:
            Dictionary with parsed JD data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Job description file not found: {file_path}")
        
        # Extract text based on file type
        file_ext = file_path.suffix.lower()
        
        try:
            if file_ext == '.pdf':
                text = self._extract_pdf(file_path)
            elif file_ext in ['.docx', '.doc']:
                text = self._extract_docx(file_path)
            else:  # .txt or any other text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
        except Exception as e:
            raise Exception(f"Error reading JD file: {e}")
        
        return self.parse_text(text)
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {e}")
        return text.strip()
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise Exception(f"Error reading DOCX: {e}")
        return text.strip()
    
    def parse_text(self, text: str) -> Dict:
        """
        Parse job description from text
        
        Args:
            text: Job description text
            
        Returns:
            Dictionary with parsed JD requirements
        """
        # Normalize text
        text_lower = text.lower()
        
        # Extract experience requirements
        min_experience = self._extract_experience(text_lower)
        
        # Split text into sections
        required_section, preferred_section = self._split_sections(text_lower)
        
        # Extract skills from each section
        required_skills = self._extract_skills(required_section)
        preferred_skills = self._extract_skills(preferred_section)
        
        # If no clear sections, extract all skills and mark as required
        if not required_skills and not preferred_skills:
            all_skills = self._extract_skills(text_lower)
            required_skills = all_skills
        
        # Extract general keywords (technologies, tools, methodologies)
        keywords = self._extract_keywords(text_lower)
        
        return {
            'text': text,
            'min_experience': min_experience,
            'required_skills': list(required_skills),
            'preferred_skills': list(preferred_skills),
            'keywords': list(keywords)
        }
    
    def _extract_experience(self, text: str) -> int:
        """Extract minimum years of experience from JD"""
        years = []
        
        for pattern in self.experience_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match.group(1))
                    years.append(year)
                except (ValueError, IndexError):
                    continue
        
        # Return the minimum mentioned (most restrictive)
        return min(years) if years else 0
    
    def _split_sections(self, text: str) -> tuple:
        """Split JD into required and preferred sections"""
        required_text = ""
        preferred_text = ""
        
        # Try to identify required section
        for keyword in self.required_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?={"|".join(self.preferred_keywords)}|$)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                required_text += match.group(1) + " "
        
        # Try to identify preferred section
        for keyword in self.preferred_keywords:
            pattern = rf'{keyword}[:\s]+(.*?)(?={"|".join(self.required_keywords)}|$)'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                preferred_text += match.group(1) + " "
        
        # If no clear sections found, return empty strings
        return required_text.strip(), preferred_text.strip()
    
    def _extract_skills(self, text: str) -> Set[str]:
        """Extract technical skills from text - Enhanced for comprehensive skill detection"""
        skills = set()

        # Comprehensive technical skills patterns
        skill_patterns = [
            # Programming languages
            r'\b(java|python|javascript|typescript|c\+\+|c#|c|ruby|php|go|golang|rust|swift|kotlin|scala|perl|r|matlab|vba|bash|shell|powershell)\b',

            # Java ecosystem
            r'\b(spring|spring\s*boot|spring\s*mvc|spring\s*cloud|hibernate|jpa|jdbc|j2ee|jee|java\s*ee|servlets|jsp|jsf|struts|maven|gradle|tomcat|jboss|wildfly|weblogic|websphere)\b',

            # Python ecosystem
            r'\b(django|flask|fastapi|pandas|numpy|scipy|tensorflow|pytorch|keras|scikit-learn|sklearn|celery|asyncio)\b',

            # JavaScript/Frontend frameworks
            r'\b(react|react\.?js|angular|angular\.?js|vue|vue\.?js|next\.?js|nuxt|svelte|ember|backbone|jquery|redux|mobx|webpack|babel|vite|npm|yarn|pnpm)\b',

            # Backend frameworks
            r'\b(node\.?js|express\.?js|express|nestjs|nest\.?js|asp\.net|\.net|\.net\s*core|rails|ruby\s*on\s*rails|laravel|symfony|codeigniter|gin|echo|fiber)\b',

            # Databases
            r'\b(mysql|postgresql|postgres|mongodb|mongo|oracle|sql\s*server|mssql|sqlite|redis|cassandra|dynamodb|couchdb|mariadb|neo4j|elasticsearch|elastic)\b',
            r'\b(sql|nosql|plsql|pl/sql|t-sql|rdbms|database)\b',

            # Cloud platforms
            r'\b(aws|amazon\s*web\s*services|azure|microsoft\s*azure|gcp|google\s*cloud|cloud|heroku|digitalocean|linode|vercel|netlify)\b',

            # AWS services
            r'\b(ec2|s3|lambda|rds|dynamodb|sqs|sns|cloudfront|cloudwatch|ecs|eks|fargate|api\s*gateway|cognito|iam)\b',

            # DevOps & CI/CD
            r'\b(docker|kubernetes|k8s|jenkins|git|github|gitlab|bitbucket|ci/cd|cicd|terraform|ansible|puppet|chef|vagrant|helm|argocd)\b',

            # Web technologies
            r'\b(html5?|css3?|sass|scss|less|tailwind|bootstrap|xml|json|yaml|rest|restful|soap|graphql|api|apis|microservices|micro-services)\b',

            # Message queues & streaming
            r'\b(kafka|rabbitmq|activemq|sqs|redis|celery|zeromq|pulsar)\b',

            # Testing tools
            r'\b(junit|testng|mockito|jest|mocha|chai|cypress|selenium|pytest|unittest|rspec|jasmine|karma|protractor)\b',

            # Project management & collaboration
            r'\b(jira|confluence|trello|asana|slack|teams|notion|monday)\b',

            # Methodologies
            r'\b(agile|scrum|kanban|waterfall|tdd|bdd|ddd|lean|xp|extreme\s*programming|devops|devsecops)\b',

            # Data & Analytics
            r'\b(hadoop|spark|hive|pig|airflow|etl|data\s*warehouse|snowflake|redshift|bigquery|tableau|power\s*bi|looker)\b',

            # Mobile development
            r'\b(android|ios|react\s*native|flutter|xamarin|ionic|swift|objective-c|kotlin)\b',

            # Security
            r'\b(oauth|jwt|ssl|tls|https|encryption|security|owasp|penetration|vulnerability)\b',

            # Monitoring & Logging
            r'\b(prometheus|grafana|elk|splunk|datadog|newrelic|dynatrace|logstash|kibana)\b',

            # Version control
            r'\b(git|svn|subversion|mercurial|github|gitlab|bitbucket)\b',

            # Architecture patterns
            r'\b(mvc|mvvm|mvp|clean\s*architecture|hexagonal|cqrs|event\s*sourcing|saga|domain\s*driven)\b',
        ]

        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill = match.group(1).strip()
                if skill:
                    # Normalize skill names
                    normalized = self._normalize_skill(skill)
                    skills.add(normalized)

        return skills

    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill names to consistent format"""
        skill = skill.lower().strip()

        # Normalize common variations
        normalizations = {
            'react.js': 'react',
            'reactjs': 'react',
            'vue.js': 'vue',
            'vuejs': 'vue',
            'node.js': 'nodejs',
            'express.js': 'express',
            'next.js': 'nextjs',
            'angular.js': 'angular',
            'angularjs': 'angular',
            'nest.js': 'nestjs',
            'golang': 'go',
            'postgres': 'postgresql',
            'mongo': 'mongodb',
            'k8s': 'kubernetes',
            'amazon web services': 'aws',
            'microsoft azure': 'azure',
            'google cloud': 'gcp',
            'pl/sql': 'plsql',
            'mssql': 'sql server',
        }

        return normalizations.get(skill, skill)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract important keywords and technologies"""
        keywords = set()
        
        # Extract capitalized technology names (e.g., "Spring Boot", "Apache Kafka")
        cap_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        matches = re.finditer(cap_pattern, text, re.MULTILINE)
        for match in matches:
            keyword = match.group(1)
            # Filter out common words
            if keyword.lower() not in ['the', 'and', 'for', 'with', 'this', 'that']:
                keywords.add(keyword.lower())
        
        # Extract version numbers with technologies
        version_pattern = r'\b([a-z]+\s*\d+(?:\.\d+)?)\b'
        matches = re.finditer(version_pattern, text, re.IGNORECASE)
        for match in matches:
            keywords.add(match.group(1).lower())
        
        return keywords


if __name__ == "__main__":
    # Test the parser
    parser = JDParser()
    
    # Test with sample JD text
    sample_jd = """
    Senior Java Developer Position
    
    Required Skills:
    - 5+ years of experience in Java development
    - Strong knowledge of Spring Boot and Hibernate
    - Experience with microservices architecture
    - Proficiency in SQL and PostgreSQL
    - RESTful API development
    
    Preferred Skills:
    - Experience with AWS or Azure
    - Knowledge of Docker and Kubernetes
    - Familiarity with React or Angular
    """
    
    result = parser.parse_text(sample_jd)
    print(f"Min Experience: {result['min_experience']} years")
    print(f"Required Skills: {result['required_skills']}")
    print(f"Preferred Skills: {result['preferred_skills']}")
    print(f"Keywords: {result['keywords']}")