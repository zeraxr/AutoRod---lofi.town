; =====================================================================
; Script Inno Setup 6 para AutoRod v2.0
; Asistente de Instalación Profesional para Windows
; =====================================================================

#define MyAppName "AutoRod"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "AutoRod Open Source Project"
#define MyAppURL "https://github.com/zeraxr/AutoRod"
#define MyAppExeName "AutoRod.exe"

[Setup]
; Identificador único de aplicación (GUID)
AppId={{5E7989C6-B68C-4D2A-94A1-2C67B340D4A0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Instalación por usuario predeterminada: no requiere permisos de administrador (UAC),
; eliminando fricciones de seguridad y alertas innecesarias de Windows.
; Permite opcionalmente al usuario instalar a nivel de sistema si lo desea.
DefaultDirName={localappdata}\Programs\{#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Iconos e imágenes del asistente
SetupIconFile=..\..\src\autorod\assets\icons\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compresión sólida y moderna
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Archivo de salida
OutputDir=..\..\dist_installer
OutputBaseFilename=AutoRod-v{#MyAppVersion}-Setup

; Gestión de procesos en ejecución (cierre limpio en caso de actualización)
CloseApplications=yes
CloseApplicationsFilter=*{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Archivos binarios del paquete compilado por PyInstaller
Source: "..\..\dist\AutoRod\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Archivo de configuración: no sobrescribir si el usuario ya personalizó sus valores
Source: "..\..\config.toml"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpieza de logs y temporales generados en tiempo de ejecución
Type: filesandordirs; Name: "{app}\logs"
