# ping_traceroute
Программа служит для проверки доступности устройств с помощью команды "ping" и проверки пути по которому данное устройство доступно. Результат работы выводится в терминал в виде таблицы со строками разного цвета. Цвет зависит от доступности/недоступности устройства и пути по которому конкретное устройство доступно (основной/резервный). 
Поддерживаемы операционные системы: Windows, Linux
В файле "list_devices.txt" содержится список устройств для проверки.
В файле "ist_paths.txt" содержатся пути до этих устройств.
Файл "ping_universal_date.py" делает всё тоже самое что и "ping_universal.py", только добавляет колонку с датой и временем начала инцидента.
P.S Не тестировалось на 32-х битных системах

The program is used to check the availability of devices using the "ping" command and check the path to which the device is available. The result of the work is output to the terminal as a table with rows of different colors. The color depends on the availability / unavailability of the device and the way in which a particular device is available (main / backup). 
Supported Operating Systems: Windows, Linux
The file "list_devices.txt" contains a list of devices to check.
The file "ist_paths.txt" contains the paths to these devices.
The file "ping_universal_date.py" does the same thing as "ping_universal.py", only adds a column with the date and time the incident began.
P.S Not tested on 32-bit systems
