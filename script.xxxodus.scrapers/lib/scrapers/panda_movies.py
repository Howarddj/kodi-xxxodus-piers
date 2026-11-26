from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
from six.moves.urllib.parse import parse_qs, quote_plus, urlparse, parse_qsl, urljoin
from six import PY2
from resources.lib.modules import lover
from resources.lib.modules import utils
from resources.lib.modules import helper
import log_utils
import kodi
import client
import dom_parser2, os,re
import requests
from bs4 import BeautifulSoup
dialog = xbmcgui.Dialog()

headers = {'User-Agent' : 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'}
buildDirectory = utils.buildDir #CODE BY NEMZZY AND ECHO
translatePath = xbmc.translatePath if PY2 else xbmcvfs.translatePath
filename     = 'pandamovie'
base_domain  = 'https://pandamovies.pw/'  # pandamovies.me answers 'Access denied' (Cloudflare) from the UK
base_name    = base_domain.replace('www.',''); base_name = re.findall('(?:\\/\\/|\\.)([^.]+)\\.',base_name)[0].title()
type         = 'movies'
menu_mode    = 297
content_mode = 298
player_mode  = 810

search_tag   = 0
search_base  = urljoin(base_domain,'?s=%s')

@utils.url_dispatcher.register('%s' % menu_mode)
def menu():
    
	lover.checkupdates()
	url = urljoin(base_domain,'movies')
	content(url)
	# try:
		# url = urljoin(base_domain,'xxx/movies/')
		# c = client.request(url)
		# r = re.findall('<div\s+class="mepo">(.*?)<div\s+class="rating">',c, flags=re.DOTALL)
		# if ( not r ):
			# log_utils.log('Scraping Error in %s:: Content of request: %s' % (base_name.title(),str(link)[:1000]), log_utils.LOGERROR)
			# kodi.notify(msg='Scraping Error: Info Added To Log File', duration=6000, sound=True)
			# quit()
	# except Exception as e:
		# log_utils.log('Fatal Error in %s:: Error: %s' % (base_name.title(),str(e)), log_utils.LOGERROR)
		# kodi.notify(msg='Fatal Error', duration=4000, sound=True)
		# quit()

	# dirlst = []

	# for i in r:
		# try:
			# name = re.findall('<h3><a href=".+?">(.*?)</a>',i,flags=re.DOTALL)[0]
			# url = re.findall('<h3><a href="(.*?)"',i,flags=re.DOTALL)[0]
			# icon = re.findall('<img src="(.*?)"',i,flags=re.DOTALL)[0]
			# desc = re.findall('<div class="texto">(.*?)</div>',i,flags=re.DOTALL)[0]
			# fanarts = translatePath(os.path.join('special://home/addons/script.xxxodus.artwork', 'resources/art/%s/fanart.jpg' % filename))
			# dirlst.append({'name': name, 'url': url, 'mode': content_mode, 'icon': icon, 'description': desc, 'fanart': fanarts ,'folder': True})
		# except Exception as e:
			# log_utils.log('Error adding a menu item in %s:: Error: %s' % (base_name.title(),str(e)), log_utils.LOGERROR)

	# if dirlst: buildDirectory(dirlst)    
	# else:
		# kodi.notify(msg='No Menu Items Found')
		# quit()
        
@utils.url_dispatcher.register('%s' % content_mode,['url'],['searched'])
def content(url,searched=False):
    try:
        if url == '':
            url = urljoin(base_domain,'movies')
        link = requests.get(url,headers=headers).text
        soup = BeautifulSoup(link, 'html.parser')
        r = soup.find_all('div', class_={'ml-item'}) or soup.find_all('a', class_={'thumb'})  # .pw layout, then the old one
        if ( not r ) and ( not searched ):
            log_utils.log('Scraping Error in %s:: Content of request: %s' % (base_name.title(),str(link)[:1000]), log_utils.LOGERROR)
            kodi.notify(msg='Scraping Error: Info Added To Log File', duration=6000, sound=True)
    except Exception as e:
        if ( not searched ):
            log_utils.log('Fatal Error in %s:: Error: %s' % (base_name.title(),str(e)), log_utils.LOGERROR)
            kodi.notify(msg='Fatal Error', duration=4000, sound=True)
            quit()    
        else: pass

    dirlst = []
        
    for i in r:
        try:
            a = i if i.name == 'a' else i.a
            title = a.get('title') or a.get('oldtitle') or i.img.get('alt') or a['href'].rstrip('/').split('/')[-1].replace('-', ' ').title()
            mediaurl = a['href']
            icon = i.img.get('data-lazy-src') or i.img.get('data-src') or i.img.get('src', '')
            desc_tag = i.find('p', class_={'f-desc'}) if i.name != 'a' else None
            #if '.gif' in icon: icon = i.img['data-wpfc-original-src']
            #dialog.ok("Media",str(icon))
            #quit()
            fanarts = translatePath(os.path.join('special://home/addons/script.xxxodus.artwork', 'resources/art/%s/fanart.jpg' % filename))
            dirlst.append({'name': title, 'url': mediaurl, 'mode': player_mode, 'icon': icon, 'fanart': fanarts, 'description': desc_tag.text.strip() if desc_tag else title, 'folder': False})
        except Exception as e:
            log_utils.log('Error adding a menu item in %s:: Error: %s' % (base_name.title(),str(e)), log_utils.LOGERROR)

    if dirlst: buildDirectory(dirlst, stopend=True, isVideo = True, isDownloadable = True)
    else:
        if (not searched):
            kodi.notify(msg='No Content Found')
            quit()
        
    if searched: return str(len(r))

    if not searched:
        
        try:
            m = re.search(r'/page/(\d+)/?$', url)
            nxt = re.sub(r'/page/\d+/?$', '/page/%d/' % (int(m.group(1)) + 1), url) if m else url.rstrip('/') + '/page/2/'
            helper.scraper().get_next_page(content_mode, nxt + '|GOT_URL', None, filename)
        except Exception as e: 
            log_utils.log('Error getting next page for %s :: Error: %s' % (base_name.title(),str(e)), log_utils.LOGERROR)