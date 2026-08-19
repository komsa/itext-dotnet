$ErrorActionPreference = "stop"
Set-StrictMode -Version Latest

# Version comes from the single source of truth: KomsaVersion in the repo-root
# Directory.Build.props. Nothing else in the repository spells the version out.
[xml]$propsXml = Get-Content -Path "$PSScriptRoot\Directory.Build.props"
$currentVersion = $propsXml.SelectSingleNode("Project/PropertyGroup/KomsaVersion").InnerText

$outputDirectory = "$PSScriptRoot\artifacts\nuget"
$nuget = "D:\Git\TeamFoundation\Binaries\Stable\nuget.exe"

# The 8 module packages are produced by GeneratePackageOnBuild during the Release build.
&dotnet build "$PSScriptRoot\iTextCore.sln" -c Release
if ($LASTEXITCODE -ne 0) { throw "Release build failed" }

# The bundle package globs the freshly built output; $version$ in itext.nuspec is
# substituted from the same KomsaVersion value.
&$nuget pack "$PSScriptRoot\itext.nuspec" -OutputDirectory $outputDirectory -Properties "version=$currentVersion" -NonInteractive
if ($LASTEXITCODE -ne 0) { throw "nuget pack failed" }

Write-Output "Packed version $currentVersion into $outputDirectory"
