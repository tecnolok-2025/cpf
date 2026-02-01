; =========================
; CPF - Instalador sin admin (per-user)
; =========================

[Setup]
AppId={{9B2F3D1C-3C3E-4B2E-9D77-CPF000000001}}
AppName=CPF
AppVersion=1.0.0
AppPublisher=Tecnolok
DefaultDirName={localappdata}\CPF
DefaultGroupName=CPF
DisableProgramGroupPage=yes

; CLAVE: evita UAC / admin
PrivilegesRequired=lowest

; Recomendado
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Salida del instalador (esto debe coincidir con tu workflow)
OutputDir=Output
OutputBaseFilename=CPF-Instalador

; Opcional: si no querés que se pueda elegir carpeta
; DisableDirPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Toma el exe que genera PyInstaller en el workflow
Source: "dist\CPF.exe"; DestDir: "{app}"; Flags: ignoreversion
; (Opcional) Si luego agregás ícono:
; Source: "assets\cpf.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\CPF"; Filename: "{app}\CPF.exe"
Name: "{userdesktop}\CPF"; Filename: "{app}\CPF.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear ícono en el Escritorio"; GroupDescription: "Accesos directos:"; Flags: checkedonce

[Run]
Filename: "{app}\CPF.exe"; Description: "Abrir CPF ahora"; Flags: nowait postinstall skipifsilent
