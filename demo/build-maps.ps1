param([ValidateSet('static','dynamic','corridor')][string]$Scene='corridor',[string]$RepoRoot='D:\workspace\be2\slam_learning_updated')
$rootw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList "-w new new-tab --title SLAM-MAP-BUILD-$Scene --suppressApplicationTitle wsl.exe -d Ubuntu-22.04 -- bash $rootw/src/scripts/presentation/build_maps.sh $Scene"
