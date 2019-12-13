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
path = r"C:\Scripts\ping_check\list_devices_date.txt"    # Список устройств
path1 = r"C:\Scripts\ping_check\list_paths_date.txt"    # Список путей
path2 = r"C:\Scripts\ping_check\failed_check.txt"
# Создаем FIFO очередь
# Create a FIFO queue
dict_failed_check_cur = {}
dict_failed_check_result = {}
dict_devices = {}
work_queue = queue.Queue()


def ping_ip(ip_address, platform):
    """
    Функция выполняющая каманду ping и возвращающая результат выполнения
    Function that executes the 'ping' command and returns the result of execution
    """
    trace = []
    if "win" in platform:
        # Определяем кодировку терминала windows
        # Define the encoding of the terminal windows
        coding = "cp{0}".format(ctypes.windll.kernel32.GetOEMCP())
        reply = subprocess.run(['ping', '-n', '10', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           encoding=coding)

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
                if re.search(r'Среднее = \d+ мсек', result) is not None:
                    a = re.search(r'Среднее = \d+ мсек', result).group(0)
                    aver_delay = re.search(r'\d+ мсек', a).group(0)
                else:
                    a = "Unknown"
                    aver_delay = "Unknown"
                if re.search(r'Максимальное = \d+ мсек', result) is not None:
                    a = re.search(r'Максимальное = \d+ мсек', result).group(0)
                    max_delay = re.search(r'\d+ мсек', a).group(0)
                else:
                    a = "Unknown"
                    max_delay = "Unknown"

            elif "en" in lang:
                if re.search(r'Average = \d+ms', result) is not None:
                    a = re.search(r'Average = \d+ms', result).group(0)
                    aver_delay = re.search(r'\d+ms', a).group(0)
                else:
                    a = "Unknown"
                    aver_delay = "Unknown"
                if re.search(r'Maximum = \d+ms', result) is not None:
                    a = re.search(r'Maximum = \d+ms', result).group(0)
                    max_delay = re.search(r'\d+ms', a).group(0)
                else:
                    a = "Unknown"
                    max_delay = "Unknown"
                # print(max_delay)
        elif "linux" in platform:
            status = "OK"
            lost = re.search(r'\d+%', result).group(0)
            delays = re.search(r"\d+\.\d+/\d+\.\d+/\d+\.\d+/\d+\.\d+", result).group(0).split("/")
            aver_delay = str(delays[1]) + "ms"
            max_delay = str(delays[2]) + "ms"
    else:
        status = result
        # print(result, 'result')
        lost = "100%"
        aver_delay = "0"
        max_delay = "0"
    return status, lost, aver_delay, max_delay


def ping(work_queue, paths):
     # dict_failed_check_cur = {}
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
        #print(result)
        #print("{0} - {1}".format(ip_address, trace))
        status, lost, aver_delay, max_delay = get_data_from_ping(result, platform)
        # print("{0} {1} {2} {3} {4}".format(hostname, status, lost, aver_delay, max_delay))
        color = Traceroute.compare_path(paths, trace, ip_address)
        #print(color)
        if color != 0:
            # print("{0} - {1}".format(ip_address, trace))
            now = datetime.datetime.now().strftime('%d %b %H:%M')
            dict_failed_check_cur[hostname] = now
        if status == 'FAILD':
            now = datetime.datetime.now().strftime('%d %b %H:%M')
            dict_failed_check_cur[hostname] = now
        # print(dict_failed_check_cur)
        dict_devices[hostname] = [status, lost, aver_delay, max_delay, color]
        work_queue.task_done()
        # print(u'Очередь: %s завершилась' % i)
        # print("Len queue {0}".format(len(work_queue.queue)))



def create_table(dict_devices, dict_failed_check_result):
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
    date = "{{{0}}}{1}{{/{0}}}".format("autoyellow", "DATE")
    table_data.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay), Color(date)])
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
            date = "{autored}" + dict_failed_check_result.get(key) + "{/autored}"
            table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay), Color(date)])
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
                date = '{autored}-{/autored}'
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay), Color(date)])
            elif color == 1:
                hostname = "{{{0}}}{1}{{/{0}}}".format("autoyellow", hostname)
                status = "{{{0}}}{1}{{/{0}}}".format("autoyellow", status)
                if lost != "0%":
                    lost = "{autocyan}" + lost + "{/autocyan}"
                else:
                    lost = "{{{0}}}{1}{{/{0}}}".format("autoyellow", lost)
                aver_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", aver_delay)
                max_delay = "{{{0}}}{1}{{/{0}}}".format("autoyellow", max_delay)
                date = "{autored}" + dict_failed_check_result.get(key) + "{/autored}"
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay), Color(date)])

            else:
                hostname = "{{{0}}}{1}{{/{0}}}".format("autowhite", hostname)
                status = "{{{0}}}{1}{{/{0}}}".format("autowhite", status)
                if lost != "0%":
                    lost = "{autocyan}" + lost + "{/autocyan}"
                else:
                    lost = "{{{0}}}{1}{{/{0}}}".format("autowhite", lost)
                aver_delay = "{{{0}}}{1}{{/{0}}}".format("autowhite", aver_delay)
                max_delay = "{{{0}}}{1}{{/{0}}}".format("autowhite", max_delay)
                date = "{autored}" + dict_failed_check_result.get(key) + "{/autored}"
                table_data_temp.append([Color(hostname), Color(status), Color(lost), Color(aver_delay), Color(max_delay), Color(date)])
    for i in sorted(table_data_temp):
        table_data.append(i)

    table_instance = SingleTable(table_data)
    table_instance.inner_heading_row_border = True
    table_instance.inner_row_border = False
    table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center', 3: 'center', 4: 'center',  5: 'center'}
    return table_instance.table


def get_failed_check_path(path2):
    """
        Функция создающая словарь из имён устройств и даты, и возвращает данный словарь.
        Пример заполнения файла путей ниже:
        device1;date
        device2;date
        dev1;24 Nov 15:33
        dev2;25 Dec 17:01
        The function creates a dictionary from device names and dates, and returns the given dictionary.
        An example of filling the path file below:
        device1; date
        device2; date
        dev1; 24 Nov 15:33
        dev2; 25 Dec 17:01
        :param path:
        :return:
        """
    paths = {}
    with open(path2, "r") as f:
        a = f.readlines()
        # print(len(a), "len dict_failed")
        for i in a:
            if (i == '\n' or i == '\r\n'):
                continue
            else:
                s = i.split(";")
                d = s[0]
                p = s[1]
                paths[d] = p
    return paths


def get_list_failed_device(dict_failed_check_cur, dict_failed_check_old):
    """
    Функция создающая результирующий словарь из текущих проблемных устройств и устройств, которые уже имели проблемы.
    Если появились новые устройства, они будут добавлены, устройства у которых проблем больше нет, будут удалены.
    A function that creates the resulting dictionary from the current problem devices and devices that already had
    problems. If new devices appear, they will be added, devices that no longer have problems will be deleted.
    :param dict_failed_check_cur:
    :param dict_failed_check_old:
    :return:
    """
    cur_m = set(dict_failed_check_cur)
    old_m = set(dict_failed_check_old)
    new_device_faild = cur_m - old_m
    old_device_faild = old_m & cur_m

    result_m = new_device_faild.union(old_device_faild)
    for i in result_m:
        if dict_failed_check_old.get(i) != None:
            dict_failed_check_result[i] =  dict_failed_check_old.get(i)
        elif dict_failed_check_cur.get(i) != None:
            dict_failed_check_result[i] =  dict_failed_check_cur.get(i)
        else:
            continue
    return dict_failed_check_result


if __name__ == "__main__":
    while True:
        # dict_devices = {}
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
        # print(paths)


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
        dict_failed_check_old = get_failed_check_path(path2)
        # print(dict_failed_check_old, 'old_dict')
        dict_failed_check_result = get_list_failed_device(dict_failed_check_cur, dict_failed_check_old)
        # print(dict_failed_check_result, 'dict_result')
        print(create_table(dict_devices, dict_failed_check_result))
        with open(path2, "w") as f:    # заполняем словарь с ранее проблемными устройствами
            for key in dict_failed_check_result:
                f.writelines('{0};{1}\r\n'.format(key, dict_failed_check_result.get(key)))
        end = datetime.datetime.now()
        delta = "{autored}" + str(end - start) + "{/autored}"
        print(Color(delta))
        print(Color("{{{0}}}{1}{{/{0}}} - main path".format("autogreen", "Color")))
        print(Color("{{{0}}}{1}{{/{0}}} - backup path".format("autoyellow", "Color")))
        print(Color("{{{0}}}{1}{{/{0}}} - Internet or not in the file paths".format("autowhite", "Color")))
        dict_failed_check_cur.clear()
        dict_failed_check_result.clear()
        dict_failed_check_old.clear()
        dict_devices.clear()
        time.sleep(10)
