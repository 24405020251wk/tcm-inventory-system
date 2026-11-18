Option Explicit
' ============================================================
' Server watchdog
'   usage 1: wscript watchdog.vbs loop   resident mode, check every 60s
'   usage 2: wscript watchdog.vbs        single check (for external timers)
' No window is shown. Log goes to logs\watchdog.log
' ============================================================
Dim shell, fso, baseDir, logFile, loopMode

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
logFile = baseDir & "\logs\watchdog.log"

If Not fso.FolderExists(baseDir & "\logs") Then
    fso.CreateFolder baseDir & "\logs"
End If

loopMode = False
If WScript.Arguments.Count > 0 Then
    If LCase(Trim(WScript.Arguments(0))) = "loop" Then loopMode = True
End If

' --- single instance guard ---
If loopMode Then
    If AlreadyRunning() Then WScript.Quit 0
End If

If loopMode Then
    WriteLog "watchdog started (loop mode, 60s interval)"
    Do
        CheckOnce
        WScript.Sleep 60000
    Loop
Else
    CheckOnce
End If

' ============================================================
Sub CheckOnce()
    Dim running

    running = PortAlive()

    If running Then
        WriteLog "OK"
        Exit Sub
    End If

    WriteLog "DOWN -> restarting"
    shell.CurrentDirectory = baseDir
    shell.Run """" & baseDir & "\serve.bat""", 0, False
End Sub

Function PortAlive()
    Dim tmpFile, line, stream, found
    tmpFile = baseDir & "\logs\_netstat.tmp"
    shell.Run "cmd /c netstat -ano -p tcp | findstr LISTENING > """ & tmpFile & """", 0, True

    found = False
    If fso.FileExists(tmpFile) Then
        Set stream = fso.OpenTextFile(tmpFile, 1, False)
        Do While Not stream.AtEndOfStream
            line = stream.ReadLine()
            If InStr(line, ":8000 ") > 0 Then found = True
        Loop
        stream.Close
        On Error Resume Next
        fso.DeleteFile tmpFile, True
        On Error Goto 0
    End If
    PortAlive = found
End Function

Sub WriteLog(msg)
    Dim f
    On Error Resume Next
    If fso.FileExists(logFile) Then
        If fso.GetFile(logFile).Size > 512000 Then fso.DeleteFile logFile, True
    End If
    Set f = fso.OpenTextFile(logFile, 8, True)
    f.WriteLine Now & "  " & msg
    f.Close
    On Error Goto 0
End Sub

Function AlreadyRunning()
    Dim svc, procs, p, n
    n = 0
    On Error Resume Next
    Set svc = GetObject("winmgmts:\\.\root\cimv2")
    Set procs = svc.ExecQuery("SELECT CommandLine FROM Win32_Process WHERE Name='wscript.exe'")
    For Each p In procs
        If Not IsNull(p.CommandLine) Then
            If InStr(LCase(p.CommandLine), "watchdog.vbs") > 0 Then n = n + 1
        End If
    Next
    On Error Goto 0
    ' current process counts itself, so n > 1 means another instance exists
    AlreadyRunning = (n > 1)
End Function
