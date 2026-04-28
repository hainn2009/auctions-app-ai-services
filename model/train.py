import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# Giả lập dữ liệu
data = pd.DataFrame([
    {"start_price": 1000, "bid_count": 8, "avg_bid_interval": 30, "item_popularity": 87, "winner_bid": 2100},
    {"start_price": 5000, "bid_count": 15, "avg_bid_interval": 20, "item_popularity": 65, "winner_bid": 9500},
    {"start_price": 2000, "bid_count": 5, "avg_bid_interval": 40, "item_popularity": 92, "winner_bid": 3100},
    {"start_price": 800, "bid_count": 10, "avg_bid_interval": 25, "item_popularity": 74, "winner_bid": 1900},
])

X = data[["start_price", "bid_count", "avg_bid_interval", "item_popularity"]]
y = data["winner_bid"]

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "model/model.pkl")
print("✅ Model trained and saved as model/model.pkl")
