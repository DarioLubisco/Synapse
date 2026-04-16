import sys
sys.path.append('c:\\source\\Synapse\\backend')
from routers.cxp import generar_pdf_retencion

config = {'RazonSocial_Agente': 'Test', 'RIF_Agente': 'J-1234', 'DireccionFiscal_Agente': 'Test address'}
ret_list = [{'NumeroD': '0193777', 'NroControl': '00-219853', 'FechaFactura': '2026-04-16', 'MontoTotal': 83037.35, 'BaseImponible': 1618.06, 'Alicuota': 16, 'IVACausado': 258.89, 'PorcentajeRetencion': 100, 'MontoRetenido': 258.89, 'CodProv': 'J-500976160', 'ProveedorNombre': 'PROVEEDOR C.A.', 'MontoExento': 81160.4}]

try:
    pdf_bytes = generar_pdf_retencion(config, ret_list)
    print(f"Generated PDF of type {type(pdf_bytes)}")
except Exception as e:
    import traceback
    traceback.print_exc()
