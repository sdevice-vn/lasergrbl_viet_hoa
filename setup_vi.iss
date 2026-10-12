; Bo cai LaserGRBL Tieng Viet - bien dich bang Inno Setup trong workflow GitHub.
; Duong dan tinh tu thu muc chua file nay; ma nguon goc nam trong thu muc "lasergrbl".

#define MyAppName "LaserGRBL (Viet hoa)"
#define MyAppExeName "LaserGRBL.exe"
#define MyBuildDir "lasergrbl\LaserGRBL\bin\Release"
#define MyAppVersion GetFileVersion(MyBuildDir + "\" + MyAppExeName)

[Setup]
AppId={{8E1F3C52-6B7A-4D0E-9C41-5A2D7F3B91E6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=LaserGRBL
AppPublisherURL=https://lasergrbl.com
DefaultDirName={autopf}\LaserGRBL-VN
DisableProgramGroupPage=yes
OutputDir=output
OutputBaseFilename=LaserGRBL_TiengViet_Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=lasergrbl\install.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Mac dinh TICH SAN de tao bieu tuong ngoai man hinh Desktop
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Excludes: "*.pdb"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "lasergrbl\lasergrblfile.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "lasergrbl\zippedbutton.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName} (disable opengl)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "nogl"
Name: "{autoprograms}\{#MyAppName} (soft opengl)"; Filename: "{app}\{#MyAppExeName}"; Parameters: "swgl"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,LaserGRBL}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCR; SubKey: ".nc"; ValueType: string; ValueData: "LaserGRBL gcode file"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL gcode file"; ValueType: string; ValueData: "GCode file for laser engraving"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL gcode file\Shell\Open\Command"; ValueType: string; ValueData: """{app}\LaserGRBL.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL gcode file\DefaultIcon"; ValueType: string; ValueData: "{app}\lasergrblfile.ico,0"; Flags: uninsdeletevalue

Root: HKCR; SubKey: ".zbn"; ValueType: string; ValueData: "LaserGRBL zipped button"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL zipped button"; ValueType: string; ValueData: "This file contains LaserGRBL custom buttons"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL zipped button\Shell\Open\Command"; ValueType: string; ValueData: """{app}\LaserGRBL.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL zipped button\DefaultIcon"; ValueType: string; ValueData: "{app}\zippedbutton.ico,0"; Flags: uninsdeletevalue

Root: HKCR; SubKey: ".lps"; ValueType: string; ValueData: "LaserGRBL Project file"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL Project file"; ValueType: string; ValueData: "Project file for laser engraving"; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL Project file\Shell\Open\Command"; ValueType: string; ValueData: """{app}\LaserGRBL.exe"" ""%1"""; Flags: uninsdeletekey
Root: HKCR; SubKey: "LaserGRBL Project file\DefaultIcon"; ValueType: string; ValueData: "{app}\lasergrblfile.ico,0"; Flags: uninsdeletevalue
