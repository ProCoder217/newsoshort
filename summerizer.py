# --- Standard Library Imports ---
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass
import threading

# --- Third-Party Imports ---
# NLTK: Ensure you have the necessary data downloaded:
# nltk.download('punkt')
# nltk.download('stopwords')
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt'); nltk.download('stopwords')"
# scikit-learn
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

# ==============================================================================
# --- CONFIGURATION: TAXONOMY ---
# ==============================================================================
# The canonical mapping of each subgenre to its main genre.
# This serves as the single source of truth for the taxonomy.
SUBGENRES: Dict[str, str] = {
    # Politics
    "Elections": "Politics", "Policy": "Politics", "Diplomacy": "Politics", "Defense": "Politics", "Parliament": "Politics",
    "Governance": "Politics", "Judiciary": "Politics", "Regulation": "Politics", "Public Health Policy": "Politics", "Civil Rights": "Politics",
    # Business
    "Markets": "Business", "Banking": "Business", "Startups": "Business", "M&A": "Business", "Earnings": "Business",
    "Commodities": "Business", "Trade": "Business", "Venture Capital": "Business", "Corporate Governance": "Business", "Retail": "Business",
    # Technology
    "AI": "Technology", "Cybersecurity": "Technology", "Gadgets": "Technology", "Software": "Technology", "Hardware": "Technology",
    "Mobile": "Technology", "Cloud": "Technology", "Social Media": "Technology", "Semiconductors": "Technology", "Enterprise IT": "Technology",
    # Science
    "Space": "Science", "Physics": "Science", "Biology": "Science", "Chemistry": "Science", "Research Funding": "Science",
    # Health
    "Public Health": "Health", "Infectious Disease": "Health", "Mental Health": "Health", "Healthcare Policy": "Health", "Pharma": "Health",
    # Sports
    "Cricket": "Sports", "Football": "Sports", "Tennis": "Sports", "Hockey": "Sports", "Olympics": "Sports",
    "Badminton": "Sports", "Athletics": "Sports", "Esports": "Sports", "Kabaddi": "Sports", "Chess": "Sports",
    # Entertainment
    "Bollywood": "Entertainment", "Streaming": "Entertainment", "Television": "Entertainment", "Music": "Entertainment", "Celebrities": "Entertainment",
    "Reviews": "Entertainment", "Box Office": "Entertainment", "Web Series": "Entertainment", "Awards": "Entertainment", "Regional Cinema": "Entertainment",
    # World
    "Geopolitics": "World", "Conflicts": "World", "Sanctions": "World", "Global Economy": "World", "International Organizations": "World",
    # India
    "Central Government": "India", "State Politics": "India", "Infrastructure": "India", "Rural Development": "India", "Social Welfare": "India",
    # Environment
    "Climate Change": "Environment", "Pollution": "Environment", "Wildlife": "Environment", "Renewable Energy": "Environment", "Conservation": "Environment",
    # Education
    "Higher Education": "Education", "Exams": "Education", "EdTech": "Education", "Scholarships": "Education", "Policy Reform": "Education",
    # Law & Order
    "Crime": "Law & Order", "Policing": "Law & Order", "Courts": "Law & Order", "Anti-corruption": "Law & Order", "Cybercrime": "Law & Order",
    # Lifestyle
    "Food": "Lifestyle", "Fashion": "Lifestyle", "Fitness": "Lifestyle", "Relationships": "Lifestyle", "Culture": "Lifestyle",
    # Opinion
    "Editorial": "Opinion", "Op-Ed": "Opinion", "Analysis": "Opinion", "Letters": "Opinion", "Columns": "Opinion",
    # Travel
    "Destinations": "Travel", "Aviation": "Travel", "Railways": "Travel", "Hospitality": "Travel", "Travel Advisory": "Travel",
    # Automobile
    "EVs": "Automobile", "Auto Launches": "Automobile", "Motorsports": "Automobile", "Auto Policy": "Automobile", "Auto Supply Chain": "Automobile",
    # Real Estate
    "Housing": "Real Estate", "Commercial": "Real Estate", "REITs": "Real Estate", "Regulatory": "Real Estate", "Home Loans": "Real Estate",
    # Finance
    "Mutual Funds": "Finance", "Insurance": "Finance", "Taxation": "Finance", "Fintech": "Finance", "Pensions": "Finance",
    # Agriculture
    "Crops": "Agriculture", "Irrigation": "Agriculture", "Agri Policy": "Agriculture", "Agri Markets": "Agriculture", "Agri Tech": "Agriculture",
    # Weather
    "Monsoon": "Weather", "Heatwave": "Weather", "Cyclone": "Weather", "Air Quality": "Weather", "Forecast": "Weather",
}


# ==============================================================================
# --- CORE LOGIC CLASS ---
# ==============================================================================

class NewsProcessor:
    """
    Encapsulates news summarization and genre classification functionality.

    This class uses a singleton pattern to ensure that the expensive resources
    (like the ML model) are initialized only once in a thread-safe manner.
    """
    _instance: Optional['NewsProcessor'] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking to ensure thread safety
                if cls._instance is None:
                    cls._instance = super(NewsProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initializes the NewsProcessor, setting up taxonomy and state."""
        # Prevent re-initialization if singleton instance already exists
        if hasattr(self, '_initialized') and self._initialized:
            return

        # --- Taxonomy setup (derived from the single source of truth) ---
        self.subgenres: Dict[str, str] = SUBGENRES
        self.subs_by_main: Dict[str, List[str]] = defaultdict(list)
        for sub, main in self.subgenres.items():
            self.subs_by_main[main].append(sub)
        self.main_genres: List[str] = list(self.subs_by_main.keys())
        
        # --- NLP and Model Resources ---
        self._stopwords: Set[str] = set(stopwords.words("english"))
        self._subgenre_clf: Optional[Pipeline] = None
        self._initialized: bool = True

    @staticmethod
    def _build_pipeline() -> Pipeline:
        """Creates the scikit-learn pipeline for classification."""
        return Pipeline(steps=[
            ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_df=0.9, min_df=2)),
            ("svm", LinearSVC(dual="auto")), # dual="auto" handles data characteristics better
        ])

    @staticmethod
    def _get_seed_corpus() -> Tuple[List[str], List[str]]:
        """
        Provides a tiny bootstrap seed corpus for initial model training.
        For production use, replace this with a large, real-world labeled dataset.
        """
        # This data is identical to the original for consistency.
        texts = [
            "Parliament passed new regulation; governance and judiciary implications discussed by policymakers.",
            "Leaders held diplomacy talks on defense and foreign policy with election campaigns ongoing.",
            "Markets rallied as banking stocks rose; earnings and trade data lifted corporate confidence.",
            "A startup announced M&A; venture capital and retail outlook improved amid commodities volatility.",
            "Mobile gadgets launched with AI features; cloud software and semiconductors drive enterprise IT.",
            "Cybersecurity incident hits social media platform; hardware updates and software patches released.",
            "Cricket team qualified for the Olympics; football and tennis highlights with athletics performance.",
            "Hockey and badminton teams progress; kabaddi and chess events noted in esports circuits.",
            "Bollywood box office surges; streaming web series win awards; regional cinema and music reviews.",
            "Celebrities attend television premieres; box office and awards dominate entertainment headlines.",
            "Public health officials report infectious disease trends; mental health and pharma policy updates.",
            "Healthcare policy reforms debated; vaccination drives and hospital capacity reviewed.",
            "Space mission advances physics research; biology and chemistry labs secure research funding.",
            "Chemistry breakthroughs; biology experiments and physics conference highlight science progress.",
            "Central government announces infrastructure push; state politics and rural development updates.",
            "Social welfare programs expanded; policy signals from New Delhi draw national attention.",
            "Geopolitics and conflicts escalate; sanctions affect global economy and international organizations.",
            "Global economy reacts to sanctions; organizations convene to address conflicts and geopolitics.",
            "Climate change impacts wildlife; conservation and renewable energy policies tackle pollution.",
            "Renewable energy projects expand; conservation efforts help wildlife amid pollution concerns.",
            "Higher education exams and scholarships; EdTech tools support policy reform in universities.",
            "Policy reform targets exams; scholarships and EdTech adoption grow across higher education.",
            "Courts address cybercrime; policing strategies updated to curb corruption and organized crime.",
            "Anti-corruption drives intensify; judiciary rulings guide policing in cybercrime cases.",
            "Fitness and fashion trends rise; food culture and relationships shape modern lifestyle.",
            "Culture festivals highlight food; fashion and fitness communities grow.",
            "Editorial analysis and op-ed columns debate policy; letters from readers spark discussion.",
            "Opinion columns and analysis review governance; editorial board publishes letters.",
            "Aviation deals and railways upgrades boost hospitality at key destinations; travel advisories issued.",
            "Railways modernize; aviation growth supports destinations and hospitality industry.",
            "EVs dominate auto launches; motorsports thrive; auto policy impacts supply chain.",
            "Auto supply chain adapts; policy shifts; motorsports and EVs headline auto news.",
            "Housing demand rises; commercial REITs expand; regulatory changes impact home loans.",
            "Home loans grow; regulatory shifts influence housing and commercial real estate.",
            "Mutual funds see inflows; insurance, taxation and pensions shape fintech landscape.",
            "Fintech adoption grows; mutual funds and insurance trends evolve with taxation rules.",
            "Crops benefit from irrigation; agri markets and policy support agri tech innovation.",
            "Agri tech expands; policy and markets evolve; irrigation helps seasonal crops.",
            "Monsoon forecast warns heatwave and cyclone risk; air quality alerts issued.",
            "Air quality fluctuates; forecast tracks cyclones as heatwave follows monsoon.",
        ]
        labels = [
            "Regulation","Diplomacy", "Markets","M&A", "Mobile","Cybersecurity", "Cricket","Hockey",
            "Box Office","Awards", "Public Health","Healthcare Policy", "Space","Physics", "Infrastructure","Social Welfare",
            "Geopolitics","Global Economy", "Climate Change","Renewable Energy", "Higher Education","Policy Reform",
            "Cybercrime","Anti-corruption", "Fitness","Culture", "Editorial","Columns", "Aviation","Railways",
            "EVs","Auto Supply Chain", "Housing","Home Loans", "Mutual Funds","Fintech", "Crops","Agri Tech",
            "Monsoon","Forecast",
        ]
        return texts, labels

    def _ensure_model_trained(self):
        """Ensures the classification model is trained, handling thread safety."""
        if self._subgenre_clf is None:
            with self._lock:
                if self._subgenre_clf is None:
                    texts, labels = self._get_seed_corpus()
                    clf = self._build_pipeline()
                    clf.fit(texts, labels)
                    self._subgenre_clf = clf
    
    def summarize(self, text: str, target_min: int = 40, target_max: int = 50) -> str:
        """
        Generates an extractive summary of the text based on word frequency.
        """
        if not text:
            return ""
        
        sents = sent_tokenize(text)
        if len(sents) <= 2: # For very short texts, just truncate
            return " ".join(text.split()[:target_max])

        words = [w.lower() for w in word_tokenize(text) if w.isalpha() and w.lower() not in self._stopwords]
        if not words:
            return " ".join(text.split()[:target_max]) # Fallback if no valid words

        freq = nltk.FreqDist(words)
        
        # Score sentences based on the frequency of their constituent words
        scored_sents = []
        for sent in sents:
            sent_words = [w.lower() for w in word_tokenize(sent) if w.isalpha()]
            score = sum(freq[w] for w in sent_words if w in freq)
            scored_sents.append((score, sent))
        
        scored_sents.sort(key=lambda x: x[0], reverse=True)
        
        # Build summary by picking highest-scored sentences
        summary_sents, word_count = [], 0
        for _, sent in scored_sents:
            if word_count >= target_min:
                break
            words_in_sent = sent.split()
            summary_sents.append(sent)
            word_count += len(words_in_sent)
            
        summary = " ".join(summary_sents)
        summary_words = summary.split()

        # Enforce hard upper limit
        if len(summary_words) > target_max:
            return " ".join(summary_words[:target_max])
        
        return summary

    def predict_subgenre(self, text: str, main_genre: str) -> str:
        """
        Predicts the most likely subgenre, constrained by the given main_genre.
        """
        self._ensure_model_trained()
        assert self._subgenre_clf is not None, "Model should be trained by this point"

        allowed_subgenres = self.subs_by_main.get(main_genre, [])
        
        # If the main genre is unknown or has no subgenres, predict from all classes.
        if not allowed_subgenres:
            return self._subgenre_clf.predict([text])[0]

        classes = self._subgenre_clf.classes_
        decision_scores = self._subgenre_clf.decision_function([text])[0]

        # Create a mapping of all class names to their scores.
        # This handles both binary and multiclass SVC outputs gracefully.
        if decision_scores.ndim == 0: # Binary classification case
            score_map = {classes[0]: -decision_scores.item(), classes[1]: decision_scores.item()}
        else: # Multiclass classification case
            score_map = {cls: score for cls, score in zip(classes, decision_scores)}

        # Find the subgenre within the allowed list that has the highest score.
        best_subgenre = max(allowed_subgenres, key=lambda sg: score_map.get(sg, float("-inf")))
        
        return best_subgenre

# ==============================================================================
# --- PUBLIC API ---
# ==============================================================================

@dataclass(frozen=True)
class SummaryResult:
    """A structured container for the processing result."""
    summary: str
    main_genre: str
    subgenre: str

def give_summary(news: str, genre: str) -> SummaryResult:
    """
    Summarizes news text and classifies its subgenre based on a primary genre.

    Args:
      news: The plain text of the news article.
      genre: The required main genre string (must match the defined taxonomy).

    Returns:
      A SummaryResult object containing the summary and classification.
    """
    if not isinstance(genre, str) or not genre.strip():
        raise ValueError("Main genre must be a non-empty string.")

    if not isinstance(news, str) or not news.strip():
        return SummaryResult(summary="", main_genre=genre, subgenre="Unknown")
    
    # Get the singleton instance of the processor
    processor = NewsProcessor()
    
    # 1. Generate the summary
    summary_text = processor.summarize(news)
    
    # 2. Predict the subgenre constrained by the main genre
    subgenre = processor.predict_subgenre(news, genre)
    
    return SummaryResult(summary=summary_text, main_genre=genre, subgenre=subgenre)


