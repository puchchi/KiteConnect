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

        # First we will set data we have on disk
        self.SetApiKey()
        self.SetApiSecretKey()
        self.SetRequestToken()

        # Second get other token from api request and write them on disk
        self.RetrieveAccessAndRefreshToken()

        # Third read newly written token from disk
        self.SetAccessToken()
        self.SetRefreshToken()

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

    """ Request token getter setter"""
    def GetRequestToken(self):
        return self.requestToken

    def SetRequestToken(self):
        self.requestToken = REQUEST_TOKEN

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

    def RetrieveAccessAndRefreshToken(self):
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
            if userData.has_key('refresh_token'):
                self.WriteRefreshTokenToFile(userData['refresh_token'])

    """ Refresh token getter setter"""
    def GetRefreshToken(self):
        if self.CheckInstance():
            return self.refreshToken
        return ""

    def SetRefreshToken(self):
        with open(KEYS_LOCATION + REFRESH_TOKEN_FILENAME, 'r') as file:
            self.refreshToken = file.read()

    def WriteRefreshTokenToFile(self, refresh_token):
        with open(KEYS_LOCATION + REFRESH_TOKEN_FILENAME, 'w+') as file:
            return file.write(refresh_token)

    def CheckInstance(self):
        if TokenManager.__instance == None:
            return False
        return True

