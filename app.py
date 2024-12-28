import tkinter as tk
from tkinter import ttk
import threading
import yfinance as yf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime
from collections import deque

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Window Properties
        self.title("Stock Price Tracker")
        self.geometry("1900x1000")

        # Create a frame for the left side
        self.left_frame = ttk.Frame(self, width=700, height=1000, padding=(10, 10))
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create input box for entering ticker
        self.label = ttk.Label(self.left_frame, text="Enter Stock Ticker:")
        self.label.pack(pady=(20, 5))

        self.entry = ttk.Entry(self.left_frame)
        self.entry.pack(pady=(5, 10))

        self.invalid_ticker_error_label = None

        # Button to add new ticker
        self.add_new_ticker_button = ttk.Button(self.left_frame, text="Track Ticker", command=self.add_new_ticker)
        self.add_new_ticker_button.pack(pady=(10, 5))

        # Create a listbox for tracked tickers
        self.ticker_listbox = tk.Listbox(self.left_frame, height=20)
        self.ticker_listbox.pack(pady=(10, 10), fill=tk.X)

        # Button to remove ticker
        self.remove_ticker_button = ttk.Button(self.left_frame, text="Remove Ticker", command=self.remove_ticker)
        self.remove_ticker_button.pack(pady=(5, 10))

        # Create a frame for the right side
        self.right_frame = ttk.Frame(self, width=1200, height=1000, padding=(10, 10))
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a figure for the plot
        self.figure, self.ax = plt.subplots()

        # Set default ticker
        self.tickers = []

        # Set plot labels and title
        self.ax.set_title("Stock Price Tracker")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)

        # Create a canvas to embed plot
        self.canvas = FigureCanvasTkAgg(self.figure, self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize data for plotting
        self.lines = {}  # Dictionary to hold plot lines for each ticker
        self.y_data = {}  # Dictionary to hold y-axis data for each ticker
        self.x_data = deque()  # Shared x-axis data (time)

        # Set up the animation
        self.ani = FuncAnimation(self.figure, self.update_plot, interval=1000)

    def fetch_stock_data(self, ticker, interval="1m", period="1d"):
        stock = yf.Ticker(ticker)
        try:
            data = stock.history(period=period, interval=interval)
            if data.empty:
                return None
            return data["Close"].iloc[-1]
        except Exception as e:
            print(f"Error fetching data for ticker {ticker}: {e}")
            return None

    def update_plot(self, frame):
        def fetch_prices():
            current_time = datetime.now().strftime("%H:%M:%S")

            if not self.x_data or self.x_data[-1] != current_time:
                self.x_data.append(current_time)
                if len(self.x_data) > 20:
                    self.x_data.popleft()

            for ticker in self.tickers:
                current_price = self.fetch_stock_data(ticker)
                if current_price is None:
                    continue

                self.y_data[ticker].append(current_price)
                if len(self.y_data[ticker]) > 20:
                    self.y_data[ticker].popleft()

                self.lines[ticker].set_data(range(len(self.x_data)), self.y_data[ticker])

            self.ax.set_xticks(range(len(self.x_data)))
            self.ax.set_xticklabels(self.x_data, rotation=45, ha="right")

            self.ax.relim()
            self.ax.autoscale_view()

            self.ax.legend(loc="upper left")

            self.canvas.draw()

        threading.Thread(target=fetch_prices, daemon=True).start()

    def add_new_ticker(self):
        new_ticker = self.entry.get().upper()

        if self.fetch_stock_data(new_ticker) is None:
            self.show_invalid_ticker_message("Invalid Ticker Symbol. Please try again.")
        elif new_ticker in self.tickers:
            self.show_invalid_ticker_message("Ticker already being tracked.")
        else:
            self.tickers.append(new_ticker)
            self.ticker_listbox.insert(tk.END, new_ticker)
            self.y_data[new_ticker] = deque()
            self.lines[new_ticker], = self.ax.plot([], [], label=new_ticker)
            self.clear_invalid_ticker_message()

    def remove_ticker(self):
        selected_index = self.ticker_listbox.curselection()
        if not selected_index:
            self.show_invalid_ticker_message("No ticker selected.")
            return

        ticker_to_remove = self.ticker_listbox.get(selected_index)
        self.ticker_listbox.delete(selected_index)

        if ticker_to_remove in self.tickers:
            self.tickers.remove(ticker_to_remove)
            del self.y_data[ticker_to_remove]
            self.lines[ticker_to_remove].remove()
            del self.lines[ticker_to_remove]

            self.ax.legend(loc="upper left")
            self.canvas.draw()

        self.clear_invalid_ticker_message()

    def show_invalid_ticker_message(self, message):
        if not self.invalid_ticker_error_label:
            self.invalid_ticker_error_label = ttk.Label(self.left_frame, text=message, foreground="red")
            self.invalid_ticker_error_label.pack(pady=10)
        else:
            self.invalid_ticker_error_label.config(text=message)

    def clear_invalid_ticker_message(self):
        if self.invalid_ticker_error_label:
            self.invalid_ticker_error_label.destroy()
            self.invalid_ticker_error_label = None

if __name__ == "__main__":
    app = App()
    app.mainloop()
