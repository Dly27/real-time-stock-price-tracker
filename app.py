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
        self.entry.insert(0, "AAPL")  # Default ticker
        self.invalid_ticker_error_label = None

        # Button to change ticker symbol
        self.submit_button = tk.Button(self.left_frame, text="Submit", command=self.update_ticker)
        self.submit_button.pack(pady=10)

        # Create a frame for the right side (where the plot will go)
        self.right_frame = tk.Frame(self, width=1200, height=1000)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Create a figure for plotting
        self.figure, self.ax = plt.subplots()

        self.ticker = "AAPL"

        # Set plot labels and title
        self.ax.set_title(f"{self.ticker}")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Value")
        self.ax.ticklabel_format(style='plain')

        # Create a canvas to embed the plot into the Tkinter window
        self.canvas = FigureCanvasTkAgg(self.figure, self.right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Initialize data for plotting
        self.x_data = deque()
        self.y_data = deque()

        # Create the plot line object
        self.line, = self.ax.plot([], [], label="Stock Price")

        # Set up the animation
        self.ani = FuncAnimation(self.figure, self.update_plot, interval=1000)

    def fetch_stock_data(self, ticker, interval="1m", period="1d"):
        stock = yf.Ticker(ticker)
        try:
            data = stock.history(period=period, interval=interval)
            # If data is empty, it's likely an invalid ticker
            if data.empty:
                return None
            return data["Close"].iloc[-1]
        except Exception as e:
            # Handle any error that occurs (e.g., invalid ticker)
            print(f"Error fetching data for ticker {ticker}: {e}")
            return None

    def update_plot(self, frame):
        # Fetch current stock price in a thread to prevent GUI blocking
        def fetch_price():
            current_price = self.fetch_stock_data(self.ticker)
            if current_price is None:
                return  # Skip if no valid price data

            current_time = datetime.now().strftime("%H:%M:%S")  # Format time as HH:MM:SS
            self.x_data.append(current_time)
            self.y_data.append(current_price)

            # Limit x-axis to the last 20 points for better visualization
            if len(self.x_data) > 20:
                self.x_data.popleft()
                self.y_data.popleft()

            # Update the line data
            self.line.set_data(range(len(self.x_data)), self.y_data)

            # Set x-axis labels
            self.ax.set_xticks(range(len(self.x_data)))
            self.ax.set_xticklabels(self.x_data, rotation=45, ha="right")

            # Adjust axes limits
            self.ax.relim()
            self.ax.autoscale_view()

            # Redraw the canvas efficiently
            self.canvas.draw()

        threading.Thread(target=fetch_price, daemon=True).start()

    def update_ticker(self):
        # Update the ticker symbol based on input box value
        new_ticker = self.entry.get().upper()

        # Check if new ticker is valid
        if self.fetch_stock_data(new_ticker) is None:
            self.show_invalid_ticker_message("Invalid Ticker Symbol. Please try again.")
        else:
            self.ticker = new_ticker
            self.ax.set_title(f"{self.ticker}")  # Update plot title
            print(f"Tracking new ticker: {self.ticker}")
            self.clear_invalid_ticker_message()

    def show_invalid_ticker_message(self, message):
        # Only create the label if it doesn't exist
        if not hasattr(self, 'error_label'):
            self.invalid_ticker_error_label = tk.Label(self.left_frame, text=message, fg="red")
            self.invalid_ticker_error_label.pack(pady=10)
        else:
            # Update the existing label's text
            self.invalid_ticker_error_label.config(text=message)

    def clear_invalid_ticker_message(self):
        # Clear previous invalid ticker message if it exists
        if hasattr(self, 'error_label'):
            self.invalid_ticker_error_label.destroy()
            del self.invalid_ticker_error_label

if __name__ == "__main__":
    app = App()
    app.mainloop()
