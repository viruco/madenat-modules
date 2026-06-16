# -*- coding: utf-8 -*-
import logging
import base64
from odoo import _
from odoo.exceptions import UserError
from .ingestion_gate import Gate0PreUpload, Gate1DocumentReconciliation

_logger = logging.getLogger(__name__)

class LumberReceptionWorkflow:
    """
    ⚙️ MOTOR DE WORKFLOW DESACOPLADO (Fase 4.2)
    Gestiona el pipeline de transiciones de estado y validaciones.
    """
    def __init__(self, env):
        self.env = env

    def run_ingestion_pipeline(self, reception):
        """
        Ejecuta el pipeline atómico de 7 pasos.
        """
        reception.ensure_one()
        guide_id = reception.name or f"Guía {reception.id}"
        
        # 🛡️ ESCUDO ANTI-CRUZAMIENTO
        self._check_file_integrity(reception)
        
        if not reception.pdf_file: raise UserError("❌ PDF Guía de Despacho requerido")
        if not reception.excel_file: raise UserError("❌ Excel Packing List requerido")

        _logger.info("🚀 INICIANDO PIPELINE FASE 2 — %s", guide_id)
        reception._add_log("=" * 80)
        reception._add_log(f"🎯 PROCESAMIENTO INICIADO — Guía: {guide_id}")

        # 1. GATE 0: Validación Pre-Parseo
        self._execute_gate_0(reception)

        try:
            # 2.1 Obtención de Tipo de Cambio
            reception._add_log("💱 Obteniendo tipo de cambio...")
            exchange_rate = reception._get_current_exchange_rate()
            reception._add_log(f"✅ TC: {exchange_rate:.2f} CLP/USD")
            
            parser = self.env['madenat.reception.parser']
            
            # 2.2 Guía PDF
            reception._add_log("📄 1/5 Parseando Guía PDF...")
            try:
                dg_bytes = base64.b64decode(reception.pdf_file)
                dg_data = parser.parse_dispatch_guide(dg_bytes, reception.name)
                reception.manual_entry = False
                reception._add_log("✅ PDF parseado correctamente")
            except Exception as e:
                _logger.warning("Parseo PDF falló → Modo manual: %s", str(e))
                reception._add_log(f"⚠️ PARSEO PDF FALLÓ → MODO MANUAL")
                reception.manual_entry = True
                dg_data = {
                    'guide_no': reception.name or 'S/N',
                    'po_ref': None,
                    'supplier_rut': None, 
                    'total_amount': 0.0,
                    'total_volume_m3': 0.0,
                    'exchange_rate': exchange_rate,
                }
            
            # 2.3 OC PDF (Opcional) y actualización BD
            oc_data = None
            if reception.oc_pdf_file:
                reception._add_log("📄 2/5 Parseando OC PDF...")
                try:
                    oc_bytes = base64.b64decode(reception.oc_pdf_file)
                    oc_data = parser.parse_purchase_order(oc_bytes)
                    reception._add_log("✅ OC PDF parseado")
                    
                    if hasattr(reception, 'purchase_order') and reception.purchase_order and oc_data.get('unit_price_usd'):
                        po_record = self.env['purchase.order'].search([('name', '=', reception.purchase_order)], limit=1)
                        if po_record:
                            po_record.write({'partner_ref': reception.purchase_order})
                            reception._add_log(f"💾 OC actualizada en BD: USD ${oc_data['unit_price_usd']}/m³")
                except Exception as e:
                    _logger.warning("Parseo OC PDF falló: %s", str(e))
                    reception._add_log(f"⚠️ OC PDF ignorado: {str(e)}")

            # 2.4 Excel Packing List y Precios
            reception._add_log("📊 3/5 Parseando Packing List...")
            excel_bytes = base64.b64decode(reception.excel_file)
            pl_data = parser.parse_excel(excel_bytes, ingestion_profile=reception.ingestion_profile)
            
            for msg in pl_data.get('logs', []): reception._add_log(msg)
            for warn in pl_data.get('warnings', []): 
                reception._add_log(warn)
                _logger.warning(warn)

            self._inject_unit_prices(reception, pl_data, oc_data)
            reception._add_log(f"✅ Packing List: {len(pl_data.get('lines', []))} líneas (Motor Desacoplado v2)")

            # 2.5 🛡️ VALIDACIÓN TEMPRANA DE DUPLICADOS (2026-06-11)
            # Se ejecuta ANTES de Gate 1, cabecera, staging y creación de lotes.
            # Si la guía ya existe, bloquea el flujo completo con UserError.
            guide_no_for_check = dg_data.get('guide_no') or pl_data.get('guide_no') or ''
            if guide_no_for_check:
                reception._add_log("🔍 Verificando duplicados antes de continuar...")
                _logger.info(
                    "🔍 PIPELINE: validación temprana de duplicados guía=%s reception=%s",
                    guide_no_for_check, reception.name
                )
                parser._check_guide_duplicate(guide_no_for_check, exclude_id=reception.id)
                reception._add_log("✅ Validación de duplicados superada — guía no existe en el sistema")
            else:
                _logger.warning(
                    "⚠️ PIPELINE: no se detectó número de guía en PDF ni Excel — "
                    "se omite validación de duplicados. reception=%s", reception.name
                )

            # 3. GATE 1: Reconciliación Documental
            self._execute_gate_1(reception, dg_data, pl_data, exchange_rate)

            # 4. Cabecera y TC (Blindaje Financiero)
            self._update_header_data(reception, dg_data, pl_data, exchange_rate)

            # 5. Llenado de Staging (SIEMPRE, incluso sin OC vinculada)
            reception._add_log("🏷️ 4/5 Generando staging...")
            if reception.reception_line_ids:
                reception.reception_line_ids.with_context(force_delete=True).unlink()
            
            reception._fill_staging_table(pl_data)
            reception._add_log(f"✅ STAGING: {len(reception.reception_line_ids)} líneas")
            
            reception._add_log("💰 Asignando costos...")
            reception._assign_costs_to_lots(pl_data)

            # 6. Resolución de Orden de Compra y Duplicados
            reception._add_log("🔍 5/5 Resolviendo Orden de Compra...")
            po, supplier = reception._find_or_create_po_intelligent(dg_data, oc_data)
            
            if not po and not reception.manual_po_name:
                reception._add_log("⏳ Sin OC → Estado 'pending_link'")
                reception.write({'state': 'pending_link'})
                return True

            reception._add_log(f"✅ OC: {po.name if po else reception.manual_po_name}")
            
            if po:
                try:
                    reception._check_duplicate_guide_processing(po)
                    reception._add_log("✅ Sin duplicados detectados")
                except Exception as e:
                    _logger.warning("Duplicados: %s", str(e))
                    reception._add_log(f"⚠️ DUPLICADOS: {str(e)}")

            # 7. TRANSICIÓN FINAL
            reception.write({'state': 'verified'})
            reception._add_log("=" * 80)
            reception._add_log("🏁 PIPELINE COMPLETADO — LISTO PARA VALIDACIÓN HUMANA")
            reception._add_log(f"📈 RESUMEN: {len(reception.reception_line_ids)} líneas | {reception.physical_volume_m3:.3f}m³")
            
            _logger.info("🏁 FASE 2 COMPLETA — Guía %s verified", guide_id)
            return True

        except UserError:
            reception.write({'state': 'error'})
            raise
        except Exception as e:
            reception.write({'state': 'error'})
            error_msg = f"💥 ERROR CRÍTICO: {str(e)[:200]}"
            reception._add_log(error_msg)
            _logger.error("PIPELINE FASE 2 FALLÓ [%s]: %s", guide_id, str(e), exc_info=True)
            raise UserError(f"Procesamiento falló: {error_msg}")

    # ========================== MÉTODOS DE SOPORTE ==========================

    def _check_file_integrity(self, reception):
        nombres = f"{reception.pdf_filename or ''} {reception.excel_filename or ''}".lower()
        palabras_proceso = ['cepillado', 'servicio', 'proceso', 'maquila']
        if any(p in nombres for p in palabras_proceso):
            raise UserError("⛔ El documento parece ser un Servicio de Proceso. Use el menú correspondiente.")

    def _execute_gate_0(self, reception):
        gate0 = Gate0PreUpload()
        r_excel = gate0.validate(reception.excel_filename or 'packing_list.xlsx', base64.b64decode(reception.excel_file), 'excel')
        if not r_excel.is_valid:
            reception._add_log(f"❌ GATE 0 - EXCEL: {r_excel.audit_summary}")
            raise UserError(r_excel.user_message)
            
        r_pdf = gate0.validate(reception.pdf_filename or 'guia.pdf', base64.b64decode(reception.pdf_file), 'pdf')
        if not r_pdf.is_valid:
            reception._add_log(f"❌ GATE 0 - PDF: {r_pdf.audit_summary}")
            raise UserError(r_pdf.user_message)
            
        reception._add_log("✅ GATE 0: Archivos validados")

    def _execute_gate_1(self, reception, dg_data, pl_data, exchange_rate):
        excel_ctx = {
            "nro_guia": str(pl_data.get("guide_no") or dg_data.get("guide_no") or "").strip(),
            "total_vol_m3": reception._safe_float(pl_data.get("total_volume_m3", 0)),
            "tipo_cambio": reception._safe_float(pl_data.get("exchange_rate", exchange_rate)),
        }
        pdf_ctx = {
            "nro_guia": str(dg_data.get("guide_no") or "").strip(),
            "total_vol_m3": reception._safe_float(dg_data.get("total_volume_m3", 0)),
            "tipo_cambio": reception._safe_float(dg_data.get("exchange_rate", 0)),
        }
        gate1 = Gate1DocumentReconciliation(self.env)
        res = gate1.validate(excel_ctx, pdf_ctx, reception.purchase_id.id if reception.purchase_id else None)
        
        if not res.is_valid:
            reception.write({'state': 'error'})
            reception._add_log(f"❌ GATE 1 BLOQUEANTE: {res.audit_summary}")
            raise UserError(res.user_message)
            
        if res.has_warnings:
            reception._add_log(f"⚠️ GATE 1 ADVERTENCIAS:\n{res.user_message}")
            _logger.warning("GATE 1 warnings: %s", res.audit_summary)
            
        _logger.info("✅ GATE 1 OK — %s", res.audit_summary)

    def _inject_unit_prices(self, reception, pl_data, oc_data):
        unit_price_usd = 0.0
        if oc_data and isinstance(oc_data, dict):
            unit_price_usd = float(oc_data.get('unit_price_usd', 0.0))
        elif hasattr(reception, 'purchase_order') and reception.purchase_order:
            po_record = self.env['purchase.order'].search([('name', '=', reception.purchase_order)], limit=1)
            if po_record and po_record.unit_price_usd > 0:
                unit_price_usd = po_record.unit_price_usd
        
        if unit_price_usd > 0:
            for line in pl_data.get('lines', []):
                line['unit_price_usd'] = unit_price_usd

    def _update_header_data(self, reception, dg_data, pl_data, exchange_rate):
        commercial_vol = reception.commercial_volume_m3 or reception._safe_float(dg_data.get('total_volume_m3', 0))
        physical_vol = reception._safe_float(pl_data.get('total_volume_m3', 0))
        net_total = reception._safe_float(dg_data.get('net_total', 0))
        
        header_vals = {
            'name': dg_data.get('guide_no') or reception.name,
            'guia_numero': dg_data.get('guide_no') or reception.name,
            'guia_fecha': dg_data.get('guide_date'),
            'commercial_volume_m3': commercial_vol,
            'physical_volume_m3': physical_vol,
            'total_amount_clp': net_total,
        }
        
        tc_pdf = dg_data.get('exchange_rate', 0.0)
        if tc_pdf > 0:
            header_vals['exchange_rate'] = tc_pdf
            reception._add_log(f"💱 Tipo de Cambio extraído del PDF: {tc_pdf}")
        elif exchange_rate > 0:
            header_vals['exchange_rate'] = exchange_rate
            reception._add_log(f"💱 TC no hallado en PDF. Usando tasa oficial Odoo: {exchange_rate}")
        else:
            raise UserError("⛔ Bloqueo Financiero: No se detectó Tipo de Cambio.")
            
        reception.write(header_vals)
        reception._add_log(f"📊 CABECERA: {commercial_vol:.3f}m³ | {net_total:,.0f} CLP")