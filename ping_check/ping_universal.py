# -*- coding: utf-8 -*-
import sys
import subprocess
import ctypes
import datetime
import queue
import threading
import time
import re
import locale
import os
from colorclass import Color, Windows
from terminaltables import SingleTable
import Traceroute

platform = sys.platform
path = r"C:\Scripts\ping_check\list_devices.txt"    # Список устройств
path1 = r"C:\Scripts\ping_check\list_paths.txt"    # Список путей
# Создаем FIFO очередь
# Create a FIFO queue
work_queue = queue.Queue()


def ping_ip(ip_address, platform):
    """
    Функция выполняющая каманду ping и возвращающая результат выполнения
    Function that executes the 'ping' command and returns the result of execution
    """
    if "win" in platform:
        # Определяем кодировку терминала windows
        # Define the encoding of the terminal windows
        coding = "cp{0}".format(ctypes.windll.kernel32.GetOEMCP())
        reply = subprocess.run(['ping', '-n', '8', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding=coding)
        trace = []
        if reply.returncode == 0:
            trace = Traceroute.traceroute(platform, ip_address)
            return reply.stdout, trace
        else:
            status = "FAILD"
            return status, trace

    elif "linux" in platform:
        reply = subprocess.run(['ping', '-c', '10', '-n', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding=sys.stdout.encoding)
        if reply.returncode == 0:
            trace = Traceroute.traceroute(platform, ip_address)
            return reply.stdout, trace
        else:
            status = "FAILD"
            return status, trace


def get_data_from_ping(result, platform):
    """
    Функция выполняющая разбор результатов команды 'ping' для получения значений потерь, средней и максимальной
    задержки
    Function that parses the results of the 'ping' command to obtain loss, average and maximum values delays
    """
    if result != "FAILD":
        if "win" in platform:
            lost = re.search(r'\d+%', result).group(0)
            status = "OK"
            lang = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
            # Определяем язык ОС Windows
            # Define the language OS Windows
            if "ru" in lang:
                a = re.search(r'Среднее = \d+ мсек', result).group(0)
                aver_delay = re.search(r'\d+ мсек', a).group(0)
                a = re.search(r'Максимальное = \d+ мсек', result).group(0)
                max_delay = re.search(r'\d+ мсек', a).group(0)

            elif "en" in lang:
                a = re.search(r'Average = \d+ms', result).group(0)
                aver_delay = re.search(r'\d+ms', a).group(0)
                a = re.search(r'Maximum = \d+ms', result).group(0)
                max_delay = re.search(r'\d+ms', a).group(0)
                print(max_delay)
        elif "linux" in platform:
            status = "OK"
            lost = re.search(r'\d+%', result).group(0)
            delays = re.search(r"\d+\.\d+/\d+\.\d+/\d+\.\d+/\d+\.\d+", result).group(0).split("/")
            aver_delay = str(delays[1]) + "ms"
            max_delay = str(delays[2]) + "ms"
    else:
        status = result
        lost = "100%"
        aver_delay = "0"
        max_delay = "0"
    return status, lost, aver_delay, max_delay


def ping(work_queue, paths):
    while not work_queue.empty():
        # Получаем задание из очереди
        i = work_queue.get()
        # print('DEVICE: ', i)
        # из строки вида hostname;xx.xx.xx.xx получаем массив в котором содержится hostname, ip adress
        # разделяя строку по ";"
        data = i.split(";")
        hostname = data[0].rstrip()
        ip_address = data[1].rstrip()
        result, trace = ping_ip(ip_address, platform)
        status, lost, aver_delay, max_delay = get_data_from_ping(result, platform)
        # print("{0} {1} {2} {3} {4}".format(hostname, status, lost, aver_delay, max_delay))
        color = Traceroute.compare_path(paths, trace, ip_address)
        dict_devices[hostname] = [status, lost, aver_delay, max_delay, color]
        work_queue.task_done()
        # print(u'Очередь: %s завершилась' % i)
        # print("Len queue {0}".format(len(work_queue.queue)))



def create_table(dict_devices):
    """
    Функция для создания отрисовки таблицы
    Function for creating a table
    """
    table_data = []
    table_data_temp =[]
    hostname = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "HOSTNAME")
    status = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "STATUS")
    lost = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "LOST")
    aver_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "AVERAGE DELAY")
    max_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "MAXIMUM DELAY")
    table_data.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay)])
    for key in dict_devices:
        hostname = key
        status = dict_devices.get(key)[0]
        lost = dict_devices.get(key)[1]
        aver_delay = dict_devices.get(key)[2]
        max_delay = dict_devices.get(key)[3]
        color = int(dict_devices.get(key)[4])
        if status == "FAILD":
            hostname = "{autored}" + hostname + "{/autored}"
            status = "{autored}" + status + "{/autored}"
            lost = "{autored}" + lost + "{/autored}"
            aver_delay = max_delay = '{autored}0{/autored}'
            table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay)])
        else:
            if color == 0:
                hostname = "{{{0}}}{1}{{/{0}}}".format("autogreen", hostname)
                status = "{{{0}}}{1}{{/{0}}}".format("autogreen", status)
                if lost !="0%":
                    lost = "{autocyan}" + lost + "{/autocyan}"
                else:
                    lost = "{{{0}}}{1}{{/{0}}}".format("autogreen", lost)
                aver_delay = "{{{0}}}{1}{{/{0}}}".format("autogreen", aver_delay)
                max_delay = "{{{0}}}{1}{{/{0}}}".format("autogreen", max_delay)
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay)])
            elif color == 1:
                hostname = "{{{0}}}{1}{{/{0}}}".format("autoyellow", hostname)
                status = "{{{0}}}{1}{{/{0}}}".format("autoyellow", status)
                if lost != "0%":
                    lost = "{autocyan}" + lost + "{/autocyan}"
                else:
                    lost = "{{{0}}}{1}{{/{0}}}".format("autoyellow", lost)
                aver_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", aver_delay)
                max_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", max_delay)
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay)])

            else:
                hostname = "{{{0}}}{1}{{/{0}}}".format("autowhite", hostname)
                status = "{{{0}}}{1}{{/{0}}}".format("autowhite", status)
                if lost != "0%":
                    lost = "{autocyan}" + lost + "{/autocyan}"
                else:
                    lost = "{{{0}}}{1}{{/{0}}}".format("autowhite", lost)
                aver_delay = "{{{0}}}{1}{{/{0}}}".format("autowhite", aver_delay)
                max_delay = "{{{0}}}{1}{{/{0}}}".format("autowhite", max_delay)
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay)])
    for i in sorted(table_data_temp):
        table_data.append(i)

    table_instance = SingleTable(table_data)
    table_instance.inner_heading_row_border = True
    table_instance.inner_row_border = False
    table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center', 3: 'center', 4: 'center'}
    return table_instance.table

while True:
    dict_devices = {}
    start = datetime.datetime.now()
    """
    Заполняем очередь устройствами из файла. 
    Пример заполнения файла:
    device1;ip_address
    device2;ip_address
    Fill the queue with devices from the file
    Example of filling a file:
    device1;ip_address
    device2;ip_address
    """
    with open(path, 'r') as f:
        a = f.readlines()
        for i in a:
            work_queue.put(i)
    # заполняем словарь с путями до удалённого хоста
    # we fill the dictionary with the paths to the remote host
    paths = Traceroute.create_dict_path(path1)

    for i in range(57):
        # print(u'Flow', str(i), u'start')
        # print(u'Поток', str(i), u'стартовал')
        # print("Number of active flows: ", threading.activeCount())
        # print(u"Количчество активных потоков: ", threading.activeCount())
        t1 = threading.Thread(target=ping, args=(work_queue, paths,))
        t1.setDaemon(True)
        t1.start()
        time.sleep(0.1)

    work_queue.join()  # Ставим блокировку до тех пор пока не будут выполнены все задания
    if "win" in platform:
        Windows.enable(auto_colors=True, reset_atexit=True)    # Enable colors in the windows terminal
    else:
        pass
    os.system("cls||clear")
    print(start)
    print(create_table(dict_devices))
    end = datetime.datetime.now()
    delta = "{autored}" + str(end - start) + "{/autored}"
    print(Color(delta))
    print(Color("{{{0}}}{1}{{/{0}}} - main path".format("autogreen", "Color")))
    print(Color("{{{0}}}{1}{{/{0}}} - backup path".format("autoyellow", "Color")))
    print(Color("{{{0}}}{1}{{/{0}}} - Internet or not in the file paths".format("autowhite", "Color")))
    time.sleep(7)