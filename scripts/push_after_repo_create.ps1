param(
  [string]$RemoteUrl = "https://github.com/whtjddlr/carch.git"
)

git remote remove origin 2>$null
git remote add origin $RemoteUrl
git branch -M main
git push -u origin main
