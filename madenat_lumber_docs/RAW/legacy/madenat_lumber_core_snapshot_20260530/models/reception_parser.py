# -*- coding: utf-8 -*-
import logging
import io
import re
import pandas as pd
from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class MadenatReceptionParser(models.AbstractModel):
    _name = 'madenat.reception.parser'
    _description = 'Dispatcher Multi-Formato para Recepción de Madera'

    _BLANKS_NOMINAL_MAP = [
        (1.0,    1.0),
        (1.25,   1.25),
        (1.5,    1.5),
        (1.5625, 1.5),
        (2.0,    2.0),
        (2.0625, 2.0),
        (2.5,    2.5),
        (3.0,    3.0),
    ]
    _NOMINAL_TOLERANCE = 0.08

    @api.model
    def _resolve_nominal(self, raw_inches):
        for physical, nominal in self._BLANKS_NOMINAL_MAP:
            if abs(raw_inches - physical) <= self._NOMINAL_TOLERANCE:
                return nominal
        return raw_inches
  
    @api.model
    def parse_excel(self, excel_bytes, ingestion_profile='f5085'):
        import re # Importante mantener esto
        import numpy as np # Necesario para manejar NaNs de texto
        logs = []
        warnings = []
        guide_no_detected = ''
        
        try:
            excel_file = io.BytesIO(excel_bytes)
            
            # ====================================================================
            # 1. BÚSQUEDA DE CABECERA Y N° GUÍA
            # ====================================================================
            df_header_search = pd.read_excel(excel_file, sheet_name=0, header=None, nrows=25)
            
            for idx, row in df_header_search.iterrows():
                row_str = ' '.join([str(x) for x in row if pd.notna(x)])
                
                match = re.search(r'gu[ií]a.*?\b(\d{4,7})\b', row_str, re.IGNORECASE)
                if match and not guide_no_detected:
                    guide_no_detected = match.group(1)

            header_row_idx = self._find_header_row(df_header_search)
            if header_row_idx is None:
                header_row_idx = 8
                warnings.append(f"⚠️ Encabezados no detectados - asumiendo fila {header_row_idx+1}")
            else:
                logs.append(f"✅ Encabezados detectados en fila {header_row_idx + 1}")

            if guide_no_detected:
                logs.append(f"📄 Nro. Guía detectado en Excel: {guide_no_detected}")

            # ====================================================================
            # 2. LECTURA HEURÍSTICA Y SCORING SEMÁNTICO (v8.0)
            # ====================================================================
            excel_file.seek(0)
            df_raw = pd.read_excel(excel_file, sheet_name=0, skiprows=header_row_idx)
            
            if df_raw.empty:
                raise UserError("El archivo Excel está vacío debajo de la fila de encabezados.")

            actual_columns = []
            for col in df_raw.columns:
                col_clean = str(col).lower().strip().replace('\n', ' ').replace('\r', '')
                col_clean = col_clean.replace('í', 'i').replace('ó', 'o').replace('á', 'a')
                actual_columns.append(col_clean)
            
            df_raw.columns = actual_columns

            aliases = {
                'package_no':   ['paquete', 'lote', 'etiqueta', 'nro', 'n°', 'id'],
                'product_code': ['codigo', 'cod', 'item', 'sku', 'material'],
                'product_name': ['producto', 'descrip', 'articulo', 'especie', 'subproducto'],
                'thickness_mm': ['espesor', 'esp', 'thick'],
                'width_mm':     ['ancho', 'anc', 'width'],
                'length_m':     ['largo', 'longitud', 'length'],
                'pieces':       ['piezas', 'pzas', 'pcs', 'cantidad', 'cant', 'unidades', 'unid'],
                'volume_m3':    ['volumen', 'vol', 'm3', 'cbm', 'cubico', 'pt']
            }

            extracted_cols = {}
            missing_critical = []

            for internal_name, alias_list in aliases.items():
                best_match_col = None
                best_score = 0
                
                for col_name in actual_columns:
                    if 'unnamed' in col_name:
                        continue
                        
                    score = 0
                    for alias in alias_list:
                        if alias == col_name:
                            score = max(score, 100)
                        elif re.search(r'\b' + alias + r'\b', col_name):
                            score = max(score, 80)
                        elif col_name.startswith(alias):
                            score = max(score, 60)
                        elif alias in col_name:
                            score = max(score, 40)
                    
                    if score > best_score:
                        best_score = score
                        best_match_col = col_name

                if best_match_col and best_score >= 40:
                    extracted_cols[internal_name] = df_raw[best_match_col]
                    logs.append(f"🎯 Mapeo: '{internal_name}' asignado a columna Excel '{best_match_col}'")
                else:
                    extracted_cols[internal_name] = pd.Series([0] * len(df_raw))
                    if internal_name in ['package_no', 'pieces', 'volume_m3', 'thickness_mm']:
                        missing_critical.append(internal_name)

            if missing_critical:
                raise UserError(
                    f"⛔ MADENAT Parser: Formato de Excel irreconocible.\n"
                    f"Faltan columnas vitales: {', '.join(missing_critical)}.\n"
                    f"Asegúrese de que los encabezados usen términos comunes (Ej: Lote, Piezas, Volumen)."
                )

            df = pd.DataFrame(extracted_cols)

            # ====================================================================
            # 3. LIMPIEZA AGRESIVA Y TRADUCTOR REGIONAL (v8.1)
            # ====================================================================
            
            def scrub_number(val):
                """ Elimina letras, unidades y repara decimales chilenos """
                if pd.isna(val): return val
                val_str = str(val).lower()
                
                # Extirpar unidades de medida
                val_str = re.sub(r'(m3|m³|mm|cm|m|pcs|pzas|pt|unid)', '', val_str).strip()
                
                # 🇨🇱 TRADUCTOR CHILENO A PYTHON
                # Si el número viene como "1.500,25" lo pasamos a "1500.25"
                if ',' in val_str:
                    val_str = val_str.replace('.', '')  # Quitamos el punto de miles
                    val_str = val_str.replace(',', '.') # Convertimos la coma decimal a punto
                
                return val_str

            # 1. Tratar al LOTE como TEXTO PURO (No convertir a float)
            df['package_no'] = df['package_no'].apply(lambda x: str(x).strip() if pd.notna(x) else np.nan)
            df['package_no'] = df['package_no'].replace({'': np.nan, 'nan': np.nan, 'none': np.nan})

            # 2. Aplicar limpiador y convertidor numérico SOLO a campos matemáticos
            numeric_cols = ['pieces', 'volume_m3', 'thickness_mm', 'width_mm', 'length_m']
            for col in numeric_cols:
                df[col] = df[col].apply(scrub_number)
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 3. Eliminar filas que quedaron sin lote, piezas o volumen
            df = df.dropna(subset=['package_no', 'pieces', 'volume_m3'], how='any')

            # 4. Filtrar datos válidos (Notar que package_no ya no se compara con > 0)
            df_clean = df[(df['pieces'] > 0) & (df['volume_m3'] > 0)].copy()
            
            if df_clean.empty:
                raise UserError("El archivo fue leído, pero no se encontraron filas válidas. Revise que los números de Piezas y Volumen no tengan formatos irreconocibles.")
            
            # Auditoría final de dimensiones
            negative_rows = df_clean[(df_clean['thickness_mm'] <= 0) | (df_clean['width_mm'] <= 0) | (df_clean['length_m'] <= 0)]
            if not negative_rows.empty:
                sample = negative_rows.head(3)
                error_details = [f"  Fila Lote {r['package_no']}: Esp:{r['thickness_mm']} Anc:{r['width_mm']} L:{r['length_m']}" for idx, r in sample.iterrows()]
                raise UserError(f"❌ DIMENSIONES INVÁLIDAS. Filas con error:\n" + "\n".join(error_details))

            # ====================================================================
            # 4. DISPATCHER E INYECCIÓN DE DATOS
            # ====================================================================
            logs.append(f"🔍 DISPATCHER: Perfil activo -> {ingestion_profile.upper()}")
            
            parsed_data = self._process_dataframe(df_clean, ingestion_profile, logs, warnings)
            parsed_data['guide_no'] = guide_no_detected
            
            return parsed_data

        except UserError:
            raise
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"❌ Error crítico en Parseo de Excel: {str(e)}", exc_info=True)
            raise UserError(f"Fallo estructural al leer el Excel:\n{str(e)}")
        
    def _find_header_row(self, df_search):
        for idx, row in df_search.iterrows():
            row_str = ' '.join([str(x).lower() for x in row if pd.notna(x)])
            # Regresamos a la lógica flexible de v5.4
            if any(keyword in row_str for keyword in ['pqte', 'package', 'codigo', 'espesor', 'ancho', 'largo']):
                return idx
        return None

    def _detect_format(self, df):
        # ✅ FIX: La columna ahora se llama estrictamente 'thickness_mm'
        if 'thickness_mm' not in df.columns:
            return 'standard'
            
        muestra_espesor = pd.to_numeric(df['thickness_mm'], errors='coerce').dropna()
        
        # Si el valor máximo es menor a 10, es madera imperial (Blanks Clear)
        if not muestra_espesor.empty and muestra_espesor.max() < 10.0:
            return 'blanks_clear'
            
        return 'standard'

    def _process_dataframe(self, df, formato, logs, warnings):
            """Procesa el DataFrame ya limpio y con columnas estandarizadas."""
            lines = []
            total_vol = 0.0

            for idx, row in df.iterrows():
                try:
                    # Ya no usamos next(), usamos los nombres limpios que le dimos en read_excel
                    package_no = int(row['package_no'])
                    pieces = int(row['pieces'])
                    vol_m3 = float(row['volume_m3'])
                    
                    raw_esp = float(row['thickness_mm'])
                    raw_anc = float(row['width_mm'])
                    raw_lar = float(row['length_m'])

                    product_name_raw = str(row['product_name']).strip().upper() if pd.notna(row['product_name']) else 'MADERA'

                  
                    # --- EL ESPEJO DOCUMENTAL Y LA REGLA DE ORO ---
                    if formato == 'f5085':
                            # 🎯 ES EL PERFIL QUE YA TENÍAS, PERO AHORA ES HÍBRIDO
                            thickness_visual = str(raw_esp)
                            width_visual = str(raw_anc)
                            
                            # Si el valor es pequeño (menor a 10), asumimos que son PULGADAS
                            # y las convertimos a MM para el inventario.
                            if raw_esp < 10:
                                thickness_mm = round(raw_esp * 25.4, 2)
                                width_mm = round(raw_anc * 25.4, 2)
                            else:
                                thickness_mm = raw_esp
                                width_mm = raw_anc

                            # Resolvemos el nominal usando tu mapa existente
                            t_nom = self._resolve_nominal(raw_esp)
                            if t_nom == raw_esp:
                                warnings.append(f"⚠️ Paquete {package_no}: nominal {raw_esp}\" sin mapeo.")
                            
                            w_nom = width_mm
                            export_rule = 'f5085'
                            
                            # Si el largo es > 10, asumimos que son PIES y pasamos a METROS
                            length_m = round(raw_lar * 0.3048, 2) if raw_lar > 10 else raw_lar

                    elif formato == 'f1550':
                            thickness_visual = str(raw_esp)
                            width_visual = str(raw_anc)
                            thickness_mm = raw_esp
                            width_mm = raw_anc
                            t_nom, w_nom = raw_esp, raw_anc
                            length_m = raw_lar
                            export_rule = 'f1550'

                    elif formato == 'blanks':
                            # 🎯 FASE 1: EL ESPEJO INAMOVIBLE (Lo que vio el Trader en el Excel)
                            # Se guarda en los campos "visual" (texto) para que no cambien jamás
                            thickness_visual = str(raw_esp) # Ej: "1.5625"
                            width_visual = str(raw_anc)     # Ej: "3.625"
                            
                            # ⚙️ FASE 2 oculta: CONVERSIÓN SILENCIOSA A MÉTRICO (Para Inventario)
                            thickness_mm = round(raw_esp * 25.4, 2)  # 1.5625 -> 39.69
                            width_mm = round(raw_anc * 25.4, 2)      # 3.625 -> 92.08
                            length_m = round(raw_lar * 0.3048, 2)    # 16 ft -> 4.88
                            
                            # El Nominal Base nace del métrico, listo para que el Wizard lo aplaste a 40x90
                            t_nom, w_nom = thickness_mm, width_mm
                            
                            # 🚀 FASE 3: REGLA DE EXPORTACIÓN (S2S)
                            export_rule = 'f1550' 

                    else: # 'metric'
                            thickness_visual = str(raw_esp)
                            width_visual = str(raw_anc)
                            thickness_mm = raw_esp
                            width_mm = raw_anc
                            t_nom, w_nom = raw_esp, raw_anc
                            length_m = raw_lar
                            export_rule = 'metric'

                    lines.append({
                        'package_no': package_no,
                        'product_code': str(row['product_code']).strip() if pd.notna(row['product_code']) else '',
                        'product_name': product_name_raw,
                        'pieces': pieces,
                        'volume_m3': vol_m3,
                        'unit_price_usd': 0.0, # El orquestador inyectará el precio real
                        'thickness_mm': thickness_mm,
                        'width_mm': width_mm,
                        'length_m': length_m,
                        'thickness_visual': thickness_visual,
                        'width_visual': width_visual,
                        'thickness_nominal': t_nom,
                        'width_nominal': w_nom,
                        'export_rule': export_rule
                    })
                    total_vol += vol_m3
                    
                except Exception as e:
                    warnings.append(f"⚠️ Omitiendo línea (Paquete {row.get('package_no', 'N/A')}): {e}")
                    continue

            logs.append(f"✅ Parser extrajo {len(lines)} líneas válidas. Volumen Excel: {total_vol:.3f} m³")

            return {
                'lines': lines,
                'total_volume_m3': total_vol,
                'total_volume_mbf': total_vol / 2.36,
                'logs': logs,
                'warnings': warnings
            }

    @api.model
    def _validate_excel_columns(self, df, required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValidationError(f"❌ Estructura de Excel inválida. Faltan las columnas: {', '.join(missing)}")

    # ====================================================================
    # 5. NORMALIZACIÓN DE ÓRDENES DE COMPRA
    # ====================================================================
    @api.model
    def normalize_po_key(self, value):
        """ Clave interna de comparación OC — elimina todo separador. """
        if not value: return ''
        import re
        return re.sub(r'[^A-Z0-9]+', '', value.upper())

    @api.model
    def normalize_po_display(self, value):
        """ Formato visual estándar MADENAT: PREFIJO 1234-567 """
        if not value: return False
        import re
        v = value.strip().upper().replace('\xa0', ' ')
        v = re.sub(r'\s+', ' ', v).strip()
        m = re.match(r'^([A-Z]{2,3})[\s\-]*(\d{3,5})[\s\-]+(\d{1,6})$', v)
        if m: return f"{m.group(1)} {m.group(2)}-{m.group(3)}"
        return v

    # ====================================================================
    # 6. PARSEO DE PDF: GUÍA DE DESPACHO
    # ====================================================================
    @api.model
    def parse_dispatch_guide(self, pdf_bytes, default_name=''):
        import pdfplumber
        import re
        import io
        from datetime import datetime, date

        def _normalizar_texto_pdf(texto):
            if not texto: return ""
            texto = texto.replace("\xa0", " ")
            texto = re.sub(r"[ \t]+", " ", texto)
            texto = re.sub(r"\s*\n\s*", "\n", texto)
            return texto.strip()

        def _normalizar_oc(oc_raw):
            if not oc_raw: return None
            oc_raw = oc_raw.replace("\xa0", " ")
            oc_raw = re.sub(r"\s+", " ", oc_raw).strip()
            match = re.search(r'([A-Z]{2,}[A-Z]?)\s*(\d{4,})\s*[-\s]?\s*(\d{1,6})', oc_raw, re.IGNORECASE)
            if not match: return oc_raw.strip()
            return f"{match.group(1).upper()} {match.group(2)} {match.group(3)}"

        pdf_buffer = io.BytesIO(pdf_bytes)
        full_text = ""
        with pdfplumber.open(pdf_buffer) as pdf:
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"

        full_text = _normalizar_texto_pdf(full_text)

        # 1. RUT Proveedor
        rut_matches = re.finditer(r'R[\.\s]*U[\.\s]*T[\.\s]*[:\s]*(\d{1,2}\.\d{3}\.\d{3}-[\dkK])', full_text, re.IGNORECASE)
        supplier_rut = None
        for m in rut_matches:
            found_rut = m.group(1).strip()
            if '76.103.087' not in found_rut:
                supplier_rut = found_rut
                break

        # 2. Nombre Proveedor
        supplier_name = "Proveedor Desconocido"
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        if lines:
            potential_name = lines[0]
            if any(x in potential_name.upper() for x in ['GUIA', 'ELECTRONICA', 'FACTURA']):
                potential_name = lines[1] if len(lines) > 1 else potential_name
            clean_name = re.split(r'R\.?U\.?T\.?|[\d]{1,2}\.[\d]{3}\.', potential_name, flags=re.IGNORECASE)[0]
            clean_name = re.sub(r'[:\-\s\.,]+$', '', clean_name).strip()
            supplier_name = clean_name[:128]

        # 3. Orden de Compra
        texto_busqueda = re.sub(r"\s+", " ", full_text).strip()
        po_ref_raw = None
        patrones_oc = [
            r'(?:ORDEN\s+DE\s+COMPRA|OC|O/C|NRO\.?|N°|Nº|Orden)\s*[:\-]?\s*([A-Z]{2,3}[\s\-]*\d{3,5}[\s\-]+\d{1,6})',
            r'\b([A-Z]{2,3}[\s\-]+\d{3,5}[\s\-]+\d{1,6})\b',
            r'\b([A-Z]{2,3}[\-]\d{3,5}[\-]\d{1,6})\b',
        ]
        for patron in patrones_oc:
            match = re.search(patron, texto_busqueda, re.IGNORECASE)
            if match:
                po_ref_raw = _normalizar_oc(match.group(1))
                break
        po_ref = self.normalize_po_display(po_ref_raw) if po_ref_raw else None

        # 4. Número Guía
        guide_match = re.search(r'(?:GUIA|GUÍA|N°|Nº)\s*[:\-]?\s*(\d+)', full_text, re.IGNORECASE)
        guide_no = guide_match.group(1).strip() if guide_match else default_name

        # 5. Totales y Volumen
        net_total = 0.0
        for pattern in [r'(?:NETO|TOTAL\sNETO|MONTO\sNETO)[\s\S]{0,20}?\$?\s*([\d\.,]{5,})', r'(?:TOTAL)[\s\S]{0,20}?\$?\s*([\d\.,]{5,})']:
            match_net = re.search(pattern, full_text, re.IGNORECASE)
            if match_net:
                clean_net = re.sub(r'[^\d]', '', match_net.group(1))
                if clean_net.isdigit() and len(clean_net) > 4:
                    net_total = float(clean_net)
                    break

        vol_match = re.search(r'(?:VOLUMEN|TOTAL M3)[\s\S]{0,20}?([\d\.,]{2,})\s*(?:M3|m3|m³)?', full_text, re.IGNORECASE)
        total_volume = 0.0
        if vol_match:
            v_str = vol_match.group(1).replace('.', '').replace(',', '.') if ',' in vol_match.group(1) else vol_match.group(1)
            try: total_volume = float(v_str)
            except: pass

        # 6. Fecha y TC
        guide_date = None
        for pattern in [r'Fecha[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})']:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                for fmt in ('%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y'):
                    try:
                        guide_date = datetime.strptime(m.group(1), fmt).date()
                        break
                    except: pass
                if guide_date: break

        pdf_exchange_rate = 0.0
        for pattern in [r'T/?\.?C\.?[\s\S]{0,15}?([\d\.,]{3,})', r'Tipo\s+de\s+Cambio[\s\S]{0,15}?([\d\.,]{3,})', r'Valor\s+USD[\s\S]{0,15}?([\d\.,]{3,})']:
            tc_match = re.search(pattern, full_text, re.IGNORECASE)
            if tc_match:
                raw_tc = tc_match.group(1).strip().split('/')[0]
                raw_tc = raw_tc.replace('.', '').replace(',', '.') if ',' in raw_tc and '.' in raw_tc else raw_tc.replace(',', '.')
                try:
                    val = float(raw_tc)
                    if val > 500.0:
                        pdf_exchange_rate = val
                        break
                except: pass

        return {
            'supplier_rut': supplier_rut,
            'supplier_name_detected': supplier_name,
            'guide_no': guide_no,
            'guide_date': guide_date,
            'exchange_rate': pdf_exchange_rate,
            'po_ref': po_ref,
            'net_total': net_total,
            'total_volume': total_volume,
            'iva': 0.0,
            'total': net_total * 1.19 if net_total else 0.0,
            '_debug_full_text': full_text[:500] 
        }

    # ====================================================================
    # 7. PARSEO DE PDF: ORDEN DE COMPRA
    # ====================================================================
    @api.model
    def parse_purchase_order(self, pdf_bytes):
        import pdfplumber
        import io
        import re

        def _norm(texto):
            if not texto: return ""
            texto = texto.replace("\xa0", " ")
            texto = re.sub(r"[ \t]+", " ", texto)
            return re.sub(r"\s*\n\s*", "\n", texto).strip()

        pdf_buffer = io.BytesIO(pdf_bytes)
        full_text = ""
        with pdfplumber.open(pdf_buffer) as pdf:
            for page in pdf.pages:
                full_text += (page.extract_text() or "") + "\n"
        full_text = _norm(full_text)

        volume_match = re.search(r'(\d{2,4})\s*M3', full_text, re.IGNORECASE)
        unit_price = None
        for pattern in [r'USD\s*\$?\s*(\d{2,4})\s*/?\s*m3', r'Precio[\s\n]+USD\s*\$?\s*(\d{2,4})']:
            price_match = re.search(pattern, full_text, re.IGNORECASE)
            if price_match:
                unit_price = float(price_match.group(1))
                break
        
        if not unit_price:
            for p in re.findall(r'USD\s*\$?\s*(\d{2,4})', full_text, re.IGNORECASE):
                if 50 <= float(p) <= 500:
                    unit_price = float(p)
                    break

        quality_match = re.search(r'COL\s*([AB])', full_text, re.IGNORECASE)
        thickness_match = re.search(r'(\d{2,3})\s*(?:mm|x)', full_text, re.IGNORECASE)
        po_ref_match = re.search(r'(?:ORDEN\s+DE\s+COMPRA|OC|O/C|NRO\.?|N°|Nº)\s*[:\-]?\s*([A-Z]{2,}[A-Z]?(?:[\s\-]*\d{3,5}){1}(?:[\s\-]*\d{1,6}){1})', full_text, re.IGNORECASE)

        return {
            'total_volume_m3': float(volume_match.group(1)) if volume_match else None,
            'unit_price_usd':  unit_price,
            'quality':         f"col_{quality_match.group(1).lower()}" if quality_match else 'col_a',
            'thickness_mm':    float(thickness_match.group(1)) if thickness_match else 45.0,
            'po_ref_fallback': po_ref_match.group(1).strip() if po_ref_match else None,
        } 