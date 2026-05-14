import json
from power_sector_dashboard import infer_job_country

with open('jobs_20260427_180812.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

count = 0
for job in jobs:
    if job.get('country') == 'in':
        desc = job.get('description', '') + ' ' + job.get('title', '')
        inferred = infer_job_country(desc, 'in')
        if inferred != 'in':
            count += 1
            print(f"Job Title: {job.get('title')}".encode('ascii', 'ignore').decode('ascii'))
            print(f"Company: {job.get('company')}".encode('ascii', 'ignore').decode('ascii'))
            print(f"Reassigned to: {inferred}".encode('ascii', 'ignore').decode('ascii'))
            print('-'*40)

print(f'\nTotal jobs posted in India but mapped to another country/offshore: {count}')
