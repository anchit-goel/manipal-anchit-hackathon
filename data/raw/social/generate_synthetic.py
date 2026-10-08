"""Script to generate realistic synthetic social posts for the 20 universe tickers."""
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(42)

OUT_PATH = Path("/Users/anchitgoel/Desktop/S&P Crisil Hackathon/manipal-anchit-hackathon/data/raw/social/synthetic_posts.json")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

TICKERS_DATA = [
    ("JPM", "JPMorgan Chase", "Banking"),
    ("BAC", "Bank of America", "Banking"),
    ("C", "Citigroup", "Banking"),
    ("HDB", "HDFC Bank", "Banking"),
    ("ICICIBANK.NS", "ICICI Bank", "Banking"),
    ("HSBA.L", "HSBC Holdings", "Banking"),
    ("XOM", "ExxonMobil", "Energy"),
    ("CVX", "Chevron", "Energy"),
    ("SHEL", "Shell plc", "Energy"),
    ("BP", "BP plc", "Energy"),
    ("MAERSK-B.CO", "A.P. Moller - Maersk", "Shipping"),
    ("ZIM", "ZIM Integrated Shipping", "Shipping"),
    ("NVDA", "NVIDIA", "Semiconductors"),
    ("TSM", "TSMC", "Semiconductors"),
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft", "Technology"),
    ("TSLA", "Tesla", "Automotive"),
    ("TM", "Toyota Motor", "Automotive"),
    ("BA", "Boeing", "Aerospace"),
    ("DAL", "Delta Air Lines", "Airlines"),
]

USERS = [
    "@MacroDeskAlerts", "@FinTwitAlpha", "@QuantFlows", "@InstitutionalWire",
    "@DeepValueCapital", "@SemiconductorPulse", "@ShippingDaily", "@EnergyTraderX",
    "@CreditRiskInsights", "@RetailBull99", "@TechMomentum", "@AviationIntel"
]

posts = []
base_time = datetime.now(timezone.utc)

# 1. High Impact / Serious Events (10 posts)
serious_templates = [
    ("MAERSK-B.CO", "A.P. Moller - Maersk", "URGENT: Maersk confirms suspension of all transit through Bab el-Mandeb strait due to maritime missile strike on nearby bulk carrier. Expect 15% freight surcharge and 14 days reroute around Cape.", "Shipping disruptions intensify as Maersk halts Red Sea transit indefinitely.", "rumor_serious"),
    ("ZIM", "ZIM Integrated Shipping", "ZIM issues emergency advisory to spot container clients: Suez bypass now standard on all Asia-Mediterranean loops. Spot FEU rates spiking above $4,500.", "ZIM reroutes container vessels around Africa as maritime risks escalate.", "standard"),
    ("C", "Citigroup", "DEVELOPING: Citigroup discloses $2.1B counterparty exposure review following sudden default notice from distressed sovereign infrastructure sponsor.", "Citigroup facing counterparty default scrutiny on commercial infrastructure portfolio.", "rumor_serious"),
    ("JPM", "JPMorgan Chase", "JPMorgan wholesale banking desk tightens credit margins on levered real estate and transport portfolios amid rising syndicated borrowing costs.", "JPMorgan tightens underwriting standards for wholesale commercial clients.", "standard"),
    ("NVDA", "NVIDIA", "US Dept of Commerce issues preliminary guidance expanding export curbs on high-bandwidth AI computing clusters to third-party transshipment hubs. $NVDA and $TSM impacted.", "Export restrictions tighten on advanced semiconductor architectures.", "standard"),
    ("TSM", "TSMC", "Taiwan media reports scheduled seismic maintenance shutdown across two N3 fabs; wafer test delays possible for top customers.", "TSMC evaluates cleanroom equipment calibration following minor seismic activity.", "rumor_serious"),
    ("XOM", "ExxonMobil", "OPEC+ emergency consultation signals potential 1.2M bpd voluntary quota extension. Brent futures rally 4.2%, lifting ExxonMobil and Chevron upstream margins.", "OPEC surprise production discipline boosts global crude pricing and upstream valuations.", "standard"),
    ("BP", "BP plc", "UK environmental regulator opens formal audit into BP North Sea asset decommissioning liabilities. Capital expenditure reallocation expected.", "Regulatory scrutiny on North Sea asset retirement obligations for BP.", "standard"),
    ("BA", "Boeing", "FAA issues airworthiness directive requiring accelerated inspection of wing de-icing assemblies across 140 commercial airframes. Deliveries slightly pushed back.", "FAA issues inspection requirement for Boeing commercial fleets.", "standard"),
    ("HDB", "HDFC Bank", "RBI supervisory team completes annual asset quality review for HDFC Bank; capital adequacy remains comfortably above Tier-1 regulatory minimums.", "RBI regulatory audit affirms solid capital buffers for HDFC Bank.", "standard"),
]

for ticker, name, text, title, p_type in serious_templates:
    dt = base_time - timedelta(hours=random.randint(2, 72), minutes=random.randint(0, 59))
    posts.append({
        "post_id": f"soc_{len(posts)+1:03d}",
        "author": random.choice(USERS),
        "published_at": dt.isoformat(),
        "title": title,
        "text": text,
        "ticker": ticker,
        "entity": name,
        "url": f"https://x.com/mock_feed/status/184300{len(posts)+1:04d}",
        "engagement": {
            "likes": random.randint(300, 4500),
            "retweets": random.randint(80, 1200),
            "replies": random.randint(25, 400),
        },
        "post_type": p_type,
        "is_synthetic": True
    })

# 2. Rumor Posts (25 posts) - unverified claims, hearsay, leaks
rumor_templates = [
    ("{ticker}", "{name}", "UNVERIFIED RUMOR: Hearing whispers that {name} desk is experiencing liquidity delays on European repo desks. No official filing yet, treat with caution.", "Market rumor: unconfirmed liquidity whispers around {name}."),
    ("{ticker}", "{name}", "Trader chatter: Rumor that {name} is preparing a $3B surprise secondary equity offering to shore up Tier 1 capital ratios.", "Rumor: possible dilutive capital raise for {name}."),
    ("{ticker}", "{name}", "Anonymous sources claim regulatory inspectors visited {name} regional compliance office yesterday. Stock down 1.5% in pre-market.", "Hearsay: regulatory scrutiny inquiry rumor for {name}."),
    ("{ticker}", "{name}", "Unsubstantiated leak: {name} might be halting supply shipments due to supplier contract disputes. Awaiting company clarification.", "Supply chain rumor circulates for {name}."),
    ("{ticker}", "{name}", "Chatter circulating on Discord trading groups that {name} CEO is abruptly stepping down ahead of board meeting. Pure rumor at this stage.", "Executive leadership rumor regarding {name}."),
]

for i in range(25):
    t_tuple = random.choice(TICKERS_DATA)
    template = random.choice(rumor_templates)
    text = template[2].format(ticker=f"${t_tuple[0]}", name=t_tuple[1])
    title = template[3].format(ticker=f"${t_tuple[0]}", name=t_tuple[1])
    dt = base_time - timedelta(hours=random.randint(4, 140), minutes=random.randint(0, 59))
    posts.append({
        "post_id": f"soc_{len(posts)+1:03d}",
        "author": random.choice(USERS),
        "published_at": dt.isoformat(),
        "title": title,
        "text": text,
        "ticker": t_tuple[0],
        "entity": t_tuple[1],
        "url": f"https://x.com/mock_feed/status/184300{len(posts)+1:04d}",
        "engagement": {
            "likes": random.randint(40, 650),
            "retweets": random.randint(10, 180),
            "replies": random.randint(15, 210),
        },
        "post_type": "rumor",
        "is_synthetic": True
    })

# 3. Hype / Exaggeration Posts (25 posts)
hype_templates = [
    ("{ticker}", "{name}", "🚀🚀 {name} to the moon!! Insane numbers coming this quarter, easily a 50% squeeze imminent. Loading up on call options!", "Speculative hype: mega bull call on {name}."),
    ("{ticker}", "{name}", "Don't sell {name}! Whispers say sovereign wealth funds are buying every dip. Target price upgraded 3x by boutique desk!", "Retail hype: speculative upgrade targets for {name}."),
    ("{ticker}", "{name}", "Massive breakthrough for {name}!! Game changing patent granted, competitors will have zero chance. Buy now or regret later! 🔥", "Hyperbolic claim regarding new patent for {name}."),
    ("{ticker}", "{name}", "Huge whale accumulation spotted in dark pools for ${ticker}! Someone knows something huge is dropping tomorrow morning!!", "Dark pool flow speculation for ${ticker}."),
    ("{ticker}", "{name}", "Guaranteed 10-bagger in the making for {name}! Institutional short squeeze will be historic! 💎🙌", "Meme style hype post on {name}."),
]

for i in range(25):
    t_tuple = random.choice(TICKERS_DATA)
    template = random.choice(hype_templates)
    text = template[2].format(ticker=t_tuple[0], name=t_tuple[1])
    title = template[3].format(ticker=t_tuple[0], name=t_tuple[1])
    dt = base_time - timedelta(hours=random.randint(5, 160), minutes=random.randint(0, 59))
    posts.append({
        "post_id": f"soc_{len(posts)+1:03d}",
        "author": random.choice(USERS),
        "published_at": dt.isoformat(),
        "title": title,
        "text": text,
        "ticker": t_tuple[0],
        "entity": t_tuple[1],
        "url": f"https://x.com/mock_feed/status/184300{len(posts)+1:04d}",
        "engagement": {
            "likes": random.randint(150, 2200),
            "retweets": random.randint(30, 480),
            "replies": random.randint(40, 310),
        },
        "post_type": "hype",
        "is_synthetic": True
    })

# 4. Standard Institutional / Market Updates (40 posts)
standard_templates = [
    ("{ticker}", "{name}", "Analyst note on {name}: Maintains Outperform rating with balanced outlook on net interest margins and prudent loan loss provisions.", "Brokerage research note maintains rating on {name}."),
    ("{ticker}", "{name}", "Quarterly production commentary: {name} operational execution steady; supply chain lead times normalizing across international hubs.", "Operational update note for {name}."),
    ("{ticker}", "{name}", "Institutional 13F filings show steady mutual fund rebalancing into {name} equity and debt instruments over the trailing month.", "Institutional holding rebalancing noted in {name}."),
    ("{ticker}", "{name}", "Treasury desk commentary: {name} successfully concludes benchmark 5-year fixed rate corporate bond issuance at tight spread.", "Corporate debt issuance successfully priced by {name}."),
    ("{ticker}", "{name}", "Market summary: Trading volume in {name} was in line with 30-day moving averages as broader indices consolidated.", "Daily trading recap and volume analysis for {name}."),
]

for i in range(40):
    t_tuple = random.choice(TICKERS_DATA)
    template = random.choice(standard_templates)
    text = template[2].format(ticker=t_tuple[0], name=t_tuple[1])
    title = template[3].format(ticker=t_tuple[0], name=t_tuple[1])
    dt = base_time - timedelta(hours=random.randint(1, 168), minutes=random.randint(0, 59))
    posts.append({
        "post_id": f"soc_{len(posts)+1:03d}",
        "author": random.choice(USERS),
        "published_at": dt.isoformat(),
        "title": title,
        "text": text,
        "ticker": t_tuple[0],
        "entity": t_tuple[1],
        "url": f"https://x.com/mock_feed/status/184300{len(posts)+1:04d}",
        "engagement": {
            "likes": random.randint(10, 320),
            "retweets": random.randint(2, 65),
            "replies": random.randint(1, 40),
        },
        "post_type": "standard",
        "is_synthetic": True
    })

# Sort newest first
posts.sort(key=lambda x: x["published_at"], reverse=True)

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(posts, f, indent=2)

print(f"Generated {len(posts)} synthetic posts at {OUT_PATH}")
