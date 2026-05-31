from odoo import models, api
import datetime
import logging

_logger = logging.getLogger(__name__)

class LumberCostReport(models.AbstractModel):
    _name = 'report.madenat_lumber_core.lumber_cost_report'
    _description = 'Reporte de Costos por Lote'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Método principal para generar valores del reporte
        """
        _logger.info("🎯🎯🎯 INICIANDO REPORTE DE COSTOS 🎯🎯🎯")
        _logger.info("📋 docids recibidos: %s", docids)
        
        # Obtener los lotes
        docs = self.env['stock.lot'].browse(docids)
        _logger.info("📦 Lotes encontrados: %s", len(docs))
        
        # DEBUG: Verificar el primer lote
        if docs:
            sample = docs[0]
            _logger.info("🔍 DEBUG Primer lote %s:", sample.name)
            _logger.info("   - ID: %s", sample.id)
            _logger.info("   - Producto: %s", sample.product_id.display_name)
            _logger.info("   - volumen_m3: %s", getattr(sample, 'volumen_m3', 'NO EXISTE'))
            _logger.info("   - wood_cost_usd: %s", getattr(sample, 'wood_cost_usd', 'NO EXISTE'))
            _logger.info("   - purchase_cost_usd: %s", getattr(sample, 'purchase_cost_usd', 'NO EXISTE'))
            _logger.info("   - Tiene cost_line_ids: %s", bool(sample.cost_line_ids))
            if sample.cost_line_ids:
                _logger.info("   - Líneas de costo: %s", len(sample.cost_line_ids))
                for line in sample.cost_line_ids:
                    _logger.info("     * %s: %s USD (Tipo: %s)", line.name, line.amount_usd, line.cost_type)
        
        # Inicializar estructura de costos
        cost_summary = {}
        total_general = 0.0
        volumen_total = 0.0
        
        for i, lot in enumerate(docs):
            _logger.info("📝 Procesando lote %s/%s: %s", i+1, len(docs), lot.name)
            
            # OBTENER COSTOS con debug
            costo_madera = self._get_costo_madera(lot)
            costo_proceso = self._get_costo_proceso(lot)
            costo_logistica = self._get_costo_logistica(lot)
            volumen_m3 = self._get_volumen_m3(lot)
            
            _logger.info("   💰 Costos obtenidos - Madera: %s, Proceso: %s, Logística: %s, Volumen: %s", 
                        costo_madera, costo_proceso, costo_logistica, volumen_m3)
            
            # Asegurar que son números
            costo_madera = self._safe_float(costo_madera)
            costo_proceso = self._safe_float(costo_proceso)
            costo_logistica = self._safe_float(costo_logistica)
            volumen_m3 = self._safe_float(volumen_m3)
            
            _logger.info("   🔢 Costos convertidos - Madera: %s, Proceso: %s, Logística: %s, Volumen: %s", 
                        costo_madera, costo_proceso, costo_logistica, volumen_m3)
            
            # Calcular totales
            total_cost = costo_madera + costo_proceso + costo_logistica
            cost_per_m3 = total_cost / volumen_m3 if volumen_m3 > 0 else 0.0
            
            # Acumular para totales generales
            total_general += total_cost
            volumen_total += volumen_m3
            
            _logger.info("   📊 Totales - Costo: %s, Costo/m³: %s, Acumulado: %s", 
                        total_cost, cost_per_m3, total_general)
            
            # Guardar en resumen
            cost_summary[lot.id] = {
                'costo_madera': costo_madera,
                'costo_proceso': costo_proceso,
                'costo_logistica': costo_logistica,
                'total_cost_usd': total_cost,
                'cost_per_m3': cost_per_m3,
                'volumen_m3': volumen_m3,
            }
        
        # DEBUG FINAL
        _logger.info("🎯 RESUMEN FINAL:")
        _logger.info("   - cost_summary entries: %s", len(cost_summary))
        _logger.info("   - total_general: %s (type: %s)", total_general, type(total_general))
        _logger.info("   - volumen_total: %s (type: %s)", volumen_total, type(volumen_total))
        
        # VALORES FINALES GARANTIZADOS
        final_total = float(total_general) if total_general is not None else 0.0
        final_volumen = float(volumen_total) if volumen_total is not None else 0.0
        
        _logger.info("🎯 VALORES FINALES:")
        _logger.info("   - final_total: %s (type: %s)", final_total, type(final_total))
        _logger.info("   - final_volumen: %s (type: %s)", final_volumen, type(final_volumen))
        
        return {
            'doc_ids': docids,
            'doc_model': 'stock.lot',
            'docs': docs,
            'cost_summary': cost_summary,
            'total_general': final_total,    # ✅ NUNCA None
            'volumen_total': final_volumen,  # ✅ NUNCA None
            'datetime': datetime,
        }
    
    def _safe_float(self, value):
        """Convertir cualquier valor a float de forma segura"""
        _logger.debug("   🔄 Convirtiendo a float: %s (type: %s)", value, type(value))
        if value is None:
            _logger.debug("   ⚠️  Valor None, retornando 0.0")
            return 0.0
        try:
            result = float(value)
            _logger.debug("   ✅ Convertido: %s", result)
            return result
        except (TypeError, ValueError) as e:
            _logger.debug("   ❌ Error convirtiendo %s: %s, retornando 0.0", value, str(e))
            return 0.0
    
    def _get_costo_madera(self, lot):
        """✅ REGLA DE ORO: Obtener costo de madera desde FUENTE DE VERDAD"""
        try:
            _logger.debug("   🔍 Buscando costo madera REAL para %s", lot.name)
            
            # ✅ PRIORIDAD 1: Desde líneas de costo (FUENTE DE VERDAD)
            if hasattr(lot, 'cost_line_ids') and lot.cost_line_ids:
                wood_lines = lot.cost_line_ids.filtered(lambda l: l.cost_type == 'wood')
                wood_cost = sum(wood_lines.mapped('amount_usd'))
                
                if wood_cost > 0:
                    _logger.debug("   ✅ Costo madera REAL desde líneas: %s", wood_cost)
                    return wood_cost
            
            # ✅ PRIORIDAD 2: Desde campos legacy (para compatibilidad)
            if hasattr(lot, 'wood_cost_usd') and lot.wood_cost_usd:
                _logger.debug("   ✅ Costo madera desde campo legacy: %s", lot.wood_cost_usd)
                return lot.wood_cost_usd
                
            # ✅ PRIORIDAD 3: Desde purchase_cost_usd (compatibilidad)
            if hasattr(lot, 'purchase_cost_usd') and lot.purchase_cost_usd:
                _logger.debug("   ✅ Costo madera desde purchase_cost: %s", lot.purchase_cost_usd)
                return lot.purchase_cost_usd
            
            _logger.debug("   ⚠️ No se encontraron costos de madera")
            return 0.0
            
        except Exception as e:
            _logger.error("❌ Error obteniendo costo madera para %s: %s", lot.name, str(e))
            return 0.0
    
    def _get_costo_proceso(self, lot):
        """✅ REGLA DE ORO: Obtener costo de proceso desde FUENTE DE VERDAD"""
        try:
            _logger.debug("   🔍 Buscando costo proceso para %s", lot.name)
            
            # ✅ PRIORIDAD 1: Desde líneas de costo (FUENTE DE VERDAD)
            if hasattr(lot, 'cost_line_ids') and lot.cost_line_ids:
                process_lines = lot.cost_line_ids.filtered(
                    lambda l: l.cost_type in ['processing', 'process']
                )
                process_cost = sum(process_lines.mapped('amount_usd'))
                
                if process_cost > 0:
                    _logger.debug("   ✅ Costo proceso REAL desde líneas: %s", process_cost)
                    return process_cost
            
            # ✅ MANTENER funcionalidad existente
            _logger.debug("   ℹ️  Sin costo de proceso configurado")
            return 0.0
            
        except Exception as e:
            _logger.error("❌ Error obteniendo costo proceso para %s: %s", lot.name, str(e))
            return 0.0
    
    def _get_costo_logistica(self, lot):
        """✅ REGLA DE ORO: Obtener costo de logística desde FUENTE DE VERDAD"""
        try:
            _logger.debug("   🔍 Buscando costo logística para %s", lot.name)
            
            # ✅ PRIORIDAD 1: Desde líneas de costo (FUENTE DE VERDAD)
            if hasattr(lot, 'cost_line_ids') and lot.cost_line_ids:
                logistic_lines = lot.cost_line_ids.filtered(
                    lambda l: l.cost_type in ['logistic', 'logistics', 'internal_freight', 'port_cost']
                )
                logistic_cost = sum(logistic_lines.mapped('amount_usd'))
                
                if logistic_cost > 0:
                    _logger.debug("   ✅ Costo logística REAL desde líneas: %s", logistic_cost)
                    return logistic_cost
            
            # ✅ MANTENER funcionalidad existente
            _logger.debug("   ℹ️  Sin costo de logística configurado")
            return 0.0
            
        except Exception as e:
            _logger.error("❌ Error obteniendo costo logística para %s: %s", lot.name, str(e))
            return 0.0
    
    def _get_volumen_m3(self, lot):
        """✅ REGLA DE ORO: Obtener volumen real del lote"""
        try:
            _logger.debug("   🔍 Buscando volumen para %s", lot.name)
            
            # ✅ PRIORIDAD 1: Campo volumen_m3 (principal)
            if hasattr(lot, 'volumen_m3') and lot.volumen_m3:
                _logger.debug("   ✅ Encontrado volumen_m3: %s", lot.volumen_m3)
                return lot.volumen_m3
            
            # ✅ PRIORIDAD 2: volume_purchase_m3 (alternativo)
            if hasattr(lot, 'volume_purchase_m3') and lot.volume_purchase_m3:
                _logger.debug("   ✅ Encontrado volume_purchase_m3: %s", lot.volume_purchase_m3)
                return lot.volume_purchase_m3
                
            # ✅ PRIORIDAD 3: vol_shipment_m3 (alternativo)
            if hasattr(lot, 'vol_shipment_m3') and lot.vol_shipment_m3:
                _logger.debug("   ✅ Encontrado vol_shipment_m3: %s", lot.vol_shipment_m3)
                return lot.vol_shipment_m3
            
            _logger.debug("   ⚠️  No se encontró volumen, usando 1.0")
            return 1.0
            
        except Exception as e:
            _logger.error("❌ Error obteniendo volumen para %s: %s", lot.name, str(e))
            return 1.0