import json
import requests
import urllib3
import urlparse

from NVMeshSDK import LoggerUtils
from NVMeshSDK.Utils import Utils

urllib3.disable_warnings()


class ConnectionManagerError(Exception):
    pass


class ManagementTimeout(ConnectionManagerError):
    def __init__(self, iport, msg=''):
        ConnectionManagerError.__init__(self, 'Could not connect to Management at {0}'.format(iport), msg)


class ManagementLoginFailed(ConnectionManagerError):
    def __init__(self, iport, msg=''):
        ConnectionManagerError.__init__(self, 'Could not login to Management at {0}'.format(iport), msg)


class ManagementHTTPError(ConnectionManagerError):
    def __init__(self, res):
        self.status_code = res.status_code
        self.message = "Reason:{0} Content:{1}".format(res.reason, res.content)


class ConnectionManager:
    DEFAULT_USERNAME = "app@excelero.com"
    DEFAULT_PASSWORD = "admin"
    DEFAULT_NVMESH_CONFIG_FILE = '/etc/opt/NVMesh/nvmesh.conf'

    __instance = None

    @staticmethod
    def getInstance(managementServer=None, user=DEFAULT_USERNAME, password=DEFAULT_PASSWORD,
                 configFile=DEFAULT_NVMESH_CONFIG_FILE, logToSysLog=True):
        if ConnectionManager.__instance is None:
            ConnectionManager(managementServer, user, password, configFile, logToSysLog)
        return ConnectionManager.__instance

    def __init__(self, managementServer=None, user=DEFAULT_USERNAME, password=DEFAULT_PASSWORD,
                 configFile=DEFAULT_NVMESH_CONFIG_FILE, logToSysLog=True):
        if ConnectionManager.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            ConnectionManager.__instance = self
            self.managementServer = None
            self.httpRequestTimeout = 60
            self.configFile = configFile
            self.setManagementServer(managementServer)
            self.user = user
            self.password = password
            self.logger = LoggerUtils.getLoggerWithHandler('ConnectionManager', logLevel=LoggerUtils.Consts.ManagementLogLevel.INFO, logToSysLog=logToSysLog)
            self.session = requests.session()
            self.isAlive()

    def setManagementServer(self, managementServers=None):
        if managementServers:
            if isinstance(managementServers, list):
                self.managementServers = managementServers
            else:
                self.managementServers = [managementServers]
        else:
            self.managementSetConfigs()

    def managementSetConfigs(self):
        configs = Utils.readConfFile(self.configFile)
        if not configs:
            self.managementServers = ['https://localhost:4000']
        else:
            if 'MANAGEMENT_PROTOCOL' in configs:
                protocol = configs['MANAGEMENT_PROTOCOL']
            else:
                raise Exception('MANAGEMENT_PROTOCOL variable could not be found in: {0}'.format(self.configFile))

            if 'MANAGEMENT_SERVERS' in configs:
                servers = configs['MANAGEMENT_SERVERS'].replace('4001', '4000').split(',')
            else:
                raise Exception('MANAGEMENT_SERVERS variable could not be found in: {0}'.format(self.configFile))

            if 'HTTP_REQUEST_TIMEOUT' in configs:
                self.httpRequestTimeout = configs['HTTP_REQUEST_TIMEOUT']

            self.managementServers = []
            for server in servers:
                self.managementServers = self.managementServers + [protocol + '://' + server]

        return self.managementServers

    def isAlive(self):
        try:
            err, out = self.get('/isAlive')
            return True if not err else False
        except ManagementLoginFailed as ex:
            return False

    def post(self, route, payload=None):
        return self.request('post', route, payload)

    def get(self, route, payload=None):
        return self.request('get', route, payload)

    def request(self, method, route, payload=None, numberOfRetries=0):
        for i in range(len(self.managementServers)):
            self.managementServer = self.managementServers[0]
            try:
                return self.do_request(method, route, payload, numberOfRetries)
            except ManagementTimeout as ex:
                # put it as last
                self.managementServers.append(self.managementServers.pop(0))

        raise ManagementTimeout(route, "Timeout from all Management Servers")

    def do_request(self, method, route, payload=None, numberOfRetries=0):
        res = None
        if route != '/isAlive':
            self.logger.debug(
                'request method={0} route={1} payload={2} retries={3}'.format(method, route, payload, numberOfRetries))
        url = ''
        try:
            url = urlparse.urljoin(self.managementServer, route)
            if method == 'post':
                res = self.session.post(url, json=payload, verify=False, timeout=self.httpRequestTimeout)
            elif method == 'get':
                res = self.session.get(url, params=payload, verify=False, timeout=self.httpRequestTimeout)

            if '/login' in res.text:
                self.login()
                numberOfRetries += 1
                if numberOfRetries < 3:
                    return self.request(method, route, payload, numberOfRetries)
                else:
                    raise ManagementLoginFailed(iport=url)

        except requests.RequestException as ex:
            raise ManagementTimeout(url, ex.message)

        jsonObj = None
        err = None

        if route != '/isAlive':
            self.logger.debug('route {0} got response: {1}'.format(route, res.content))

        if res.status_code in [200, 304]:
            try:
                if res.content:
                    jsonObj = json.loads(res.content)
            except Exception as ex:
                err = {
                    "code": res.status_code,
                    "message": ex.message,
                    "content": res.content
                }
        else:
            err = {
                "code": res.status_code,
                "message": res.reason,
                "content": res.content
            }

        return err, jsonObj

    def login(self):
        try:
            out = self.session.post("{}/login".format(self.managementServer),
                              data={"username": self.user, "password": self.password}, verify=False)

        except requests.ConnectionError as ex:
            raise ManagementTimeout(self.managementServer, ex.message)
