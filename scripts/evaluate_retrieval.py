"""Small transparent diagnostic fixture, not a production accuracy benchmark."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.engine import retrieve
DOCS=[
 ('leave','Employee handbook.txt','Employees receive 25 days of paid annual leave. Vacation requests require approval from a manager two weeks before travel.'),
 ('security','Security policy.txt','Staff must use multi-factor authentication. Security incidents must be reported within 24 hours. Encrypt sensitive customer records.'),
 ('refund','Refund rules.txt','Customers can request a refund within thirty days of purchase. Reimbursement takes five working days to process.'),
 ('vehicle','Motor cover.txt','Car insurance covers vehicle theft and automobile collision damage. Renew coverage annually.'),
 ('expense','Travel expenses.txt','Submit business travel receipts within ten days. The finance team pays approved expenses at the end of each month.'),
 ('clinic','Panel clinics managed by Micare.txt','Approved panel clinics include Sunrise Medical Centre in Shah Alam and Lakeside Clinic in Petaling Jaya. Bring an employee card.'),
 ('research','Cross-media relationship classification.txt','This study describes a neural network combining image and text representations for multimodal relation prediction.'),
 ('damansara','Panel clinic directory.txt','Panel clinics in Damansara include Example Damansara Medical Centre. This fictional test clinic accepts employee medical cards.'),
 ('parking','Damansara shopping.txt','The Damansara shopping centre parking area opens at seven. Visitors can buy groceries and clothing.'),
 ('food','Cafeteria menu.txt','Lunch includes rice, chicken, vegetables and fruit. Breakfast is served at eight in the morning.'),
 ('password','Account recovery.txt','Reset a forgotten password using the recovery email. Contact the IT help desk if you cannot access the email account.'),
 ('search','Retrieval guide.txt','Hybrid search combines BM25 keyword matching with semantic retrieval. Reciprocal rank fusion merges the two rankings.'),
]
CASES=[
 ('literal','annual leave','leave'),('literal','multi-factor authentication','security'),
 ('literal','refund thirty days','refund'),('literal','vehicle theft','vehicle'),
 ('literal','travel receipts','expense'),('literal','Sunrise Medical Centre','clinic'),
 ('literal','multimodal relation prediction','research'),('literal','breakfast','food'),
 ('literal','forgotten password','password'),('literal','reciprocal rank fusion','search'),
 ('filename','Micare','clinic'),('filename','Cross-media relationship classification','research'),
 ('synonym','holiday approval','leave'),('synonym','automobile protection','vehicle'),
 ('paraphrase','How do I get my money back?','refund'),
 ('paraphrase','Where can I eat in the morning?','food'),
 ('paraphrase','I cannot log in to my account','password'),
 ('location','i want to know panel clinic in damansara area','damansara'),
 ('location','panel clinics in Damansara','damansara'),
 ('location','panel clinic Shah Alam','clinic'),
 ('no-answer','What is the quantum flux capacitor warranty?',None),
 ('no-answer','What is the lunar geology protocol?',None),
 ('no-answer','the and is',None),
]
def evaluate():
 rows=[{'id':i,'document_id':i,'name':n,'text':t,'position':1} for i,n,t in DOCS]
 report={'scope':'23 hand-labelled diagnostic queries over 12 synthetic documents. Not representative of user files.','modes':{}}
 for mode in ['keyword','semantic','hybrid']:
  results=[]
  for category,query,expected in CASES:
   found=retrieve(rows,query,mode=mode,top_k=3)
   ids=[r['document_id'] for r in found]
   rank=ids.index(expected)+1 if expected in ids else None
   results.append({'category':category,'query':query,'expected':expected,'returned':ids,'top1_correct':ids[0]==expected if ids and expected else not ids if expected is None else False,'reciprocal_rank':1/rank if rank else 0})
  positive=[r for r in results if r['expected']];negative=[r for r in results if not r['expected']]
  report['modes'][mode]={'answerable_queries':len(positive),'top1_accuracy':sum(r['top1_correct'] for r in positive)/len(positive),'recall_at_3':sum(r['expected'] in r['returned'] for r in positive)/len(positive),'mrr_at_3':sum(r['reciprocal_rank'] for r in positive)/len(positive),'no_answer_correct':sum(r['top1_correct'] for r in negative),'no_answer_queries':len(negative),'queries':results}
 return report
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 report=evaluate();Path(args.output).write_text(json.dumps(report,indent=2))
 for mode,r in report['modes'].items():print(mode,{k:v for k,v in r.items() if k!='queries'})
