param(
  [int]$SlideIndex=1,
  [string]$Region='workflow',
  [switch]$ExportOnly,
  [string]$RepoRoot=([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..')))
)
$ErrorActionPreference='Stop'
# Native COM drawer. Explicit UTF-8 avoids the MCP bridge's ANSI decoding of CJK.
$assetRoot=Join-Path $RepoRoot 'docs\assets\direction\v3'
$plan=Get-Content -LiteralPath (Join-Path $assetRoot 'design.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$deckPath=Join-Path $assetRoot 'direction-analysis.editable.pptx'
try{$app=[Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')}
catch{$app=New-Object -ComObject PowerPoint.Application}
$deck=$null
foreach($candidate in $app.Presentations){if($candidate.FullName -eq $deckPath){$deck=$candidate;break}}
if($null -eq $deck){
  if(Test-Path -LiteralPath $deckPath){$deck=$app.Presentations.Open($deckPath,$false,$false,$true)}
  else{$deck=$app.Presentations.Add($true);$deck.PageSetup.SlideWidth=960;$deck.PageSetup.SlideHeight=540;$deck.SaveAs($deckPath)}
}
if($ExportOnly){
  $deck.Save()
  for($idx=1;$idx -le $plan.slides.Count;$idx++){
    $deck.Slides.Item($idx).Export((Join-Path $assetRoot $plan.slides[$idx-1].output),'PNG',1920,1080)
  }
  Write-Output 'Exported four previews from the saved native deck; no objects rebuilt.'
  exit
}
$slidePlan=$plan.slides[$SlideIndex-1]
while($deck.Slides.Count -lt $SlideIndex){$null=$deck.Slides.Add($deck.Slides.Count+1,12)}
$slide=$deck.Slides.Item($SlideIndex)
$slide.Name=$slidePlan.name

function Rgb([string]$Hex){
  $s=$Hex.TrimStart('#')
  return [Convert]::ToInt32($s.Substring(0,2),16) -bor ([Convert]::ToInt32($s.Substring(2,2),16) -shl 8) -bor ([Convert]::ToInt32($s.Substring(4,2),16) -shl 16)
}
function Has($Object,[string]$Name){return $null -ne $Object.PSObject.Properties[$Name]}
function Shape([string]$Name){foreach($item in $slide.Shapes){if($item.Name -eq $Name){return $item}};throw "Missing $Name"}
$regionPlan=@($slidePlan.regions | Where-Object {$_.id -eq $Region})
if($regionPlan.Count -ne 1){throw 'Region not found'}
# Delete only generated objects in the requested region, to allow exact reruns.
foreach($op in $regionPlan[0].operations){
  for($idx=$slide.Shapes.Count;$idx -ge 1;$idx--){if($slide.Shapes.Item($idx).Name -eq $op.name){$slide.Shapes.Item($idx).Delete()}}
}
foreach($op in $regionPlan[0].operations){
  if($op.type -eq 'add_textbox'){
    if([string]::IsNullOrEmpty($op.text)){$s=$slide.Shapes.AddShape(1,$op.left,$op.top,$op.width,$op.height)}
    else{$s=$slide.Shapes.AddTextbox(1,$op.left,$op.top,$op.width,$op.height)}
    $s.Name=$op.name
    $s.Fill.Visible=0;$s.Line.Visible=0
    if(Has $op 'fill_color'){$s.Fill.Visible=-1;$s.Fill.Solid();$s.Fill.ForeColor.RGB=Rgb $op.fill_color}
    if(Has $op 'line_color'){$s.Line.Visible=-1;$s.Line.ForeColor.RGB=Rgb $op.line_color;$s.Line.Weight=[single]$op.line_width}
    if((Has $op 'line_dash') -and $op.line_dash -eq 'dash'){$s.Line.DashStyle=4}
    $s.Shadow.Visible=0
    if(-not [string]::IsNullOrEmpty($op.text)){
      $s.TextFrame2.AutoSize=0
      $s.TextFrame2.WordWrap=-1
      $s.TextFrame2.MarginLeft=$op.margin_left;$s.TextFrame2.MarginRight=$op.margin_right
      $s.TextFrame2.MarginTop=$op.margin_top;$s.TextFrame2.MarginBottom=$op.margin_bottom
      $s.TextFrame2.TextRange.Text=$op.text.Replace("`n","`r")
      $s.TextFrame2.TextRange.Font.Name=$op.font_name
      $s.TextFrame2.TextRange.Font.NameFarEast=$op.font_name
      $s.TextFrame2.TextRange.Font.Size=[single]$op.font_size
      $s.TextFrame2.TextRange.Font.Bold= $(if($op.bold){-1}else{0})
      $s.TextFrame2.TextRange.Font.Fill.ForeColor.RGB=Rgb $op.font_color
      $s.TextFrame2.TextRange.ParagraphFormat.SpaceBefore=0
      $s.TextFrame2.TextRange.ParagraphFormat.SpaceAfter=0
      $s.TextFrame2.TextRange.ParagraphFormat.Alignment=$(if($op.alignment -eq 'center'){2}else{1})
      $s.TextFrame2.VerticalAnchor=$(if($op.vertical_alignment -eq 'middle'){3}else{1})
    }
    # Enforce planned bounds after all text/font operations.
    $s.Left=[single]$op.left;$s.Top=[single]$op.top;$s.Width=[single]$op.width;$s.Height=[single]$op.height
    $s.AlternativeText='Native editable direction figure; object '+$op.name
  } elseif($op.type -eq 'add_connector'){
    $src=Shape $op.source_name;$dst=Shape $op.target_name
    $s=$slide.Shapes.AddConnector(1,0,0,10,10)
    $s.Name=$op.name
    $s.ConnectorFormat.BeginConnect($src,$op.source_site)
    $s.ConnectorFormat.EndConnect($dst,$op.target_site)
    $s.Line.ForeColor.RGB=Rgb $op.line_color;$s.Line.Weight=[single]$op.line_width
    $s.Line.BeginArrowheadStyle=1
    $s.Line.EndArrowheadStyle=$(if($op.end_arrow -eq 'triangle'){2}else{1})
    $s.AlternativeText='Native attached semantic connector; '+$op.source_name+' to '+$op.target_name
  } else {throw 'Unsupported operation'}
  Start-Sleep -Milliseconds 20
}
$deck.Save()
$textFit=@()
foreach($s in $slide.Shapes){
  if($s.HasTextFrame -and $s.TextFrame2.HasText){
    $textFit+=@{name=$s.Name;left=[double]$s.Left;top=[double]$s.Top;width=[double]$s.Width;height=[double]$s.Height;
      text=$s.TextFrame2.TextRange.Text;bound_width=[double]$s.TextFrame2.TextRange.BoundWidth;
      bound_height=[double]$s.TextFrame2.TextRange.BoundHeight;
      inner_width=[double]($s.Width-$s.TextFrame2.MarginLeft-$s.TextFrame2.MarginRight);
      inner_height=[double]($s.Height-$s.TextFrame2.MarginTop-$s.TextFrame2.MarginBottom)}
  }
}
$report=@{slide=$SlideIndex;region=$Region;native_objects=$slide.Shapes.Count;text_fit=$textFit;renderer='PowerPoint COM'}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $assetRoot "structure-$SlideIndex.json") -Encoding UTF8
Write-Output ('Drawn '+$slide.Name+' / '+$Region+' / '+$slide.Shapes.Count+' native objects')
