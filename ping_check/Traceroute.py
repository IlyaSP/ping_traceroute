# -*- coding: utf-8 -*-
import subprocess
import re
import ctypes
import sys


path = r"C:\Scripts\ping_check\list_paths.txt"
ip_address = "10.194.255.1"
platform = sys.platform


def traceroute(platform, ip_address):
    """
    Функция выполняющая команду tracert/traceroute и возвращает её результат в виде массива из ip адресов.
    A function that executes the tracert / traceroute command and returns its result as an array of ip addresses.
    :param platform:
    :param ip_address:
    :return:
    """
    if "win" in platform:
        # Определяем кодировку терминала windows
        # Define the encoding of the terminal windows
        coding = "cp{0}".format(ctypes.windll.kernel32.GetOEMCP())
        reply = subprocess.run(['tracert', '-d', '-h', '25', '-w', '2000', ip_address], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, encoding=coding)
    elif "linux" in platform:
        reply = subprocess.run(['traceroute', '-I', '-n', '-w', '2', '-q', '2', ip_address], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, encoding=sys.stdout.encoding)
    # print(reply.stdout)
    trace_temp = re.findall(r"\d+.\d+.\d+.\d+", reply.stdout)
    trace = []
    for i in trace_temp:
        if i != ip_address:
            trace.append(i)
        else:
            continue
    return trace


def create_dict_path(path):
    """
    Функция создающая словарь из ip адресов устройств и путей до устройств и возвращает данный словарь.
    Пример заполнения файла путей ниже:
    device1:path1;path2
    device2:path1
    dev1:1.1.1.1;2.2.2.2
    dev2:3.3.3.3
    путь в файл добавляется без последнего хопа
    A function that creates a dictionary from ip addresses of devices and paths to devices and returns this dictionary.
    An example of filling the path file below:
    device1:path1;path2
    device2:path1
    dev1:1.1.1.1;2.2.2.2
    dev2:3.3.3.3
    the path to the file is added without the last hop
    :param path:
    :return:
    """
    paths = {}
    with open(path, "r") as f:
        a = f.readlines()
        for i in a:
            s = i.split(":")
            d = s[0]
            p = s[1]
            paths[d] = p
    return paths


def compare_path(paths, trace_path, ip_address):
    """
    Функция сранивающая путь полученный из вывода команды tracert/traceroute и сравнивает со славарём полученным из
    файла и возвращает результат сравнения.
    The function is the path from tracert / traceroute and compares it with the result of file and returns the result
    of the comparison.
    :param paths:
    :param trace_path:
    :param ip_address:
    :return:
    """
    path_number = -1
    paths_in_file = paths.get(ip_address)
    if paths_in_file is not None:
        # Получаем список путей до устройства
        # Get list of paths to device
        paths_in_file1 = paths_in_file.split(";")
        for i in paths_in_file1:
            trace_in_file = i.replace("\n", "").split(",")
            if trace_path == trace_in_file:
                path_number = paths_in_file1.index(i)
                return path_number
            else:
                continue
    else:
        return 0

    if path_number == -1:
        return 2

if __name__ == "__main__":
    # Запускается только в случае выполнения скрипта
    trace_path = traceroute(platform, ip_address)
    # print(trace_path)
    paths = create_dict_path(path)
    # print(paths)
    print(compare_path(paths, trace_path, ip_address))

