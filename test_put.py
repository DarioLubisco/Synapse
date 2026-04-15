import requests

url = "http://localhost:8000/api/procurement/providers/VEP"
payload = {
    "CodProv": "VEP",
    "BaseDiasCredito": "Recepcion Mercancia", # Or EMISION
    "DiasNoIndexacion": 15,
    "DiasVencimiento": 15,
    "Descuentos": [
        {"DiasDesde": 0, "DiasHasta": 2, "Porcentaje": 12, "DeduceIVA": False},
        {"DiasDesde": 3, "DiasHasta": 6, "Porcentaje": 6, "DeduceIVA": False}
    ],
    "DescuentoBase_Pct": 0,
    "DescuentoBase_Condicion": "INDEPENDIENTE",
    "DescuentoBase_DeduceIVA": False,
    "Email": "test@test.com",
    "IndexaIVA": True,
    "DecimalesTasa": 4,
    "TipoPersona": "PJ"
}
try:
    response = requests.put(url, json=payload)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print(e)
