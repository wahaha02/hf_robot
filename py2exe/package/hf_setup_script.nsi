; 该脚本使用 HM VNISEdit 脚本编辑器向导产生

; 安装程序初始定义常量
!define PRODUCT_NAME "HF_ROBOT"
!define PRODUCT_VERSION "1.02"
!define PRODUCT_PUBLISHER "Alex"
!define PRODUCT_WEB_SITE "http://wahaha02.spaces.live.com "
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\vcredist_x86.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

SetCompressor lzma

; ------ MUI 现代界面定义 (1.67 版本以上兼容) ------
!include "MUI.nsh"

; MUI 预定义常量

!define MUI_ABORTWARNING
!define MUI_ICON "hf.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; 欢迎页面
; 引号内为位图的路径，位图大小大约为165*298
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_WELCOMEPAGE_TITLE "\r\n　　　开心农场助手V${PRODUCT_VERSION}安装向导"
!define MUI_WELCOMEPAGE_TEXT  "　　开心农场助手是一款游戏辅助工具，旨在提高游戏效率，增强游戏体验。欢迎使用。\r\n\r\n　　软件作者：alex\r\n\r\n　　更新网址：wahaha02.spaces.live.com\r\n\r\n　　$_CLICK"
!insertmacro MUI_PAGE_WELCOME

; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY

; 安装过程页面
!insertmacro MUI_PAGE_INSTFILES

; 安装完成页面
;------------------------------------------------------
!define MUI_FINISHPAGE_RUN "$INSTDIR\hf_robot.exe"
;------------------------------------------------------
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\conf\conf.ini"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "查看 配置文件"
;------------------------------------------------------
!define MUI_FINISHPAGE_LINK_LOCATION "$INSTDIR\${PRODUCT_NAME}.url"
!define MUI_FINISHPAGE_LINK "查看 更新主页"
;------------------------------------------------------
!insertmacro MUI_PAGE_FINISH

; 安装卸载过程页面
!insertmacro MUI_UNPAGE_INSTFILES

; 安装界面包含的语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装预释放文件
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS
; ------ MUI 现代界面定义结束 ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "HF_ROBOT_${PRODUCT_VERSION}_Setup.exe"
InstallDir "$PROGRAMFILES\HF_ROBOT"
InstallDirRegKey HKLM "${PRODUCT_UNINST_KEY}" "UninstallString"
ShowInstDetails show
ShowUnInstDetails show
BrandingText "开心农场助手V${PRODUCT_VERSION}"
DirText "安装程序将安装 $(^NameDA) 在下列文件夹。要安装到不同文件夹，单击 [浏览(B)] 并选择其他的文件夹。 $_CLICK"

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
 *  以下是安装程序的卸载部分  *
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

#-- 根据 NSIS 脚本编辑规则，所有 Function 区段必须放置在 Section 区段之后编写，以避免安装程序出现未可预知的问题。--#

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "你确实要完全移除 $(^Name) ，及其所有的组件？" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) 已成功地从你的计算机移除。"
FunctionEnd
