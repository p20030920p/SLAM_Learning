from pathlib import Path
import json
import hashlib
import shutil

root=Path(r'D:\workspace\be2\submission-review')
evidence=root/'results/reference/visual-review'
summary=json.loads((evidence/'summary.json').read_text(encoding='utf-8'))
for item in summary:
    item['human_visual_review']='AI visual inspection completed; no independent human review claimed'
    item['visual_review_note']='All 21 stage frames inspected individually or in contact sheets: graphical cloud visible, stage labels legible, mapping snapshots distinguished from final queries; independent human review remains available.'
with (evidence/'summary.json').open('w',encoding='utf-8',newline='\n') as f:json.dump(summary,f,indent=2);f.write('\n')
shutil.copy2(Path(__file__).with_name('make_visual_contact.py'),evidence/'make_visual_contact.source.py')
shutil.copy2(Path(__file__),evidence/'finalize_visual_evidence.source.py')
record=json.loads((evidence/'record.json').read_text(encoding='utf-8'))
record['summary']=summary
record['visual_review']={'reviewer':'AI visual inspection, not independent human validation','stages':21,'result':'accepted for measured-output graphical inspection','contact_sheets':['contact-1.png','contact-2.png']}
record['artifacts']={p.relative_to(evidence).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'availability':'portable'} for p in sorted(evidence.rglob('*')) if p.is_file() and p.name!='record.json'}
with (evidence/'record.json').open('w',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
index=Path(r'D:\workspace\be2\SLAM_Recordings\2026-10-08\rviz-review-v3\VIDEO_INDEX.md')
text='# 实际 RViz 图形窗口录制\n\n保存的实测输出查看，不是实时算法推理；实际 RViz 画面、单调时钟 5 fps 抓屏。原片完整解码，21 个阶段图像由 AI 视觉检查；未声称独立人工审核。\n\n| 方法 | 时长 | 视频 | 展示 |\n| --- | ---: | --- | --- |\n'
descriptions={'dufomap':'原始／移除／保留，同一抽样点','beautymap':'原始／移除／保留，同一抽样点','conceptgraphs':'5 个原生历史快照 + 4 项最终查询','hovsg':'最终分段地图 + 4 项查询'}
for item in summary:
    m=item['method']
    text+=f"| {m} | {item['duration_seconds']} s | [MP4]({m}/capture/full-session.mp4) | {descriptions[m]} |\n"
text+='\n每个目录保留 data/manifest.json、源脚本、来源文件哈希、review.rviz；capture/ 保留命令、退出码、终端与录制时序。v1／v2 失败和调试片未列入此最终索引。\n'
with index.open('w',encoding='utf-8',newline='\n') as f:f.write(text)
private=Path(r'D:\workspace\be2\SLAM_Private\2026-10-08\README.zh-CN.md')
with private.open('w',encoding='utf-8',newline='\n') as f:f.write('# 个人材料索引\n\n不上传主分支。\n\n- [手动复现与录制](MANUAL_RECORDING.zh-CN.md)\n- [居家采集步骤](HOME_RUNBOOK.zh-CN.md)\n- [自己补充研究判断](RESEARCH_WRITING.zh-CN.md)\n- original-docs/：整理前的完整手册\n\n本地分支 local/full-notes-20261008 保留整理前 Git 快照；WSL 保留 stash 未动。\n')
print('Finalized visual review evidence and local indexes')
