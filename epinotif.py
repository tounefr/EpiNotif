#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import os
import time
import re
import argparse

class Requester:

    INSTANCE = None

    def load_requester(self):
        self.reqsess = requests.Session()
        self.reqsess.verify = False
        self.io = IO.getInstance()

    @staticmethod
    def getInstance():
        if Requester.INSTANCE == None:
            Requester.INSTANCE = Requester()
        return Requester.INSTANCE

    def connection_request(self, username, password):
        try:
            res = self.reqsess.post("https://intra.epitech.eu/", data={
                "login": username, "password": password })
        except requests.exceptions.ConnectionError as m:
            self.io.debug("Failed to connect")
            time.sleep(10)
            self.connection_request(username, password)

    def notifs_request(self):
        try:
            res = self.reqsess.get("https://intra.epitech.eu/user/notification/message?format=json")
            if None == re.search("application/json", res.headers["Content-Type"]):
                self.io.debug("Wrong notifs_request response !")
            return json.loads(res.text)
        except requests.exceptions.ConnectionError as m:
            self.io.debug("Failed to fetch notifs")
            time.sleep(10)
            self.notifs_request()

class IO:

    INSTANCE = None

    def io_load(self, notifs_data_file_path = os.path.expanduser("~/.epinotif")):
        self.notifs_data_file = None
        self.notifs_data_file_path = notifs_data_file_path
        print(self.notifs_data_file_path)
        self.open_files()

    @staticmethod
    def getInstance():
        if IO.INSTANCE == None:
            IO.INSTANCE = IO()
        return IO.INSTANCE

    def open_files(self):
        self.notifs_data_file = open(self.notifs_data_file_path, 'a+')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.notifs_data_file != None:
            self.notifs_data_file.close()

    def notify(self, msg):
        msg = re.sub("<.*?>", "", msg)
        msg = msg.encode('utf-8', 'ignore')
        msg = msg.replace('"', '\'')
        cmd = "notify-send \"EPINOTIF : {}\"".format(msg)
        try:
            if os.system(cmd) != 0:
                self.debug("Failed to execute cmd : {}".format(cmd))
        except:
            self.debug("Failed to execute command : {}".format(cmd))
            exit(1)

    def write_notifs_file(self, notifs):
        try:
            self.notifs_data_file.write(json.dumps(notifs))
        except:
            self.debug("Failed to write into notifs file")

    def load_notifs(self):
        try:
            return json.loads(self.notifs_data_file.read())
        except ValueError:
            return []
        except:
            self.debug("Failed to read notifs from file")
            exit(1)

    def debug(self, msg, notify=False):
        print(msg)
        if notify:
            self.notify(msg)

class Epinotif:

    INSTANCE = None

    @staticmethod
    def getInstance():
        if Epinotif.INSTANCE == None:
            Epinotif.INSTANCE = Epinotif()
        return Epinotif.INSTANCE

    def __init__(self):
        self.io = IO.getInstance()
        self.io.io_load()
        self.notifs = self.io.load_notifs()
        self.requester = Requester.getInstance()
        self.requester.load_requester()
        self.parse_args()

    def parse_args(self):
        parser = argparse.ArgumentParser(prog="EpiNotif v1.0.0",
                                         description="Récupère les notifications sur l'intranet",
                                         prefix_chars="--",
                                         add_help=False)
        parser.add_argument("--username", help="Votre nom de compte d'accès à l'intranet", default="", required=True)
        parser.add_argument("--password", help="Votre mot de passe d'accès à l'intranet", default="", required=True)
        parser.add_argument("--check_interval", help="Interval de récupération des notifications sur l'intranet", type=int, default=60)
        parser.add_argument("--help", help="Affiche les commandes disponibles")
        self.args = parser.parse_args()

    def fetch_notifs(self):
        self.requester.connection_request(self.args.username, self.args.password)
        while True:
            json_res = self.requester.notifs_request()
            if "message" in json_res and json_res["message"] == "Veuillez vous connecter":
                self.io.debug("Vos identifiants sont incorrects !", notify=True)
                break
            for notif in reversed(json_res):
                if notif not in self.notifs:
                    self.io.debug(notif["title"], notify=True)
                    self.notifs.append(notif)
                time.sleep(5)
            self.io.write_notifs_file(self.notifs)
            time.sleep(self.args.check_interval)

if __name__ == "__main__":
    epinotif = Epinotif()
    epinotif.fetch_notifs()