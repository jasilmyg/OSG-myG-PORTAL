import urllib.request
import json
import re

url = 'https://www.postman.com/telinfy-89/telinfy-platforms-by-greenads-global/request/32953601-5222e827-0471-4573-822d-2965f0eb4633?ctx=documentation'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    match = re.search(r'__PRELOADED_STATE__\s*=\s*(\{.*?\});', html)
    if match:
        data = json.loads(match.group(1))
        with open('postman_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print('Saved to postman_data.json')
    else:
        print('No preloaded state found')
except Exception as e:
    print(e)
