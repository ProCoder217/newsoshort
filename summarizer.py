# --- Standard Library Imports ---
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass
import threading

# --- Third-Party Imports ---
# NLTK: For sentence tokenization
import nltk
from nltk.tokenize import sent_tokenize

# scikit-learn: For classification and LSA summarization
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.linear_model import LogisticRegression

# Ensure the 'punkt' tokenizer is downloaded for NLTK
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

# ==============================================================================
# --- CONFIGURATION: TAXONOMY ---
# ==============================================================================
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
    # Entertainment
    "Bollywood": "Entertainment", "Streaming": "Entertainment", "Television": "Entertainment", "Music": "Entertainment", "Celebrities": "Entertainment",
    # World
    "Geopolitics": "World", "Conflicts": "World", "Sanctions": "World", "Global Economy": "World", "International Organizations": "World",
    # India
    "Central Government": "India", "State Politics": "India", "Infrastructure": "India", "Rural Development": "India", "Social Welfare": "India",
    # Environment
    "Climate Change": "Environment", "Pollution": "Environment", "Wildlife": "Environment", "Renewable Energy": "Environment", "Conservation": "Environment",
    # Automobile
    "EVs": "Automobile", "Auto Launches": "Automobile", "Motorsports": "Automobile", "Auto Policy": "Automobile", "Auto Supply Chain": "Automobile"
}


# ==============================================================================
# --- CORE LOGIC CLASS ---
# ==============================================================================

class NewsProcessor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(NewsProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # --- Taxonomy setup ---
        self.subgenres: Dict[str, str] = SUBGENRES
        self.subs_by_main: Dict[str, List[str]] = defaultdict(list)
        for sub, main in self.subgenres.items():
            self.subs_by_main[main].append(sub)

        # --- LSA Summarizer components ---
        self.summarizer_vectorizer = TfidfVectorizer(stop_words='english')
        self.summarizer_svd = TruncatedSVD(n_components=1, n_iter=7, random_state=42)

        # --- Subgenre Classifier ---
        self._subgenre_clf: Optional[Pipeline] = None
        self._ensure_model_trained()
        self._initialized: bool = True

    @staticmethod
    def _get_seed_corpus() -> Tuple[List[str], List[str]]:
        """Provides the bootstrap seed corpus for the classifier."""
        texts = [
            "Parliament passed new regulation; governance and judiciary implications discussed by policymakers.", "Leaders held diplomacy talks on defense and foreign policy with election campaigns ongoing.",
            "Markets rallied as banking stocks rose; earnings and trade data lifted corporate confidence.", "A startup announced M&A; venture capital and retail outlook improved amid commodities volatility.",
            "Mobile gadgets launched with AI features; cloud software and semiconductors drive enterprise IT.", "Cybersecurity incident hits social media platform; hardware updates and software patches released.",
            "Cricket team qualified for the Olympics; football and tennis highlights with athletics performance.",
            "Bollywood box office surges; streaming web series win awards; regional cinema and music reviews.",
            "Public health officials report infectious disease trends; mental health and pharma policy updates.",
            "Space mission advances physics research; biology and chemistry labs secure research funding.",
            "Central government announces infrastructure push; state politics and rural development updates.",
            "Geopolitics and conflicts escalate; sanctions affect global economy and international organizations.",
            "Climate change impacts wildlife; conservation and renewable energy policies tackle pollution.",
            "EVs dominate auto launches; motorsports thrive; auto policy impacts supply chain.",
        ]
        labels = [
            "Regulation", "Diplomacy", "Markets", "M&A", "Mobile", "Cybersecurity", "Cricket", "Bollywood", # Corrected "Box Office" to a valid subgenre
            "Public Health", "Space", "Infrastructure", "Geopolitics", "Climate Change", "EVs",
        ]
        return texts, labels

    def _ensure_model_trained(self):
        """Ensures the classification model is trained."""
        if self._subgenre_clf is None:
            with self._lock:
                if self._subgenre_clf is None:
                    texts, labels = self._get_seed_corpus()
                    
                    clf = Pipeline(steps=[
                        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_df=0.9, min_df=2)),
                        ("lr", LogisticRegression(dual=False, max_iter=1000)),
                    ])
                    clf.fit(texts, labels)
                    self._subgenre_clf = clf

    def summarize(self, text: str, max_words: int = 53) -> str:
        """
        Generates an extractive summary using LSA, constrained by a maximum word count.
        It will add the most important sentences one by one until the next sentence
        would exceed the max_words limit.
        """
        if not text:
            return ""
        
        sentences = sent_tokenize(text)
        
        # If the original text is already short, return it.
        if len(text.split()) <= max_words:
            return text

        # Step 1: Score all sentences using LSA
        tfidf_matrix = self.summarizer_vectorizer.fit_transform(sentences)
        self.summarizer_svd.fit(tfidf_matrix)
        concept_vector = self.summarizer_svd.components_[0]
        
        sentence_scores = {
            i: sum(concept_vector[j] * tfidf_matrix[i, j] 
                   for j, _ in enumerate(self.summarizer_vectorizer.get_feature_names_out()) 
                   if tfidf_matrix[i, j] > 0)
            for i, _ in enumerate(sentences)
        }
        
        # Step 2: Sort sentences by score, from most to least important
        sorted_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
        
        # Step 3: Build the summary iteratively based on word count
        summary_indices = []
        total_words = 0
        
        for index in sorted_indices:
            sentence_to_add = sentences[index]
            words_in_sentence = len(sentence_to_add.split())
            
            # Check if adding the next most important sentence exceeds the limit
            if total_words + words_in_sentence <= max_words:
                summary_indices.append(index)
                total_words += words_in_sentence
        
        # Step 4: Sort the selected sentence indices to maintain original order
        summary_indices.sort()
        
        return " ".join([sentences[i] for i in summary_indices])

    def predict_subgenre(self, text: str, main_genre: str) -> str:
        """
        Predicts the single best subgenre from the entire list of subgenres.
        """
        assert self._subgenre_clf is not None, "Model should be trained"

        # Get the model's prediction.
        best_subgenre = self._subgenre_clf.predict([text])[0]
        
        return best_subgenre

# ==============================================================================
# --- PUBLIC API ---
# ==============================================================================

@dataclass(frozen=True)
class SummaryResult:
    summary: str
    main_genre: str
    subgenre: str

def give_summary(news: str, genre: str) -> SummaryResult:
    """
    Takes a news article and its main genre, returns a summary, the main genre,
    and a predicted subgenre.
    """
    if not isinstance(news, str) or not news.strip():
        return SummaryResult(summary="", main_genre=genre, subgenre=genre)
    
    processor = NewsProcessor()
    summary_text = processor.summarize(news) # This now uses the word-count based summarizer
    subgenre = processor.predict_subgenre(news, genre)
    
    return SummaryResult(summary=summary_text, main_genre=genre, subgenre=subgenre)

