' launch_hidden.vbs
Set WshShell = CreateObject("WScript.Shell")

' Launch the Flask backend using Waitress.
' Change the directory to your Backend folder then run the waitress command.
WshShell.Run "cmd /c cd /d D:\Dokumenty\GitHub\QuestDM\QuestDM\Backend && waitress-serve --listen=127.0.0.1:5000 app:app", 0, False

' Launch the Vue production preview.
' Change the directory to your Frontend folder then run npm run preview.
WshShell.Run "cmd /c cd /d D:\Dokumenty\GitHub\QuestDM\QuestDM\Frontend && npm run preview", 0, False
