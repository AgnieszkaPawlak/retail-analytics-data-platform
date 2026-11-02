#!/usr/bin/env python3
"""DE-002 evidence collector for UCI Online Retail and the ECB EXR API.

Usage:
    python profile_sources.py --retail-xlsx 'Online Retail.xlsx' --with-ecb
    python profile_sources.py --download-retail --with-ecb

Run on an internet-connected machine with: pip install pandas openpyxl requests.
This emits raw empirical observations to profiling_evidence.json; it does NOT
interpret business revenue or invent a cancellation-to-order matching policy.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from collections import Counter
from datetime import datetime, timezone

import pandas as pd
import requests

UCI_ZIP = 'https://archive.ics.uci.edu/static/public/352/online+retail.zip'
ECB_BASE = 'https://data-api.ecb.europa.eu/service/data/EXR/D.GBP.EUR.SP00.A'
BASE_COLUMNS = ['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as file:
        for part in iter(lambda: file.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def download_retail(path):
    r = requests.get(UCI_ZIP, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith('.xlsx')]
        if len(names) != 1:
            raise RuntimeError(f'Expected exactly one XLSX, got {names!r}')
        path.write_bytes(archive.read(names[0]))
    return path


def numeric_summary(series):
    n = pd.to_numeric(series, errors='coerce')
    valid = n.dropna()
    return {
        'min': float(valid.min()) if len(valid) else None,
        'p01': float(valid.quantile(.01)) if len(valid) else None,
        'median': float(valid.median()) if len(valid) else None,
        'p99': float(valid.quantile(.99)) if len(valid) else None,
        'max': float(valid.max()) if len(valid) else None,
    }


def retail_profile(path):
    df = pd.read_excel(path, engine='openpyxl', dtype={'InvoiceNo':'string','StockCode':'string','Description':'string','Country':'string'})
    if sorted(df.columns.tolist()) != sorted(BASE_COLUMNS):
        raise ValueError(f'Unexpected columns: {df.columns.tolist()}')
    n = len(df)
    dates = pd.to_datetime(df['InvoiceDate'], errors='coerce')
    q = pd.to_numeric(df['Quantity'], errors='coerce')
    p = pd.to_numeric(df['UnitPrice'], errors='coerce')
    inv = df['InvoiceNo'].astype('string')
    cancel = inv.str.upper().str.startswith('C', na=False)
    negq = q < 0
    has_cust = df['CustomerID'].notna()
    month = dates.dt.to_period('M')
    daily = dates.dt.normalize().dropna().drop_duplicates()
    if dates.notna().any():
        span = pd.date_range(dates.min().normalize(), dates.max().normalize(), freq='D')
        absent = span.difference(pd.DatetimeIndex(daily))
    else:
        absent = pd.DatetimeIndex([])
    # This check counts only exact same eight-column rows. Identical lines may
    # still represent legitimate repeated items; do not delete automatically.
    duplicates = int(df.duplicated(keep='first').sum())
    product_desc = df[['StockCode','Description']].dropna().groupby('StockCode')['Description'].nunique()
    grouped = df.groupby(month, dropna=False)
    months = []
    for key, subset in grouped:
        if pd.isna(key):
            label = '(invalid/missing date)'
        else:
            label = str(key)
        months.append({'month': label,'rows': int(len(subset)),
                       'missing_customer_id': int(subset['CustomerID'].isna().sum()),
                       'missing_description': int(subset['Description'].isna().sum()),
                       'cancellation_prefix_rows': int(subset['InvoiceNo'].astype('string').str.upper().str.startswith('C',na=False).sum())})
    return {
        'source_file': str(path), 'source_sha256': sha256_file(path),
        'rows': n, 'columns': df.columns.tolist(),
        'dtype_inferred': {k:str(v) for k,v in df.dtypes.items()},
        'missing': {k:int(v) for k,v in df.isna().sum().items()},
        'missing_pct': {k:round(float(v/n*100),4) for k,v in df.isna().sum().items()},
        'description_missing_with_customer_missing':int((df['Description'].isna() & ~has_cust).sum()),
        'full_duplicate_rows_excluding_first':duplicates,
        'unique_invoices':int(inv.nunique(dropna=True)),
        'unique_customers':int(df['CustomerID'].nunique(dropna=True)),
        'unique_stock_codes':int(df['StockCode'].nunique(dropna=True)),
        'unique_countries':int(df['Country'].nunique(dropna=True)),
        'unique_invoice_stock_pairs':int(df[['InvoiceNo','StockCode']].drop_duplicates().shape[0]),
        'repeated_invoice_stock_rows_excluding_first':int(df.duplicated(['InvoiceNo','StockCode'],keep='first').sum()),
        'stock_codes_with_multiple_descriptions':int((product_desc>1).sum()),
        'cancellation_prefix_rows':int(cancel.sum()),
        'negative_quantity_rows':int(negq.sum()),
        'negative_quantity_without_cancellation_prefix':int((negq & ~cancel).sum()),
        'cancel_prefix_without_negative_quantity':int((cancel & ~negq).sum()),
        'zero_quantity_rows':int((q==0).sum()),
        'zero_unit_price_rows':int((p==0).sum()),
        'negative_unit_price_rows':int((p<0).sum()),
        'non_numeric_quantity_rows':int((q.isna() & df['Quantity'].notna()).sum()),
        'non_numeric_unit_price_rows':int((p.isna() & df['UnitPrice'].notna()).sum()),
        'invalid_invoice_dates':int((dates.isna() & df['InvoiceDate'].notna()).sum()),
        'quantity_distribution':numeric_summary(q),
        'unit_price_distribution':numeric_summary(p),
        'first_invoice_ts': dates.min().isoformat() if dates.notna().any() else None,
        'last_invoice_ts': dates.max().isoformat() if dates.notna().any() else None,
        'active_calendar_days':int(daily.nunique()),
        'calendar_days_without_transactions':int(len(absent)),
        'days_without_transactions_sample': [d.strftime('%Y-%m-%d') for d in absent[:30]],
        'months':months,
        'country_top_10':{str(k):int(v) for k,v in df['Country'].value_counts().head(10).items()},
        'notes':['Raw source preserved; no cleaning, line matching, currency conversion or revenue recognition policy applied.']
    }


def fetch_ecb(start='2010-12-01',end='2011-12-09'):
    url = ECB_BASE
    params = {'startPeriod':start,'endPeriod':end,'format':'csvdata'}
    r = requests.get(url,params=params,headers={'Accept':'text/csv'},timeout=45)
    record={'request_url':r.url,'status_code':r.status_code,'content_type':r.headers.get('Content-Type'),
            'response_bytes':len(r.content),'request_period':[start,end]}
    if r.status_code != 200:
        record['body_preview']=r.text[:500]
        return record
    try:
        data = pd.read_csv(io.BytesIO(r.content))
        record['response_fields']=list(data.columns)
        record['observations']=len(data)
        if {'TIME_PERIOD','OBS_VALUE'}.issubset(data.columns):
            dates=pd.to_datetime(data['TIME_PERIOD'],errors='coerce')
            vals=pd.to_numeric(data['OBS_VALUE'],errors='coerce')
            record['first_observation_date']=dates.min().strftime('%Y-%m-%d') if dates.notna().any() else None
            record['last_observation_date']=dates.max().strftime('%Y-%m-%d') if dates.notna().any() else None
            record['invalid_dates']=int(dates.isna().sum())
            record['missing_or_invalid_rates']=int(vals.isna().sum())
            record['zero_or_negative_rates']=int((vals<=0).sum())
            record['duplicate_observation_dates']=int(dates.duplicated().sum())
            record['weekend_observations']=int((dates.dt.weekday>=5).sum())
            record['rate_min']=float(vals.min())
            record['rate_max']=float(vals.max())
            record['sample_first_3_rows']=data.head(3).astype(str).to_dict(orient='records')
        else:
            record['parse_warning']='Missing TIME_PERIOD or OBS_VALUE'
    except Exception as ex:
        record['parse_error']=repr(ex)
    return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--retail-xlsx',type=Path)
    parser.add_argument('--download-retail',action='store_true')
    parser.add_argument('--with-ecb',action='store_true')
    parser.add_argument('--output',type=Path,default=Path('profiling_evidence.json'))
    args=parser.parse_args()
    output={'run_utc':datetime.now(timezone.utc).isoformat(),
            'provenance':{'uci_url':UCI_ZIP,'ecb_url':ECB_BASE},'status':{}}
    path=args.retail_xlsx
    if args.download_retail:
        path=Path('Online Retail.xlsx')
        try:
            download_retail(path)
        except Exception as ex:
            output['status']['uci_download_error']=repr(ex)
    if path and path.exists():
        output['uci_retail']=retail_profile(path)
        output['status']['uci']='measured_from_supplied_file'
    elif path:
        output['status']['uci']='not_measured_no_file'
    if args.with_ecb:
        try:
            output['ecb_fx']=fetch_ecb()
            output['status']['ecb']='response_observed'
        except Exception as ex:
            output['status']['ecb']='request_failed'
            output['ecb_fx']={'exception':repr(ex),'url':ECB_BASE}
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Wrote {args.output}')
    print(json.dumps(output['status'],indent=2))

if __name__=='__main__': main()