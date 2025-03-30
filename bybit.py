from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import requests
import pandas as pd
import numpy as np

class CryptoScanner(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        
        self.capital_input = TextInput(hint_text="Enter Trading Capital ($)", multiline=False)
        self.add_widget(self.capital_input)
        
        self.scan_button = Button(text="Scan Patterns")
        self.scan_button.bind(on_press=self.scan_patterns)
        self.add_widget(self.scan_button)
        
        self.result_label = Label(text="Results will appear here")
        self.add_widget(self.result_label)
    
    def fetch_data(self, symbol, interval):
        url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={symbol}&interval={interval}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    
    def detect_pattern(self, df):
        close = df["close"].astype(float)
        pattern = "No Clear Pattern"
        tp1, tp2, tp3, sl = None, None, None, None
        
        if close.iloc[-1] > close.iloc[-2]:
            pattern = "Bullish Reversal"
            tp1, tp2, tp3 = close.iloc[-1] * 1.02, close.iloc[-1] * 1.04, close.iloc[-1] * 1.06
            sl = close.iloc[-1] * 0.98
        elif close.iloc[-1] < close.iloc[-2]:
            pattern = "Bearish Reversal"
            tp1, tp2, tp3 = close.iloc[-1] * 0.98, close.iloc[-1] * 0.96, close.iloc[-1] * 0.94
            sl = close.iloc[-1] * 1.02
        
        return pattern, tp1, tp2, tp3, sl
    
    def calculate_trade(self, capital, entry, tp1, tp2, tp3, sl):
        leverage = round(1000 / entry, 1)
        profit_tp1 = (tp1 - entry) * leverage
        profit_tp2 = (tp2 - entry) * leverage
        profit_tp3 = (tp3 - entry) * leverage
        loss = (entry - sl) * leverage
        return leverage, profit_tp1, profit_tp2, profit_tp3, loss
    
    def scan_patterns(self, instance):
        capital = float(self.capital_input.text) if self.capital_input.text else 100
        symbol = "BTCUSDT"
        interval = "15"
        data = self.fetch_data(symbol, interval)
        
        if data and "result" in data and "list" in data["result"]:
            columns = ["timestamp", "open", "high", "low", "close", "volume", "turnover"]
            df = pd.DataFrame(data["result"]["list"], columns=columns)
            pattern, tp1, tp2, tp3, sl = self.detect_pattern(df)
            leverage, profit_tp1, profit_tp2, profit_tp3, loss = self.calculate_trade(capital, df.iloc[-1]["close"], tp1, tp2, tp3, sl)
            
            result_text = f"Pattern: {pattern}\nTP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}\nSL: {sl}\nLeverage: {leverage}\nProfit TP1: {profit_tp1}\nProfit TP2: {profit_tp2}\nProfit TP3: {profit_tp3}\nLoss: {loss}"
            self.result_label.text = result_text
        else:
            self.result_label.text = "Error fetching data"

class CryptoScannerApp(App):
    def build(self):
        return CryptoScanner()

if __name__ == "__main__":
    CryptoScannerApp().run()
