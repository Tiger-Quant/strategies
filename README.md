# SMA Crossover Automated Trading Bot Tutorial

This guide will walk you through setting up and running an automated trading bot that uses a Simple Moving Average (SMA) crossover strategy with the Alpaca Markets API.

You can run this project in two ways: locally on your own computer (recommended for long-term use) or in Google Colab (great for quick testing).

---

## Option 1: Running Locally on Your Computer
This method uses a Python virtual environment to keep the project's dependencies isolated and organized.

### 1. Prerequisites
- Make sure you have **Python 3.8** or newer installed.
- Make sure you have **Git** installed for cloning the repository.
- You will need an **Alpaca paper trading account** to get your API keys.

### 2. Clone the Repository
Open your terminal or command prompt and clone the project repository:
```bash
git clone <your-repo-url-here>
cd <your-repo-name-here>
```

### 3. Set Up a Virtual Environment
A virtual environment is a private sandbox for your project's libraries.

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

You'll know it's active when you see `(venv)` at the beginning of your terminal prompt.

### 4. Install Dependencies
Install all the required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 5. Add Your API Keys
Your secret API keys should never be saved in your code. We'll use a `.env` file to store them securely.

1. Create a new file in the project folder named `.env`.
2. Open the file and add your keys from the Alpaca dashboard:
```python
API_KEY="YOUR_ALPACA_API_KEY_ID"
SECRET_KEY="YOUR_ALPACA_SECRET_KEY"
```

### 6. Run the Bot
You're all set! Start the bot with this command:
```bash
python september30.py
```

The script will now run in a loop, checking for trading signals every minute.


## Option 2: Running in Google Colab

This method is perfect for a workshop or for users who don't want to set up a local Python environment.

### 1. Open Google Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Tiger-Quant/strategies/blob/main/september30.ipynb)

### 2. Add API Keys via Secrets Manager
Colab has a secure way to store your keys for each session.

1. Click the key icon (🔑) in the left sidebar.
2. Click "+ Add a new secret".
3. For the Name, enter API_KEY. For the Value, paste your Alpaca API Key ID.
4. Click "+ Add a new secret" again.
5. For the Name, enter SECRET_KEY. For the Value, paste your Alpaca Secret Key.

### 3. Start the bot
Run all cells in the notebook to start the bot.
