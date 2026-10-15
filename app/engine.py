"""Local retrieval: BM25 + latent semantic analysis, fused by weighted RRF."""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

# Small transparent query expansion helps cold-start collections. LSA learns corpus relations.
CONCEPTS = [('car','automobile','vehicle'), ('employee','staff','worker','personnel'),
 ('holiday','vacation','leave'), ('price','cost','pricing','expense'),
 ('security','protection','safety'), ('refund','reimbursement','repayment'),
 ('search','retrieval','lookup'), ('ai','artificial intelligence','machine learning')]
def tokens(text):
    return re.findall(r'\b\w+\b', text.lower())
def expand(text):
    words=set(tokens(text))
    return text+' '+' '.join(' '.join(group) for group in CONCEPTS if words.intersection(group))
def chunks(text, size=180, overlap=35):
    words=text.split()
    return [' '.join(words[i:i+size]) for i in range(0,len(words),size-overlap) if words[i:i+size]]

def retrieve(rows, query, mode='hybrid', alpha=.5, top_k=5, min_score=0):
    if not rows: return []
    texts=[r['text'] for r in rows]; docs=[tokens(t) for t in texts]; q=tokens(query)
    lengths=np.array([len(d) for d in docs]); avg=max(float(lengths.mean()),1)
    bm=np.zeros(len(docs))
    for term in set(q):
        tf=np.array([d.count(term) for d in docs]); df=np.count_nonzero(tf)
        bm+=np.log(1+(len(docs)-df+.5)/(df+.5))*tf*2.5/(tf+1.5*(.25+.75*lengths/avg))
    vectorizer=TfidfVectorizer(preprocessor=expand,ngram_range=(1,2),sublinear_tf=True)
    try:
        matrix=vectorizer.fit_transform(texts); query_vector=vectorizer.transform([query])
        if min(matrix.shape)>2:
            svd=TruncatedSVD(n_components=min(128,min(matrix.shape)-1),random_state=42)
            latent=normalize(svd.fit_transform(matrix)); projected=normalize(svd.transform(query_vector))
            semantic=np.maximum(0,(latent@projected.T).ravel())
        else:
            semantic=np.maximum(0,(matrix@query_vector.T).toarray().ravel())
    except ValueError:
        semantic=np.zeros(len(docs))
    def ranks(values):
        out=np.zeros(len(values))
        for rank,i in enumerate(np.argsort(-values),1):
            if values[i]>1e-8: out[i]=61/(60+rank)
        return out
    score=ranks(bm) if mode=='keyword' else ranks(semantic) if mode=='semantic' else (1-alpha)*ranks(bm)+alpha*ranks(semantic)
    results=[]
    for i in np.argsort(-score):
        if score[i]<=max(min_score,1e-8): continue
        results.append({**rows[i], 'score':round(float(score[i]),4),'keyword_score':round(float(bm[i]),4),'semantic_score':round(float(semantic[i]),4)})
        if len(results)>=top_k: break
    return results
