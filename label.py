#!/bin/python3


"""
 Implements a simple HTTP/1.0 Server
 for printng labels from PROMED
 
"""


import sys
import socket
import ssl
import os
import json
from multiprocessing import Process
from subprocess import Popen, PIPE


# Define SSL certificate
SSLCERT = './printcert.pem'
# Define socket host and port
SERVER_HOST = '0.0.0.0'
HTTP_PORT = 9100
HTTPS_PORT = 9101


def make_print_list() -> list:
    '''Get list of system printers'''
    p = Popen(['lpstat', '-a'], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output, errors = p.communicate()
    lines = output.decode().split('\n')
    printers = [x.split(' ')[0] for x in lines]
    item = iter(printers)
    json_list = list()
    for i in range(len(printers) - 1):
        entry = {
    "deviceType": "printer",
    "uid": "ZDesigner ZD511-300dpi ZPL",
    "provider": "com.zebra.ds.webdriver.desktop.provider.DefaultDeviceProvider",
    "name": next(item),
    "connection": "driver",
    "version": 4,
    "manufacturer": "Zebra Technologies"
		}
        json_list.append(entry)
        i + 1
    cont = {
        "printer":json_list
        }
    cont = json.dumps(cont)
    return cont

def handle_request(request):
    """Handles the HTTP request."""
    try:
        content = make_print_list()
        #print(type(new_content))
    except FileNotFoundError:
        content = 'Not Found'
    headers = 'Access-Control-Allow-Origin: * \n\n'
    response = 'HTTP/1.1 200 OK\n' + headers + str(content)
    #print(response)
    return response

def label_print(request) -> None:
    '''Printing label'''
    s = request.decode().split('\n')
    j = json.loads(s[-1])
    printer = j['device']['name'] # Define printer from response
    if os.name == 'posix':
        save_path = '/tmp'
        file_name = 'print.zpl'
        print_file = os.path.join(save_path, file_name)
        d = j['data']
        data = d.replace("^BCN,", "^BCR,") # Barcode Rotation
        with open(print_file, 'w') as file:
            file.write(data)
        print("PRINTING!")
        os.system("lpr -P {} -o raw {}".format(printer, print_file))
        os.system("rm -rf {}".format(print_file)) 
    else:
        print("Mock Print")

def create_socket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(5)
    if port == HTTPS_PORT:
        s = ssl.wrap_socket(s, certfile = SSLCERT)
    print('Listening on port {} ...'.format(port))
    return s

def runner(host, port):
    soc = create_socket(host, port)
    while True:
        try:
            conn, addr = soc.accept()
            req = conn.recv(1024)
            if "POST" in req.decode():
                label_print(req)
            resp = handle_request(req)
            conn.sendall(resp.encode())
            conn.close()
        except KeyboardInterrupt:
            break
        except:
            continue
    soc.close()


if __name__ == '__main__':
    try:
        http_serv = Process(target=runner, args=(SERVER_HOST, HTTP_PORT,))
        http_serv.start()
        https_serv = Process(target=runner, args=(SERVER_HOST, HTTPS_PORT,))
        https_serv.start()
        http_serv.join()
        https_serv.join()
    except KeyboardInterrupt:
        sys.exit("Server shutdown")

