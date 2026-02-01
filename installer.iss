[Setup]
AppId={{9A3E7B50-CPF-APP-2026}}
AppName=CPF
AppVersion=1.0.0
DefaultDirName={localappdata}\CPF
DefaultGroupName=CPF
UninstallDisplayIcon={app}\CPF.exe
OutputDir=Output
OutputBaseFilename=CPF-Instalador
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "dist\CPF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CPF"; Filename: "{app}\CPF.exe"
Name: "{userdesktop}\CPF"; Filename: "{app}\CPF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el Escritorio"; GroupDescription: "Accesos directos"
