;--------------------------------
;Include Modern UI

  !include "MUI2.nsh"


;--------------------------------
;General

  ;Properly display all languages
  Unicode true

  ;Define name of the product
  !define PRODUCT "ethz-document-fetcher"


  ;Define the main name of the installer
  Name "${PRODUCT}"

  ;Define the directory where the installer should be saved
  OutFile ".\..\${PRODUCT}-windows-x86-64-installer.exe"


  ;Define the default installation folder (Windows ProgramFiles example)
  InstallDir "$PROGRAMFILES64\${PRODUCT}"

  ;Define optional a directory for program files that change (Windows AppData example)
  !define INSTDIR_DATA "$APPDATA\${PRODUCT}"


  ;Request rights if you want to install the program to program files
  RequestExecutionLevel admin

  ;Properly display all languages
  Unicode true


  ;Show 'console' in installer and uninstaller
  ShowInstDetails "show"
  ShowUninstDetails "show"

  ;Get installation folder from registry if available
  InstallDirRegKey HKLM "Software\${PRODUCT}" ""


;--------------------------------
;Interface Settings

  ;Show warning if user wants to abort
  !define MUI_ABORTWARNING

  ;Show all languages, despite user's codepage
  !define MUI_LANGDLL_ALLLANGUAGES

  ;Use optional a custom icon:
  #!define MUI_ICON "..\example_resources\example_icon_installer.ico" # for the Installer
  #!define MUI_UNICON "..\example_resources\example_icon_uninstaller.ico" # for the later created UnInstaller

  ;Use optional a custom picture for the 'Welcome' and 'Finish' page:
  #!define MUI_HEADERIMAGE_RIGHT
  #!define MUI_WELCOMEFINISHPAGE_BITMAP "..\example_resources\example_picture_installer.bmp"  # for the Installer
  #!define MUI_UNWELCOMEFINISHPAGE_BITMAP "..\example_resources\example_picture_uninstaller.bmp"  # for the later created UnInstaller

  ;Optional no descripton for all components
  !define MUI_COMPONENTSPAGE_NODESC


;--------------------------------
;Pages

  ;For the installer
  !insertmacro MUI_PAGE_WELCOME # simply remove this and other pages if you don't want it
  !insertmacro MUI_PAGE_LICENSE ".\..\LICENSE" # link to an ANSI encoded license file
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  ;For the uninstaller
  !insertmacro MUI_UNPAGE_WELCOME
  !insertmacro MUI_UNPAGE_COMPONENTS
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  !insertmacro MUI_UNPAGE_FINISH


;--------------------------------
;Languages

  ;At start will be searched if the current system language is in this list,
  ;if not the first language in this list will be chosen as language
  !insertmacro MUI_LANGUAGE "English"


;--------------------------------
;Installer Section

Section "Main Component"
  SectionIn RO # Just means if in component mode this is locked

  ;Set output path to the installation directory.
  SetOutPath $INSTDIR

  ;Put the following file in the SetOutPath
  File /r ".\..\distwin\ethz-document-fetcher\*.*"

  ;Store installation folder in registry
  WriteRegStr HKLM "Software\${PRODUCT}" "" $INSTDIR

  ;Registry information for add/remove programs
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "DisplayName" "${PRODUCT}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "UninstallString" '"$INSTDIR\${PRODUCT}-uninstaller.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" "NoRepair" 1

  ;Create optional start menu shortcut for uninstaller and Main component
  CreateDirectory "$SMPROGRAMS\${PRODUCT}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT}\ethz-document-fetcher.lnk" "$INSTDIR\ethz-document-fetcher.exe" "" "$INSTDIR\ethz-document-fetcher.exe " 0


  ApplicationID::Set "$SMPROGRAMS\${PRODUCT}\ethz-document-fetcher.lnk" "ethz-document-fetcher.ethz-document-fetcher"

  ;Create uninstaller
  WriteUninstaller "${PRODUCT}-uninstaller.exe"

SectionEnd


;--------------------------------
;Uninstaller Section

Section "un.Main"
  SectionIn RO

  ;Remove all registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"
  DeleteRegKey HKLM "Software\${PRODUCT}"

  ;Delete the installation directory + all files in it
  ;Add 'RMDir /r "$INSTDIR\folder\*.*"' for every folder you have added additionaly
  RMDir /r "$INSTDIR\*.*"
  RMDir "$INSTDIR"

  ;Delete Start Menu Shortcuts
  Delete "$SMPROGRAMS\${PRODUCT}\*.*"
  RmDir  "$SMPROGRAMS\${PRODUCT}"

SectionEnd

Section /o "un.Settings/Config/Cache"
  SectionIn 1

  ;Delete the appdata directory + files
  RMDir /r "${INSTDIR_DATA}\*.*"
  RMDir "${INSTDIR_DATA}"

SectionEnd