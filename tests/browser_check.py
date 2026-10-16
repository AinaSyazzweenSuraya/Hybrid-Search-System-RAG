from playwright.sync_api import sync_playwright
from pathlib import Path
import os, socket, subprocess, tempfile, time, urllib.request, contextlib
root=Path(__file__).resolve().parents[1]
@contextlib.contextmanager
def server():
 with tempfile.TemporaryDirectory(prefix='hybrid-search-browser-') as folder:
  with socket.socket() as sock:
   sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
  url=f'http://127.0.0.1:{port}'
  with open(Path(folder)/'server.log','w') as log:
   proc=subprocess.Popen([str(root/'.venv/bin/python'),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=root,env={**os.environ,'RAG_DATA_DIR':folder},stdout=log,stderr=log)
   try:
    for _ in range(100):
     try:
      with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
       if response.status==200: break
     except Exception: time.sleep(.1)
    else: raise RuntimeError('Temporary server did not become ready')
    yield url
   finally:
    proc.terminate();proc.wait(timeout=10)
with server() as base_url, sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else None),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base_url);page.wait_for_function("document.querySelector('#health').textContent === 'Engine online'")
 assert page.title()=='Hybrid Search Engine — Search your documents'
 assert page.get_by_role('link',name='Hybrid Search Engine home').is_visible()
 assert page.locator('#gettingStarted').is_visible()
 page.click('#openHelp');assert page.locator('#helpDialog').is_visible()
 assert page.locator('#helpDialog li').count()==3
 page.click('#closeHelp');assert not page.locator('#helpDialog').is_visible()
 page.screenshot(path=str(root/'docs/screenshots/explorer.png'),full_page=True)
 # Exercise errors returned by a hosting proxy before the app can produce JSON.
 for status in [500,413,504]:
  page.route('**/api/documents?*',lambda route,request,code=status:route.fulfill(status=code,content_type='text/html',body='<html>Hosting error</html>'))
  page.click('#uploadTop');page.locator('#files').set_input_files({'name':'error.txt','mimeType':'text/plain','buffer':b'Test hosting error'})
  page.wait_for_selector('#uploadStatus .error')
  assert f'HTTP {status}' in page.locator('#uploadStatus .error').inner_text()
  assert 'unreadable response' not in page.locator('#uploadStatus .error').inner_text()
  page.click('#closeUpload');page.unroute('**/api/documents?*')
 page.route('**/api/documents?*',lambda route:route.fulfill(status=503,json={'detail':'The document database is unavailable.','reference':'test-ref-123'}))
 page.click('#uploadTop');page.locator('#files').set_input_files({'name':'db-error.txt','mimeType':'text/plain','buffer':b'Test database error'})
 page.wait_for_selector('#uploadStatus .error');assert 'test-ref-123' in page.locator('#uploadStatus .error').inner_text()
 page.click('#closeUpload');page.unroute('**/api/documents?*')
 page.click('#uploadTop');page.locator('#files').set_input_files({'name':'invalid.exe','mimeType':'application/octet-stream','buffer':b'bad'});page.wait_for_selector('#uploadStatus .error');page.click('#closeUpload')
 page.click('#loadDemo');page.wait_for_selector('.result');assert page.locator('#docCount').inner_text()=='3'
 assert page.locator('#evidencePanel').is_visible()
 assert not page.locator('#gettingStarted').is_visible()
 page.click('#toggleParams');page.locator('#alpha').fill('0.75');page.locator('#alpha').dispatch_event('input');assert page.locator('#alphaValue').inner_text()=='75%'
 page.locator('[data-mode=semantic]').click();page.locator('#query').fill('staff vacation');page.click('#searchButton');page.wait_for_selector('.result');page.screenshot(path=str(root/'docs/screenshots/results.png'),full_page=True)
 assert page.locator('#alpha').is_disabled()
 assert page.locator('[data-mode=semantic]').get_attribute('aria-pressed')=='true'
 assert 'related concepts' in page.locator('#modeHelp').inner_text()
 page.click('#resetSettings');assert page.locator('#alpha').is_enabled()
 assert page.locator('#alpha').input_value()=='0.5'
 assert page.locator('[data-mode=hybrid]').get_attribute('aria-pressed')=='true'
 page.click('#uploadTop');page.locator('#files').set_input_files({'name':'browser-upload.txt','mimeType':'text/plain','buffer':b'Browser upload confirms searchable astronaut telescope mission documents.'});page.wait_for_selector('#uploadStatus .success');page.click('#finishUpload');assert page.locator('#query').evaluate('(e)=>e===document.activeElement')
 page.locator('#query').fill('astronaut');page.locator('[data-mode=keyword]').click();page.click('#searchButton');page.wait_for_function("document.querySelector('.result h3')?.textContent === 'browser-upload.txt'")
 page.click('#libraryNav');assert page.locator('.library-item').count()==4
 page.on('dialog',lambda d:d.accept());page.locator('.library-item').filter(has_text='browser-upload.txt').get_by_role('button',name='Delete').click();page.wait_for_function("document.querySelector('#docCount').textContent === '3'")
 page.click('#searchNav');assert page.locator('#resultTitle').inner_text()=='Your search results'
 page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(root/'docs/screenshots/mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 assert not errors,errors
 print('Browser checks passed: sample ingestion, hybrid/semantic search, parameters, citations, upload, keyword retrieval, deletion, mobile layout; help, mode guidance, reset settings, upload-to-search focus; no JavaScript errors.')
 browser.close()
