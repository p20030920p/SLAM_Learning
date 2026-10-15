param(
  [ValidateSet('2D','3D')][string]$Dimension='3D',
  [ValidateSet('all','raw','dufomap','beautymap','choose')][string]$Method='all',
  [ValidateSet('static','dynamic','large-change','corridor','choose')][string]$Scene='choose',
  [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
  [double]$Duration=86400,
  [switch]$Auto
)
$ErrorActionPreference='Stop'
if (-not ('MappingDemoWindows' -as [type])) {
Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public class MappingDemoWindow { public IntPtr Id; public string Caption; }
public static class MappingDemoWindows {
  delegate bool Callback(IntPtr hwnd, IntPtr data);
  [DllImport("user32.dll")] static extern bool EnumWindows(Callback callback, IntPtr data);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int width, int height, uint flags);
  public static MappingDemoWindow[] List() {
    var windows = new List<MappingDemoWindow>();
    EnumWindows((hwnd,data) => {
      var text = new StringBuilder(1024); GetWindowText(hwnd,text,text.Capacity);
      if(IsWindowVisible(hwnd) && text.Length>0) windows.Add(new MappingDemoWindow {Id=hwnd,Caption=text.ToString()});
      return true;
    }, IntPtr.Zero);
    return windows.ToArray();
  }
  public static bool Move(IntPtr hwnd,int x,int y,int width,int height) {
    return SetWindowPos(hwnd,IntPtr.Zero,x,y,width,height,0x44);
  }
}
'@
}
$previousWindows=@([MappingDemoWindows]::List() | ForEach-Object {$_.Id.ToInt64()})
if ($Scene -eq 'choose') {
  Write-Host 'Scene: 1 static / 2 moving obstacles / 3 persistent change / 4 corridor'
  $answer=Read-Host 'Choose [default 2]'
  $Scene=switch ($answer) {'1' {'static'} '3' {'large-change'} '4' {'corridor'} default {'dynamic'}}
}
if ($Method -eq 'choose') {
  Write-Host 'Method: 1 Raw / 2 DUFOMap / 3 BeautyMap'
  $answer=Read-Host 'Choose [default 1]'
  $Method=switch ($answer) {'2' {'dufomap'} '3' {'beautymap'} default {'raw'}}
}
$methods=if ($Method -eq 'all') {'raw,dufomap,beautymap'} else {$Method}
$flow='mapping-compare-'+$Dimension.ToLower()+'-'+$Scene
$id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$flow+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$id)
New-Item -ItemType Directory -Path (Join-Path $run 'logs') -Force | Out-Null
function To-Wsl([string]$path) {
  $absolute=[IO.Path]::GetFullPath($path)
  if ($absolute -notmatch '^[A-Za-z]:\\') {throw 'Expected a local drive path'}
  '/mnt/'+$absolute.Substring(0,1).ToLower()+'/'+$absolute.Substring(3).Replace('\','/')
}
$repoWsl=To-Wsl $RepoRoot
$runWsl=To-Wsl $run
$autoText=if ($Auto) {'true'} else {'false'}
Write-Host 'Phase A: keyboard mapping inputs -> actual author cleaning in periodic batches.'
Write-Host 'BeautyMap is offline. All views use the SAME completed batch and provided mapping poses.'
if ($Dimension -eq '2D') {Write-Host '2D = projection of measured 3D maps; DUFOMap / BeautyMap require the 3D lidar.'}
Write-Host 'Keyboard in MAP-KEYBOARD: i/k forward/back; j/l yaw; u/o sideways; SPACE stop; q finish A.'
$workerArgs="-d Ubuntu-22.04 -- python3 $repoWsl/src/scripts/presentation/mapping_compare_worker.py $runWsl $methods"
$worker=Start-Process -FilePath wsl.exe -ArgumentList $workerArgs -WindowStyle Hidden -PassThru
$terminalArgs="-w new --pos 0,740 --size 200,13 new-tab --title MAP-KEYBOARD --suppressApplicationTitle wsl.exe -d Ubuntu-24.04 -- bash $repoWsl/src/scripts/presentation/run_live.sh $flow $runWsl $Duration $autoText false $methods"
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList $terminalArgs
$deadline=(Get-Date).AddMinutes(4)
try {
  while (-not (Test-Path (Join-Path $run 'ready.json'))) {
    foreach ($failure in @('failed.json','compare-failed.json')) {
      if (Test-Path (Join-Path $run $failure)) {throw (Get-Content (Join-Path $run $failure) -Raw)}
    }
    if ((Get-Date) -gt $deadline) {throw ('Gazebo did not become ready: '+$run)}
    Start-Sleep -Milliseconds 500
  }
  [IO.File]::WriteAllText((Join-Path $run 'recording.started'),(Get-Date -Format o))
  # Arrange only new windows from this launch; preserve other open applications.
  Add-Type -AssemblyName System.Windows.Forms
  $screen=[System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
  $layoutDeadline=(Get-Date).AddSeconds(12)
  do {
    $owned=@([MappingDemoWindows]::List() | Where-Object {$_.Id.ToInt64() -notin $previousWindows})
    $views=@(foreach ($selectedMethod in $methods.Split(',')) {
      $owned | Where-Object {$_.Caption -like ('MAP BATCH - '+$selectedMethod+' - '+$flow+'*')}
    })
    $gazebo=@($owned | Where-Object {$_.Caption -like 'Gazebo Sim*'})
    $keyboard=@($owned | Where-Object {$_.Caption -eq 'MAP-KEYBOARD'})
    if ($views.Count -eq $methods.Split(',').Count -and $gazebo.Count -and $keyboard.Count) {break}
    Start-Sleep -Milliseconds 300
  } while ((Get-Date) -lt $layoutDeadline)
  $layout=@()
  $topHeight=[int]($screen.Height*0.57)
  $bottomHeight=$screen.Height-$topHeight
  if ($Method -eq 'all') {
    $viewWidth=[int]($screen.Width/3)
    for ($index=0;$index -lt $views.Count;$index++) {
      $null=[MappingDemoWindows]::Move($views[$index].Id,$screen.X+$index*$viewWidth,$screen.Y,$viewWidth,$topHeight)
      $layout+=@{title=$views[$index].Caption;kind='rviz'}
    }
    $leftWidth=[int]($screen.Width*0.55)
    foreach ($window in $gazebo) {$null=[MappingDemoWindows]::Move($window.Id,$screen.X,$screen.Y+$topHeight,$leftWidth,$bottomHeight)}
    foreach ($window in $keyboard) {$null=[MappingDemoWindows]::Move($window.Id,$screen.X+$leftWidth,$screen.Y+$topHeight,$screen.Width-$leftWidth,$bottomHeight)}
  } else {
    $half=[int]($screen.Width/2)
    foreach ($window in $views) {$null=[MappingDemoWindows]::Move($window.Id,$screen.X+$half,$screen.Y,$half,$screen.Height);$layout+=@{title=$window.Caption;kind='rviz'}}
    foreach ($window in $gazebo) {$null=[MappingDemoWindows]::Move($window.Id,$screen.X,$screen.Y,$half,$topHeight)}
    foreach ($window in $keyboard) {$null=[MappingDemoWindows]::Move($window.Id,$screen.X,$screen.Y+$topHeight,$half,$bottomHeight)}
  }
  [IO.File]::WriteAllText((Join-Path $run 'compare-windows.json'),(ConvertTo-Json -InputObject @{views=$layout;gazebo=$gazebo.Count;keyboard=$keyboard.Count} -Depth 5))
  if ($views.Count -ne $methods.Split(',').Count -or -not $gazebo.Count -or -not $keyboard.Count) {throw 'Some requested application windows did not open; inspect logs.'}
  Write-Host ('LIVE: '+$run)
  while (-not (Test-Path (Join-Path $run 'session-stopped.json'))) {
    foreach ($failure in @('failed.json','compare-failed.json')) {
      if (Test-Path (Join-Path $run $failure)) {throw (Get-Content (Join-Path $run $failure) -Raw)}
    }
    Start-Sleep -Milliseconds 500
  }
} finally {
  [IO.File]::WriteAllText((Join-Path $run 'STOP'),'Launcher finished')
  if (-not $worker.HasExited) {$null=$worker.WaitForExit(3000)}
  # The isolated worker finishes its current batch; no other WSL processes are stopped.
}
Write-Host ('Mapping outputs: '+$run)
Write-Host 'The existing localization demos use frozen A maps in a fresh B run; mapping views above do not estimate pose.'
