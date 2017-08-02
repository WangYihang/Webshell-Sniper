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

Example : 

> v1.1.0

[![A Pentest Example via Webshell-Sniper (YouTube)](./images/pentest_0.png)](https://www.youtube.com/watch?v=iAUwb8SSS4s)

[![A Pentest Example via Webshell-Sniper (YouTube)](./images/pentest_1.png)](https://www.youtube.com/watch?v=iAUwb8SSS4s)

> v1.0.5

[![v1.0.5](https://asciinema.org/a/Si84wbgKpRBmfyhrnPOL6H4nj.png)](https://asciinema.org/a/130893)


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
- [x] 下载文件
- [x] 下载文件使用正则过滤下载的文件名
- [x] 自定义参数下载文件
- [ ] 缓存
- [ ] 多线程
- [ ] 效率
- [ ] 上传文件
- [ ] 修复自定义 SQL 语句执行的输出问题
- [ ] 解决 nc 不能使用 -e 参数的问题
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
- [x] 检测 SUID 程序
- [x] 获取被禁用的函数列表
- [ ] 非阻塞式的反弹 shell
- [x] 设置默认命令执行目标
- [x] socat 反弹一个交互式的 shell (可用 vim 等全屏工具)
- [x] 检测可写目录
- [x] 检测配置文件错误
- [ ] 利用 PHP 常驻内存
- [ ] 使用代理
- [ ] Tor
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
- [x] 自动寻找配置文件
- [x] 整站打包下载
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
