import json
import os
import requests
from rx import Observable, Observer


def check_forecast(event, context):
    forecast = get_forecast()
    handle_forecast(forecast)
    return {
        'forecast': forecast,
    }


def get_forecast():
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    params = {
        'q': 'Warszawa,PL',
        'appid': os.getenv('OPENWEATHER_APIKEY'),
        'units': 'metric',
    }
    response = requests.get(url, params)
    response.raise_for_status()
    forecast = response.json()['list']
    return forecast

class SmsObserver(Observer):

    def __init__(self, api_key, msisdn, test=False):
        self._api_key = api_key
        self._msisdn = msisdn
        self._messages = []
        self._test = test

    def __len__(self):
        return len('\n'.join(self._messages))

    def on_next(self, forecast):
        print(f'Received forecast: {forecast}')
        self._messages.append(f"{forecast[0]}: {forecast[1]}")

    def on_completed(self):
        print('Done')
        url = 'https://api.smsapi.pl/sms.do'
        params = {
            'access_token': self._api_key,
            'to': self._msisdn,
            'message': '\n'.join(self._messages),
            'from': 'Eco',
            'details': 1,
            'normalize': 1,
            'format': 'json',
            'test': int(self._test),
        }
        resp = requests.post(url, params)
        resp.raise_for_status()
        if self._test:
            print(resp.text)

    def on_error(self, error):
        print(f'Error occurred: {error}')

def handle_forecast(forecast):
    Observable.from_(forecast) \
        .map(lambda f: (f['dt_txt'], f['main']['temp_min'])) \
        .filter(lambda f: f[1] < 10) \
        .subscribe(SmsObserver(
            api_key=os.getenv('SMSAPI_KEY'),
            msisdn=os.getenv('MSISDN'),
            test=False,
        ))
