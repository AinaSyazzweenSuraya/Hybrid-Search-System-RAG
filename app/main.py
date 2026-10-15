import io,os,sqlite3,threading,time,uuid,zipfile
from .storage import connect, initialize
from contextlib import contextmanager
from pathlib import Path
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .parsers import SUPPORTED,extract
from .engine import chunks,retrieve

DATABASE_URL=os.environ.get('DATABASE_URL')
if os.environ.get('VERCEL') and not DATABASE_URL:
    raise RuntimeError('Configure DATABASE_URL with a persistent PostgreSQL connection before deploying to Vercel.')
DATA=Path(os.environ.get('RAG_DATA_DIR','data'))
if not DATABASE_URL: DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'search.db'
_initialized=False
_schema_lock=threading.Lock()
@contextmanager
def db():
    global _initialized
    c=connect(DATABASE_URL,DB)
    try:
        with _schema_lock:
            if not _initialized:
                initialize(c)
                c.commit()
                _initialized=True
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally: c.close()
app=FastAPI(title='Neon Atlas · Hybrid document search',version='1.0.0')
app.mount('/static',StaticFiles(directory=Path(__file__).parent/'static'),name='static')
@app.get('/')
def home(): return FileResponse(Path(__file__).parent/'static/index.html')
@app.get('/api/health')
def health():
    with db() as c: c.execute('SELECT 1').fetchone()
    return {'status':'ok','storage':'postgresql' if DATABASE_URL else 'sqlite','max_upload_bytes':(4 if os.environ.get('VERCEL') else 10)*1024*1024,'semantic_engine':'local-lsa','generation':'extractive','formats':sorted(SUPPORTED)}
@app.get('/api/documents')
def documents():
    with db() as c:
        return [dict(r) for r in c.execute('SELECT d.*,COUNT(c.id) AS chunks FROM documents d LEFT JOIN chunks c ON c.document_id=d.id GROUP BY d.id ORDER BY d.created DESC')]
@app.post('/api/documents',status_code=201)
async def upload(file:UploadFile=File(...),chunk_size:int=180,overlap:int=35):
    if not 60<=chunk_size<=600 or not 0<=overlap<chunk_size: raise HTTPException(422,'Chunk size must be 60–600 and overlap must be smaller than chunk size.')
    name=Path((file.filename or '').replace('\\','/')).name; ext=Path(name).suffix.lower()
    if ext not in SUPPORTED: raise HTTPException(415,'Unsupported format. Supported: '+', '.join(sorted(SUPPORTED)))
    data=await file.read(10*1024*1024+1)
    limit=4*1024*1024 if os.environ.get('VERCEL') else 10*1024*1024
    if len(data)>limit: raise HTTPException(413,f'Maximum file size is {limit//(1024*1024)} MB.')
    try:
        if ext in {'.docx','.pptx','.xlsx'}:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if sum(i.file_size for i in z.infolist())>50*1024*1024: raise ValueError('Expanded document exceeds 50 MB.')
        text=extract(name,data)
        if len(text)>2_000_000: raise ValueError('Extracted text exceeds 2 million characters.')
        if not text.strip(): raise ValueError('No readable text found. Scanned PDFs need OCR before upload.')
    except Exception as e: raise HTTPException(422,'Could not read document. Ensure it is valid, unencrypted, and contains selectable text.') from e
    identifier=uuid.uuid4().hex; parts=chunks(text,chunk_size,overlap)
    with db() as c:
        c.execute('INSERT INTO documents(id,name,format,bytes) VALUES(?,?,?,?)',(identifier,name,ext,len(data)))
        c.executemany('INSERT INTO chunks VALUES(?,?,?,?)',[(uuid.uuid4().hex,identifier,i+1,t) for i,t in enumerate(parts)])
    return {'id':identifier,'name':name,'chunks':len(parts)}
@app.delete('/api/documents/{identifier}')
def delete(identifier:str):
    with db() as c:
        if not c.execute('SELECT 1 FROM documents WHERE id=?',(identifier,)).fetchone(): raise HTTPException(404,'Document not found')
        c.execute('DELETE FROM chunks WHERE document_id=?',(identifier,)); c.execute('DELETE FROM documents WHERE id=?',(identifier,))
    return {'deleted':identifier}
class Query(BaseModel):
    query:str=Field(min_length=1,max_length=1000)
    mode:str='hybrid'
    alpha:float=Field(default=.5,ge=0,le=1)
    top_k:int=Field(default=5,ge=1,le=30)
    min_score:float=Field(default=0,ge=0,le=1)
    document_id:str|None=None
@app.post('/api/search')
def search(q:Query):
    if q.mode not in {'hybrid','keyword','semantic'} or not q.query.strip(): raise HTTPException(422,'Enter a query and select a valid search mode.')
    started=time.perf_counter()
    with db() as c:
        rows=[dict(r) for r in c.execute('SELECT c.*,d.name FROM chunks c JOIN documents d ON d.id=c.document_id'+(' WHERE d.id=?' if q.document_id else ''),(q.document_id,) if q.document_id else ())]
    results=retrieve(rows,q.query,q.mode,q.alpha,q.top_k,q.min_score)
    # Evidence extraction is deliberately distinct from generative question answering.
    evidence=[{'citation':i+1,'document':r['name'],'chunk':r['position'],'text':r['text']} for i,r in enumerate(results[:3])]
    return {'results':results,'evidence':evidence,'elapsed_ms':round((time.perf_counter()-started)*1000,1),'engine':'BM25 + local LSA / weighted reciprocal rank fusion'}
