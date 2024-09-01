
import requests
register_url = 'https://api.watttime.org/register'
params = {'username': 'westkath',
         'password': '0Carbon>apocalypse',
         'email': 'k.west.1@research.gla.ac.uk',
         'org': 'University of Glasgow'}
rsp = requests.post(register_url, json=params)
print(rsp.text)
