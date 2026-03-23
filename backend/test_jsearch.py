import requests

print('=== 1. Test JSearch API Directly ===')
url = 'https://jsearch.p.rapidapi.com/search'
querystring = {'query': 'Software Engineer fresher India', 'page': '1', 'num_pages': '1'}
headers = {
    'X-RapidAPI-Key': 'aab041dac2msh037e436419fbfc3p1cfd22jsnf40409c69de',
    'X-RapidAPI-Host': 'jsearch.p.rapidapi.com'
}
try:
    r = requests.get(url, headers=headers, params=querystring, timeout=10)
    print('STATUS:', r.status_code)
    if r.status_code == 200:
        data = r.json()
        jobs = data.get('data', [])
        print(f'SUCCESS! Found {len(jobs)} jobs.')
        if jobs:
            print(f'First job: {jobs[0].get("job_title")} at {jobs[0].get("employer_name")}')
    else:
        print('JSON:', r.text[:200])
except Exception as e:
    print('Error:', e)

print('\n=== 2. Test Local Backend Endpoint ===')
try:
    r = requests.get('http://127.0.0.1:8000/api/jobs/listings/Software%20Engineer', timeout=15)
    print('STATUS:', r.status_code)
    data = r.json()
    print('Response Source:', data.get('source'))
    print('Jobs Count:', len(data.get('jobs', [])))
    if data.get('jobs'):
        print(f'First job: {data["jobs"][0].get("job_title")} at {data["jobs"][0].get("employer_name")}')
except Exception as e:
    print('Error:', e)
