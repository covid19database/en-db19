import requests
res = requests.get('http://localhost:5000/get-diagnosis-keys')
print(res.ok)
print(res.json())
