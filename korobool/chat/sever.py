import sys
import threading
import time

__author__ = 'Oleksandr Korobov'

import socket
import signal

from collections import deque

from korobool.chat.Threaded import ServingThreadWrapper

class ChatServer:
    def __init__(self, PORT=50007):
        self.port = PORT
        self.host = ''
        self.__clients_pool = []
        self.closing = False
        self.__notifications_queue = deque()
        self.__notification_lock = threading.RLock()

    def __start_serve_connection(self, conn, addr):
        stw = ServingThreadWrapper(self, conn, addr)
        self.__clients_pool.append(stw)

    def __close_all_clients(self):
        print('closing ', len(self.__clients_pool), 'clients')
        
        while len(self.__clients_pool) > 0:
            self.__clients_pool[0].close()
        #self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def serve(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

        self.socket.settimeout(2)
        while not self.closing:

            self.socket.listen(5)

            self.__process_notifications()
            try:
                conn, addr = self.socket.accept()
                self.__start_serve_connection(conn, addr)
            except:
                pass # Remove this awful exception swallowing
        self.__close_all_clients()

    def stop_serve(self):
        self.closing = True
        self.__close_all_clients()

    def notify(self, sender, message):
        print('Notification received:', message)
        with self.__notification_lock:
            self.__notifications_queue.append((sender, message))

    def __process_notifications(self):
        while len(self.__notifications_queue) > 0:
            notification = self.__notifications_queue.pop()
            self.__process_notification(notification)

    def __process_notification(self, notification):
        if not notification: return
        sender = notification[0]
        message = notification[1]

        if message['cmd'] == 'CDM_FREE_RESOURCES':
            sender.thread.join

        if message['cmd'] == 'CMD_BROADCAST':
            for client in self.__clients_pool:
                if not client is None and not client.closing:
                    #print('Posting to '. client.name)
                    client.post(message)

        if message['cmd'] == 'CMD_MESSAGE':
            client.post({'cmd': 'CMD_SEVER_WARNING', 'msg': 'message sending is not implemented yet'})

        if message['cmd'] == 'CMD_CLIENT_LEFT':
            print('Client left', message['id'])
            self.__clients_pool.remove(message['id'])

        if message['cmd'] == 'CMD_SCLOSESERVER':
            self.closing = True

chat_sever = ChatServer(PORT = 50007)

def signal_handler(signal, frame):
    print('CTRL+C caught. Wait... Server is closing now....')
    chat_sever.stop_serve()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

chat_sever.serve()
