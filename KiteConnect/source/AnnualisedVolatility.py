import requests, json, logging

class AnnualisedVolatility():

    def __init__(self, underlying, expiry):
        self.underlying = underlying
        self.expiry = expiry

    def GetAnnualisedVolatility(self):
        url = 'https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/ajaxFOGetQuoteJSON.jsp?underlying=' + self.underlying + '&instrument=FUTIDX&expiry=' + self.expiry + '&type=SELECT&strike=SELECT'
        referer = 'https://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuoteFO.jsp?underlying=' + self.underlying + '&instrument=FUTIDX&expiry=' + self.expiry +'&type=-&strike=-'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5','Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': referer}
        counter = 10
        flag = False
        annVolatility = 0.0
        while(counter >= 0 and flag == False):
            try:
                counter -= 1
                response = requests.get(url, headers = headers)
                if response.status_code != 200:
                    continue
                data = response.text
                if data.find('annualisedVolatility') != -1 and data.find('data') != -1:
                    dataDict = json.loads(data)
                    annVolatility = float(dataDict['data'][0]['annualisedVolatility'])
                    flag = True
                    break
            except Exception as e:
                self.DumpExceptionInfo(e, "GetAnnualisedVolatility")

        return annVolatility

    def DumpExceptionInfo(self, e, funcName):
        logging.error("Error in AnnualisedVolatility::" + funcName, exc_info=True)
        print e
        print "Error in AnnualisedVolatility::" + funcName