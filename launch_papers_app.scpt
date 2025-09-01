tell application "Terminal"
	activate
	set currentPath to (do shell script "dirname " & quoted form of POSIX path of (path to me))
	do script "cd " & quoted form of currentPath & " && source venv/bin/activate && cd papers-desktop-app && python -m app.main"
end tell
