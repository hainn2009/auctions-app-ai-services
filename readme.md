### Install

- Create environment

python -m venv venv

- Active it

venv\Scripts\activate

pip install -r requirements.txt

python model/train.py

uvicorn app:app --reload --port 8000

### What is available

- `POST /predict`:
    - Keeps the existing price suggestion endpoint.
- `POST /analytics/summary`:
    - Accepts a list of auction records and returns KPI-style reporting.
- `GET /analytics/sample`:
    - Returns a sample report so you can test the feature immediately.
- `GET /health`:
    - Checks whether the service and model are ready.

### Example analytics payload

```json
{
    "top_n": 5,
    "auctions": [
        {
            "auction_id": "AUCT-1001",
            "item_name": "Vintage Watch",
            "item_category": "accessories",
            "starting_price": 120,
            "current_price": 260,
            "item_start_date": "2026-04-26T09:00:00",
            "item_end_date": "2026-04-30T09:00:00",
            "seller_id": "seller-1",
            "bids": [
                {
                    "bidder_id": "u1",
                    "amount": 150,
                    "bid_time": "2026-04-26T09:05:00"
                }
            ]
        }
    ]
}
```
