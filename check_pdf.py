import sys
sys.path.append('c:\\source\\Synapse\\backend')
import database
from routers.cxp import generar_pdf_nc_request

try:
    nc_data = {'Id': 17, 'NumeroD': '054393', 'Motivo': 'PAGO_EXCESO', 'MontoBs': 100.0, 'MontoUsd': 5.0, 'Observacion': ''}
    prov_data = {'CodProv': 'J-411993918-8', 'Descrip': 'DROPHARMA D.M', 'ID3': 'J-411993918-8', 'Email': 'test@test.com'}
    pdf_bytes = generar_pdf_nc_request(nc_data, prov_data, "Prueba cuerpo")
    print("PDF bytes generated correctly, size:", len(pdf_bytes))
    with open("c:\\source\\test_pdf.pdf", "wb") as f:
        f.write(pdf_bytes)
except Exception as e:
    import traceback
    traceback.print_exc()
