from kodi_six import xbmc, xbmcaddon, xbmcgui, xbmcvfs
from contextlib import closing
import os, requests, json, re
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings() #Silence uneeded warnings
WIN = xbmcgui.Window(10000)
# WIN.clearProperty('rbt.script_started')
if not WIN.getProperty('rbt.script_started'):
	xbmc.log(msg='Retro BIOS Tool:  Tool Started', level=xbmc.LOGNOTICE)
	WIN.setProperty('rbt.script_started','True')
	addon_name = 'plugin.program.retrobiostool'
	addon_handle = xbmcaddon.Addon(id='%(addon_name)s' % {'addon_name':addon_name})
	bios_folder = addon_handle.getSetting(id='rbt_folder')
	addon_timeout = 5
	bios_keyword = ['firmware%(number)s_path'%{'number':x} for x in range(0,21)]
	libretro_git = r'https://raw.githubusercontent.com/libretro/libretro-super/master/dist/info/xxx_core_xxx.info'
	ignore_these_addons = ['game.libretro','game.libretro.2048','game.libretro.chailove','game.libretro.dinothawr','game.libretro.tyrquake','game.libretro.nx','game.libretro.mrboom','game.libretro.lutro'] #These games do not require any system/bios files
	retroplayer_to_libretro_map = {'bsnes-mercury-accuracy':'bsnes_mercury_accuracy',
	'bsnes-mercury-balanced':'bsnes_mercury_balanced',
	'bsnes-mercury-performance':'bsnes_mercury_performance',
	'genplus':'genesis_plus_gx',
	'beetle-gba':'mednafen_gba',
	'beetle-lynx':'mednafen_lynx',
	'beetle-ngp':'mednafen_ngp',
	'beetle-pce-fast':'mednafen_pce_fast',
	'beetle-pcfx':'mednafen_pcfx',
	'beetle-psx':'mednafen_psx',
	'beetle-saturn':'mednafen_saturn',
	'beetle-bsnes':'mednafen_snes',
	'beetle-supergrafx':'mednafen_supergrafx',
	'beetle-vb':'mednafen_vb',
	'beetle-wswan':'mednafen_wswan',
	'pcsx-rearmed':'pcsx_rearmed',
	'uae':'puae',
	'vba-next':'vba_next',
	'vice':'vice_x64'}

	if bios_folder is None or len(bios_folder)<1:
		ret = current_dialog.ok('Retro BIOS Tool','The tool did not run.[CR]Enter a BIOS file location in settings first!')
	else:
		try:
			addons_available = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Addons.GetAddons","params":{"type":"kodi.gameclient"}, "id": "1"}')
			addon_ids = [x.get('addonid') for x in json.loads(addons_available).get('result').get('addons') if x.get('type') == 'kodi.gameclient' and x.get('addonid') not in ignore_these_addons]
		except:
			addon_ids = None
		if addon_ids is not None:
			total_files_copied = 0
			dp = xbmcgui.DialogProgress()
			dp.create('Retro BIOS Tools','Checking for BIOS Files','')
			dp.update(0)
			s = requests.Session()
			for iiaid,aid in enumerate(addon_ids):
				dp.update(100*(iiaid+1)/len(addon_ids))
				if dp.iscanceled():
					run_was_cancelled = True
					dp.close()
					raise
				if aid.replace('game.libretro.','') in retroplayer_to_libretro_map.keys():
					current_git_url = libretro_git.replace('xxx_core_xxx',retroplayer_to_libretro_map[aid.replace('game.libretro.','')]+'_libretro')
				else:
					current_git_url = libretro_git.replace('xxx_core_xxx',aid.replace('game.libretro.','')+'_libretro')
				xbmc.log(msg='Retro BIOS Tool:  Checking libretro for core info at %(current_git_url)s' % {'current_git_url':current_git_url}, level=xbmc.LOGDEBUG)
				try:
					r = s.get(current_git_url,verify=False,stream=True,timeout=addon_timeout)
				except Exception as current_exc:
					xbmc.log(msg='Retro BIOS Tool:  Error getting libretro for core info at %(current_exc)s' % {'current_exc':current_exc}, level=xbmc.LOGDEBUG)
				current_info = r.text
				current_bios_files = list()
				for bk in bios_keyword:
					current_check = re.findall(r'%(current_bk)s\s+=\s+\"(.*?)\"'%{'current_bk':bk},current_info)
					if current_check is not None and len(current_check)>0:
						current_bios_files.append(current_check[0].strip())
				if len(current_bios_files)>0:
					xbmc.log(msg='Retro BIOS Tool:  Looking for the following bios files %(current_files)s' % {'current_files':', '.join(current_bios_files)}, level=xbmc.LOGDEBUG)
					current_addon = xbmcaddon.Addon(id='%(addon_name)s' % {'addon_name':aid})
					current_addon_data_folder = xbmc.translatePath(current_addon.getAddonInfo('profile')).decode('utf-8')
					current_addon_resources_folder = os.path.join(current_addon_data_folder,'resources')
					current_addon_systems_folder = os.path.join(current_addon_resources_folder,'system')
					for cbf in current_bios_files:
						current_bios_fullpath = os.path.join(bios_folder,cbf)
						if xbmcvfs.exists(current_bios_fullpath):
							xbmc.log(msg='Retro BIOS Tool: Found file %(current_cbf)s' % {'current_cbf':cbf}, level=xbmc.LOGDEBUG)
							if not xbmcvfs.exists(os.path.join(current_addon_data_folder,'')):
								xbmc.log(msg='Retro BIOS Tool:  The folder %(current_folder)s does not yet exist, so it will be created' % {'current_folder':current_addon_data_folder}, level=xbmc.LOGDEBUG)
								if not xbmcvfs.mkdir(os.path.join(current_addon_data_folder,'')):
									xbmc.log(msg='Retro BIOS Tool:  Unable to create addon_data folder', level=xbmc.LOGERROR)
							if not xbmcvfs.exists(os.path.join(current_addon_resources_folder,'')):
								xbmc.log(msg='Retro BIOS Tool:  The folder %(current_folder)s does not yet exist, so it will be created' % {'current_folder':current_addon_resources_folder}, level=xbmc.LOGDEBUG)
								if not xbmcvfs.mkdir(os.path.join(current_addon_resources_folder,'')):
									xbmc.log(msg='Retro BIOS Tool:  Unable to create addon_data resources folder', level=xbmc.LOGERROR)
							if not xbmcvfs.exists(os.path.join(current_addon_systems_folder,'')):
								xbmc.log(msg='Retro BIOS Tool:  The folder %(current_folder)s does not yet exist, so it will be created' % {'current_folder':current_addon_systems_folder}, level=xbmc.LOGDEBUG)
								if not xbmcvfs.mkdir(os.path.join(current_addon_systems_folder,'')):
									xbmc.log(msg='Retro BIOS Tool:  Unable to create addon_data resources/system folder', level=xbmc.LOGERROR)
							if not xbmcvfs.exists(os.path.join(current_addon_systems_folder,cbf)):
								if xbmcvfs.copy(os.path.join(bios_folder,cbf),os.path.join(current_addon_systems_folder,cbf)): #Copy the file to the correct system folder
									xbmc.log(msg='Retro BIOS Tool: Copying file %(current_cbf)s to %(current_folder)s' % {'current_cbf':os.path.join(bios_folder,cbf),'current_folder':os.path.join(current_addon_systems_folder,cbf)}, level=xbmc.LOGNOTICE)
									total_files_copied = total_files_copied+1
								else:
									xbmc.log(msg='Retro BIOS Tool: Error copying file %(current_cbf)s to %(current_folder)s' % {'current_cbf':os.path.join(bios_folder,cbf),'current_folder':os.path.join(current_addon_systems_folder,cbf)}, level=xbmc.LOGERROR)
						else:
							xbmc.log(msg='Retro BIOS Tool: File already exists %(current_cbf)s ' % {'current_cbf':os.path.join(bios_folder,cbf)}, level=xbmc.LOGERROR)
				else:
					xbmc.log(msg='Retro BIOS Tool: No bios files found for %(current_aid)s' % {'current_aid':aid}, level=xbmc.LOGNOTICE)
			dp.close()
			current_dialog = xbmcgui.Dialog()
			if total_files_copied >0:
				ok_ret = current_dialog.ok('Completed','Tool copied %(total_files_copied)s total files.'% {'total_files_copied': total_files_copied})
			else:
				ok_ret = current_dialog.ok('Completed','Tool did not copy any files'% {'total_files_copied': total_files_copied})
	WIN.clearProperty('rbt.script_started')
	xbmc.log(msg='Retro BIOS Tool:  Tool completed', level=xbmc.LOGNOTICE)
else:
	xbmc.log(msg='Retro BIOS Tool:  Tool already running', level=xbmc.LOGNOTICE)