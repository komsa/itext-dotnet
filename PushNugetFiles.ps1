$ErrorActionPreference = "stop"
Set-StrictMode -Version Latest

# Version comes from the single source of truth used by every project.
[xml]$propsXml = Get-Content -Path "$PSScriptRoot\itext\Directory.Build.props"
$currentVersion = $propsXml.SelectSingleNode("Project/PropertyGroup/VersionPrefix").InnerText

# Both the 8 module packages (dotnet pack / GeneratePackageOnBuild) and the
# bundle package (nuget.exe pack itext.nuspec) are written to this directory.
$outputDirectory = "$PSScriptRoot\artifacts\nuget"

&dotnet nuget push -s "https://tfs-01/DefaultCollection/_packaging/Komsa/nuget/v3/index.json" -k AzureDevOps "$outputDirectory\Komsa.*.$currentVersion.nupkg"
pause
