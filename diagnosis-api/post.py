import requests
from util import generate_random_tek, encodeb64

data = {
    'authority': '2iUNf7/8pjS/mzjpQwUIuw==',
    'reports': [],
}
for i in range(10):
    tek, enin = generate_random_tek()
    data['reports'].append({
        'TEK': encodeb64(tek),
        'ENIN': enin,
    })

res = requests.post('http://localhost:5000/add-report', json=data)
print(res.ok)
print(res.json())
