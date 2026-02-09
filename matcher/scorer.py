from typing import Dict, List,Set
import json

class ResumeScorer:
    def __init__(self, path: str = None):
        self.config = self.load_config(path)
        self.weights = self.config.get("weights", {
            'rskills' : 0.5,
            'pskills' : 0.25,
            'experience' : 0.15,
            'keyword_density' : 0.1   
        })

    def load_config(self, path: str= None) -> Dict:
        if path:
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {
                    'weights': {   
                        'rskills' : 0.5,
                        'pskills' : 0.25,
                        'experience' : 0.15,
                        'keyword_density' : 0.1   
                    },
                    'min_score': 0.0,
                    'exp_tolerance': 2
                }
    def score_resume(self, resume_skills: Set[str],resume_exp:int,
                     resume_keywords:List[str], jd_data: Dict) -> Dict:
        jd_req=set(skill.lower() for skill in jd_data.get("rskills", []))
        jd_pref=set(skill.lower() for skill in jd_data.get("pskills", []))
        jd_keywords=jd_data.get("keywords", [])
        jd_min_exp=jd_data.get("min_experience", 0)

        rscore=self.calculate_skillmatch(resume_skills, jd_req)
        pscore=self.calculate_skillmatch(resume_skills, jd_pref)
        expscore=self.calculate_experiencematch(resume_exp, jd_min_exp)
        keywordscore=self.calculate_keywordmatch(resume_keywords, jd_keywords)

        total_score=(rscore * self.weights['rskills'] +
                        pscore * self.weights['pskills'] +
                        expscore * self.weights['experience'] +
                        keywordscore * self.weights['keyword_density'])
        return {
            'total_score': round(total_score *100 , 2),
            'rskillscore': round(rscore *100 , 2),
            'pskillscore': round(pscore *100 , 2),
            'experience_score': round(expscore *100 , 2),
            'keyword_score': round(keywordscore *100 , 2),
            'matched_rskills':  list(jd_req.intersection(resume_skills)),
            'matched_pskills': list(jd_pref.intersection(resume_skills)),
            'missing_rskills': list(jd_req.difference(resume_skills)),
            'resume_exp': resume_exp,
            'required_exp': jd_min_exp

        }
    
                     

    def calculate_skillmatch(self, resume_skills: Set[str], jd_skills: Set[str]) -> float:
        if not jd_skills:
            return 1.0
        matched_skills = jd_skills.intersection(resume_skills)
        matched_ratio = len(matched_skills) / len(jd_skills)
        return matched_ratio
    
  
    def calculate_experiencematch(self, resume_exp: int, req_exp: int) -> float:
        if req_exp == 0:
            return 1.0
        
        tolerance = self.config.get("exp_tolerance", 2)

        if resume_exp >= req_exp:
            return 1.0
        
        if resume_exp >= req_exp - tolerance:
            gap = req_exp - resume_exp
            score = 1.0 - (gap / (tolerance+1) *0.3)
            return max(0.7,score)
        
        ratio = resume_exp / req_exp if req_exp > 0 else 0
        return max(0.0, ratio * 0.7)
        



    def calculate_keywordmatch(self, resume_keywords: List[str], jd_keywords: List[str]) -> float:
        if not jd_keywords:
            return 1.0
        resume_kw_set = set(kw.lower() for kw in resume_keywords)
        jd_kw_set = set(kw.lower() for kw in jd_keywords)
        matched_keywords = jd_kw_set.intersection(resume_kw_set)
        if not jd_kw_set:
            return 1.0
        matched_ratio = len(matched_keywords) / len(jd_kw_set)

        freq_bonus = 0
        if resume_keywords:
            keywordc = sum(1 for kw in resume_keywords if kw.lower() in jd_kw_set)
            freq_bonus = min(0.2, keywordc / (len(resume_keywords) ))

        return min(1.0, matched_ratio + freq_bonus)
    
    

    def rankresumes(self, scored_resumes: List[Dict]) -> List[Dict]:

        return sorted(scored_resumes, key=lambda x: x['total_score'], reverse=True)

    def filterbythersold(self, scored_resumes: List[Dict], min_score: float=None) -> List[Dict]:
        if min_score is None:
            min_score = self.config.get("min_score", 0.0)
        return [res for res in scored_resumes if res['total_score'] >= min_score]


     


if __name__ == "main":
    scorer = ResumeScorer()
    resume_skills = {"python", "machine learning", "data analysis"}
    resume_exp = 3
    resume_keywords = ["python", "data analysis", "sql"]
    jd_data = {
        "rskills": ["python", "machine learning"],
        "pskills": ["data analysis", "sql"],
        "keywords": ["python", "data analysis", "sql"],
        "min_experience": 2
    }
    score = scorer.score_resume(resume_skills, resume_exp, resume_keywords, jd_data)
    print(f"Total Score: {score['total_score']}%")
    print(f"Required Skills Score: {score['rskillscore']}%")
    print(f"Preferred Skills Score: {score['pskillscore']}%")
    print(f"Experience Score: {score['experience_score']}%")
    print(f"Keyword Score: {score['keyword_score']}%")
    print(f"Matched Required Skills: {score['matched_rskills']}")
    print(f"Matched Preferred Skills: {score['matched_pskills']}")


