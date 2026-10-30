"""Build frozen paired format controls from raw SEC rows, without the verifier."""
from pathlib import Path
from datetime import date
import hashlib,json,subprocess,textwrap
from decimal import Decimal
from PIL import Image,ImageDraw,ImageFont
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
CACHE=ROOT/'.cache/sec-refresh-2026-10-30'
ESPEAK=Path('/tmp/claimcheck-mm-espeak/bin/espeak-ng')
SPLITS={'dev':['AAPL','NVDA'],'test':['AMZN','INTC','TSLA','MSFT','GOOGL','META']}
PERIOD={'AAPL':('FY2026Q3','Apple'),'NVDA':('FY2027Q2','Nvidia'),'AMZN':('FY2026Q3','Amazon'),'INTC':('FY2026Q3','Intel'),'TSLA':('FY2026Q3','Tesla'),'MSFT':('FY2027Q1','Microsoft'),'GOOGL':('FY2026Q3','Alphabet'),'META':('FY2026Q3','Meta Platforms')}
CONCEPTS={'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet','RevenueFromContractWithCustomerIncludingAssessedTax'], 'net_income':['NetIncomeLoss','ProfitLoss'],'eps':['EarningsPerShareDiluted']}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def fmt(v,metric):
    d=Decimal(str(v))/(1 if metric=='eps' else Decimal(10)**9)
    return format(d.normalize(),'f')+(' US dollars' if metric=='eps' else ' billion US dollars')

def main():
    if (OUT/'manifest.json').exists():raise SystemExit('corpus exists; preserve frozen inputs')
    mapping={r['ticker']:r for r in json.loads((CACHE/'company_tickers.json').read_text()).values()}
    docs=[];cases=[]
    for split,tickers in SPLITS.items():
      for ticker in tickers:
        period,name=PERIOD[ticker];cik=f"{mapping[ticker]['cik_str']:010d}";source=CACHE/f'companyfacts-CIK{cik}.json';doc=json.loads(source.read_text());facts=doc['facts']['us-gaap'];year=int(period[2:6]);quarter=period[-2:]
        selected={}
        for metric,concepts in CONCEPTS.items():
          choices=[]
          for concept in concepts:
            for unit,values in facts.get(concept,{}).get('units',{}).items():
              if unit!=('USD/shares' if metric=='eps' else 'USD'):continue
              for r in values:
                if r.get('form') not in ('10-Q','10-K') or r.get('filed','9999')>'2026-10-30' or r.get('fy')!=year or r.get('fp')!=quarter or 'start' not in r:continue
                if 65<=(date.fromisoformat(r['end'])-date.fromisoformat(r['start'])).days<=105:
                  choices.append((r['end'],r['filed'],concept,unit,r))
          if not choices:raise ValueError(f'No direct quarter row for {ticker} {metric} {period}')
          _,_,concept,unit,row=max(choices,key=lambda x:(x[0],x[1]))
          selected[metric]={'concept':concept,'unit':unit,'row':row,'snapshot':str(source.relative_to(ROOT)),'source_sha256':sha(source),'cik':cik}
        assert len({x['row']['end'] for x in selected.values()})==1
        def sentence(metric,value,fy=year,q=quarter):
          label={'revenue':'revenue','net_income':'net income','eps':'diluted EPS'}[metric]
          return f'{name} reported {label} of {fmt(value,metric)} for fiscal {q} {fy}.'
        actual=selected['net_income']['row']['val'];wrong=actual+max(abs(actual)*Decimal('0.2'),Decimal(1000000))
        specs=[('revenue',selected['revenue']['row']['val'],'supported',year,quarter),('net_income',wrong,'contradicted',year,quarter),('eps',selected['eps']['row']['val'],'supported',year,quarter),('revenue',selected['revenue']['row']['val'],'insufficient_evidence',2028,'Q4')]
        gold=[]
        for i,(metric,value,verdict,fy,q) in enumerate(specs):
          gold.append({'id':f'{ticker}-{i+1}','ticker':ticker,'metric':metric,'period':f'FY{fy}{q}','statement':sentence(metric,value,fy,q),'gold':verdict,'stated_value':float(value),'reference':selected[metric] if fy==year else {'reason':'No recorded SEC fact for this future period as of 2026-10-30','as_of':'2026-10-30'},'mutation':'net income changed by +20% or $1M' if i==1 else 'future period with no evidence' if i==3 else None})
        text='Controlled financial-claim test. Some statements are deliberately incorrect or lack evidence.\n\n'+'\n'.join(g['statement'] for g in gold)+'\n'
        folder=OUT/'inputs'/ticker;folder.mkdir(parents=True)
        (folder/'input.txt').write_text(text);(folder/'input.md').write_text(text)
        font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',30)
        image=Image.new('RGB',(1440,900),'white');draw=ImageDraw.Draw(image)
        draw.multiline_text((55,50),'\n\n'.join('\n'.join(textwrap.wrap(line,78)) for line in text.splitlines() if line),font=font,fill='black',spacing=12)
        image.save(folder/'input.png');image.save(folder/'input.jpg',quality=85);image.save(folder/'input.webp',quality=85)
        writer=PdfWriter();page=writer.add_blank_page(width=612,height=792)
        fontobj=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):writer._add_object(fontobj)})})
        lines=['BT /F1 11 Tf 40 740 Td 17 TL']
        for line in text.splitlines():
          for row in textwrap.wrap(line,85) or ['']:
            row=row.replace('\\','\\\\').replace('(','\\(').replace(')','\\)');lines.append('('+row+') Tj T*')
        stream=DecodedStreamObject();stream.set_data(('\n'.join(lines)+'\nET').encode());page[NameObject('/Contents')]=writer._add_object(stream);writer.write(folder/'input.pdf')
        run([str(ESPEAK),'-v','en-us','-s','145','-f',str(folder/'input.txt'),'-w',str(folder/'input.wav')])
        run(['ffmpeg','-v','error','-i',str(folder/'input.wav'),'-codec:a','libmp3lame','-q:a','4',str(folder/'input.mp3')])
        run(['ffmpeg','-v','error','-loop','1','-framerate','1','-i',str(folder/'input.png'),'-i',str(folder/'input.wav'),'-c:v','libx264','-tune','stillimage','-pix_fmt','yuv420p','-c:a','aac','-b:a','64k','-shortest',str(folder/'input.mp4')])
        docs.append({'id':ticker,'split':split,'ticker':ticker,'period':period,'gold':gold,'reference_text':str((folder/'input.txt').relative_to(ROOT))})
        for ext in ['txt','md','pdf','png','jpg','webp','wav','mp3','mp4']:
          path=folder/f'input.{ext}';cases.append({'id':f'{ticker}-{ext}','document':ticker,'split':split,'format':ext,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size})
    (OUT/'gold.json').write_text(json.dumps(docs,indent=2,default=float)+'\n')
    manifest={'schema_version':1,'cutoff':'2026-10-30','kind':'new controlled paired-format study; synthetic media, not real speaker recordings','dev_documents':2,'test_documents':6,'test_assertions':24,'formats':['txt','md','pdf','png','jpg','webp','wav','mp3','mp4'],'cases':cases,'gold_sha256':sha(OUT/'gold.json'),'generation':{'speech':'eSpeak NG en-us 145 wpm offline formant synthesis','image':'Pillow, Arial 30, 1440x900; JPEG/WebP quality 85','pdf':'pypdf native Helvetica text','video':'static same-page image with same synthetic audio, H264/AAC; no dynamic-video generalization'},'source_manifest':'docs/evidence/sec-refresh-2026-10-30/manifest.json','source_manifest_sha256':sha(ROOT/'docs/evidence/sec-refresh-2026-10-30/manifest.json'),'input_budget_authorization_usd':{'meta':40,'baseten':40,'fireworks':40}}
    for page in (4,5,23):
        path=ROOT/f'docs/evidence/real-media-2026-10-30/images/tesla-q3-2026-{page:02}.png'
        cases.append({'id':f'REAL-TSLA-{page}','document':f'REAL-TSLA-{page}','split':'diagnostic','format':'png','path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'annotation_scope':'unscored real-document diagnostic; no complete gold denominator'})
    manifest['diagnostic_images']=3
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Built',len(cases),'paired files;',len(docs),'issuer documents')
if __name__=='__main__':main()
