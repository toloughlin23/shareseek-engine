# update_branding.ps1
# Replaces project name and branding in README.md

README.md = "README.md"

if (-Not (Test-Path README.md)) {
    Write-Error "Could not find README.md in the current directory."
    exit 1
}

# Read in the file
 = Get-Content README.md -Raw

# Replace the top-level title (any H1) with "# share-seek"
# and swap any “trading_dashboard” or “stock seek” to “share-seek”
 =  -replace '(?m)^#\s+.*', '# share-seek'
 =  -replace '(?i)trading_dashboard|stock seek', 'share-seek'

# Write it back out
Set-Content -Path README.md -Value  -Encoding UTF8

Write-Host "README.md has been updated to use 'share-seek' branding."
