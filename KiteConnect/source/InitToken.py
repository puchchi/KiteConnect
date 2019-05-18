import hashlib
import requests

from Utility import *


class TokenManager(object):
    __instance = None

    @staticmethod
    def GetInstance():
        ''' Static access method'''
        if TokenManager.__instance == None:
            TokenManager()
        return TokenManager.__instance

    def __init__(self):
        if TokenManager.__instance != None:
            raise Exception ("TokenManager!This class is singleton!")
        else:
            TokenManager.__instance = self

        print "Initializing token manager....."
        # First we will set data we have on disk
        self.SetApiKey()
        self.SetApiSecretKey()
        self.SetUserId()
        self.SetPassword()
        self.SetPin()

        # Retireve and set request token
        print "Retrieving request token....."
        self.SetRequestToken(self.RetrieveRequestToken())

        # Second get other token from api request and write them on disk
        print "Retrieving access token....."
        self.RetrieveAccessToken()

        # Third read newly written token from disk
        self.SetAccessToken()

    """ Api_key getter setter"""
    def GetApiKey(self):
        if self.CheckInstance():
            return self.apiKey
        return ""

    def SetApiKey(self):
        with open(KEYS_LOCATION + API_KEY_FILENAME, 'r') as file:
            self.apiKey = file.read()

    """ Api secret key getter setter"""
    def GetApiSecretKey(self):
        if self.CheckInstance():
            return self.apiSecretKey
        return ""

    def SetApiSecretKey(self):
        with open(KEYS_LOCATION + API_SECRET_FILENAME, 'r') as file:
            self.apiSecretKey = file.read()

    """ User id getter setter"""
    def GetUserId(self):
        if self.CheckInstance():
            return self.userId
        return ""

    def SetUserId(self):
        with open(KEYS_LOCATION + USERID_FILENAME, 'r') as file:
            self.userId = file.read()

    """ Password getter setter"""
    def GetPassword(self):
        if self.CheckInstance():
            return self.password
        return ""

    def SetPassword(self):
        with open(KEYS_LOCATION + PASSWORD_FILENAME, 'r') as file:
            self.password = file.read()

    """ Pin getter setter"""
    def GetPin(self):
        if self.CheckInstance():
            return self.pin
        return ""

    def SetPin(self):
        with open(KEYS_LOCATION + PIN_FILENAME, 'r') as file:
            self.pin = file.read()

    """ Access token getter setter"""
    def GetAccessToken(self):
        if self.CheckInstance():
            return self.accessToken
        return ""

    def SetAccessToken(self):
        with open(KEYS_LOCATION + ACCESS_TOKEN_FILENAME, 'r') as file:
            self.accessToken = file.read()

    def WriteAccessTokenToFile(self, access_token):
        with open(KEYS_LOCATION + ACCESS_TOKEN_FILENAME, 'w+') as file:
            return file.write(access_token)

    def RetrieveAccessToken(self):
        checkSumString = self.GetApiKey() + self.GetRequestToken() + self.GetApiSecretKey()
        checkSumHash = GETSHA256(checkSumString)

        header = {'X-Kite-Version':'3',}
        data = {'api_key':self.GetApiKey(), 'request_token':self.GetRequestToken(), 'checksum': checkSumHash}
        response = requests.post(ACCESS_TOKEN_URL, data=data, headers=header)

        responseData = response.json()
        if responseData.has_key('error_type') and responseData['error_type'] == 'TokenException':
            raise Exception("Token exception: " + responseData['message'])
        elif responseData.has_key('data'):
            userData = responseData['data']
            if userData.has_key('access_token'):
                self.WriteAccessTokenToFile(userData['access_token'])
                print "Access token retrieved successfully....."

    """ Request token getter and setter"""
    def GetRequestToken(self):
        if self.CheckInstance():
            return self.requestToken
        return ""

    def SetRequestToken(self, requestToken):
        self.requestToken = requestToken

    def RetrieveRequestToken(self):
        header1 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5','Content-Type': 'application/x-www-form-urlencoded',
                    'Connection': 'close', 'Upgrade-Insecure-Requests': '1'}
        _url1 = 'https://kite.zerodha.com/connect/login?v=3&api_key=' + self.GetApiKey()
        response = requests.get(_url1, headers=header1)
        self.CheckResponse(response)
        responseUrl = response.url

        # Now we will get sess_id from response url
        if responseUrl.find('sess_id') == -1:
            raise "Session id not found in url1"
        sessionID = responseUrl.split('sess_id=')[1].split('&')[0]

        header2 = header1
        _url2 = 'https://kite.zerodha.com/connect/login?api_key=' + self.GetApiKey() + '&sess_id=' + sessionID
        response = requests.get(_url2, headers=header2)
        self.CheckResponse(response)
        cookies = response.cookies.get_dict()

        _url3 = 'https://kite.zerodha.com/api/login'
        header3 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/x-www-form-urlencoded',
                    'Connection': 'close', 'Upgrade-Insecure-Requests': '1',
                    'Referer': _url2, 'X-Kite-Version': '2.1.0',
                    'X-Kite-Userid': self.GetUserId(), 'X-CSRFTOKEN': 'undefined'}
        params = {'user_id':self.GetUserId(), 'password':self.GetPassword()}
        response = requests.post(_url3, headers=header3, data=params, cookies=cookies)
        self.CheckResponse(response)
        responseDict = response.json()

        # Check if we are on pin submission page
        if responseDict['status'] == 'success' and responseDict['data']['twofa_status'] == 'active':
            _url4 = 'https://kite.zerodha.com/api/twofa'
            header4 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/x-www-form-urlencoded',
                        'Connection': 'close', 'Upgrade-Insecure-Requests': '1',
                        'Referer': _url2, 'X-Kite-Version': '2.1.0',
                        'X-Kite-Userid': self.GetUserId(), 'X-CSRFTOKEN': 'undefined'}
            data = {'user_id':self.GetUserId(), 'request_id':responseDict['data']['request_id'], 'twofa_value':self.GetPin()}
            response = requests.post(_url4, headers=header4, data=data, cookies=cookies)
            self.CheckResponse(response)
            newCookies = response.cookies.get_dict()

            # adding new cookies in old cookies
            cookies.update(newCookies)
            _url5 = 'https://kite.zerodha.com/connect/login?api_key=' + self.GetApiKey() + '&sess_id=' + sessionID + '&skip_session=true'
            header5 ={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5', 'Content-Type': 'application/x-www-form-urlencoded',
                        'Connection': 'close', 'Upgrade-Insecure-Requests': '1',
                        'Referer': _url2}
            try:
                response = requests.get(_url5, headers=header5, cookies=cookies, allow_redirects=False)
                if response.status_code == 302:         # Redirection
                    redirectedUrl = response.headers['Location']
                    if redirectedUrl.find('request_token') != -1:
                        requestToken = redirectedUrl.split('request_token=')[1].split('&')[0]
                        print "Request token retrieved successfully....."
                        return requestToken
            except requests.exceptions.ConnectionError as e:
                print e
        return ""

    def CheckInstance(self):
        if TokenManager.__instance == None:
            return False
        return True

    def CheckResponse(self, response):
        if response.status_code != 200:
            raise "Bad response!!!"


