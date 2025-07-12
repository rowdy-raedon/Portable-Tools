# Portable Apps PowerShell Launcher
# CLI interface for managing and launching portable applications

param(
    [string]$Action = "list",
    [string]$AppName = "",
    [switch]$Help
)

# Configuration
$PortableAppsDir = Join-Path $PSScriptRoot "Portable apps"
$ConfigFile = Join-Path $PSScriptRoot "config.json"

function Show-Help {
    Write-Host "Portable Apps PowerShell Launcher" -ForegroundColor Green
    Write-Host "Usage: .\Portable.ps1 [Action] [Options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Actions:" -ForegroundColor Cyan
    Write-Host "  list              List all available portable apps"
    Write-Host "  launch <name>     Launch a specific app"
    Write-Host "  search <term>     Search for apps containing the term"
    Write-Host "  favorites         List favorite apps"
    Write-Host "  recent            List recently used apps"
    Write-Host "  add <path>        Add a new portable app"
    Write-Host "  remove <name>     Remove an app from the list"
    Write-Host "  info <name>       Show app information"
    Write-Host "  gui               Launch the GUI version"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Magenta
    Write-Host "  .\Portable.ps1 list"
    Write-Host "  .\Portable.ps1 launch notepad"
    Write-Host "  .\Portable.ps1 search edit"
    Write-Host "  .\Portable.ps1 add 'C:\Tools\app.exe'"
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  -Help             Show this help message"
}

function Get-PortableApps {
    $apps = @()
    
    if (Test-Path $ConfigFile) {
        try {
            $config = Get-Content $ConfigFile | ConvertFrom-Json
            $apps = $config.apps
        }
        catch {
            Write-Warning "Failed to load config file. Scanning directory..."
        }
    }
    
    # If no config or failed to load, scan directory
    if ($apps.Count -eq 0) {
        if (Test-Path $PortableAppsDir) {
            $exeFiles = Get-ChildItem -Path $PortableAppsDir -Filter "*.exe" -Recurse
            foreach ($exe in $exeFiles) {
                $apps += @{
                    name = $exe.BaseName
                    path = $exe.FullName
                    favorite = $false
                    last_run = ""
                    run_count = 0
                }
            }
        }
    }
    
    return $apps
}

function Show-AppsList {
    param([array]$Apps, [string]$Title = "Available Portable Apps")
    
    if ($Apps.Count -eq 0) {
        Write-Host "No portable apps found." -ForegroundColor Yellow
        Write-Host "Place .exe files in the '$PortableAppsDir' directory or use 'add' command." -ForegroundColor Gray
        return
    }
    
    Write-Host $Title -ForegroundColor Green
    Write-Host ("=" * $Title.Length) -ForegroundColor Green
    
    $index = 1
    foreach ($app in $Apps) {
        $star = if ($app.favorite) { "★" } else { " " }
        $lastRun = if ($app.last_run) { 
            try {
                $date = [DateTime]::Parse($app.last_run)
                $date.ToString("yyyy-MM-dd")
            }
            catch {
                "Unknown"
            }
        } else { "Never" }
        
        Write-Host ("{0,2}. {1} {2,-30} Last run: {3}" -f $index, $star, $app.name, $lastRun)
        $index++
    }
    
    Write-Host ""
    Write-Host "Legend: ★ = Favorite" -ForegroundColor Gray
}

function Launch-App {
    param([string]$Name)
    
    $apps = Get-PortableApps
    $app = $apps | Where-Object { $_.name -like "*$Name*" } | Select-Object -First 1
    
    if (-not $app) {
        Write-Host "App '$Name' not found." -ForegroundColor Red
        Write-Host "Use 'list' action to see available apps." -ForegroundColor Gray
        return
    }
    
    if (-not (Test-Path $app.path)) {
        Write-Host "App file not found: $($app.path)" -ForegroundColor Red
        return
    }
    
    try {
        Write-Host "Launching $($app.name)..." -ForegroundColor Green
        Start-Process -FilePath $app.path -WorkingDirectory (Split-Path $app.path)
        
        # Update last run time
        $app.last_run = (Get-Date).ToString("o")
        $app.run_count = [int]$app.run_count + 1
        
        # Save updated config
        Save-Config -Apps $apps
        
        Write-Host "Successfully launched $($app.name)" -ForegroundColor Green
    }
    catch {
        Write-Host "Failed to launch $($app.name): $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Search-Apps {
    param([string]$SearchTerm)
    
    if ([string]::IsNullOrWhiteSpace($SearchTerm)) {
        Write-Host "Please provide a search term." -ForegroundColor Red
        return
    }
    
    $apps = Get-PortableApps
    $results = $apps | Where-Object { $_.name -like "*$SearchTerm*" }
    
    if ($results.Count -eq 0) {
        Write-Host "No apps found matching '$SearchTerm'" -ForegroundColor Yellow
    }
    else {
        Show-AppsList -Apps $results -Title "Search Results for '$SearchTerm'"
    }
}

function Show-Favorites {
    $apps = Get-PortableApps
    $favorites = $apps | Where-Object { $_.favorite -eq $true }
    
    Show-AppsList -Apps $favorites -Title "Favorite Apps"
}

function Show-Recent {
    $apps = Get-PortableApps
    $recent = $apps | Where-Object { $_.last_run } | Sort-Object last_run -Descending | Select-Object -First 10
    
    Show-AppsList -Apps $recent -Title "Recently Used Apps"
}

function Add-App {
    param([string]$AppPath)
    
    if ([string]::IsNullOrWhiteSpace($AppPath)) {
        Write-Host "Please provide the path to the executable." -ForegroundColor Red
        return
    }
    
    if (-not (Test-Path $AppPath)) {
        Write-Host "File not found: $AppPath" -ForegroundColor Red
        return
    }
    
    $file = Get-Item $AppPath
    if ($file.Extension -ne ".exe") {
        Write-Host "Only .exe files are supported." -ForegroundColor Red
        return
    }
    
    # Ensure portable apps directory exists
    if (-not (Test-Path $PortableAppsDir)) {
        New-Item -ItemType Directory -Path $PortableAppsDir -Force | Out-Null
    }
    
    try {
        # Copy to portable apps directory
        $destPath = Join-Path $PortableAppsDir $file.Name
        Copy-Item -Path $AppPath -Destination $destPath -Force
        
        # Add to config
        $apps = Get-PortableApps
        $newApp = @{
            name = $file.BaseName
            path = $destPath
            favorite = $false
            last_run = ""
            run_count = 0
        }
        
        # Check if app already exists
        $existing = $apps | Where-Object { $_.name -eq $newApp.name }
        if ($existing) {
            Write-Host "App '$($newApp.name)' already exists. Updating path..." -ForegroundColor Yellow
            $existing.path = $destPath
        }
        else {
            $apps += $newApp
            Write-Host "Added '$($newApp.name)' to portable apps." -ForegroundColor Green
        }
        
        Save-Config -Apps $apps
    }
    catch {
        Write-Host "Failed to add app: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Remove-App {
    param([string]$Name)
    
    if ([string]::IsNullOrWhiteSpace($Name)) {
        Write-Host "Please provide the app name." -ForegroundColor Red
        return
    }
    
    $apps = Get-PortableApps
    $app = $apps | Where-Object { $_.name -like "*$Name*" } | Select-Object -First 1
    
    if (-not $app) {
        Write-Host "App '$Name' not found." -ForegroundColor Red
        return
    }
    
    $confirmation = Read-Host "Remove '$($app.name)' from the list? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        $updatedApps = $apps | Where-Object { $_.name -ne $app.name }
        Save-Config -Apps $updatedApps
        Write-Host "Removed '$($app.name)' from the list." -ForegroundColor Green
        
        # Ask if user wants to delete the file
        if (Test-Path $app.path) {
            $deleteFile = Read-Host "Also delete the file? (y/N)"
            if ($deleteFile -eq 'y' -or $deleteFile -eq 'Y') {
                try {
                    Remove-Item -Path $app.path -Force
                    Write-Host "Deleted file: $($app.path)" -ForegroundColor Green
                }
                catch {
                    Write-Host "Failed to delete file: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
        }
    }
    else {
        Write-Host "Cancelled." -ForegroundColor Gray
    }
}

function Show-AppInfo {
    param([string]$Name)
    
    if ([string]::IsNullOrWhiteSpace($Name)) {
        Write-Host "Please provide the app name." -ForegroundColor Red
        return
    }
    
    $apps = Get-PortableApps
    $app = $apps | Where-Object { $_.name -like "*$Name*" } | Select-Object -First 1
    
    if (-not $app) {
        Write-Host "App '$Name' not found." -ForegroundColor Red
        return
    }
    
    Write-Host "App Information" -ForegroundColor Green
    Write-Host "===============" -ForegroundColor Green
    Write-Host "Name:      $($app.name)"
    Write-Host "Path:      $($app.path)"
    Write-Host "Favorite:  $(if ($app.favorite) { 'Yes' } else { 'No' })"
    Write-Host "Run Count: $($app.run_count)"
    
    if ($app.last_run) {
        try {
            $lastRun = [DateTime]::Parse($app.last_run)
            Write-Host "Last Run:  $($lastRun.ToString('yyyy-MM-dd HH:mm:ss'))"
        }
        catch {
            Write-Host "Last Run:  Unknown"
        }
    }
    else {
        Write-Host "Last Run:  Never"
    }
    
    if (Test-Path $app.path) {
        $file = Get-Item $app.path
        Write-Host "File Size: $([math]::Round($file.Length / 1MB, 2)) MB"
        Write-Host "Modified:  $($file.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    }
    else {
        Write-Host "Status:    File not found!" -ForegroundColor Red
    }
}

function Launch-GUI {
    $guiPath = Join-Path $PSScriptRoot "launcher.pyw"
    if (Test-Path $guiPath) {
        try {
            Start-Process -FilePath "pythonw" -ArgumentList $guiPath
            Write-Host "Launched GUI launcher." -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to launch GUI. Make sure Python and PyQt5 are installed." -ForegroundColor Red
            Write-Host "Alternative: try 'python launcher.pyw'" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "GUI launcher not found: $guiPath" -ForegroundColor Red
    }
}

function Save-Config {
    param([array]$Apps)
    
    try {
        $config = @{
            apps = $Apps
            last_updated = (Get-Date).ToString("o")
        }
        
        $config | ConvertTo-Json -Depth 10 | Set-Content -Path $ConfigFile -Encoding UTF8
    }
    catch {
        Write-Warning "Failed to save configuration: $($_.Exception.Message)"
    }
}

# Main script logic
if ($Help) {
    Show-Help
    exit
}

switch ($Action.ToLower()) {
    "list" { 
        $apps = Get-PortableApps
        Show-AppsList -Apps $apps
    }
    "launch" { 
        if ([string]::IsNullOrWhiteSpace($AppName)) {
            Write-Host "Please specify an app name to launch." -ForegroundColor Red
            Write-Host "Usage: .\Portable.ps1 launch <appname>" -ForegroundColor Gray
        }
        else {
            Launch-App -Name $AppName
        }
    }
    "search" { 
        if ([string]::IsNullOrWhiteSpace($AppName)) {
            Write-Host "Please specify a search term." -ForegroundColor Red
            Write-Host "Usage: .\Portable.ps1 search <term>" -ForegroundColor Gray
        }
        else {
            Search-Apps -SearchTerm $AppName
        }
    }
    "favorites" { Show-Favorites }
    "recent" { Show-Recent }
    "add" { 
        if ([string]::IsNullOrWhiteSpace($AppName)) {
            Write-Host "Please specify the path to the executable." -ForegroundColor Red
            Write-Host "Usage: .\Portable.ps1 add 'C:\path\to\app.exe'" -ForegroundColor Gray
        }
        else {
            Add-App -AppPath $AppName
        }
    }
    "remove" { 
        if ([string]::IsNullOrWhiteSpace($AppName)) {
            Write-Host "Please specify an app name to remove." -ForegroundColor Red
            Write-Host "Usage: .\Portable.ps1 remove <appname>" -ForegroundColor Gray
        }
        else {
            Remove-App -Name $AppName
        }
    }
    "info" { 
        if ([string]::IsNullOrWhiteSpace($AppName)) {
            Write-Host "Please specify an app name." -ForegroundColor Red
            Write-Host "Usage: .\Portable.ps1 info <appname>" -ForegroundColor Gray
        }
        else {
            Show-AppInfo -Name $AppName
        }
    }
    "gui" { Launch-GUI }
    "help" { Show-Help }
    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host "Use -Help for usage information." -ForegroundColor Gray
    }
}