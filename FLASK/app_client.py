import requests

url = 'http://127.0.0.1:1080/predict'  # localhost and the defined port + endpoint
body = {
    "date": '2018-01-01',
    "store": 1,
    "item": 1
}
response = requests.post(url, data=body)
print(response.json())