; �ýű�ʹ�� HM VNISEdit �ű��༭���򵼲���

; ��װ�����ʼ���峣��
!define PRODUCT_NAME "HF_ROBOT"
!define PRODUCT_VERSION "1.02"
!define PRODUCT_PUBLISHER "Alex"
!define PRODUCT_WEB_SITE "http://wahaha02.spaces.live.com "
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\vcredist_x86.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; ------ MUI �ִ����涨�� (1.67 �汾���ϼ���) ------
!include "MUI.nsh"

; MUI Ԥ���峣��

!define MUI_ABORTWARNING
!define MUI_ICON "hf.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ��ӭҳ��
; ������Ϊλͼ��·����λͼ��С��ԼΪ165*298
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_WELCOMEPAGE_TITLE "\r\n����������ũ������V${PRODUCT_VERSION}��װ��"
!define MUI_WELCOMEPAGE_TEXT  "��������ũ��������һ����Ϸ�������ߣ�ּ�������ϷЧ�ʣ���ǿ��Ϸ���顣��ӭʹ�á�\r\n\r\n����������ߣ�alex\r\n\r\n����������ַ��wahaha02.spaces.live.com\r\n\r\n����$_CLICK"
!insertmacro MUI_PAGE_WELCOME

; ��װĿ¼ѡ��ҳ��
!insertmacro MUI_PAGE_DIRECTORY

; ��װ����ҳ��
!insertmacro MUI_PAGE_INSTFILES

; ��װ���ҳ��
;------------------------------------------------------
!define MUI_FINISHPAGE_RUN "$INSTDIR\hf_robot.exe"
;------------------------------------------------------
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\conf\conf.ini"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "�鿴 �����ļ�"
;------------------------------------------------------
!define MUI_FINISHPAGE_LINK_LOCATION "$INSTDIR\${PRODUCT_NAME}.url"
!define MUI_FINISHPAGE_LINK "�鿴 ������ҳ"
;------------------------------------------------------
!insertmacro MUI_PAGE_FINISH

; ��װж�ع���ҳ��
!insertmacro MUI_UNPAGE_INSTFILES

; ��װ�����������������
!insertmacro MUI_LANGUAGE "SimpChinese"

; ��װԤ�ͷ��ļ�
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS
; ------ MUI �ִ����涨����� ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "HF_ROBOT_${PRODUCT_VERSION}_Setup.exe"
InstallDir "$PROGRAMFILES\HF_ROBOT"
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
ShowInstDetails show
ShowUnInstDetails show
BrandingText "����ũ������V${PRODUCT_VERSION}"
DirText "��װ���򽫰�װ $(^NameDA) �������ļ��С�Ҫ��װ����ͬ�ļ��У����� [���(B)] ��ѡ���������ļ��С� $_CLICK"

Section "HF_ROBOT" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  File "vcredist_x86.exe"
  ExecWait "$INSTDIR\vcredist_x86.exe"
  
  SetOutPath "$INSTDIR\conf"
  File "..\dist\conf\conf.ini"
  File "..\dist\conf\logging.conf"
  SetOutPath "$INSTDIR"
  File "..\dist\hf_robot.exe"
  
  CreateShortCut "$DESKTOP\hf_robot.exe.lnk" "$INSTDIR\hf_robot.exe"
  
SectionEnd

Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
  CreateDirectory "$SMPROGRAMS\HF_ROBOT"
  CreateShortCut "$SMPROGRAMS\HF_ROBOT\hf_robot.exe.lnk" "$INSTDIR\hf_robot.exe"
  CreateShortCut "$SMPROGRAMS\HF_ROBOT\conf.ini.lnk" "$INSTDIR\conf\conf.ini"
  CreateShortCut "$SMPROGRAMS\HF_ROBOT\Website.lnk" "$INSTDIR\${PRODUCT_NAME}.url"
  CreateShortCut "$SMPROGRAMS\HF_ROBOT\Uninstall.lnk" "$INSTDIR\uninst.exe"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\vcredist_x86.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\vcredist_x86.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
SectionEnd

/******************************
 *  �����ǰ�װ�����ж�ز���  *
 ******************************/

Section Uninstall
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  Delete "$INSTDIR\hf_robot.exe"
  Delete "$INSTDIR\conf\logging.conf"
  Delete "$INSTDIR\conf\conf.ini"
  Delete "$INSTDIR\vcredist_x86.exe"

  Delete "$SMPROGRAMS\HF_ROBOT\Uninstall.lnk"
  Delete "$SMPROGRAMS\HF_ROBOT\Website.lnk"
  Delete "$SMPROGRAMS\HF_ROBOT\hf_robot.exe.lnk"
  Delete "$SMPROGRAMS\HF_ROBOT\conf.ini.lnk"
  Delete "$DESKTOP\hf_robot.exe.lnk"

  RMDir "$SMPROGRAMS\HF_ROBOT"
  RMDir "$INSTDIR\conf"
  RMDir ""

  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  SetAutoClose true
SectionEnd

#-- ���� NSIS �ű��༭�������� Function ���α�������� Section ����֮���д���Ա��ⰲװ�������δ��Ԥ֪�����⡣--#

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "��ȷʵҪ��ȫ�Ƴ� $(^Name) ���������е������" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) �ѳɹ��ش���ļ�����Ƴ���"
FunctionEnd
