# EVIDENCIA — Respaldo (Fase B)

## Ubicación protegida

`/home/viruco/dev-stack/odoo/odoo-18-ce/backups/FASE_B_20261007_153214/` (permisos `700`).

> Contiene material **sensible** (dump de BD, `odoo.conf` con credenciales). NO se
> incluye en este paquete documental. Ubicación restringida al usuario del proyecto.

## Artefactos y checksums (SHA-256)

| Artefacto | Bytes | SHA-256 |
|---|---|---|
| `madenat_test.dump` | 11 355 542 | `7a683ade58d92cfc3f4151d0d108b11e3326a320353791c02050562337cd6266` |
| `filestore_madenat_test.tar.gz` | 21 226 420 | `b565036e0215ed9577bf23a2d31178e4c72204d3fa0671f293675e37be0249a9` |
| `custom_addons_worktree.tar.gz` | 26 169 455 | `6c684c8387b74648c047944ceb74fd6a865134ad0981c6ffa17463f2b6e96ec0` |
| `custom_addons_history.bundle` | 3 117 807 | `5f693977742e124a76614fdc63f50991797e62db163771753dc11f84f12861cf` |
| `config/odoo.conf` | 517 | `79b3847461a0b0e6db5fde2c55d1eb798e28ed938d236b2df2ba316101885235` |
| `docker-compose.yml` | 7 552 | `96ef56cdbb8d6e40b5dc5b00c1413c3381d47c634664d9d8592b9998baf91efa` |
| `Dockerfile` | 730 | `27f87e064e8acf53d2e3af3d8e088ea47d1292065f99a693eb43412d04d0ac65` |
| `git_status_before.txt` | 2 271 | `a1d7fa123c47a2c9d61d650f93bc328ee3d83abda71c85488bc51bfae1bf3318` |
| `git_status_before_full.txt` | 3 001 | `a74d927b046202f5f1de4aa65c0a7917635d1f4eb77cc96cf27c1677aaddb742` |
| `git_stash_list.txt` (vacío) | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

Listado completo en `backups/FASE_B_20261007_153214/SHA256SUMS.txt`.

## Cobertura del respaldo de código (requisito de la autorización)

- **Árbol de trabajo completo** (modificados + no rastreados + `.git`): `custom_addons_worktree.tar.gz`
  (4 555 entradas; `gzip -t` OK).
- **Historial Git**: `custom_addons_history.bundle` (`git bundle verify` OK → "records a complete history").
- **No** se usó `git bundle` como único respaldo (hay además la copia del árbol completo).
- **No** se usó `stash`, `reset`, `checkout` ni `commit`. Cambios locales preexistentes preservados.

## Método de captura

- **Ventana sin escritores primero**: `odoo18_app` detenido; único backend cliente sobre
  `madenat_test` era la sesión `psql` administrativa propia.
- **Base**: `pg_dump -U odoo -Fc madenat_test` (formato CUSTOM, extensión `.dump`).
- **Filestore**: leído del volumen `odoo-18-ce_odoo-web-data` mediante un **contenedor
  efímero de solo lectura** (`docker run … -v …:/data:ro … tar`), **sin** `docker exec`
  sobre `odoo18_app` (estaba detenido) y **sin arrancar** el servicio para copiarlo.
- **Código/config**: `tar` del árbol + `git bundle` + copia de `odoo.conf`, `docker-compose.yml`, `Dockerfile`.

## Verificaciones ejecutadas

| Artefacto | Verificación | Resultado |
|---|---|---|
| `madenat_test.dump` | `pg_restore --list` | OK · **13 325** entradas TOC |
| `madenat_test.dump` | cabecera | Format CUSTOM · DB 15.19 |
| `filestore_madenat_test.tar.gz` | `gzip -t` | OK |
| `filestore_madenat_test.tar.gz` | conteo | 208 archivos / 513 dirs (== volumen) |
| `filestore_madenat_test.tar.gz` | agregado sha256 (rutas relativas) | `56d36f951989240c27d2c23c66e323887acb9b5fbf7ed12dabdb7a8afcf26a7e` |
| **volumen filestore** | mismo agregado sha256 | `56d36f951989240c27d2c23c66e323887acb9b5fbf7ed12dabdb7a8afcf26a7e` (**idéntico**) |
| `custom_addons_worktree.tar.gz` | `gzip -t` | OK |
| `custom_addons_history.bundle` | `git bundle verify` | OK (historial completo) |

## Declaración expresa

**NO se realizó una restauración de prueba.** La verificación del dump se limita a la
lectura de su índice (`pg_restore --list`) y a la comprobación de formato; eso **no**
equivale a una restauración probada. El filestore sí fue verificado por igualdad de
contenido (agregado de hashes) entre el volumen y el tar.
