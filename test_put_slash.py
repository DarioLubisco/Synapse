import requests

url = "http://localhost:8000/api/procurement/providers/MAS%2F001"
payload = {
    "CodProv": "MAS/001",
    "BaseDiasCredito": "ENTREGA",
    "DiasNoIndexacion": 15,
    "DiasVencimiento": 15,
}
try:
    response = requests.put(url, json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print(e)
