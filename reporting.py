from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class BidEvent(BaseModel):
    bidder_id: Optional[str] = None
    amount: float
    bid_time: Optional[datetime] = None


class AuctionRecord(BaseModel):
    auction_id: str
    item_name: str
    item_category: str = "unknown"
    starting_price: float
    current_price: float
    item_start_date: datetime
    item_end_date: datetime
    seller_id: Optional[str] = None
    bids: list[BidEvent] = Field(default_factory=list)


class CategoryReport(BaseModel):
    item_category: str
    auction_count: int
    total_bids: int
    average_bids: float
    average_price_growth: float
    average_price_growth_pct: float


class HotAuction(BaseModel):
    auction_id: str
    item_name: str
    item_category: str
    bid_count: int
    price_growth: float
    price_growth_pct: float
    bid_velocity_per_minute: float


class AuctionReportRequest(BaseModel):
    auctions: list[AuctionRecord]
    top_n: int = 5


class AuctionReport(BaseModel):
    generated_at: datetime
    total_auctions: int
    active_auctions: int
    ended_auctions: int
    upcoming_auctions: int
    total_bids: int
    average_bids_per_auction: float
    average_start_price: float
    average_current_price: float
    average_price_growth: float
    average_price_growth_pct: float
    peak_bid_hour: Optional[int] = None
    top_categories: list[CategoryReport]
    hottest_auctions: list[HotAuction]


def _safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _auction_status(auction: AuctionRecord, now: datetime) -> str:
    start_date = _normalize_datetime(auction.item_start_date)
    end_date = _normalize_datetime(auction.item_end_date)

    if start_date > now:
        return "upcoming"
    if end_date < now:
        return "ended"
    return "active"


def build_auction_report(auctions: list[AuctionRecord], top_n: int = 5) -> AuctionReport:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if top_n < 1:
        top_n = 1

    total_auctions = len(auctions)
    active_auctions = 0
    ended_auctions = 0
    upcoming_auctions = 0
    total_bids = 0
    total_start_price = 0.0
    total_current_price = 0.0
    total_price_growth = 0.0
    total_price_growth_pct = 0.0
    bid_hours: list[int] = []

    category_counts: Counter[str] = Counter()
    category_bids: Counter[str] = Counter()
    category_growth: Counter[str] = Counter()
    category_growth_pct: Counter[str] = Counter()

    hottest_candidates: list[HotAuction] = []

    for auction in auctions:
        status = _auction_status(auction, now)
        if status == "active":
            active_auctions += 1
        elif status == "ended":
            ended_auctions += 1
        else:
            upcoming_auctions += 1

        bid_count = len(auction.bids)
        start_date = _normalize_datetime(auction.item_start_date)
        end_date = _normalize_datetime(auction.item_end_date)
        price_growth = auction.current_price - auction.starting_price
        price_growth_pct = _safe_div(price_growth * 100.0, auction.starting_price)
        duration_minutes = max(
            _safe_div((end_date - start_date).total_seconds(), 60.0),
            1.0,
        )
        bid_velocity_per_minute = _safe_div(bid_count, duration_minutes)

        total_bids += bid_count
        total_start_price += auction.starting_price
        total_current_price += auction.current_price
        total_price_growth += price_growth
        total_price_growth_pct += price_growth_pct

        category_counts[auction.item_category] += 1
        category_bids[auction.item_category] += bid_count
        category_growth[auction.item_category] += price_growth
        category_growth_pct[auction.item_category] += price_growth_pct

        for bid in auction.bids:
            if bid.bid_time is not None:
                bid_hours.append(_normalize_datetime(bid.bid_time).hour)

        hottest_candidates.append(
            HotAuction(
                auction_id=auction.auction_id,
                item_name=auction.item_name,
                item_category=auction.item_category,
                bid_count=bid_count,
                price_growth=round(price_growth, 2),
                price_growth_pct=round(price_growth_pct, 2),
                bid_velocity_per_minute=round(bid_velocity_per_minute, 4),
            )
        )

    top_categories = [
        CategoryReport(
            item_category=category,
            auction_count=count,
            total_bids=category_bids[category],
            average_bids=round(_safe_div(category_bids[category], count), 2),
            average_price_growth=round(_safe_div(category_growth[category], count), 2),
            average_price_growth_pct=round(_safe_div(category_growth_pct[category], count), 2),
        )
        for category, count in category_counts.most_common()
    ]

    hottest_auctions = sorted(
        hottest_candidates,
        key=lambda auction: (auction.bid_count, auction.price_growth, auction.bid_velocity_per_minute),
        reverse=True,
    )[:top_n]

    peak_bid_hour = None
    if bid_hours:
        peak_bid_hour = Counter(bid_hours).most_common(1)[0][0]

    return AuctionReport(
        generated_at=now,
        total_auctions=total_auctions,
        active_auctions=active_auctions,
        ended_auctions=ended_auctions,
        upcoming_auctions=upcoming_auctions,
        total_bids=total_bids,
        average_bids_per_auction=round(_safe_div(total_bids, total_auctions), 2),
        average_start_price=round(_safe_div(total_start_price, total_auctions), 2),
        average_current_price=round(_safe_div(total_current_price, total_auctions), 2),
        average_price_growth=round(_safe_div(total_price_growth, total_auctions), 2),
        average_price_growth_pct=round(_safe_div(total_price_growth_pct, total_auctions), 2),
        peak_bid_hour=peak_bid_hour,
        top_categories=top_categories,
        hottest_auctions=hottest_auctions,
    )


def sample_auctions() -> list[AuctionRecord]:
    return [
        AuctionRecord(
            auction_id="AUCT-1001",
            item_name="Vintage Watch",
            item_category="accessories",
            starting_price=120.0,
            current_price=260.0,
            item_start_date=datetime(2026, 4, 26, 9, 0, 0),
            item_end_date=datetime(2026, 4, 30, 9, 0, 0),
            seller_id="seller-1",
            bids=[
                BidEvent(bidder_id="u1", amount=150.0, bid_time=datetime(2026, 4, 26, 9, 5, 0)),
                BidEvent(bidder_id="u2", amount=180.0, bid_time=datetime(2026, 4, 26, 10, 12, 0)),
                BidEvent(bidder_id="u3", amount=220.0, bid_time=datetime(2026, 4, 27, 14, 45, 0)),
                BidEvent(bidder_id="u4", amount=260.0, bid_time=datetime(2026, 4, 27, 18, 20, 0)),
            ],
        ),
        AuctionRecord(
            auction_id="AUCT-1002",
            item_name="Gaming Laptop",
            item_category="electronics",
            starting_price=900.0,
            current_price=1280.0,
            item_start_date=datetime(2026, 4, 24, 8, 0, 0),
            item_end_date=datetime(2026, 4, 29, 8, 0, 0),
            seller_id="seller-2",
            bids=[
                BidEvent(bidder_id="u5", amount=980.0, bid_time=datetime(2026, 4, 24, 8, 15, 0)),
                BidEvent(bidder_id="u6", amount=1100.0, bid_time=datetime(2026, 4, 24, 9, 45, 0)),
                BidEvent(bidder_id="u7", amount=1280.0, bid_time=datetime(2026, 4, 25, 11, 10, 0)),
            ],
        ),
        AuctionRecord(
            auction_id="AUCT-1003",
            item_name="Sneaker Limited Edition",
            item_category="fashion",
            starting_price=80.0,
            current_price=95.0,
            item_start_date=datetime(2026, 4, 29, 10, 0, 0),
            item_end_date=datetime(2026, 5, 3, 10, 0, 0),
            seller_id="seller-3",
            bids=[
                BidEvent(bidder_id="u8", amount=95.0, bid_time=datetime(2026, 4, 29, 10, 10, 0)),
            ],
        ),
    ]
