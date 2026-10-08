"""Optional ConceptGraphs provider adapter, with an immutable USD 1 task ceiling.

Uses a full-context worst-case reservation rather than an unverified tokenizer.
No retries; uncertain failures retain their reservation. Linux flock serializes
all callers sharing the task ledger. Original GPT-4 prompts are not edited here.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
from urllib.request import Request, urlopen
from datetime import datetime, timezone


class BudgetExceeded(RuntimeError):
    pass


def create(*, messages, model=None, timeout=120, **kwargs):
    if kwargs:
        raise ValueError('Unsupported author request options: ' + ', '.join(sorted(kwargs)))
    key = os.environ['DEEPSEEK_API_KEY']
    ledger_path = Path(os.environ['DEEPSEEK_BUDGET_LEDGER']).resolve()
    config = json.loads((Path(__file__).resolve().parents[1] / 'config/deepseek-budget.json').read_text())
    body = {'model': config['model'], 'messages': messages, 'stream': False,
            'max_tokens': config['max_output_tokens'], 'thinking': {'type': 'disabled'}}
    payload = json.dumps(body, ensure_ascii=False).encode('utf-8')
    reserve = (Decimal(config['input_reservation_tokens']) * Decimal(config['peak_input_usd_per_million'])
               + Decimal(config['max_output_tokens']) * Decimal(config['peak_output_usd_per_million'])) / Decimal(1000000)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
            'cap_usd': '1.00', 'provider': 'DeepSeek', 'reserved_usd': '0', 'calls': []}
        # A ledger/config may lower the cap, but cannot raise the human-approved ceiling.
        cap = min(Decimal('1.00'), Decimal(config['task_cap_usd']), Decimal(ledger['cap_usd']))
        total = Decimal(ledger['reserved_usd']) + reserve
        if total > cap:
            raise BudgetExceeded(f'Request refused before HTTP: reserved USD {total} would exceed USD {cap}')
        index = len(ledger['calls'])
        entry = {'index': index, 'at': datetime.now(timezone.utc).isoformat(),
                 'request_sha256': hashlib.sha256(payload).hexdigest(), 'model': config['model'],
                 'reserved_usd': str(reserve), 'status': 'reserved'}
        ledger['calls'].append(entry)
        ledger['reserved_usd'] = str(total)
        def save():
            temp = ledger_path.with_suffix('.tmp')
            temp.write_text(json.dumps(ledger, indent=2) + '\n')
            temp.replace(ledger_path)
        save()  # Persist before any potentially billable network operation.
        request = Request(config['endpoint'], data=payload, headers={
            'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read()
            result = json.loads(raw)
            entry.update(status='returned', usage=result.get('usage'), response_sha256=hashlib.sha256(raw).hexdigest())
            if not result.get('usage'):
                raise RuntimeError('Provider omitted usage; reservation retained')
            usage = result['usage']
            # An upper bound at peak cache-miss rates, not an invoice claim.
            entry['usage_cost_upper_usd'] = str((Decimal(usage['prompt_tokens']) * Decimal(config['peak_input_usd_per_million'])
                + Decimal(usage['completion_tokens']) * Decimal(config['peak_output_usd_per_million'])) / Decimal(1000000))
            result_path = ledger_path.parent / f'deepseek-response-{index:04d}.json'
            result_path.write_bytes(raw)  # Local output may contain scene captions; never a key.
            save()
            return result
        except Exception as exc:
            entry.update(status='failed_or_uncertain', error_type=type(exc).__name__)
            save()  # Do not print provider headers, request credentials or error bodies.
            raise RuntimeError(f'DeepSeek request {index} failed; reservation retained ({type(exc).__name__})') from None
