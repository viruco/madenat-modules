#!/usr/bin/env python3
"""Find _create_lots_from_packing in lumber_reception.py"""
import subprocess, os

env = {k: v for k, v in os.environ.items() if not k.startswith('SSH_')}
for k in ['SSH_AGENT_PID','SSH_AUTH_SOCK','SSH_ASKPASS','GIT_SSH','GIT_SSH_COMMAND']:
    env.pop(k, None)

result = subprocess.run(
    ['grep', '-n', '_create_lots_from_packing',
     '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/lumber_reception.py'],
    capture_output=True, text=True, timeout=10
)
with open('/home/viruco/dev-stack/odoo/odoo-18-ce/_check_result.txt', 'w') as f:
    f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\nRC: {result.returncode}\n")

# Also grep for guia_processing_id in madenat_guia_processing.py (lot creation, lines with =)
result2 = subprocess.run(
    ['grep', '-n', 'guia_processing_id|stock\.lot.*create|_create_lot|action_confirm|create.*vals|lot_vals',
     '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/madenat_guia_processing.py'],
    capture_output=True, text=True, timeout=10
)
with open('/home/viruco/dev-stack/odoo/odoo-18-ce/_check_result2.txt', 'w') as f:
    f.write(f"STDOUT:\n{result2.stdout}\n\nSTDERR:\n{result2.stderr}\n\nRC: {result2.returncode}\n")

# Also check: what does reception_service write?
result3 = subprocess.run(
    ['grep', '-n', 'lumber_reception_id\|reception_id', 
     '/home/viruco/dev-stack/odoo/odoo-18-ce/custom_addons/madenat_lumber_core/models/reception_service.py'],
    capture_output=True, text=True, timeout=10
)
with open('/home/viruco/dev-stack/odoo/odoo-18-ce/_check_result3.txt', 'w') as f:
    f.write(f"STDOUT:\n{result3.stdout}\n\nSTDERR:\n{result3.stderr}\n\nRC: {result3.returncode}\n")

print("Done. Check _check_result.txt, _check_result2.txt, _check_result3.txt")