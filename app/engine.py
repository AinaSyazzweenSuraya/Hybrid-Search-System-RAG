"""Local retrieval: BM25 + latent semantic analysis, fused by weighted RRF."""
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

# Small transparent query expansion helps cold-start collections. LSA learns corpus relations.
CONCEPTS = [('car','automobile','vehicle'), ('employee','staff','worker','personnel'),
 ('holiday','vacation','leave'), ('price','cost','pricing','expense'),
 ('security','protection','safety'), ('refund','reimbursement','repayment'),
 ('search','retrieval','lookup'), ('ai','artificial intelligence','machine learning')]
QUERY_STOP_WORDS=set(ENGLISH_STOP_WORDS)|{'want','know','please','tell','area','information','document','documents'}
SINGULAR={'clinics':'clinic','employees':'employee','vehicles':'vehicle','refunds':'refund','holidays':'holiday'}
def tokens(text):
    return [SINGULAR.get(t,t) for t in re.findall(r'\b\w+\b', text.lower().replace('_',' '))]
def expand(text):
    words=set(tokens(text))
    return text+' '+' '.join(' '.join(group) for group in CONCEPTS if words.intersection(group))
def chunks(text, size=180, overlap=35):
    words=list(re.finditer(r'\S+',text))
    return [text[words[i].start():words[min(i+size,len(words))-1].end()] for i in range(0,len(words),size-overlap)]

def retrieve(rows, query, mode='hybrid', alpha=.5, top_k=5, min_score=0):
    if not rows: return []
    texts=[re.sub(r'\.[a-zA-Z0-9]+$','',r.get('name',''))+'\n'+r['text'] for r in rows]
    docs=[tokens(t) for t in texts]; q=[t for t in tokens(query) if t not in QUERY_STOP_WORDS]
    if not q: return []
    clean_query=' '.join(q)
    lengths=np.array([len(d) for d in docs]); avg=max(float(lengths.mean()),1)
    bm=np.zeros(len(docs))
    for term in set(q):
        tf=np.array([d.count(term) for d in docs]); df=np.count_nonzero(tf)
        bm+=np.log(1+(len(docs)-df+.5)/(df+.5))*tf*2.5/(tf+1.5*(.25+.75*lengths/avg))
    vectorizer=TfidfVectorizer(preprocessor=lambda t:expand(' '.join(tokens(t))),stop_words=sorted(QUERY_STOP_WORDS),ngram_range=(1,2),sublinear_tf=True)
    try:
        matrix=vectorizer.fit_transform(texts); query_vector=vectorizer.transform([clean_query])
        lexical=(matrix@query_vector.T).toarray().ravel()
        if min(matrix.shape)>2:
            svd=TruncatedSVD(n_components=min(128,min(matrix.shape)-1),random_state=42)
            latent=normalize(svd.fit_transform(matrix)); projected=normalize(svd.transform(query_vector))
            semantic=.6*lexical+.4*np.maximum(0,(latent@projected.T).ravel())
            # Projection alone can invent matches in tiny corpora; require expanded term evidence.
            semantic=np.where(lexical>1e-8,semantic,0)
        else:
            semantic=lexical
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
        matched=[t for t in dict.fromkeys(q) if t in docs[i]]
        missing=[t for t in dict.fromkeys(q) if t not in docs[i]]
        results.append({**rows[i], 'matched_terms':matched,'missing_terms':missing, 'score':round(float(score[i]),4),'keyword_score':round(float(bm[i]),4),'semantic_score':round(float(semantic[i]),4)})
        if len(results)>=top_k: break
    return results
