"""Archive the completed Codex page/frame inspection without changing measurements."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

root = Path('D:/workspace/be2/SLAM_DelayedCorrection')
generation = root / 'results/runs/delayed-pdfs-447ea1b2efe9'
target = root / 'results/reference/delayed-report-review'
target.mkdir(exist_ok=False)
shutil.copytree(generation / 'inputs', target / 'generation-inputs')
shutil.copy2(generation / 'record.json', target / 'generation-record.json')
shutil.copy2(__file__, target / 'executed-review-export.py')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, obj):
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

pages = []
for language, label in [('en', 'en'), ('zh-CN', 'zh')]:
    name = f'delayed-study.{language}.pdf'
    source = root / 'output/pdf' / name
    if sha(source) != sha(generation / name):
        raise ValueError('Published PDF differs from reviewed generation')
    shutil.copy2(source, target / name)
    count = len(PdfReader(source).pages)
    if count != 3:
        raise ValueError('Unexpected final page count')
    for i in range(1, count + 1):
        image = root / 'tmp/pdfs' / f'delayed-v3-{label}-{i}.png'
        dest = target / f'{label}-page-{i}.png'
        shutil.copy2(image, dest)
        pages.append({'pdf': name, 'page': i, 'render_sha256': sha(dest),
                      'review': 'Codex visually inspected this final Poppler rendering; no clipping, overlap or missing glyphs'})
write(target / 'qa.json', {'reviewer': 'Codex visual inspection', 'human_review': False,
      'renderer': 'Poppler pdftoppm at 100 DPI', 'renderer_font_warnings': ['Symbol', 'ArialUnicode'],
      'note': 'Fonts are embedded; all final pages visually checked despite renderer font lookup warnings.',
      'pages': pages, 'all_passed': True})
record = {'schema_version': 1, 'kind': 'delayed_report_layout_review', 'status': 'executed', 'exit_code': 0,
          'finished_at': datetime.now(timezone.utc).isoformat(), 'summary': {'pages': len(pages),
          'review': 'All six final rendered pages visually inspected by Codex; no independent human review'},
          'artifacts': {p.relative_to(target).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size,
                       'availability': 'portable'} for p in target.rglob('*') if p.is_file()}}
write(target / 'record.json', record)

slots_path = root / 'docs/figures/slots.json'
slots = json.loads(slots_path.read_text(encoding='utf-8'))
new = [
    ('delayed-primary-figure', 'results/reference/delayed-pose/figures/delayed-results.png',
     'results/reference/delayed-pose/record.json', 'figures/delayed-results.png',
     'Frozen room1 primary comparisons: means and seed ranges; AI labels await human review.',
     '冻结 room1 主实验：均值与种子范围；AI 标注待人工复核。'),
    ('delayed-support-figure', 'results/reference/delayed-support-control/figures/support-control.png',
     'results/reference/delayed-support-control/record.json', 'figures/support-control.png',
     'Six separate post-hoc support controls; candidate counts are not false-positive rates.',
     '六个独立事后支持门槛对照；候选数不是假阳性率。')]
for identity, path, source, artifact, en, zh in new:
    if any(s['id'] == identity for s in slots['slots']):
        raise ValueError('Duplicate slot')
    slots['slots'].append({'id': identity, 'path': path, 'stage': 'Delayed correction diagnostic',
                          'status': 'published', 'caption': {'en': en, 'zh': zh},
                          'source_records': [source], 'source_artifact': artifact})
write(slots_path, slots)

video_target = root / 'results/reference/delayed-recording-review'
video_target.mkdir(exist_ok=False)
video_qa = []
for folder in ['delayed-room1-frontend-v1', 'delayed-room1-suite-attempt2', 'delayed-room1-support-followup-v1']:
    source = root / 'tmp/pdfs' / f'{folder}-review.png'
    shutil.copy2(source, video_target / source.name)
    video_qa.append({'recording': folder, 'frames': ['start', 'middle', 'end'],
                     'review': 'Codex visually inspected all three frames; real terminal, startup and completed exit visible'})
write(video_target / 'qa.json', {'recordings': video_qa, 'all_passed': True, 'human_review': False,
                                'source_record_sha256': sha(root / 'results/reference/delayed-recordings/record.json')})
write(video_target / 'record.json', {'schema_version': 1, 'kind': 'delayed_recording_visual_review',
      'status': 'executed', 'exit_code': 0, 'finished_at': datetime.now(timezone.utc).isoformat(),
      'scope': 'Three recordings, start/middle/end inspected; full decoder checks reside in source recording metadata',
      'artifacts': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size, 'availability': 'portable'}
                    for p in video_target.iterdir() if p.is_file()}})
print('Archived six PDF pages, nine recording frames and two hash-bound figure slots')
