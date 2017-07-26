# websniper

Usage :
```
Usage : 
        python websniper.py [URL] [METHOD] [AUTH]
Example : 
        python websniper.py http://127.0.0.1/c.php POST c
Author : 
        WangYihang <wangyihanger@gmail.com>
```

ScreenShot : 
![ScreenShot](example.png)

TODO :
- [x] 基础 shell 功能
- [x] 检测 shell 是否可用
- [ ] 维护目录栈
- [ ] WebShell批量管理
- [x] 初始化检测
- [ ] 模块化
- [x] 检测代码/命令执行结果 (通过插入 token 来判断)
- [x] 检测目标服务器禁用的 PHP 函数
- [ ] 如果命令执行失败 , 则使用可替代的 PHP 函数
- [ ] HTTP代理实现
- [ ] SOCKS代理实现
- [ ] 编写多种编码器 , 对消息进行编码
- [ ] 在 HTTP 头部中隐藏信息
- [ ] 关联 MSF
- [ ] 内核版本
- [ ] 检测 SUID 程序
- [ ] 检测可写目录
- [ ] 检测配置文件错误
- [ ] 利用 PHP 常驻内存
- [ ] 交互界面
- [ ] 帮助文档
- [ ] 使用一些通用的技巧来绕过 WAF
- [ ] webshell 生成器
- [ ] 寻找可写 php 文件(.htaccess / .user.ini)来达到更深层的隐藏目的
- [ ] 不直接执行命令 , 而是构造一个比较隐蔽的漏洞
- [ ] 反弹 shell 模块
- [ ] 检测边界防火墙端口 / 协议禁用情况
