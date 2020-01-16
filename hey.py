from miio.vacuum import Vacuum
import time 
ip = "192.168.178.23"
token = "30556a51426c516d67766a6e734b3646"
from appdirs import user_cache_dir
import pathlib
import json 
while True:
	try:
		id_file =user_cache_dir("python-miio") + "/python-mirobo.seq"
		start_id = manual_seq = 0
		try:
			with open(id_file, "r") as f:
				x = json.load(f)
				start_id = x.get("seq", 0)
				manual_seq = x.get("manual_seq", 0)
				print("Read stored sequence ids: %s", x)
		except (FileNotFoundError, TypeError, ValueError):
			pass

		vac = miio.Vacuum(ip, token, start_id)
		vac.manual_seqnum = manual_seq
		res = vac.status()
		print("Battery: %s %%" % res.battery)
		print("Fanspeed: %s %%" % res.fanspeed)
		print("Cleaning since: %s" % res.clean_time)
		print("Cleaned area: %s m²" % res.clean_area)
		if vac.ip is None:  # dummy Device for discovery, skip teardown
			continue
		seqs = {"seq": vac.raw_id, "manual_seq": vac.manual_seqnum}
		path_obj = pathlib.Path(id_file)
		dir = path_obj.parents[0]
		try:
			dir.mkdir(parents=True)
		except FileExistsError:
			pass  # after dropping py3.4 support, use exist_ok for mkdir
		with open(id_file, "w") as f:
			json.dump(seqs, f)
	except:
		pass
	time.sleep(20)