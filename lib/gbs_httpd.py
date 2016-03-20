#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import socket
import subprocess
from gbs_util import GbsUtil


class GbsHttpDaemon:

    def __init__(self, param):
        self.param = param

    def run(self):
        cfgf = os.path.join(self.param.tmpDir, "httpd.conf")
        outf = os.path.join(self.param.logDir, "httpd-out.log")

        self._generateCfgFile(cfgf)
        GbsUtil.mkDirAndClear(self.param.webRootDir)
        
        cmd = ""
        cmd += "/usr/sbin/apache2 "
        cmd += "-d %s " % (self.param.tmpDir)
        cmd += "-f %s " % (cfgf)
        cmd += "-DFOREGROUND > %s" % (outf)
        proc = subprocess.Popen(cmd, shell=True, universal_newlines=True)

        return proc

    def _generateCfgFile(self, cfgf):
        APACHE_MODULES_DIR = "/usr/lib/apache2/modules"
        APACHE_PID_FILE = os.path.join(self.param.tmpDir, "httpd.pid")
        APACHE_ERROR_LOG = os.path.join(self.param.logDir, "httpd-error.log")
        APACHE_ACCESS_LOG = os.path.join(self.param.logDir, "httpd-access.log")

        buf = ""
        buf += "# Auto generated by gentoo-build-server\n"
        buf += "\n"
        buf += "LoadModule log_config_module  %s/mod_log_config.so\n" % (APACHE_MODULES_DIR)
        buf += "LoadModule env_module         %s/mod_env.so\n" % (APACHE_MODULES_DIR)
        buf += "LoadModule unixd_module       %s/mod_unixd.so\n" % (APACHE_MODULES_DIR)
        buf += "LoadModule alias_module       %s/mod_alias.so\n" % (APACHE_MODULES_DIR)
        if self.param.protocol == "HTTPS":
            buf += "LoadModule ssl_module         %s/mod_ssl.so\n" % (APACHE_MODULES_DIR)
        if self.param.protocol == "HTPASSWD":
            buf += "LoadModule auth_basic_module  %s/mod_auth_basic.so\n" % (APACHE_MODULES_DIR)
            buf += "LoadModule authn_core_module  %s/mod_authn_core.so\n" % (APACHE_MODULES_DIR)
            buf += "LoadModule authn_file_module  %s/mod_authn_file.so\n" % (APACHE_MODULES_DIR)
            buf += "LoadModule authz_core_module  %s/mod_authz_core.so\n" % (APACHE_MODULES_DIR)
            buf += "LoadModule authz_user_module  %s/mod_authz_user.so\n" % (APACHE_MODULES_DIR)
        buf += "LoadModule wsgi_module        %s/mod_wsgi.so\n" % (APACHE_MODULES_DIR)
        buf += "\n"
        buf += "ServerName %s\n" % (socket.gethostname())
        buf += "DocumentRoot \"%s\"\n" % (self.param.webRootDir)
        buf += "\n"
        buf += "PidFile \"%s\"\n" % (APACHE_PID_FILE)
        buf += "ErrorLog \"%s\"\n" % (APACHE_ERROR_LOG)
        buf += "LogFormat \"%h %l %u %t \\\"%r\\\" %>s %b \\\"%{Referer}i\\\" \\\"%{User-Agent}i\\\"\" common\n"
        buf += "CustomLog \"%s\" common\n" % (APACHE_ACCESS_LOG)
        buf += "\n"
        if self.param.protocol == "HTTP":
            buf += "Listen %d http\n" % (self.param.port)
        elif self.param.protocol == "HTTPS":
            buf += "Listen %d https\n" % (self.param.port)
        else:
            assert False
        buf += "\n"
        buf += "WSGIDaemonProcess gentoo_build_server\n"
        buf += "WSGIProcessGroup gentoo_build_server\n"
        buf += "WSGIScriptAlias / %s\n" % (os.path.join(self.param.wsgiDir, "main.wsgi"))
        buf += "\n"
        if self.param.authType == "HTPASSWD":
            buf += "<Directory %s>\n" % (self.param.wsgiDir)
            buf += "    AuthType Basic\n"
            buf += "    AuthName \"Gentoo Build Server\"\n"
            buf += "    AuthBasicProvider file\n"
            buf += "    AuthUserFile \"%s\"\n" % (self.param.clientPasswdFile)
            buf += "    Require valid-user\n"
            buf += "</Directory>\n"

        with open(cfgf, "w") as f:
            f.write(buf)