/** @odoo-module **/

import { registry } from "@web/core/registry";

/**
 * Client action MADENAT: ejecuta un action dict interno reemplazando el
 * controller actual del action stack, evitando acumular breadcrumbs en el
 * ciclo Ingreso Global → Abrir origen → Volver a Ingreso Global.
 *
 * Sin patch global, sin listeners globales, sin navegación manual.
 */
async function replaceCurrentAction(env, action) {
    const params = action.params || {};
    const actionToExecute = params.action_to_execute;
    if (!actionToExecute || typeof actionToExecute !== "object") {
        throw new Error(
            "replace_current_action: falta un action dict válido en params.action_to_execute"
        );
    }
    // Call once: reemplaza el controller actual sin acumular.
    await env.services.action.doAction(actionToExecute, {
        stackPosition: "replaceCurrentAction",
    });
}

registry
    .category("actions")
    .add("madenat_lumber_intake.replace_current_action", replaceCurrentAction);