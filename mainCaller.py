import pygame
from servecies import *
from ui_controller import WebLockView
from threading import Thread , Event
import time 
from appdirs import user_cache_dir
import pathlib
import json 
from miio.vacuum import Vacuum
import sys
class WebLock():
    def __init__(self):
        self.view = WebLockView()
        self.closeAppFlag = False
        # .................. install services ...................
        self.screen_saver_service = ScreenSaver()
        self.wifi_service = WifiService()
        self.scroll_service = ScrollerService(self.view.set_guest_name)
        # access control service --- pulling passwords
        self.pulling_password_sevice = PullingPasswordService()
        self.pulling_password_sevice.guest_names_received = self.scroll_service.set_guest_names
        self.pulling_password_sevice.led_color_received = self.view.set_led_color
        self.pulling_password_sevice.help_number_received = self.view.set_phone_number
        self.pulling_password_sevice.unit_number_received = self.view.set_unit_id
        # access control service --- lock mangment
        self.lock_management_service = LockManagementService(self.view.set_password , self.view.start_animation  )
        self.pulling_password_sevice.codes_received = self.lock_management_service.new_passwords_received
        self.view.is_pressed_signal = self.lock_management_service.led_has_pressed
        # pir service
        self.motion_service = MotionService()
        self.motion_service.start()
        # mqtt
        self.mqtt_client = MqttClient()
        self.pulling_password_sevice.new_fr_configuration_received = self.mqtt_client.update_sensor_measurement
        self.mqtt_client.new_record_ref = self.pulling_password_sevice.update_request_prams
        self.mqtt_client.start()
        self.vacuum_cleaner_service = VacuumCleaner()
        self.pulling_password_sevice.new_vacuum_configuration_received = self.vacuum_cleaner_service.new_configurations


        #start view  rendering
        self.wifi_service.start_service()
        self.pulling_password_sevice.start_service()
        self.lock_management_service.start_service()
        self.view.update_view()
        self.view.is_pressed_signal = self.lock_management_service.led_has_pressed
        self.__vac_status_service = Thread(target=self.get_vac_status)
        self.__vac_status_service_ce = Event()
        self.__vac_status_service.start()

    def get_vac_status(self):
        try:
            while not self.__vac_status_service_ce.is_set():
                __ip, __token = ConfigurationLoader.get_vacuum_cleaner_info()
                try:
                    status = self.get_status(__ip , __token)
                    self.pulling_password_sevice.update_request_prams({"vac_status": status})
                except Exception as e:
                    print(e)
                self.__vac_status_service_ce.wait(120)
        except Exception as e:
            print(e)
    

    def get_status(self, ip , token):
        res = ["" , "" , ""]
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

            vac = Vacuum(ip, token, start_id)
            vac.manual_seqnum = manual_seq
            res = vac.status()
            res = [res.state , res.battery , res.is_on]
            if vac.ip is None:  # dummy Device for discovery, skip teardown
                return res
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
        return res 

    def close_all(self):
        self.scroll_service.close_service()
        self.pulling_password_sevice.close_service()
        self.wifi_service.close_service()
        self.lock_management_service.close_service()
        self.motion_service.close_service()
        self.mqtt_client.close_service()
        self.__vac_status_service_ce.set()

    
    def restart_application(self):
        pass
    


if __name__ == "__main__":
    test_obj = WebLock()
    while test_obj.closeAppFlag == False :
        pygame.display.update()
        time.sleep(1)
    test_obj.close_all()
    pygame.quit()
    sys.exit(0)
