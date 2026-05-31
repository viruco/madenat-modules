# Guía de Producción / Validación Final

**Versión documental:** 6.0.0  
**Fecha:** 2026-05-13  
**Estado:** NO LISTO PARA PRODUCCIÓN

---

## 1. Motivo

El módulo no debe marcarse como listo para producción mientras exista error de instalación por `Wrong @depends`.

---

## 2. Secuencia correcta antes de producción

1. Corregir compute de largo.
2. Actualizar módulo sin error.
3. Ejecutar pruebas base.
4. Ejecutar pruebas nuevas de largo.
5. Revisar warnings y constraints.
6. Solo entonces preparar deploy.

---

## 3. Comandos de referencia

### Update de prueba
```bash
docker exec -it odoo18_app bash -lc "
odoo -u madenat_lumber_core -d madenattest \
--db_host=db --db_user=odoo --db_password=odoo \
--xmlrpc-port=8072 --test-enable --stop-after-init \
--log-level=test
"
```

### Búsqueda de naming roto
```bash
grep -RniE "lengthinputraw|length_input_raw|lengthuom|length_uom|_compute_lengthm" models wizard tests views
```

---

## 4. Regla de deploy

Sin instalación limpia, no hay deploy.  
Sin T29–T32 validadas, no hay cierre del feature de largo.
