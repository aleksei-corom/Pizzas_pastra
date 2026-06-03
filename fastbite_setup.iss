; ============================================================
;  FastBite POS — Inno Setup Installer Script
;  Compilar con Inno Setup Compiler 6.x+
; ============================================================

#define MyAppName      "FastBite POS"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "FastBite"
#define MyAppExeName   "FastBitePOS.exe"
#define MyAppDir       "FastBite POS"

[Setup]
AppId={{A3F8C2D1-7B44-4E90-9C5F-2E1D0B8A3F67}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppDir}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=FastBite_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
; No necesita privilegios de administrador si se instala en AppData
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Copiar el ejecutable y todos los recursos de la carpeta dist\
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}";      FileName: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; FileName: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";    FileName: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Accesos directos:"

; ============================================================
;  Pascal Script — Páginas personalizadas para la configuración
;  inicial (nombre del negocio, usuario admin y contraseña).
;  Al finalizar la instalación, escribe los datos en
;  setup_init.ini dentro de la carpeta de instalación.
; ============================================================
[Code]

var
  PageBusiness : TWizardPage;
  PageAdmin    : TWizardPage;

  edtBusinessName    : TEdit;
  edtAdminUsername   : TEdit;
  edtAdminPassword   : TEdit;
  edtAdminPassword2  : TEdit;
  lblPassMatch       : TLabel;

{ --- Crear páginas personalizadas --- }
procedure InitializeWizard;
begin
  { Página 1: Nombre del Negocio }
  PageBusiness := CreateCustomPage(
    wpSelectDir,
    'Configuración del Negocio',
    'Ingrese el nombre de su negocio. Este aparecerá en los recibos y en la pantalla principal.'
  );

  with TLabel.Create(PageBusiness) do
  begin
    Parent  := PageBusiness.Surface;
    Caption := 'Nombre del Negocio:';
    Left    := 0;
    Top     := 8;
    Width   := PageBusiness.SurfaceWidth;
  end;

  edtBusinessName              := TEdit.Create(PageBusiness);
  edtBusinessName.Parent       := PageBusiness.Surface;
  edtBusinessName.Left         := 0;
  edtBusinessName.Top          := 28;
  edtBusinessName.Width        := PageBusiness.SurfaceWidth;
  edtBusinessName.Text         := 'Mi Negocio';

  { Página 2: Credenciales del Administrador }
  PageAdmin := CreateCustomPage(
    PageBusiness.ID,
    'Cuenta de Administrador',
    'Cree las credenciales del primer usuario administrador.'
  );

  with TLabel.Create(PageAdmin) do
  begin
    Parent  := PageAdmin.Surface;
    Caption := 'Usuario:';
    Left    := 0;
    Top     := 8;
    Width   := PageAdmin.SurfaceWidth;
  end;

  edtAdminUsername              := TEdit.Create(PageAdmin);
  edtAdminUsername.Parent       := PageAdmin.Surface;
  edtAdminUsername.Left         := 0;
  edtAdminUsername.Top          := 28;
  edtAdminUsername.Width        := PageAdmin.SurfaceWidth;
  edtAdminUsername.Text         := 'admin';

  with TLabel.Create(PageAdmin) do
  begin
    Parent  := PageAdmin.Surface;
    Caption := 'Contraseña:';
    Left    := 0;
    Top     := 68;
    Width   := PageAdmin.SurfaceWidth;
  end;

  edtAdminPassword              := TEdit.Create(PageAdmin);
  edtAdminPassword.Parent       := PageAdmin.Surface;
  edtAdminPassword.Left         := 0;
  edtAdminPassword.Top          := 88;
  edtAdminPassword.Width        := PageAdmin.SurfaceWidth;
  edtAdminPassword.PasswordChar := '*';

  with TLabel.Create(PageAdmin) do
  begin
    Parent  := PageAdmin.Surface;
    Caption := 'Repetir Contraseña:';
    Left    := 0;
    Top     := 128;
    Width   := PageAdmin.SurfaceWidth;
  end;

  edtAdminPassword2              := TEdit.Create(PageAdmin);
  edtAdminPassword2.Parent       := PageAdmin.Surface;
  edtAdminPassword2.Left         := 0;
  edtAdminPassword2.Top          := 148;
  edtAdminPassword2.Width        := PageAdmin.SurfaceWidth;
  edtAdminPassword2.PasswordChar := '*';

  { Etiqueta de validación de contraseña }
  lblPassMatch              := TLabel.Create(PageAdmin);
  lblPassMatch.Parent       := PageAdmin.Surface;
  lblPassMatch.Left         := 0;
  lblPassMatch.Top          := 188;
  lblPassMatch.Width        := PageAdmin.SurfaceWidth;
  lblPassMatch.Caption      := '';
  lblPassMatch.Font.Color   := clRed;
end;

{ --- Validación de páginas antes de avanzar --- }
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = PageBusiness.ID then
  begin
    if Trim(edtBusinessName.Text) = '' then
    begin
      MsgBox('Por favor, ingrese el nombre del negocio.', mbError, MB_OK);
      Result := False;
    end;
  end

  else if CurPageID = PageAdmin.ID then
  begin
    if Trim(edtAdminUsername.Text) = '' then
    begin
      MsgBox('Por favor, ingrese un nombre de usuario.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if Length(edtAdminPassword.Text) < 4 then
    begin
      MsgBox('La contraseña debe tener al menos 4 caracteres.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if edtAdminPassword.Text <> edtAdminPassword2.Text then
    begin
      lblPassMatch.Caption    := '⚠ Las contraseñas no coinciden.';
      lblPassMatch.Font.Color := clRed;
      MsgBox('Las contraseñas no coinciden. Por favor, verifique.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    lblPassMatch.Caption := '';
  end;
end;

{ --- Escribir setup_init.ini después de instalar los archivos --- }
procedure CurStepChanged(CurStep: TSetupStep);
var
  IniPath : String;
begin
  if CurStep = ssPostInstall then
  begin
    IniPath := ExpandConstant('{app}\setup_init.ini');

    SetIniString('Setup', 'BusinessName',   Trim(edtBusinessName.Text),   IniPath);
    SetIniString('Setup', 'AdminUsername',  Trim(edtAdminUsername.Text),  IniPath);
    SetIniString('Setup', 'AdminPassword',  edtAdminPassword.Text,        IniPath);

    Log('setup_init.ini escrito en: ' + IniPath);
  end;
end;
