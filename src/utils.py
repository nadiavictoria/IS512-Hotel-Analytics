import re
import itertools
import numpy as np
import umap
from sentence_transformers import SentenceTransformer

def get_stopwords_list(stop_file_path):
    """load stop words """
    
    with open(stop_file_path, 'r', encoding="utf-8") as f:
        stopwords = f.readlines()
        stop_set = set(m.strip() for m in stopwords)
        return list(frozenset(stop_set))
    
def clean_text(text, punctuation):
    """Doc cleaning"""
    
    # Lowering text
    text = text.lower()
    
    # Removing punctuation
    text = "".join([c for c in text if c not in punctuation])
    
    # Removing whitespace and newlines
    text = re.sub('\s+',' ',text)
    
    return text

def sort_coo(coo_matrix):
    """Sort a dict with highest score"""
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    """get the feature names and tf-idf score of top n items"""
    
    #use only topn items from vector
    sorted_items = sorted_items[:topn]

    score_vals = []
    feature_vals = []
    
    # word index and corresponding tf-idf score
    for idx, score in sorted_items:
        
        #keep track of feature name and its corresponding score
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    #create a tuples of feature, score
    results= {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]]=score_vals[idx]
    
    return results

def get_keywords(vectorizer, feature_names, doc, top_k_keywords=10):
    """Return top k keywords from a doc using TF-IDF method"""

    #generate tf-idf for the given document
    tf_idf_vector = vectorizer.transform([doc])
    
    #sort the tf-idf vectors by descending order of scores
    sorted_items=sort_coo(tf_idf_vector.tocoo())

    #extract only TOP_K_KEYWORDS
    keywords=extract_topn_from_vector(feature_names,sorted_items,top_k_keywords)
    
    return list(keywords.keys())

def generate_keyword_embeddings_2d(final_df, n_words=None, random_state=None, model_name='all-MiniLM-L6-v2'):
    """
    Generate 2D embeddings using umap.
    """

    # Flatten all keywords into a unique set
    all_words = set(itertools.chain.from_iterable(final_df['top_keywords']))
    print(f"Number of unique words: {len(all_words)}")

    # Select up to n_words randomly
    if random_state is not None:
        np.random.seed(random_state)
    
    # Get all words
    word_list = list(all_words)

    if n_words is not None and len(word_list) > n_words:
        selected_words = np.random.choice(word_list, size=n_words, replace=False)
    else:
        selected_words = word_list

    # Load embedding model
    model = SentenceTransformer(model_name)
    embeddings = model.encode(selected_words)
    print(f"Embedding shape: {embeddings.shape}")

    # Reduce to 2D with UMAP
    reducer = umap.UMAP(n_components=2, random_state=random_state)
    embeddings_2d = reducer.fit_transform(embeddings)
    print(f"2D embedding shape: {embeddings_2d.shape}")

    return embeddings_2d, selected_words