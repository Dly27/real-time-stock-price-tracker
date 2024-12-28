import tkinter as tk
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
        self.left_frame = tk.Frame(self, width=700, height=1000)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create input box for entering ticker
        self.label = tk.Label(self.left_frame, text="Enter Stock Ticker:")
        self.label.pack(pady=20)
        self.entry = tk.Entry(self.left_frame)
        self.entry.pack(pady=10)
        self.invalid_ticker_error_label = None

        # Button to add new ticker written input box to plot
        self.add_new_ticker_button = tk.Button(self.left_frame, text="Track ticker", command=self.add_new_ticker)
        self.add_new_ticker_button.pack(pady=10)

        # Button to remove ticker written in input box from plot
        self.remove_ticker_button = tk.Button(self.left_frame, text="Remove ticker", command=self.remove_ticker)
        self.remove_ticker_button.pack(pady=10)

        # Create a frame for the right side
        self.right_frame = tk.Frame(self, width=1200, height=1000)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a figure for the plot
        self.figure, self.ax = plt.subplots()

        # Set default ticker
        self.tickers = []

        # Set plot labels and title
        self.ax.set_title("Stock price tracker")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.ticklabel_format(style='plain')

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
            # Handle any error that occurs
            print(f"Error fetching data for ticker {ticker}: {e}")
            return None

    def update_plot(self, frame):
        # Fetch current stock prices in a thread to prevent GUI blocking
        def fetch_prices():
            current_time = datetime.now().strftime("%H:%M:%S")  # HH:MM:SS time format

            # Only append new time if it's different from the last one
            if not self.x_data or self.x_data[-1] != current_time:
                self.x_data.append(current_time)
                if len(self.x_data) > 20:  # Limit to last 20 points
                    self.x_data.popleft()

            for ticker in self.tickers:
                current_price = self.fetch_stock_data(ticker)
                if current_price is None:
                    continue  # Skip if no valid price data

                # Update the y_data for the current ticker
                self.y_data[ticker].append(current_price)
                if len(self.y_data[ticker]) > 20:  # Limit to last 20 points
                    self.y_data[ticker].popleft()

                # Update line data
                self.lines[ticker].set_data(range(len(self.x_data)), self.y_data[ticker])

            # Set x-axis labels
            self.ax.set_xticks(range(len(self.x_data)))
            self.ax.set_xticklabels(self.x_data, rotation=45, ha="right")

            # Adjust axes limits
            self.ax.relim()
            self.ax.autoscale_view()

            # Update legend dynamically
            self.ax.legend(loc="upper left")

            # Redraw canvas
            self.canvas.draw()

        threading.Thread(target=fetch_prices, daemon=True).start()

    def add_new_ticker(self):
        # Update the ticker symbol based on input box value
        new_ticker = self.entry.get().upper()

        # Check if new ticker is valid
        if self.fetch_stock_data(new_ticker) is None:
            self.show_invalid_ticker_message("Invalid Ticker Symbol. Please try again.")
        elif new_ticker in self.tickers:
            self.show_invalid_ticker_message("Ticker already being tracked.")
        else:
            self.tickers.append(new_ticker)
            self.y_data[new_ticker] = deque()
            self.lines[new_ticker], = self.ax.plot([], [], label=new_ticker)
            print(f"Tracking new ticker: {new_ticker}")
            self.clear_invalid_ticker_message()
    def remove_ticker(self):
        ticker_to_remove = self.entry.get().upper()

        if ticker_to_remove not in self.tickers:
            self.show_invalid_ticker_message("Ticker not being tracked")
        else:
            # Remove the ticker from tracked lists and dictionaries
            self.tickers.remove(ticker_to_remove)
            del self.y_data[ticker_to_remove]
            self.lines[ticker_to_remove].remove()  # Remove the plot line
            del self.lines[ticker_to_remove]

            # Redraw the canvas
            self.ax.legend(loc="upper left")
            self.canvas.draw()

            self.clear_invalid_ticker_message()

    def show_invalid_ticker_message(self, message):
        # Create the error label if it doesn't exist
        if not self.invalid_ticker_error_label:
            self.invalid_ticker_error_label = tk.Label(self.left_frame, text=message, fg="red")
            self.invalid_ticker_error_label.pack(pady=10)
        else:
            # Update the existing label's text
            self.invalid_ticker_error_label.config(text=message)

    def clear_invalid_ticker_message(self):
        # Clear and destroy the error label if it exists
        if self.invalid_ticker_error_label:
            self.invalid_ticker_error_label.destroy()
            self.invalid_ticker_error_label = None


if __name__ == "__main__":
    app = App()
    app.mainloop()
