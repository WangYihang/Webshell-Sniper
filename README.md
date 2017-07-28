# Webshell-Sniper
A webshell manager via terminal

Usage :
```
Usage : 
        python sniper.py [URL] [METHOD] [AUTH]
Example : 
        python sniper.py http://127.0.0.1/c.php POST c
Author : 
        WangYihang <wangyihanger@gmail.com>
```

ScreenShot : 
[![asciicast](https://asciinema.org/a/Si84wbgKpRBmfyhrnPOL6H4nj.png)](https://asciinema.org/a/130893)

```
===================================================
           ____        _
          / ___| _ __ (_)_ __   ___ _ __
          \___ \| '_ \| | '_ \ / _ \ '__|
           ___) | | | | | |_) |  __/ |
          |____/|_| |_|_| .__/ \___|_|
                      |_|
===================================================
|          WebShell Manager Via Terminal          |
|  https://github.com/wangyihang/webshell-sniper  |
===================================================
[+] Checking the connection to the webshell...
[+] The status code is 200
[+] Checking whether the webshell is still work...
[+] Using challenge key : [AGWIBE] , value : [eOkdpmxxVDjKBCRLLcPShiXKuRNyJYfx]
[+] Using token : [rbVMwcFhabWLYlmTZTxEjNCZOqcNBVFM]
[+] Using POST method...
[+] The content is :
 rbVMwcFhabWLYlmTZTxEjNCZOqcNBVFMstring(32) "eOkdpmxxVDjKBCRLLcPShiXKuRNyJYfx"
rbVMwcFhabWLYlmTZTxEjNCZOqcNBVFMtest

[+] It works well!
[+] PHP 7.0.18-0ubuntu0.17.04.1 (cli) (built: Apr 26 2017 23:59:48) ( NTS )
Copyright (c) 1997-2017 The PHP Group
Zend Engine v3.0.0, Copyright (c) 1998-2017 Zend Technologies
    with Zend OPcache v7.0.18-0ubuntu0.17.04.1, Copyright (c) 1999-2017, by Zend Technologies
[+] Linux sun 4.10.0-28-generic #32-Ubuntu SMP Fri Jun 30 05:32:18 UTC 2017 x86_64 x86_64 x86_64 GNU/Linux
[+] ================================
[+] URL : http://127.0.0.1/c.php
[+] Method : POST
[+] Password : c
[+] Document Root : /var/www/html
[+] ================================
[+] PHP version : 
	PHP 7.0.18-0ubuntu0.17.04.1 (cli) (built: Apr 26 2017 23:59:48) ( NTS )
Copyright (c) 1997-2017 The PHP Group
Zend Engine v3.0.0, Copyright (c) 1998-2017 Zend Technologies
    with Zend OPcache v7.0.18-0ubuntu0.17.04.1, Copyright (c) 1999-2017, by Zend Technologies
[+] Kernel version : 
	Linux sun 4.10.0-28-generic #32-Ubuntu SMP Fri Jun 30 05:32:18 UTC 2017 x86_64 x86_64 x86_64 GNU/Linux
[+] ================================
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
        13. [q|quit|exit] : quit
[sniper]=>
```

TODO :
- [x] 基础 shell 功能
- [x] 检测 shell 是否可用
- [ ] 维护目录栈
- [ ] WebShell批量管理
- [x] 初始化检测
- [x] 模块化
- [ ] 更深层的模块化
- [ ] UDP端口扫描
- [ ] 主机存活检测
- [ ] 处理反弹shell的时候的阻塞情况
- [x] 数据进行压缩
- [x] 检测代码/命令执行结果 (通过插入 token 来判断)
- [x] 检测目标服务器禁用的 PHP 函数
- [ ] 如果命令执行失败 , 则使用可替代的 PHP 函数
- [ ] HTTP代理实现
- [ ] SOCKS代理实现
- [ ] 编写多种编码器 , 对消息进行编码
- [ ] 在 HTTP 头部中隐藏信息
- [ ] 关联 MSF
- [x] 内核版本
- [ ] 检测 SUID 程序
- [x] 获取被禁用的函数列表
- [ ] 非阻塞式的反弹 shell
- [x] socat 反弹一个交互式的 shell (可用 vim 等全屏工具)
- [x] 检测可写目录
- [x] 检测配置文件错误
- [ ] 利用 PHP 常驻内存
- [x] 交互界面
- [ ] 帮助文档
- [ ] 使用一些通用的技巧来绕过 WAF
- [ ] webshell 生成器
- [x] 寻找可写 php 文件(.htaccess / .user.ini)来达到更深层的隐藏目的
- [ ] 不直接执行命令 , 而是构造一个比较隐蔽的漏洞
- [x] 反弹 shell 模块
- [ ] 检测边界防火墙端口 / 协议禁用情况
- [x] 端口扫描
- [ ] 自动检测更新
- [x] 日志分等级
- [ ] WIKI 模块
- [ ] 开发文档(如何编写插件)
- [x] 数据库支持
- [ ] 自动寻找配置文件
- [ ] 整站打包下载
- [x] 数据库管理
- [ ] 插件市场
- [ ] 处理 Ctrl + C 信号
- [ ] 支持命令历史 (readline库)
- [ ] 实现 PDO / mysql_connection 的数据库操作方式 (目前只实现了 mysqli_connection )

支持情况 :
```
测试环境 :
===================================
    攻击者 :
        Linux
        python 2.7
    被控者 :
        apache 2.4
        php 7.0
===================================
目前只支持攻击者为 Linux 平台
被控者为为 PHP 与 MYSQL
```
