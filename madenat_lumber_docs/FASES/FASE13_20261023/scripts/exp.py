import io, openpyxl
P=env['madenat.reception.parser']

def patched(path, patch):
    wb=openpyxl.load_workbook(path)
    ws=wb.worksheets[0]
    patch(ws)
    b=io.BytesIO(); wb.save(b)
    return P.parse_excel(b.getvalue(),'f5085')

print('=== VIRGO: etiquetas alfanumericas -> numericas (simula que int() no las descarte) ===')
def p1(ws):
    n=1
    for r in range(1,ws.max_row+1):
        v=ws.cell(r,5).value
        if isinstance(v,str) and v.upper().startswith('A1F'):
            ws.cell(r,5).value=n; n+=1
r=patched('/tmp/tarjas/v.xlsx',p1)
print(' lineas=',len(r['lines']),'vol=%.3f'%sum(float(l['volume_m3']) for l in r['lines']),'warns=',len(r['warnings']))
seen=set()
for l in r['lines']:
    k=(l['thickness_visual'],l['width_visual'],l['length_input_raw'],l['thickness_mm'],l['width_mm'],l['length_m'],l['length_uom'])
    if k in seen or len(seen)>8: continue
    seen.add(k); print('   esp_v=%r anc_v=%r lar_raw=%r -> %s mm / %s mm / %s %s'%k)

print('=== ELENOIRE: 6/4 -> 1.5 numerico (simula celda en pulgadas decimales) ===')
def p2(ws):
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value,str) and c.value.strip()=='6/4':
                c.value=1.5; c.number_format='General'
r=patched('/tmp/tarjas/e.xlsx',p2)
print(' lineas=',len(r['lines']),'vol=%.3f'%sum(float(l['volume_m3']) for l in r['lines']),'warns=',len(r['warnings']))
seen=set()
for l in r['lines']:
    k=(l['thickness_visual'],l['width_visual'],l['length_input_raw'],l['thickness_mm'],l['width_mm'],l['length_m'],l['length_uom'],l['thickness_nominal'])
    if k in seen or len(seen)>8: continue
    seen.add(k); print('   esp_v=%r anc_v=%r lar_raw=%r -> %s mm / %s mm / %s %s nom=%s'%k)
env.cr.rollback()
