# Seguridad del guion de inspección (Parte C) — comando → lectura/escritura → riesgo

**Archivo:** `docs/INSPECCION_REMOTO_SOLO_LECTURA.sh` · **Validación:** `bash -n` OK; todas las sentencias SQL
son `SELECT`; 0 operaciones de escritura.

| # | Comando (resumen) | ¿Lee? | ¿Escribe? | Riesgo | Nota |
|---|---|---|---|---|---|
| 1 | `odoo --version` | Sí | No | Nulo | Imprime el build y sale; no arranca el servicio. |
| 1b | `git -C <addons> rev-parse HEAD` | Sí | No | Nulo | Sólo si el core es un checkout git legible. |
| 2 | `psql -tAc "SELECT … FROM ir_module_module"` | Sí | No | Nulo | Estado/versión de módulos MADENAT. |
| 3 | `psql -tAc "SELECT … WHERE name='madenat_vendor_payment'"` | Sí | No | Nulo | ¿Está instalado? |
| 4 | `psql -tAc "SELECT … FROM ir_ui_view WHERE arch_db LIKE …"` | Sí | No | Nulo | Vistas con `oe_chatter` / `<chatter/>`. |
| 5a | `grep … form_compiler.js` | Sí | No | Nulo | Selector del chatter en el core. |
| 5b | `grep -rl 'oe_chatter' …/mail…/web…` | Sí | No | Nulo | ¿Soporta `div.oe_chatter`? |
| 6 | `grep -oE 'version' <manifest>` (bucle `for`) | Sí | No | Nulo | Versiones en disco de los manifests. |
| 7 | `psql -tAc "SELECT max(write_date) …"` | Sí | No | Nulo | Última actualización de módulos. |
| 8 | `grep -aiE 'OwlError|urlRelation|…' <log> \| tail` | Sí | No | Nulo | Filtrado; no vuelca el log completo. |
| 9 | `psql -tAc "SELECT count(*) FROM res_users …"` | Sí | No | Nulo | **Sólo conteo**; no imprime identidades. |
| — | `date`, `echo`, `head`, `\|\|` | Sí | No | Nulo | Utilidades de presentación. |

**No incluye** (verificado por `grep`): `systemctl stop/start/restart`, `pg_restore`, `pg_dump`,
`UPDATE/INSERT/DELETE/DROP/ALTER/TRUNCATE`, `odoo -u`, `rm/mv/mkdir/touch/chmod`, ni redirecciones de escritura.

**Privacidad:** la salida no contiene correos, contraseñas ni datos de clientes. Antes de pegarla, Mauricio debe
recortar cualquier aviso de `psql` con rutas o nombres. **No** pegar el `odoo.conf` ni credenciales.

**Nota de uso:** el único redireccionamiento del propio guion es `2>/dev/null` (descarta stderr). El `tee` del
ejemplo escribe **en la máquina donde lo ejecuta Mauricio**, no en el servidor.
