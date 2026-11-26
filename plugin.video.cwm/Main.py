import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import os
import sys
import time
import pyxbmct
import requests
from resources.libs import net  # default timeout for every request
import xbmcvfs
from resources.libs import look  # one text colour: strips [COLOR]/[B]/[I] from all window text
import Cats
from datetime import datetime
import random
import string
import re
####################################################################
###########################CUSTOM OPTIONS###########################
_addon_id_	= 'plugin.video.cwm'
MainTextColour = 'gold'
AddonTitle = ('[COLOR %s][B]Cum With Me[/B][/COLOR]' % MainTextColour)
####################################################################
_self_		= xbmcaddon.Addon(id=_addon_id_)
_images_	= '/resources/artwork/'
dialog = look.PlainDialog()
Date = time.strftime("%d/%m")
get_setting = _self_.getSetting
set_setting = _self_.setSetting
Skin_Path = xbmcvfs.translatePath(os.path.join('special://home/addons/' + _addon_id_ + _images_))
Icon			= xbmcvfs.translatePath(os.path.join('special://home/addons/' + _addon_id_, 'icon.png'))
AddonIcon		= xbmcvfs.translatePath(os.path.join('special://home/addons/' + _addon_id_, 'icon.png'))
FanArt			= xbmcvfs.translatePath(os.path.join('special://home/addons/' + _addon_id_, 'fanart.jpg'))
Background_Image	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'AddonBG.png'))
AppIcon	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'AppIconRound.png'))  # smaller, rounded corners
AppTitle	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'AppTitle3.gif'))
LiveF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'LiveF1.png'))
LiveNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'LiveNF.png'))
CamF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'CamF1.png'))
CamNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'CamNF.png'))
MoviesF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'MoviesF1.png'))
MoviesNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'MoviesNF.png'))
SitesF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'SitesF1.png'))
SitesNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'SitesNF.png'))
ExitF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'ExitF1.png'))
ExitNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'ExitNF.png'))
SendF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'MessageF1.png'))
SendNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'MessageNF.png'))
RefreshF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'RefreshF1.png'))
RefreshNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'RefreshNF.png'))
UserF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'UserchangeF2.png'))
UserNF	= xbmcvfs.translatePath(os.path.join(Skin_Path, 'UserchangeNF1.png'))
BackgroundBox = xbmcvfs.translatePath(os.path.join(Skin_Path, 'BackBox.png'))
AddonInfoUrl = 'https://pinsystem.co.uk/CumWithMe/CumWithMeNotice.txt'
ChatMsgsUrl = 'https://pinsystem.co.uk/CumWithMe/Chat/getmsg.php'
ChatMsgSendurl = 'https://pinsystem.co.uk/CumWithMe/Chat/addmsg.php?user=%s&msg=%s'
ApiUrl = 'https://pinsystem.co.uk/CumWithMe/api.php'
CheckMonitor = get_setting('Monitor')
if CheckMonitor == 'false': CheckMon = '[COLOR red]OFF[/COLOR]'
if CheckMonitor == 'true': CheckMon = '[COLOR lime]ON[/COLOR]'
# CheckPin() removed: it required an access token from pinsystem.co.uk on every launch
def MainWindow():
    window = Main('cwm')
    window.doModal()
    del window
def MoveToCat(self,option):
    ApiInfo(self)
    Cats.MainWindow(option)
def tick(self):
    time2 = time.strftime("%I:%M %p")
    self.TIME.setLabel(str(time2))
def QuitAddon(self):
    self.close()
def GetAddonInfo(self):
    try:
        link = requests.get(AddonInfoUrl).text
    except Exception as e:
        xbmc.log('CWM: notice unavailable :: %s' % e, xbmc.LOGINFO)
        link = 'Cum With Me (Kodi 22 / 23 patched build)'
    self.AddonTextInfo.setText(link)
def GetChatMsgs(self):
    ApiInfo(self)
    chatboxshow = get_setting('ShowChat')
    if chatboxshow == 'true':
        try:
            link = requests.get(ChatMsgsUrl).json()
            messages = []
            reservednames = ["nemzzy", "nemzzzy", "nemzzyy","nemesis","nemzzy668","manc","_manc","_manc_","lordjd","jdlord"]
            for i in link:
                Name = i['items']['Name']
                Message = i['items']['Message']
                Time = i['items']['Time']
                if any(x in Name.lower() for x in reservednames):
                    Msg = ('[COLOR magenta]%s : [COLOR purple]%s -  [COLOR white]%s[/COLOR]\n' % (Time,Name,Message))
                else:
                    Msg = ('[COLOR magenta]%s : [COLOR green]%s -  [COLOR white]%s[/COLOR]\n' % (Time,Name,Message))
                messages.append(Msg)
            chatstring = ''
            for message in messages:
                chatstring = chatstring+message
            self.ChatBox.setText(chatstring)
            dialog.notification(AddonTitle, '[COLOR pink]Chat Window Refreshed[/COLOR]', AddonIcon, 2500)
            GetAddonInfo(self)
        except:
            self.ChatBox.setText('[COLOR magenta]Admin Message : [COLOR purple]Nemzzy -  [COLOR white]Welcome to CumWithMe, Enjoy the chat room, don\'t be a keyboard warrior! Your not hard, not yet anyway! Enjoy the porn[/COLOR]\n')
    else:
        self.ChatBox.setText('[COLOR magenta]Admin Message : [COLOR purple]Nemzzy -  [COLOR white]You\'ve turned chat off in settings, turn on again to show messages[/COLOR]\n')
def SendChatMsg(self):
    checkusername = get_setting('Username')
    reservednames = ["nemzzy", "nemzzzy", "nemzzyy","nemesis","nemzzy668","manc","_manc","_manc_","lordjd","jdlord","admin","nemz","jd","nemz","streamarmy","streamarmyteam","streamarmyadmin","adminstreamarmy"]
    if any(x in checkusername.lower() for x in reservednames):
        checkadmin = get_setting('adminchatpass')
        if checkadmin.lower() == 'manclovescock': pass
        else:
            dialog.ok(AddonTitle,"You have tried to use a name reserved for Stream Army Team Members, Please enter the password to continue")
            string =''
            keyboard = xbmc.Keyboard(string, 'Enter Password')
            keyboard.doModal()
            if keyboard.isConfirmed():
                string = keyboard.getText()
                if string.lower() == 'manclovescock':
                    set_setting(id='adminchatpass', value=string.lower())
                    SendChatMsg(self)
                else:
                    dialog.ok(AddonTitle,"Wrong Password, Please Choose A Different Chat Name")
                    set_setting(id='Username', value='')
                    SendChatMsg(self)
            else: return  # was quit(): that killed the whole add-on from inside the window
    if checkusername == '':
        string =''
        keyboard = xbmc.Keyboard(string, 'You need to set a chat username first ( Some Admin Names reserved! )')
        keyboard.doModal()
        if keyboard.isConfirmed():
            string = keyboard.getText()
            if len(string)>1:
                term = string.lower()
                if not any(x in term.lower() for x in reservednames):
                    if len(string)>1:
                        set_setting(id='Username', value=string.title())
                        SendChatMsg(self)
                else:
                    dialog.ok(AddonTitle,"You have tried to use a name reserved for Stream Army Team Members, Please enter the password to continue")
                    stringpass =''
                    keyboard = xbmc.Keyboard(stringpass, 'Enter Password')
                    keyboard.doModal()
                    if keyboard.isConfirmed():
                        stringpass = keyboard.getText()
                        if stringpass.lower() == 'manclovescock':
                            set_setting(id='adminchatpass', value=stringpass.lower())
                            set_setting(id='Username', value=string.title())
                            SendChatMsg(self)
                        else:
                            dialog.ok(AddonTitle,"Wrong Password, Please Choose A Different Chat Name")
                            SendChatMsg(self)
        else: return  # was quit(): that killed the whole add-on from inside the window
    else:
        string =''
        keyboard = xbmc.Keyboard(string, 'Type Chat Message ( Don\'t be offensive )')
        keyboard.doModal()
        if keyboard.isConfirmed():
            string = keyboard.getText()
            if len(string)>1:
                term = string.lower()
                term = term.replace(' ','%20')
                try:
                    sendmessage = requests.get(ChatMsgSendurl % (checkusername,term))
                except Exception as e:
                    xbmc.log('CWM: chat send failed :: %s' % e, xbmc.LOGINFO)
                    dialog.notification(AddonTitle, 'Chat is unavailable right now', AddonIcon, 2500)
                    return
                dialog.notification(AddonTitle, '[COLOR pink]Message Sent[/COLOR]', AddonIcon, 2500)
                GetChatMsgs(self)
            else:
                dialog.notification(AddonTitle, '[COLOR pink]Message needs to be longer[/COLOR]', AddonIcon, 2500)
def RandomUserID(self):
    pass  # used to register a random user ID with pinsystem.co.uk on every launch (usage tracking); removed
def ApiInfo(self):
    try:
        link = requests.get(ApiUrl).json()
        for data in link:
            usersonline = data['usercount']['Users']
            camsonline = data['usercount']['CamsOnline']
            videos = data['usercount']['Videos']
            self.USERS.setLabel('Current Cummers Online : %s' % usersonline)
            self.CHANNELS.setLabel('Live Cams Online : %s' % camsonline)
            self.MOVIES.setLabel('Movies Available : %s' % videos)
    except: pass
def ChangeUserName(self):
    reservednames = ["nemzzy", "nemzzzy", "nemzzyy","nemesis","nemzzy668","manc","_manc","_manc_","lordjd","jdlord","admin","nemz","jd","nemz","streamarmy","streamarmyteam","streamarmyadmin","adminstreamarmy"]
    string =''
    keyboard = xbmc.Keyboard(string, 'Change User Name')
    keyboard.doModal()
    if keyboard.isConfirmed():
        string = keyboard.getText()
        if len(string)>3:
            term = string.title()
            if any(x in term.lower() for x in reservednames):
                checkadmin = get_setting('adminchatpass')
                if checkadmin.lower() == 'manclovescock':
                    set_setting('Username', term)
                    dialog.notification(AddonTitle, '[COLOR pink]Username Set[/COLOR]', AddonIcon, 2500)
                else:
                    dialog.ok(AddonTitle,"You have tried to use a name reserved for Stream Army Team Members, Please enter the password to continue")
                    string =''
                    keyboard = xbmc.Keyboard(string, 'Enter Password')
                    keyboard.doModal()
                    if keyboard.isConfirmed():
                        string = keyboard.getText()
                        if string.lower() == 'manclovescock':
                            set_setting(id='adminchatpass', value=string.lower())
                            set_setting('Username', term)
                            dialog.notification(AddonTitle, '[COLOR pink]Username Set[/COLOR]', AddonIcon, 2500)
                        else:
                            dialog.ok(AddonTitle,"Wrong Password, Please Choose A Different Chat Name")
                            set_setting(id='Username', value='')
                            ChangeUserName(self)
                    else: return  # was quit(): that killed the whole add-on from inside the window
            else:
                set_setting('Username', term)
                dialog.notification(AddonTitle, '[COLOR pink]Username Set[/COLOR]', AddonIcon, 2500)
        else:
            dialog.notification(AddonTitle, '[COLOR pink]Username needs to be longer[/COLOR]', AddonIcon, 2500)
def ScraperCheck(self):
    try:
        scrapertheirs = xbmcvfs.translatePath(os.path.join('special://home/addons/' + 'script.cwm.scrapers', 'addon.xml'))
        with open (scrapertheirs) as f:
            yourversion = re.findall('<addon id="script.cwm.scrapers".*?version="(.*?)"',f.read(),flags=re.DOTALL)[0]
        # no online version check: this build is updated from the Howarddj repository
        self.ScraperInfo = pyxbmct.Label('Scrapers : %s' % yourversion, textColor='0xFFFFFFFF', font='font12', alignment=pyxbmct.ALIGN_CENTER)
        self.placeControl(self.ScraperInfo,  12, 10, 12, 40)
    except:
        self.ScraperInfo = pyxbmct.Label('Scrapers : not installed', textColor='0xFFFFFFFF', font='font12')
        self.placeControl(self.ScraperInfo,  12, 10, 12, 40)
class Main(pyxbmct.AddonFullWindow):
    xbmc.executebuiltin("Dialog.Close(busydialog)")
    def __init__(self, title='cwm'):
        super(Main, self).__init__(title)
        self.setGeometry(1280, 720,150, 50)
        # no background image: pyxbmct's plain dark window background shows instead
        self.set_info_controls()
        self.set_active_controls()
        self.set_navigation()
        self.connect(pyxbmct.ACTION_NAV_BACK, lambda:QuitAddon(self))
        AppLogo = pyxbmct.Image(AppIcon, aspectRatio=2)
        self.placeControl(AppLogo, -8, 46, 20, 4)
        AppHeader = pyxbmct.Label('Cum With Me', textColor=look.TEXT_COLOUR, font='font13_title')
        self.placeControl(AppHeader, -8, 0, 12, 20)
        self.AddonInfo = pyxbmct.Label('ADDON INFORMATION',textColor='0xFFFFFFFF', font='font14')
        self.placeControl(self.AddonInfo,  20, 26, 12, 15)
        self.ChatInfo = pyxbmct.Label('CHAT ROOM',textColor='0xFFFFFFFF', font='font14')
        self.placeControl(self.ChatInfo,  84, 26, 12, 15)
        self.AddonTextInfo	=	pyxbmct.TextBox()
        self.placeControl(self.AddonTextInfo, 26, 14, 60, 34)
        self.AddonTextInfo.autoScroll(1000, 1500, 2000)
        GetAddonInfo(self)
        self.setFocus(self.LiveChanBut)
        RandomUserID(self)
        self.ChatBox	=	pyxbmct.TextBox()
        self.placeControl(self.ChatBox, 90, 14, 54, 34)
        self.ChatBox.autoScroll(2000, 800, 2000)
        GetChatMsgs(self)
        ScraperCheck(self)
    def set_info_controls(self):
        self.TIME = pyxbmct.Label('',textColor='0xFFFFFFFF', font='font14')
        self.USERS = pyxbmct.Label('',textColor='0xFFFFFFFF', font='font14')
        self.CHANNELS = pyxbmct.Label('',textColor='0xFFFFFFFF', font='font14')
        self.MonitorStatus = pyxbmct.Label('',textColor='0xFFFFFFFF', font='font14')
        self.MOVIES = pyxbmct.Label('',textColor='0xFFFFFFFF', font='font14')
        self.placeControl(self.TIME, 158,47, 12, 10)
        self.placeControl(self.USERS, 158,0, 12, 20)
        self.placeControl(self.CHANNELS, 150,0, 12, 20)
        self.placeControl(self.MonitorStatus, 150,10, 12, 20)
        self.placeControl(self.MOVIES, 142,0, 12, 20)
        time2 = time.strftime("%I:%M %p")
        self.TIME.setLabel(str(time2))
        self.USERS.setLabel('Current Cummers Online : ')
        self.CHANNELS.setLabel('Live Cams Available : ')
        self.MonitorStatus.setLabel(' | Monitor Status : %s' % CheckMon)
        self.MOVIES.setLabel('Movies Available : ')
    def Multi_Update(self):
        tick(self)
    def set_active_controls(self):
        # T L W H
        self.LiveChanBut = look.button('Live XXX Channels')
        self.placeControl(self.LiveChanBut, 34, 0, 14, 10)
        self.LiveCamBut = look.button('Live XXX Cams')
        self.placeControl(self.LiveCamBut, 51, 0, 14, 10)
        self.LiveMovieBut = look.button('XXX Movies')
        self.placeControl(self.LiveMovieBut, 68, 0, 14, 10)
        self.LiveSiteBut = look.button('XXX Sites')
        self.placeControl(self.LiveSiteBut, 85, 0, 14, 10)
        self.ExitSiteBut = look.button('Exit')
        self.placeControl(self.ExitSiteBut, 102, 0, 14, 10)
        self.RefMsgBut = look.button('Refresh Chat')
        self.placeControl(self.RefMsgBut, 146, 14, 11, 7)
        self.ChangeUserBut = look.button('Change Name')
        self.placeControl(self.ChangeUserBut, 146, 22, 11, 7)
        self.SendMsgBut = look.button('Send Message')
        self.placeControl(self.SendMsgBut, 146, 30, 11, 7)
        self.connect(self.ExitSiteBut, lambda:QuitAddon(self))
        self.connect(self.LiveChanBut, lambda:MoveToCat(self,'Live'))
        self.connect(self.LiveCamBut, lambda:MoveToCat(self,'Cam'))
        self.connect(self.LiveMovieBut, lambda:MoveToCat(self,'Movie'))
        self.connect(self.LiveSiteBut, lambda:MoveToCat(self,'Sites'))
        self.connect(self.RefMsgBut, lambda:GetChatMsgs(self))
        self.connect(self.SendMsgBut, lambda:SendChatMsg(self))
        self.connect(self.ChangeUserBut, lambda:ChangeUserName(self))
        self.connectEventList(
            [pyxbmct.ACTION_MOVE_DOWN,
            pyxbmct.ACTION_MOVE_UP,
            pyxbmct.ACTION_MOUSE_WHEEL_DOWN,
            pyxbmct.ACTION_MOUSE_WHEEL_UP,
            pyxbmct.ACTION_MOUSE_MOVE],
            self.Multi_Update)
    def set_navigation(self):
        #DOWN
        self.LiveChanBut.controlDown(self.LiveCamBut)
        self.LiveCamBut.controlDown(self.LiveMovieBut)
        self.LiveMovieBut.controlDown(self.LiveSiteBut)
        self.LiveSiteBut.controlDown(self.ExitSiteBut)
        #UP
        self.ExitSiteBut.controlUp(self.LiveSiteBut)
        self.LiveSiteBut.controlUp(self.LiveMovieBut)
        self.LiveMovieBut.controlUp(self.LiveCamBut)
        self.LiveCamBut.controlUp(self.LiveChanBut)
        #RIGHT
        self.LiveChanBut.controlRight(self.RefMsgBut)
        self.LiveCamBut.controlRight(self.RefMsgBut)
        self.LiveMovieBut.controlRight(self.RefMsgBut)
        self.LiveSiteBut.controlRight(self.RefMsgBut)
        self.ExitSiteBut.controlRight(self.RefMsgBut)
        self.RefMsgBut.controlRight(self.ChangeUserBut)
        self.ChangeUserBut.controlRight(self.SendMsgBut)
        #LEFT
        self.SendMsgBut.controlLeft(self.ChangeUserBut)
        self.RefMsgBut.controlLeft(self.LiveChanBut)
        self.ChangeUserBut.controlLeft(self.RefMsgBut)

    def list_update(self):
        pass
def _handle():
    try: return int(sys.argv[1])
    except (IndexError, ValueError): return -1


if __name__ == '__main__':
    try:
        MainWindow()
    finally:
        # Kodi opened this as a plugin folder; tell it there is no listing so it stays where it
        # was. (Replaces Container.Update(path,replace), which pointed Kodi at a folder called "path".)
        if _handle() >= 0:
            xbmcplugin.endOfDirectory(_handle(), succeeded=False, cacheToDisc=False)