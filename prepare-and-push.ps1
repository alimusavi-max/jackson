Write-Host "Starting cleanup..."

# Update .gitignore
@"
node_modules/
.next/
.next/cache/
dist/
build/
out/
*.log
.env
.DS_Store
*.zip
*.tar.gz
*.rar
*.sqlite
*.bak
*.tmp
"@ | Out-File -Encoding UTF8 .gitignore -Force

Write-Host ".gitignore updated."

# Remove cached folders from git index
git rm -r --cached node_modules -f 2>$null
git rm -r --cached .next -f 2>$null
git rm -r --cached dist -f 2>$null
git rm -r --cached build -f 2>$null
git rm -r --cached out -f 2>$null

Write-Host "Removed cached folders from git index."

# Remove .next folder completely from disk
if (Test-Path ".next") {
    Remove-Item -Recurse -Force .next
    Write-Host ".next folder deleted from disk."
} else {
    Write-Host ".next folder does not exist on disk."
}

# Search for files larger than 10MB (optional warning)
$largeFiles = Get-ChildItem -Recurse -File | Where-Object { $_.Length -gt 10MB }
if ($largeFiles.Count -gt 0) {
    Write-Host "Warning: found files larger than 10MB:"
    $largeFiles | ForEach-Object {
        Write-Host ("{0} - {1:N2} MB" -f $_.FullName, ($_.Length / 1MB))
    }
} else {
    Write-Host "No files larger than 10MB found."
}

# Commit changes and push
git add .
git commit -m "Cleanup cached heavy folders and update .gitignore"
git remote remove origin 2>$null
git remote add origin https://github.com/alimusavi-max/jackson.git
git push -u origin main

Write-Host "Push completed."
