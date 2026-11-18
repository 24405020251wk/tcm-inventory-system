Option Explicit
' One-click launcher: makes sure the server is running (hidden), then opens the browser.
Dim fso, shell, baseDir, serve, url

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
serve = baseDir & "\serve.bat"
url = "http://127.0.0.1:8000/accounts/login/"

If Not fso.FileExists(serve) Then
    MsgBox "serve.bat was not found in:" & vbCrLf & baseDir, 16, "TCM Inventory"
    WScript.Quit 1
End If

' Start the server in the background. If it is already running, the new
' instance simply exits because the port is occupied - harmless.
shell.CurrentDirectory = baseDir
shell.Run """" & serve & """", 0, False

' Give Django a moment to bind the port, then open the browser.
WScript.Sleep 3500
shell.Run url, 1, False
