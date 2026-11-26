import pkgutil
import os.path
import importlib.util
import xbmc
Notice = xbmc.LOGINFO  # LOGNOTICE was removed in Kodi 19; kodi_six/six were never declared as requirements
def sources():
	try:
		sourceDict = []
		for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.dirname(__file__)]):
			if is_pkg:
				continue
			try:
				# find_module()/load_module() were removed in Python 3.12, so on Kodi 22/23 every
				# scraper failed to load and the XXX Sites screen was empty
				spec = loader.find_spec(module_name)
				module = importlib.util.module_from_spec(spec)
				spec.loader.exec_module(module)
				sourceDict.append((module_name, module.Scraper()))
			except Exception as e:
				xbmc.log('Could not load %s: %s' % (module_name, e), Notice)
		return sourceDict
	except:
		return []