import talib
import pandas as pd
import time
import requests
import tkinter as tk
import hmac
import base64
import hashlib
import json
from datetime import datetime
from tkinter import ttk
from threading import Thread

def get_history_candlestick_data(symbol, granularity, end_time, limit=100, product_type="usdt-futures"):
    base_url = "https://api.bitget.com/api/v2/mix/market/candles"

    # Convert end_time to string
    end_time_str = str(end_time)

    # Prepare request parameters
    params = {
        'symbol': symbol,
        'granularity': granularity,
        'endTime': end_time_str,
        'limit': limit,
        'productType': product_type
    }

    # Make the API request
    response = requests.get(base_url, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json().get('data', [])
        df = pd.DataFrame(data, columns=['time', 'entry', 'high', 'low', 'close',
                                         'volume_base', 'volume_quote'])
        df['time'] = pd.to_datetime(df['time'].astype(float), unit='ms')
        df.set_index('time', inplace=True)
        df = df.astype(float)
        return df
    else:
        # If the request was not successful, print the error message
        print(f"Error: {response.status_code} - {response.text}")
        return None

def get_latest_price(symbol, _product_type):
    base_url = "https://api.bitget.com/api/v2/mix/market/ticker?"

    params = {
        'symbol': symbol,
        'productType': _product_type
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        _data = response.json().get('data', [])
        return _data[0].get('lastPr')
    else:
        return None

def get_all_symbols(_product_type):
    base_url = "https://api.bitget.com/api/v2/mix/market/tickers?"
    params = {
        'productType': _product_type
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        _data = response.json().get('data', [])
        symbols = [item["symbol"] for item in _data]
        symbols = sorted(symbols)
        return symbols
    else:
        return None

def get_account_info(access_key, secret_key, passphrase, symbol, productType, marginCoin):
    # API endpoint
    url = "https://api.bitget.com/api/v2/mix/account/account"

    # Params
    params = {
        "symbol": symbol,
        "productType": productType,
        "marginCoin": marginCoin
    }

    # Current timestamp in milliseconds
    timestamp = str(int(time.time() * 1000))
    #Signature
    message = timestamp + f"GET/api/v2/mix/account/account?symbol={symbol}&productType={productType}&marginCoin={marginCoin}"
    signature = base64.b64encode(hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest())

    headers = {
        "ACCESS-KEY": access_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

    # Send the request
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        response_data = response.json()
        if 'data' in response_data:
            data_values = response_data['data']
            return data_values
        else:
            return None
    else:
        print(f"Request failed with status code {response.status_code}. Response content:")
        print(response.text)
        return None

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Parameters")
        # Bot
        self.bot = None

        # SMA Period
        sma_label = tk.Label(root, text="SMA Periodo:")
        sma_label.grid(row=0, column=0)
        self.sma_entry = tk.Entry(root)
        self.sma_entry.insert(0, "20")
        self.sma_entry.grid(row=0, column=1)

        # EMA Period
        ema_label = tk.Label(root, text="EMA Periodo:")
        ema_label.grid(row=1, column=0)
        self.ema_entry = tk.Entry(root)
        self.ema_entry.insert(0, "21")
        self.ema_entry.grid(row=1, column=1)

        # Granularidad
        granularidad_label = tk.Label(root, text="Granularidad:")
        granularidad_label.grid(row=2, column=0)
        granularidad_options = ["1m", "5m", "15m", "30m", "1h", "4h", "6h", "12h", "1d", "3d", "1w", "1M"]
        self.granularidad_combobox = ttk.Combobox(root, values=granularidad_options)
        self.granularidad_combobox.grid(row=2, column=1)
        self.granularidad_combobox.set("1m")

        # Product Type
        product_type_label = tk.Label(root, text="Product Type:")
        product_type_label.grid(row=3, column=0)
        product_type_options = ["usdt-futures", "usdc-futures", "susdt-futures", "susdc-futures"]
        self.product_type_combobox = ttk.Combobox(root, values=product_type_options, state="readonly")
        self.product_type_combobox.grid(row=3, column=1)
        self.product_type_combobox.bind("<<ComboboxSelected>>", self.update_symbol_options)

        # Symbol
        symbol_label = tk.Label(root, text="Simbolo:")
        symbol_label.grid(row=4, column=0)
        self.symbol_combobox = ttk.Combobox(root, state="readonly")
        self.symbol_combobox.grid(row=4, column=1)

        #Keys
        apikey_label = tk.Label(root, text="APIKEY:")
        apikey_label.grid(row=5, column=0)
        self.apikey_entry = tk.Entry(root, show="*")
        self.apikey_entry.grid(row=5, column=1)

        secretkey_label = tk.Label(root, text="SECRETKEY:")
        secretkey_label.grid(row=6, column=0)
        self.secretkey_entry = tk.Entry(root, show="*")
        self.secretkey_entry.grid(row=6, column=1)

        passphrase_label = tk.Label(root, text="PASSPHRASE")
        passphrase_label.grid(row=7, column=0)
        self.passphrase_entry = tk.Entry(root, show="*")
        self.passphrase_entry.grid(row=7, column=1)

        ordersize_label = tk.Label(root, text="Tamaño de la orden en % de patrimonio")
        ordersize_label.grid(row=0, column=2)
        self.ordersize_entry = tk.Entry(root)
        self.ordersize_entry.insert(0,"50")
        self.ordersize_entry.grid(row=0, column=3)

        operaciones_label = tk.Label(root, text="Efecto piramide")
        operaciones_label.grid(row=1, column=2)
        self.operaciones_entry = tk.Entry(root)
        self.operaciones_entry.insert(0,"1")
        self.operaciones_entry.grid(row=1, column=3)

        apalancamiento_label = tk.Label(root, text="Apalancamiento x")
        apalancamiento_label.grid(row=2, column =2)
        self.apalancamiento_entry = tk.Entry(root)
        self.apalancamiento_entry.insert(0, "1")
        self.apalancamiento_entry.grid(row=2, column=3)

        # Actualizaciones por minuto
        actualizaciones_label = tk.Label(root, text="Actualizaciones por minuto")
        actualizaciones_label.grid(row=3, column=2)
        self.actualizaciones_entry = tk.Spinbox(root, from_=0, to=100)
        self.actualizaciones_entry.delete(0, "end")
        self.actualizaciones_entry.insert(0, "30")
        self.actualizaciones_entry.grid(row=3, column=3)

        # Start Button
        self.start_button = tk.Button(root, text="Start", command=self.start_bot, state=tk.NORMAL)
        self.start_button.grid(row = 8, column = 0, columnspan = 2, pady = 10)

        # Stop Button
        self.stop_button = tk.Button(root, text="Stop", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.grid(row=8, column= 1, columnspan = 2, pady = 10)

        # Stop and close button
        self.stop_and_close_button = tk.Button(root, text="Stop+Cerrar", command=self.stop_bot_and_close_operations, state=tk.DISABLED)
        self.stop_and_close_button.grid(row=8, column=2, columnspan=2, pady=10)

        # Log Text
        log_label = tk.Label(root, text="Log:")
        log_label.grid(row=9, column=0, sticky="w")
        self.log_text = tk.Text(root, height=20, width=120)
        self.log_text.grid(row=10, column=0, columnspan=2, pady=10)

        #Order log Text
        order_log_label= tk.Label(root, text="Order Log:")
        order_log_label.grid(row=9, column=2, sticky="w")
        self.order_log_text = tk.Text(root, height=20, width=40)
        self.order_log_text.grid(row=10, column=2, columnspan=1, pady=10)


    def update_symbol_options(self, event):
        selected_product_type = self.product_type_combobox.get()

        # Fetch symbols based on the selected product type using requests
        symbols = get_all_symbols(selected_product_type)

        # Update the symbol combobox with the fetched symbols
        self.symbol_combobox["values"] = symbols
        self.symbol_combobox.current(0)  # Set the default selection

    def start_bot(self):
        sma_periodo = int(self.sma_entry.get())
        ema_periodo = int(self.ema_entry.get())
        granularidad = self.granularidad_combobox.get()
        product_type = self.product_type_combobox.get()
        simbolo = self.symbol_combobox.get()
        ordersize = self.ordersize_entry.get()
        pyramiding = self.operaciones_entry.get()
        apalancamiento = self.apalancamiento_entry.get()
        actualizaciones = int(self.actualizaciones_entry.get())

        #Keys
        api_key = self.apikey_entry.get()
        secretkey = self.secretkey_entry.get()
        passphrase = self.passphrase_entry.get()

        params_definidos = True

        if not sma_periodo:
            self.log_text.insert(tk.END, "Introduce sma periodo\n")
            params_definidos = False

        if not ema_periodo:
            self.log_text.insert(tk.END, "Introduce ema periodo\n")
            params_definidos = False

        if not granularidad:
            self.log_text.insert(tk.END, "Introduce granularidad\n")
            params_definidos = False

        if not product_type:
            self.log_text.insert(tk.END, "Introduce product type\n")
            params_definidos = False

        if not simbolo:
            self.log_text.insert(tk.END, "Introduce simbolo\n")
            params_definidos = False

        if not api_key:
            self.log_text.insert(tk.END, "Introduce APIKEY\n")
            params_definidos = False

        if not secretkey:
            self.log_text.insert(tk.END, "Introduce SECRETKEY\n")
            params_definidos = False

        if not passphrase:
            self.log_text.insert(tk.END, "Introduce PASSPHRASE\n")
            params_definidos = False

        if not ordersize:
            self.log_text.insert(tk.END, "Introduce tamaño de orden\n")
            params_definidos = False

        if not pyramiding:
            self.log_text.insert(tk.END, "Introduce valor efecto piramide\n")
            params_definidos = False

        if not apalancamiento:
            self.log_text.insert(tk.END, "Introduce valor de apalancamiento\n")
            params_definidos = False

        if params_definidos:
            self.start_button['state'] = tk.DISABLED
            self.stop_button['state'] = tk.NORMAL
            self.stop_and_close_button['state'] = tk.NORMAL
            self.bot = TradingBot(sma_periodo, ema_periodo, granularidad, product_type, simbolo, api_key, secretkey, passphrase, ordersize, pyramiding, apalancamiento, actualizaciones, log_text=self.log_text, order_log_text=self.order_log_text)
            bot_thread = Thread(target=self.bot.iniciar_bot)
            bot_thread.start()

    def stop_bot(self):
        self.bot.detener_bot()
        self.start_button['state'] = tk.NORMAL
        self.stop_button['state'] = tk.DISABLED
        self.stop_and_close_button['state'] = tk.DISABLED

    def stop_bot_and_close_operations(self):
        self.stop_bot()
        self.bot.cerrarOperaciones("long")
        self.bot.cerrarOperaciones("short")

class TradingBot:
    def __init__(self, sma_periodo, ema_periodo, granularidad, product_type, simbolo, api_key, secret_key, passphrase,
                 ordersize, pyramiding, leverage, actualizaciones, log_text, order_log_text):
        self.sma_periodo = sma_periodo
        self.ema_periodo = ema_periodo
        self.simbolo = simbolo
        self.granularidad = granularidad
        self.product_type = product_type

        self.margin_mode = "isolated"
        self.margin_coin = self.get_margin_coin(product_type)

        self.ordersize = ordersize
        self.pyramiding = pyramiding
        self.leverage = leverage

        self.actualizaciones = actualizaciones

        self.log_text = log_text
        self.log_text.insert(tk.END, "*" * 50 + "\n")
        self.log_text.insert(tk.END, "Bot creado con:\n")
        self.log_text.insert(tk.END, f"sma_periodo:{sma_periodo}\n")
        self.log_text.insert(tk.END, f"ema_periodo:{ema_periodo}\n")
        self.log_text.insert(tk.END, f"granularidad:{granularidad}\n")
        self.log_text.insert(tk.END, f"product_type:{product_type}\n")
        self.log_text.insert(tk.END, f"simbolo:{simbolo}\n")
        self.log_text.insert(tk.END, f"tamaño de la orden en % de patrimonio:{ordersize}\n")
        self.log_text.insert(tk.END, f"efecto piramide:{pyramiding}\n")
        self.log_text.insert(tk.END, f"apalancamiento:{leverage}\n")
        self.log_text.insert(tk.END, f"actualizaciones por minuto:{actualizaciones}\n")
        self.log_text.insert(tk.END, "*" * 50 + "\n")

        self.order_log_text = order_log_text

        #KEYS
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

        self.running = False

        self.buy_signal = False
        self.sell_signal = False
        self.orden_en_ejecucion = False
        self.orders_count = 0

    def iniciar_bot(self):
        self.running = True

        self.log_text.insert(tk.END, f"Informacion de la cuenta:\n")
        account_data = get_account_info(self.api_key, self.secret_key, self.passphrase, self.simbolo, self.product_type, self.margin_coin)
        cached_available = float(account_data['available'])
        self.log_text.insert(tk.END, f"Moneda de margen:{account_data['marginCoin']}\n"
                                     f"Margen disponible:{account_data['available']}\n")

        self.set_leverage_value(self.leverage,"long")
        self.set_leverage_value(self.leverage, "short")

        while self.running:
            # Sample OHLC data (replace this with your actual price data)
            data = get_history_candlestick_data(self.simbolo, self.granularidad, int(time.time() * 1000),
                                                product_type=self.product_type)

            # Define indicators
            src = data['close']
            closesma = talib.SMA(src, timeperiod=self.sma_periodo)
            ema = talib.EMA(src, timeperiod=self.ema_periodo)

            # Define the Bull Market Support Band as a variable
            bmsbmayor = pd.concat([closesma, ema], axis=1).max(axis=1)
            bmsbmenor = pd.concat([closesma, ema], axis=1).min(axis=1)

            ultimo_close = data['close'].iloc[-2]
            bmsb_mayor = bmsbmayor.iloc[-2]
            bmsb_menor = bmsbmenor.iloc[-2]
            close_anterior = data['close'].iloc[-3]
            bmsb_mayor_anterior = bmsbmayor.iloc[-3]
            bmsb_menor_anterior = bmsbmenor.iloc[-3]

            if (ultimo_close > bmsb_mayor) and (close_anterior < bmsb_mayor_anterior):
                self.log_text.insert(tk.END,'_' * 100 + "\n")
                self.log_text.insert(tk.END,
                    f'El precio de cierre ha cruzado de abajo hacia arriba la BMSB. Oportunidad de compra a las {datetime.now().time()}\n')
                self.log_text.insert(tk.END,
                    f"precio actual: {get_latest_price(self.simbolo, self.product_type)}, precio de cierre: {ultimo_close}, valores de la banda a eliminar:{bmsb_menor},{bmsb_mayor} \n")
                self.buy_signal = True
                self.sell_signal = False
            elif (ultimo_close < bmsb_menor) and (close_anterior > bmsb_menor_anterior):
                self.log_text.insert(tk.END, '_' * 100 + "\n")
                self.log_text.insert(tk.END,
                    f"El precio de cierre ha cruzado de arriba hacia abajo la BMSB. Oportunidad de venta a las {datetime.now().time()}\n")
                self.log_text.insert(tk.END,
                    f"precio actual: {get_latest_price(self.simbolo, self.product_type)}, precio de cierre: {ultimo_close}, valores de la banda a eliminar:{bmsb_menor},{bmsb_mayor} \n")
                self.buy_signal = False
                self.sell_signal = True
            else:
                self.log_text.insert(tk.END,'_' * 100 + "\n")
                self.log_text.insert(tk.END,f"El precio de cierre no ha cruzado la BMSB y son las {datetime.now().time()}\n")
                self.log_text.insert(tk.END,
                    f"precio actual: {get_latest_price(self.simbolo, self.product_type)}, precio de cierre: {ultimo_close}, valores de la banda a eliminar:{bmsb_menor},{bmsb_mayor}\n ")
                self.buy_signal = False
                self.sell_signal = False

            # Calcular los lotajes e importes usando los parametros recibidos de la interfaz y ejecutar las operaciones
            if self.buy_signal and self.orders_count < int(self.pyramiding) and not self.orden_en_ejecucion:
                #Cerrar operaciones de venta abierta y abrir una nueva operacion de compra
                if self.cerrarOperaciones("short"):
                    account_data = get_account_info(self.api_key, self.secret_key, self.passphrase, self.simbolo,
                                                    self.product_type, self.margin_coin)
                    size = float(self.ordersize) / 100 * cached_available
                    actual_available = float(account_data['available'])

                    if size > actual_available:
                        size = actual_available


                    self.order_log_text.insert(tk.END, "*" * 40 + "\n")
                    self.order_log_text.insert(tk.END, f"Se ha iniciado una nueva orden de compra\n")
                    self.order_log_text.insert(tk.END, f"parametros de la operacion de compra:\n"
                                                 f"Modo={self.margin_mode}\n"
                                                 f"Moneda de margen={self.margin_coin}\n"
                                                 f"Tamaño de la orden en {self.margin_coin}={size}\n")

                    coin_asking_price = self.get_asking_price(self.simbolo, self.product_type)
                    size = size / float(coin_asking_price)
                    self.order_log_text.insert(tk.END, f"Tamaño de la orden={size}\n")

                    #orders_count = self.abrirOperacionDeCompra(self.margin_mode, self.margin_coin, size)

                    compra_thread = Thread(target=self.bucleAbrirOperacionesDeCompra, args=(self.margin_mode, self.margin_coin, size))
                    compra_thread.start()

            if self.sell_signal and self.orders_count < int(self.pyramiding) and not self.orden_en_ejecucion:
                # TODO Cerrar operacion de compra abierta, abrir una nueva operacion de venta
                if self.cerrarOperaciones("long"):
                    account_data = get_account_info(self.api_key, self.secret_key, self.passphrase, self.simbolo,
                                                    self.product_type, self.margin_coin)
                    size = float(self.ordersize) / 100 * cached_available
                    actual_available = float(account_data['available'])

                    if size > actual_available:
                        size = actual_available

                    self.order_log_text.insert(tk.END, "*" * 40 + "\n")
                    self.order_log_text.insert(tk.END, f"Se ha iniciado una nueva orden de venta\n")
                    self.order_log_text.insert(tk.END, f"parametros de la operacion de compra:\n"
                                                 f"Modo={self.margin_mode}\n"
                                                 f"Moneda de margen={self.margin_coin}\n"
                                                 f"Tamaño de la orden en {self.margin_coin}={size}\n")

                    coin_asking_price = self.get_asking_price(self.simbolo, self.product_type)
                    size = size / float(coin_asking_price)
                    self.order_log_text.insert(tk.END, f"Tamaño de la orden={size}\n")

                    #orders_count = orders_count +self.abrirOperacionDeCompra(self.margin_mode, self.margin_coin, size)

                    venta_thread = Thread(target=self.bucleAbrirOperacionesDeVenta,
                                           args=(self.margin_mode, self.margin_coin, size))
                    venta_thread.start()

            self.log_text.insert(tk.END, f"Numero de operaciones abiertas:{self.orders_count}\n")
            self.log_text.insert(tk.END, '_' * 100 + "\n")
            self.log_text.see(tk.END)

            time.sleep(60/self.actualizaciones)

        self.log_text.insert(tk.END, f"El bot se ha detenido exitosamente:\n")
        self.log_text.insert(tk.END, "*" * 50 + "\n")

    def detener_bot(self):
        self.running = False

    def abrirOperacionDeVenta(self, marginMode, marginCoin, size):
        base_url = "https://api.bitget.com"
        endpoint = "/api/v2/mix/order/place-order"

        params = {
            "symbol": self.simbolo,
            "productType": self.product_type,
            "marginMode": marginMode,
            "marginCoin": marginCoin,
            "size": size,
            "side": "sell",
            "orderType": "market",
            "tradeSide": "open"
        }

        timestamp = str(int(time.time() * 1000))
        message = timestamp + "POST" + endpoint + json.dumps(params)
        signature = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        response = requests.post(base_url + endpoint, headers=headers, data=json.dumps(params))
        if response.status_code == 200:
            response_data = response.json()
            if 'data' in response_data:
                print(response.json())
                data_values = response_data['data']
                self.order_log_text.insert(tk.END, "Orden procesada exitosamente\n")
                self.orders_count = self.orders_count + 1
                return 1
            else:
                print(response.text)
                return 0
        else:
            print("Operacion de venta no realizada")
            print(response.text)
            return 0

    def abrirOperacionDeCompra(self, marginMode, marginCoin, size):
        base_url = "https://api.bitget.com"
        endpoint = "/api/v2/mix/order/place-order"

        params = {
            "symbol": self.simbolo,
            "productType": self.product_type,
            "marginMode": marginMode,
            "marginCoin": marginCoin,
            "size": size,
            "side": "buy",
            "orderType": "market",
            "tradeSide": "open"
        }

        timestamp = str(int(time.time() * 1000))
        message = timestamp + "POST" + endpoint + json.dumps(params)
        signature = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        response = requests.post(base_url + endpoint, headers=headers, data=json.dumps(params))
        if response.status_code == 200:
            response_data = response.json()
            if 'data' in response_data:
                print(response.json())
                data_values = response_data['data']
                self.order_log_text.insert(tk.END, "Orden procesada exitosamente\n")
                self.orders_count = self.orders_count + 1
                return 1
            else:
                print(response.text)
                return 0
        else:
            print("Operacion de compra no realizada")
            print(response.text)
            return 0

    def bucleAbrirOperacionesDeCompra(self,marginMode, marginCoin, size):
        operacion_ejecutada = 0
        size_percentage = size
        percentage = 0.0
        self.orden_en_ejecucion = True
        while self.buy_signal and operacion_ejecutada == 0 and size_percentage > 0:
            size_percentage = size * (1 - percentage)
            percentage += 0.01
            operacion_ejecutada = self.abrirOperacionDeCompra(marginMode,marginCoin,size_percentage)
        self.orden_en_ejecucion = False
        return operacion_ejecutada

    def bucleAbrirOperacionesDeVenta(self,marginMode, marginCoin, size):
        operacion_ejecutada = 0
        size_percentage = size
        percentage = 0.0
        self.orden_en_ejecucion = True
        while self.sell_signal and operacion_ejecutada == 0 and size_percentage > 0:
            size_percentage = size * (1 - percentage)
            percentage += 0.01
            operacion_ejecutada = self.abrirOperacionDeVenta(marginMode, marginCoin, size)
        self.orden_en_ejecucion = False
        return operacion_ejecutada

    def cerrarOperaciones(self, holdSide):
        base_url = "https://api.bitget.com"
        endpoint = "/api/v2/mix/order/close-positions"

        params = {
            "symbol": self.simbolo,
            "holdSide": holdSide,
            "productType": self.product_type,
        }

        timestamp = str(int(time.time() * 1000))
        message = timestamp + "POST" + endpoint + json.dumps(params)
        signature = base64.b64encode(hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        response = requests.post(base_url + endpoint, headers=headers, data=json.dumps(params))
        response_data = response.json()
        print(response.json())
        print("Se cerro")
        if response.status_code == 200 or response_data['code'] == '22002':
            if response_data['code'] == '00000':
                self.orders_count = 0
                self.log_text.insert(tk.END, f"Las operaciones en {holdSide} se han cerrado con exito.\n")
                return True
            else:
                self.log_text.insert(tk.END, f"No hay operaciones en {holdSide}\n")
                return True
        else:
            self.log_text.insert(tk.END, f"No se cerro ninguna operacion en {holdSide}\n")
            return False

    def set_leverage_value(self, leverage, holdSide):
        base_url = "https://api.bitget.com"
        endpoint = "/api/v2/mix/account/set-leverage"

        params = {
            "symbol": self.simbolo,
            "productType": self.product_type,
            "marginCoin": self.margin_coin,
            "leverage": leverage,
            "holdSide": holdSide,
        }

        timestamp = str(int(time.time() * 1000))
        message = timestamp + "POST" + endpoint + json.dumps(params)
        signature = base64.b64encode(
            hmac.new(self.secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest())

        headers = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json"
        }

        response = requests.post(base_url + endpoint, headers=headers, data=json.dumps(params))
        if response.status_code == 200:
            response_data = response.json()
            if 'data' in response_data:
                print(response.json())
                self.log_text.insert(tk.END, f"Apalancamiento {holdSide} cambiado a {leverage}x\n")
                data_values = response_data['data']
                return data_values
            else:
                print(response.text)
                return None
        else:
            print("No se pudo cambiar el apalancamiento en long")
            print(response.text)
            return None

    def get_margin_coin(self, productType):
        if productType == "usdt-futures":
            return "USDT"

        if productType == "usdc-futures":
            return "USDC"

        if productType == "susdt-futures":
            return "SUSDT"

        if productType == "susdc-futures":
            return "SUSDC"

    def get_asking_price(self, symbol, _productType):
        base_url = "https://api.bitget.com/api/v2/mix/market/ticker?"

        params = {
            'symbol': symbol,
            'productType': _productType
        }

        response = requests.get(base_url, params=params)

        if response.status_code == 200:
            _data = response.json().get('data', [])
            return _data[0].get('askPr')
        else:
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
    input("Press Enter to exit")
