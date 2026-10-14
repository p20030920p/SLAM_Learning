param(
  [ValidateSet('en','zh-CN')][string]$Language='en',
  [ValidateSet('plan','canvas','platform','observations','slam','recovery','flow','check','finalize')][string]$Region='plan',
  [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
  [string]$PresentationRoot='F:\be2演讲\ppt',
  [switch]$Resume,
  [switch]$RefreshPictures,
  [switch]$ApplyPlanGeometry
)
$ErrorActionPreference='Stop'
$build=Join-Path $RepoRoot '.cache\direction-v2'
$assets=Join-Path $RepoRoot 'docs\assets\direction'
New-Item -ItemType Directory -Path $build -Force | Out-Null
$reference='D:\workspace\semantic\output\ITMO_Thesis_Proposal_Simple_Talk_Illustrated.pptx'
$palette=@{purple='#9307FE';white='#FFFFFF';ink='#171717';grey='#545454';green='#17664B';lavender='#F7F1FD'}
$words=@{
  en=@{
    title='Robust localization and SLAM'; subtitle='Dynamic environments and localization self-recovery';
    headings=@('01  Robot platform','02  Observations','03  Pose and map','04  Open question');
    chassis='Physical omnidirectional base';sensors='2D LiDAR + depth camera';scan2='Gazebo: 2D laser scan';scan3='Gazebo: 3D laser scan';
    pose='Pose estimation';hypotheses='Pose hypotheses (schematic)';map='Map estimation';given='Mapping A: provided poses';corridor='Gazebo: corridor degradation';
    steps=@('1  Detect tracking loss','2  Diagnose the cause','3  Recover the pose','4  Confirm over time');
    process=@("Omnidirectional base`n2D + independent 3D LiDAR", "Laser scans`nand motion input", "Joint estimation`nof pose and map", "After tracking loss:`nrecover and confirm");
    question='Candidate question: avoid false convergence when useful geometry returns';
    scope='Physical photos. Gazebo scans, provided-pose 3D map and corridor. Physical tests pending.'
  };
  'zh-CN'=@{
    title='动态环境中的鲁棒定位与 SLAM'; subtitle='同时估计位姿与地图，研究定位失效后的持续恢复';
    headings=@('01  机器人平台','02  传感器观测','03  位姿与地图','04  开放问题');
    chassis='实体三轮全向底盘';sensors='二维激光 + 深度相机';scan2='Gazebo：二维激光扫描';scan3='Gazebo：三维激光扫描';
    pose='位姿估计';hypotheses='位姿假设（示意）';map='地图估计';given='建图 A：使用给定位姿';corridor='Gazebo：走廊退化场景';
    steps=@('1  检测定位失效','2  诊断失效原因','3  恢复位姿估计','4  确认持续恢复');
    process=@("三轮全向底盘`n二维 + 独立三维激光", "激光扫描`n与运动输入", "联合估计`n位姿与地图", "定位失效后`n恢复并持续确认");
    question='候选问题：观测重新充分后，如何避免错误收敛并确认持续恢复？';
    scope='实体照片；Gazebo 扫描、给定位姿三维地图与走廊。实体机器人测试待测。'
  }
}

function Make-Plan([string]$lang) {
  $w=$words[$lang]
  $objects=[Collections.Generic.List[object]]::new()
  function T($name,$region,$text,$x,$y,$width,$height,$size,$color,$bold=$false,$align='left') {
    $objects.Add(@{kind='text';name=$name;region=$region;text=$text;x=$x;y=$y;w=$width;h=$height;size=$size;color=$color;bold=$bold;align=$align})
  }
  function B($name,$region,$x,$y,$width,$height,$fill,$stroke,$round=$false) {
    $objects.Add(@{kind='box';name=$name;region=$region;x=$x;y=$y;w=$width;h=$height;fill=$fill;stroke=$stroke;round=$round})
  }
  function P($name,$region,$file,$x,$y,$width,$height,$crop,$reason) {
    $objects.Add(@{kind='picture';name=$name;region=$region;file=$file;x=$x;y=$y;w=$width;h=$height;crop=$crop;raster_reason=$reason;atomic_raster_unit=$true;contains_reconstructable_content=$false;decomposition_note='One independent photographic or dense measured geometric field. Captions, nodes, arrows and pose-hypothesis glyphs are separate native objects.'})
  }
  function C($name,$region,$from,$fromSite,$to,$toSite,$color,$arrow=$true,$dash=$false) {
    $objects.Add(@{kind='connector';name=$name;region=$region;from=$from;fromSite=$fromSite;to=$to;toSite=$toSite;color=$color;arrow=$arrow;dash=$dash})
  }
  B 'canvas' 'canvas' 32 110 896 410 $palette.white $palette.white $true
  T 'title' 'canvas' $w.title 58 22 850 48 36 $palette.white $true
  T 'subtitle' 'canvas' $w.subtitle 58 75 850 25 17 $palette.white
  $xs=@(58,276,494,712)
  for($i=0;$i -lt 4;$i++){T ('stage-'+($i+1)) 'canvas' $w.headings[$i] $xs[$i] 136 190 25 17.3 $palette.purple $true}

  P 'chassis' 'platform' 'docs/assets/robot/chassis.jpg' 66 176 174 103 @(0,0,0,0) 'One user-supplied photograph of the physical omnidirectional chassis.'
  T 'chassis-caption' 'platform' $w.chassis 58 284 190 20 12.8 $palette.grey $false 'center'
  P 'sensors' 'platform' 'docs/assets/robot/sensors.png' 66 310 174 93 @(0,0,0,0) 'One user-supplied photograph of the physical sensors.'
  T 'sensors-caption' 'platform' $w.sensors 58 410 190 20 12.8 $palette.grey $false 'center'

  P 'scan2' 'observations' 'docs/assets/direction/scan-2d.png' 280 176 176 108 @(.16,.03,.16,.02) 'One measured 2D LaserScan geometric field from the declared recorded bag, with no rasterized axes or labels.'
  T 'scan2-caption' 'observations' $w.scan2 273 290 190 20 12.8 $palette.grey $false 'center'
  P 'scan3' 'observations' 'docs/assets/direction/scan-3d.png' 280 313 176 90 @(.17,.20,.17,.08) 'One dense actual 3D LiDAR scan from the declared recording, with no labels or axes.'
  T 'scan3-caption' 'observations' $w.scan3 273 410 190 20 12.8 $palette.grey $false 'center'

  B 'pose-node' 'slam' 505 177 160 37 $palette.lavender $palette.purple
  T 'pose-title' 'slam' $w.pose 509 183 152 25 16.5 $palette.ink $false 'center'
  $dots=@(@(539,253),@(553,250),@(568,257),@(583,251),@(598,260),@(615,253),@(627,261),@(548,265),@(565,268),@(582,265),@(603,271),@(619,271))
  for($i=0;$i -lt $dots.Count;$i++){$objects.Add(@{kind='dot';name=('hypothesis-'+$i);region='slam';x=$dots[$i][0];y=($dots[$i][1]-20);w=4.5;h=4.5;fill=$palette.purple})}
  $objects.Add(@{kind='group';name='pose-hypotheses-schematic';region='slam';members=@(0..11|ForEach-Object{'hypothesis-'+$_})})
  T 'hypotheses-caption' 'slam' $w.hypotheses 501 257 168 17 11.1 $palette.grey $false 'center'
  P 'map3' 'slam' 'docs/assets/direction/map-3d.png' 503 281 164 92 @(.27,.10,.17,.23) 'One dense recorded 3D map field from controlled mapping A with supplied sensor poses.'
  T 'map-scope' 'slam' $w.given 501 379 168 18 11.7 $palette.grey $false 'center'
  B 'map-node' 'slam' 505 404 160 26 $palette.lavender $palette.purple
  T 'map-title' 'slam' $w.map 509 405 152 23 15.4 $palette.ink $false 'center'
  foreach($a in @(@('pose-right',680,194.5),@('map-right',680,416),@('map-left',490,416),@('pose-left',490,194.5))){$objects.Add(@{kind='anchor';name=$a[0];region='slam';x=$a[1];y=$a[2];w=2;h=2})}
  C 'pose-to-map-out' 'slam' 'pose-node' 4 'pose-right' 2 $palette.purple $false
  C 'pose-to-map-rail' 'slam' 'pose-right' 3 'map-right' 1 $palette.purple $false
  C 'pose-to-map-in' 'slam' 'map-right' 2 'map-node' 4 $palette.purple
  C 'map-to-pose-out' 'slam' 'map-node' 2 'map-left' 4 $palette.green $false
  C 'map-to-pose-rail' 'slam' 'map-left' 1 'pose-left' 3 $palette.green $false
  C 'map-to-pose-in' 'slam' 'pose-left' 4 'pose-node' 2 $palette.green

  P 'gazebo' 'recovery' 'docs/assets/direction/gazebo-corridor.png' 713 177 190 101 @(0,0,0,0) 'One simulator-rendered corridor viewport from the genuine native execution recording; window chrome, RViz and Terminal excluded.'
  T 'corridor-caption' 'recovery' $w.corridor 713 284 190 20 12.4 $palette.grey $false 'center'
  for($i=0;$i -lt 4;$i++){$color=$palette.ink;if($i -eq 3){$color=$palette.green};T ('recovery-step-'+($i+1)) 'recovery' $w.steps[$i] 721 (311+$i*29) 179 25 14.1 $color ($i -eq 3)}

  for($i=0;$i -lt 4;$i++){
    B ('process-node-'+($i+1)) 'flow' $xs[$i] 442 190 43 $palette.lavender $palette.purple
    T ('process-text-'+($i+1)) 'flow' $w.process[$i] ($xs[$i]+4) 448 182 33 13.5 $palette.ink $false 'center'
  }
  for($i=1;$i -le 3;$i++){C ('pipeline-'+$i) 'flow' ('process-node-'+$i) 4 ('process-node-'+($i+1)) 2 $palette.purple $true ($i -eq 3)}
  T 'candidate-question' 'flow' $w.question 58 493 844 23 15.5 $palette.purple $true
  T 'scope-footer' 'flow' $w.scope 58 525 850 13 10.7 $palette.white
  foreach($o in $objects){if($o.ContainsKey('x')){switch($o.region){'observations'{$o.x+=3};'slam'{$o.x+=6};'recovery'{$o.x-=1}}}}
  return ,$objects.ToArray()
}

$plan=@{
  kind='bilingual_direction_figure_v2';canvas_points=@(960,540);application='Microsoft PowerPoint';backend='COM';
  reference=@{file=$reference;sha256=(Get-FileHash -LiteralPath $reference -Algorithm SHA256).Hash.ToLower();inspected_slides=@(3,4,6,11);use='Visual style only: purple palette, Golos typography, white rounded canvas, numbered horizontal process, aligned evidence fields. No semantic-mapping content or source-deck mutation.'};
  palette=$palette;typography=@{en='Golos Text Figures';'zh-CN'='Microsoft YaHei';title=36;stage=17.3;body=14.1};
  region_order=@('canvas','platform','observations','slam','recovery','flow');
  semantics=@('SLAM jointly estimates pose and map; two attached routes show their mutual dependence.','Mapping A picture uses provided sensor poses and does not demonstrate complete 3D SLAM.','Pose-hypothesis glyph is illustrative native geometry, not measured particle data.','Recovery is an open research question, not a demonstrated new strategy.','Physical photographs are distinct from Gazebo-generated evidence; physical tests pending.');
  local_acceptance=@('No text clipping or unintended label overlap.','Every evidence image remains a separate atomic picture; captions are editable.','All relationships use attached native connectors and reserved lanes.','English and Chinese carry parallel scientific meaning.');
  languages=@{en=(Make-Plan 'en');'zh-CN'=(Make-Plan 'zh-CN')}
}
$planPath=Join-Path $assets 'design.v2.json'
$plan | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $planPath -Encoding UTF8
if($Region -eq 'plan'){Write-Output ('Wrote reconstruction plan: '+$planPath);exit}

function RGB([string]$hex){$hex=$hex.TrimStart('#');return [Convert]::ToInt32($hex.Substring(0,2),16)+256*[Convert]::ToInt32($hex.Substring(2,2),16)+65536*[Convert]::ToInt32($hex.Substring(4,2),16)}
$app=New-Object -ComObject PowerPoint.Application
$work=Join-Path $build ('SLAM_direction_'+$Language+'_working.pptx')
$p=$null
foreach($candidate in $app.Presentations){if($candidate.FullName -eq $work){$p=$candidate;break}}
if($null -eq $p){
  if(Test-Path -LiteralPath $work){$p=$app.Presentations.Open($work,0,0,-1)}
  elseif($Region -eq 'canvas'){$p=$app.Presentations.Add(-1);$p.PageSetup.SlideWidth=960;$p.PageSetup.SlideHeight=540;$null=$p.Slides.Add(1,12);$p.SaveAs($work,24)}
  else{throw 'Create the isolated canvas before drawing another region.'}
}
if($p.FullName -ne $work){throw 'Target presentation identity changed.'}
$slide=$p.Slides.Item(1)
$slide.FollowMasterBackground=0
$slide.Background.Fill.Solid();$slide.Background.Fill.ForeColor.RGB=(RGB $palette.purple)
$font=if($Language -eq 'en'){'Golos Text Figures'}else{'Microsoft YaHei'}

function Text-Style($shape,$o){
  $frame=$shape.TextFrame;$frame.AutoSize=0;$frame.WordWrap=-1
  $frame.MarginLeft=0;$frame.MarginRight=0;$frame.MarginTop=0;$frame.MarginBottom=0
  $frame.VerticalAnchor=3
  $range=$frame.TextRange;$range.Text=$o.text;$range.Font.Name=$font;$range.Font.NameFarEast='Microsoft YaHei'
  $range.Font.Size=[single]$o.size;$range.Font.Bold=if($o.bold){-1}else{0};$range.Font.Color.RGB=(RGB $o.color)
  $range.ParagraphFormat.Alignment=if($o.align -eq 'center'){2}else{1}
  $range.ParagraphFormat.SpaceBefore=0;$range.ParagraphFormat.SpaceAfter=0
}
function Find-Shape([string]$name){foreach($shape in $slide.Shapes){if($shape.Name -eq $name){return $shape}};throw ('Missing named object: '+$name)}
function Tag($shape,[string]$key,[string]$value){
  $shape.Tags.Add($key,$value)
  $known=@{raster_reason='ScientificIllustratorRasterReason';source_is_tightly_cropped='ScientificIllustratorSourceTightlyCropped';atomic_raster_unit='ScientificIllustratorAtomicRasterUnit';contains_reconstructable_content='ScientificIllustratorContainsReconstructableContent';decomposition_note='ScientificIllustratorDecompositionNote'}
  if($known.ContainsKey($key)){$shape.Tags.Add($known[$key],$value)}
}
function Fit-Picture($shape,$o){
  Add-Type -AssemblyName System.Drawing
  $image=[Drawing.Image]::FromFile((Join-Path $RepoRoot $o.file))
  $naturalW=[double]$image.Width;$naturalH=[double]$image.Height;$image.Dispose()
  $l=$o.crop[0];$t=$o.crop[1];$r=$o.crop[2];$b=$o.crop[3]
  $ratio=$naturalW*(1-$l-$r)/($naturalH*(1-$t-$b))
  $width=[Math]::Min($o.w,$o.h*$ratio);$height=$width/$ratio
  $shape.LockAspectRatio=0;$shape.Width=[single]$width;$shape.Height=[single]$height
  $crop=$shape.PictureFormat.Crop
  $crop.PictureWidth=[double]($width/(1-$l-$r));$crop.PictureHeight=[double]($height/(1-$t-$b))
  $crop.PictureOffsetX=[double](($r-$l)*$crop.PictureWidth/2);$crop.PictureOffsetY=[double](($b-$t)*$crop.PictureHeight/2)
  $shape.Left=[single]($o.x+($o.w-$width)/2);$shape.Top=[single]($o.y+($o.h-$height)/2)
  $shape.LockAspectRatio=-1
}
function Picture-Tags($shape,$o){
  Tag $shape 'raster_reason' $o.raster_reason;Tag $shape 'source_is_tightly_cropped' 'true'
  Tag $shape 'atomic_raster_unit' 'true';Tag $shape 'contains_reconstructable_content' 'false'
  Tag $shape 'decomposition_note' $o.decomposition_note;Tag $shape 'source_crop_ltrb_fraction' ($o.crop -join ',')
  $shape.Tags.Add('ScientificIllustratorSourcePath',(Join-Path $RepoRoot $o.file));$shape.AlternativeText=$o.raster_reason
}
if($ApplyPlanGeometry){foreach($o in $plan.languages[$Language]){
  if($o.kind -in @('connector','dot')){continue}
  try{$shape=Find-Shape $o.name}catch{if($_.Exception.Message -like 'Missing named object*'){continue}else{throw}}
  if($o.kind -eq 'group'){$members=@($plan.languages[$Language]|Where-Object{$_.name -in $o.members});$shape.Left=[single](($members|Measure-Object -Property x -Minimum).Minimum);$shape.Top=[single](($members|Measure-Object -Property y -Minimum).Minimum)}
  elseif($o.kind -ne 'picture'){$shape.Left=[single]$o.x;$shape.Top=[single]$o.y;$shape.Width=[single]$o.w;$shape.Height=[single]$o.h}
}}
if($RefreshPictures){foreach($o in $plan.languages[$Language]){if($o.kind -eq 'picture'){try{$shape=Find-Shape $o.name;Fit-Picture $shape $o;Picture-Tags $shape $o}catch{if($_.Exception.Message -notlike 'Missing named object*'){throw}}}}}

if($Region -ne 'finalize'){
  foreach($o in $plan.languages[$Language]){
    if($o.region -ne $Region){continue}
    $existing=$null;foreach($shape in $slide.Shapes){if($shape.Name -eq $o.name){$existing=$shape;break}}
    if($null -ne $existing){if($Resume){continue};throw ('Region already contains '+$o.name+'; correct specific native objects rather than redrawing it.')}
    switch($o.kind){
      'text' {$shape=$slide.Shapes.AddTextbox(1,$o.x,$o.y,$o.w,$o.h);$shape.Fill.Visible=0;$shape.Line.Visible=0;Text-Style $shape $o}
      'box' {$kind=if($o.round){5}else{1};$shape=$slide.Shapes.AddShape($kind,$o.x,$o.y,$o.w,$o.h);$shape.Fill.ForeColor.RGB=(RGB $o.fill);$shape.Line.ForeColor.RGB=(RGB $o.stroke);$shape.Line.Weight=1.1;if($o.round){$shape.Adjustments.Item(1)=.06}}
      'dot' {$shape=$slide.Shapes.AddShape(9,$o.x,$o.y,$o.w,$o.h);$shape.Fill.ForeColor.RGB=(RGB $o.fill);$shape.Line.Visible=0}
      'anchor' {$shape=$slide.Shapes.AddShape(1,$o.x,$o.y,$o.w,$o.h);$shape.Fill.Visible=0;$shape.Line.Visible=0}
      'picture' {
        $imagePath=Join-Path $RepoRoot $o.file
        $shape=$slide.Shapes.AddPicture($imagePath,0,-1,$o.x,$o.y,-1,-1)
        Fit-Picture $shape $o
        Picture-Tags $shape $o
      }
      'connector' {
        $begin=Find-Shape $o.from;$end=Find-Shape $o.to
        $shape=$slide.Shapes.AddConnector(1,$begin.Left,$begin.Top,$end.Left,$end.Top)
        $shape.ConnectorFormat.BeginConnect($begin,$o.fromSite);$shape.ConnectorFormat.EndConnect($end,$o.toSite)
        $shape.Line.ForeColor.RGB=(RGB $o.color);$shape.Line.Weight=1.3
        $shape.Line.EndArrowheadStyle=if($o.arrow){3}else{1};if($o.dash){$shape.Line.DashStyle=4}
      }
      'group' {$shape=$slide.Shapes.Range([object[]]$o.members).Group();Tag $shape 'schematic_not_measured' 'true'}
      default {throw ('Unsupported object kind '+$o.kind)}
    }
    $shape.Name=$o.name;Tag $shape 'region' $Region
    Start-Sleep -Milliseconds 35
  }
}

$inventory=@();$findings=@()
foreach($shape in $slide.Shapes){
  $item=@{name=$shape.Name;id=$shape.Id;type=$shape.Type;x=$shape.Left;y=$shape.Top;width=$shape.Width;height=$shape.Height}
  if($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1){
    $frame=$shape.TextFrame;$item.text=$frame.TextRange.Text;$item.bound_height=$frame.TextRange.BoundHeight;$item.bound_width=$frame.TextRange.BoundWidth
    if($item.bound_height -gt $shape.Height+.8 -or $item.bound_width -gt $shape.Width+.8){$findings+=@{object=$shape.Name;category='text-fit';bounds=@($item.bound_width,$item.bound_height);frame=@($shape.Width,$shape.Height)}}
  }
  if($shape.Left -lt -.8 -or $shape.Top -lt -.8 -or $shape.Left+$shape.Width -gt 960.8 -or $shape.Top+$shape.Height -gt 540.8){$findings+=@{object=$shape.Name;category='out-of-bounds'}}
  if($shape.Type -eq 13){$item.raster_reason=$shape.Tags.Item('raster_reason');$item.atomic_raster_unit=$shape.Tags.Item('atomic_raster_unit');$item.crop=$shape.Tags.Item('source_crop_ltrb_fraction');if(-not $item.raster_reason -or $item.atomic_raster_unit -ne 'true'){$findings+=@{object=$shape.Name;category='raster-declaration'}}}
  if($shape.Connector -eq -1){$item.begin_connected=$shape.ConnectorFormat.BeginConnected;$item.end_connected=$shape.ConnectorFormat.EndConnected;if($item.begin_connected -ne -1 -or $item.end_connected -ne -1){$findings+=@{object=$shape.Name;category='detached-connector'}}}
  if($shape.Type -eq 6){$item.group_members=$shape.GroupItems.Count}
  $inventory+=$item
}
$report=@{language=$Language;region=$Region;application='Microsoft PowerPoint';backend='COM';renderer='Microsoft PowerPoint';fixed_target=$p.FullName;objects=$inventory;hard_failure_count=$findings.Count;findings=$findings}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $build ($Language+'-'+$Region+'-structure.json')) -Encoding UTF8
$p.Save()
$slide.Export((Join-Path $build ($Language+'-'+$Region+'.png')),'PNG',1920,1080)
if($findings.Count){$findings|ConvertTo-Json -Depth 5;throw 'Local structure gate failed; correct the named objects before continuing.'}
if($Region -eq 'finalize'){
  $suffix=if($Language -eq 'en'){'EN'}else{'ZH'}
  $repoDeck=Join-Path $RepoRoot ('docs\assets\slam-recovery-flow.'+$Language+'.v2.pptx')
  $repoImage=Join-Path $RepoRoot ('docs\assets\slam-recovery-flow.'+$Language+'.v2.png')
  $notes='Conceptual SLAM pose-map loop. Localizers: AMCL, IR-MCL, AdaM-MCL, NDT and GICP. Map cleaners: DUFOMap and BeautyMap. These have different roles; the sketch does not imply all these methods jointly implement SLAM. Mapping A uses provided poses; physical tests pending. Pose glyph is schematic, not measured particles. All raster sources: docs/assets/direction/sources.json. Style reference only: '+$reference
  $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text=$notes
  $p.Save();$p.SaveCopyAs($repoDeck,24);$slide.Export($repoImage,'PNG',2400,1350)
  Copy-Item -LiteralPath $repoDeck -Destination (Join-Path $PresentationRoot ('SLAM定义与开放问题流程_'+$suffix+'_v2.pptx'))
  Copy-Item -LiteralPath $repoImage -Destination (Join-Path $PresentationRoot ('SLAM定义与开放问题流程_'+$suffix+'_v2.png'))
  Write-Output ('Delivered '+$repoDeck)
}
Write-Output ($Language+' / '+$Region+': '+$slide.Shapes.Count+' native top-level objects, no structure findings; fixed target '+$p.FullName)
