"""Universe service: provides index constituent lists."""

from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx
import pandas as pd

logger = logging.getLogger(__name__)

_CONSTITUENT_CACHE: dict[str, list[str]] = {}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

# ---------------------------------------------------------------------------
# iShares ETF proxy configuration
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ISharesETFConfig:
    product_id: int
    slug: str
    ticker: str
    max_holdings: int = 0  # 0 = no limit


_ISHARES_ETF_CONFIGS: dict[str, ISharesETFConfig] = {
    "msci_europe": ISharesETFConfig(264617, "ishares-core-msci-europe-etf", "IEUR"),
    "msci_usa": ISharesETFConfig(239693, "ishares-msci-usa-etf", "EUSA"),
    "msci_em": ISharesETFConfig(244050, "ishares-core-msci-emerging-markets-etf", "IEMG", max_holdings=500),
    "msci_world_sc": ISharesETFConfig(342357, "ishares-msci-world-small-cap-etf", "WSML", max_holdings=500),
    "msci_japan": ISharesETFConfig(239665, "ishares-msci-japan-etf", "EWJ"),
    "msci_pacific_ex_jp": ISharesETFConfig(239668, "ishares-msci-pacific-ex-japan-etf", "EPP"),
}

_ISHARES_BASE_URL = "https://www.ishares.com/us/products"

# Maps iShares exchange name → Yahoo Finance ticker suffix
_ISHARES_EXCHANGE_TO_YF_SUFFIX: dict[str, str] = {
    # US
    "NYSE": "",
    "NASDAQ": "",
    "Cboe BZX": "",
    "Nyse Mkt Llc": "",
    # UK
    "London Stock Exchange": ".L",
    # Germany
    "Xetra": ".DE",
    # France / Belgium / Netherlands / Portugal
    "Nyse Euronext - Euronext Paris": ".PA",
    "Nyse Euronext - Euronext Brussels": ".BR",
    "Euronext Amsterdam": ".AS",
    "Nyse Euronext - Euronext Lisbon": ".LS",
    # Switzerland
    "SIX Swiss Exchange": ".SW",
    # Nordics
    "Nasdaq Omx Nordic": ".ST",
    "Nasdaq Omx Helsinki Ltd.": ".HE",
    "Omx Nordic Exchange Copenhagen A/S": ".CO",
    "Oslo Bors Asa": ".OL",
    "AKT": ".ST",
    # Italy / Spain / Austria / Ireland
    "Borsa Italiana": ".MI",
    "Bolsa De Madrid": ".MC",
    "Wiener Boerse Ag": ".VI",
    "Irish Stock Exchange - All Market": ".IR",
    # Japan
    "Tokyo Stock Exchange": ".T",
    # Asia-Pacific
    "Asx - All Markets": ".AX",
    "Hong Kong Exchanges And Clearing Ltd": ".HK",
    "Singapore Exchange": ".SI",
    "New Zealand Exchange Ltd": ".NZ",
    # Emerging markets
    "Taiwan Stock Exchange": ".TW",
    "Gretai Securities Market": ".TWO",
    "Korea Exchange (Stock Market)": ".KS",
    "Korea Exchange (Kosdaq)": ".KQ",
    "National Stock Exchange Of India": ".NS",
    "Bse Ltd": ".BO",
    "Bursa Malaysia": ".KL",
    "Stock Exchange Of Thailand": ".BK",
    "Indonesia Stock Exchange": ".JK",
    "Philippine Stock Exchange Inc.": ".PS",
    "Johannesburg Stock Exchange": ".JO",
    "Saudi Stock Exchange": ".SR",
    "Qatar Exchange": ".QA",
    "Kuwait Stock Exchange": ".KW",
    "Abu Dhabi Securities Exchange": ".AD",
    "Dubai Financial Market": ".DU",
    "Bolsa Mexicana De Valores": ".MX",
    "Santiago Stock Exchange": ".SN",
    "Bolsa De Valores De Colombia": ".CL",
    "XBSP": ".SA",
    "Warsaw Stock Exchange/Equities/Main Market": ".WA",
    "Budapest Stock Exchange": ".BD",
    "Prague Stock Exchange": ".PR",
    "Athens Exchange S.A. Cash Market": ".AT",
    "Istanbul Stock Exchange": ".IS",
    "Egyptian Exchange": ".CA",
    "Standard-Classica-Forts": ".ME",
    "Tel Aviv Stock Exchange": ".TA",
    "Shanghai Stock Exchange": ".SS",
    "Shenzhen Stock Exchange": ".SZ",
    "Toronto Stock Exchange": ".TO",
}


def _scrape_sp500() -> list[str]:
    import urllib.request
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()
    tables = pd.read_html(io.StringIO(html))
    df = tables[0]
    tickers = df["Symbol"].tolist()
    return [t.replace(".", "-") for t in tickers]


def _scrape_nasdaq100() -> list[str]:
    import urllib.request
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()
    tables = pd.read_html(io.StringIO(html))
    for t in tables:
        if "Ticker" in t.columns:
            return t["Ticker"].tolist()
        if "Symbol" in t.columns:
            return t["Symbol"].tolist()
    return []


def _scrape_dow30() -> list[str]:
    import urllib.request
    url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode()
    tables = pd.read_html(io.StringIO(html))
    for t in tables:
        if "Symbol" in t.columns:
            return t["Symbol"].tolist()
    return []


# ---------------------------------------------------------------------------
# iShares ETF holdings fetcher
# ---------------------------------------------------------------------------

def _to_yf_ticker(raw_ticker: str, exchange: str) -> str | None:
    """Convert an iShares ticker + exchange name to a Yahoo Finance symbol."""
    ticker = raw_ticker.strip().replace("/", "-").rstrip(".")
    if not ticker or ticker == "-":
        return None
    suffix = _ISHARES_EXCHANGE_TO_YF_SUFFIX.get(exchange)
    if suffix is None:
        logger.warning("Unmapped iShares exchange %r for ticker %r", exchange, ticker)
        return None
    return f"{ticker}{suffix}"


def _fetch_ishares_holdings(config: ISharesETFConfig) -> list[str]:
    """Download holdings from an iShares ETF and return Yahoo Finance tickers."""
    url = (
        f"{_ISHARES_BASE_URL}/{config.product_id}/{config.slug}"
        "/1467271812596.ajax?fileType=json&tab=all"
    )
    with httpx.Client(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    data = json.loads(resp.content.decode("utf-8-sig"))
    rows = data.get("aaData", [])

    # Detect column layout: "Equity" can be at index 3 (17-col) or 4 (18-col)
    equity_idx = None
    for row in rows:
        if "Equity" in row[:6]:
            equity_idx = row.index("Equity")
            break
    if equity_idx is None:
        logger.warning("No equity rows found for %s", config.ticker)
        return []

    # Relative offsets from equity_idx
    weight_offset = 2   # weight dict is 2 positions after "Equity"
    exchange_offset = 10  # exchange name is 10 positions after "Equity"

    holdings: list[tuple[float, str]] = []
    for row in rows:
        if len(row) <= equity_idx + exchange_offset:
            continue
        if row[equity_idx] != "Equity":
            continue

        weight_val = row[equity_idx + weight_offset]
        weight = weight_val["raw"] if isinstance(weight_val, dict) else 0.0
        exchange = row[equity_idx + exchange_offset]
        yf_ticker = _to_yf_ticker(row[0], exchange)
        if yf_ticker:
            holdings.append((weight, yf_ticker))

    # Sort by weight descending, apply cap if set
    holdings.sort(key=lambda x: x[0], reverse=True)
    if config.max_holdings > 0:
        holdings = holdings[: config.max_holdings]

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for _, ticker in holdings:
        if ticker not in seen:
            seen.add(ticker)
            result.append(ticker)
    return result


def _make_ishares_scraper(universe_id: str):
    """Create a scraper closure for an iShares-backed MSCI universe."""
    config = _ISHARES_ETF_CONFIGS[universe_id]

    def _scraper() -> list[str]:
        return _fetch_ishares_holdings(config)

    return _scraper


_STATIC_SP500 = [
    "AAPL","ABBV","ABT","ACN","ADBE","ADI","ADM","ADP","ADSK","AEE","AEP","AES","AFL","AIG","AIZ",
    "AJG","AKAM","ALB","ALGN","ALK","ALL","ALLE","AMAT","AMCR","AMD","AME","AMGN","AMP","AMT","AMZN",
    "ANET","ANSS","AON","AOS","APA","APD","APH","APTV","ARE","ATO","ATVI","AVGO","AVY","AWK","AXP",
    "AZO","BA","BAC","BAX","BBWI","BBY","BDX","BEN","BF-B","BIO","BIIB","BK","BKNG","BKR","BLK",
    "BMY","BR","BRK-B","BRO","BSX","BWA","BXP","C","CAG","CAH","CARR","CAT","CB","CBOE","CBRE",
    "CCI","CCL","CDAY","CDNS","CDW","CE","CEG","CF","CFG","CHD","CHRW","CHTR","CI","CINF","CL",
    "CLX","CMA","CMCSA","CME","CMG","CMI","CMS","CNC","CNP","COF","COO","COP","COST","CPB","CPRT",
    "CPT","CRL","CRM","CSCO","CSGP","CSX","CTAS","CTLT","CTRA","CTSH","CTVA","CVS","CVX","CZR",
    "D","DAL","DD","DE","DFS","DG","DGX","DHI","DHR","DIS","DISH","DLTR","DOV","DOW","DPZ",
    "DRI","DTE","DUK","DVA","DVN","DXC","DXCM","EA","EBAY","ECL","ED","EFX","EIX","EL","EMN",
    "EMR","ENPH","EOG","EPAM","EQIX","EQR","EQT","ES","ESS","ETN","ETR","ETSY","EVRG","EW","EXC",
    "EXPD","EXPE","EXR","F","FANG","FAST","FBHS","FCX","FDS","FDX","FE","FFIV","FIS","FISV","FITB",
    "FLT","FMC","FOX","FOXA","FRC","FRT","FTNT","FTV","GD","GE","GEHC","GEN","GILD","GIS","GL",
    "GLW","GM","GNRC","GOOG","GOOGL","GPC","GPN","GRMN","GS","GWW","HAL","HAS","HBAN","HCA","HD",
    "HSIC","HST","HSY","HUM","HWM","IBM","ICE","IDXX","IEX","IFF","ILMN","INCY","INTC","INTU","INVH",
    "IP","IPG","IQV","IR","IRM","ISRG","IT","ITW","IVZ","J","JBHT","JCI","JKHY","JNJ","JNPR",
    "JPM","K","KDP","KEY","KEYS","KHC","KIM","KLAC","KMB","KMI","KMX","KO","KR","L","LDOS",
    "LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNC","LNT","LOW","LRCX","LUMN","LUV","LVS","LW",
    "LYB","LYV","MA","MAA","MAR","MAS","MCD","MCHP","MCK","MCO","MDLZ","MDT","MET","META","MGM",
    "MHK","MKC","MKTX","MLM","MMC","MMM","MNST","MO","MOH","MOS","MPC","MPWR","MRK","MRNA","MRO",
    "MS","MSCI","MSFT","MSI","MTB","MTCH","MTD","MU","NCLH","NDAQ","NDSN","NEE","NEM","NFLX","NI",
    "NKE","NOC","NOW","NRG","NSC","NTAP","NTRS","NUE","NVDA","NVR","NWL","NWS","NWSA","NXPI","O",
    "ODFL","OGN","OKE","OMC","ON","ORCL","ORLY","OTIS","OXY","PARA","PAYC","PAYX","PCAR","PCG",
    "PEAK","PEG","PEP","PFE","PFG","PG","PGR","PH","PHM","PKG","PKI","PLD","PM","PNC","PNR",
    "PNW","POOL","PPG","PPL","PRU","PSA","PSX","PTC","PVH","PWR","PXD","PYPL","QCOM","QRVO","RCL",
    "RE","REG","REGN","RF","RHI","RJF","RL","RMD","ROK","ROL","ROP","ROST","RSG","RTX","SBAC",
    "SBNY","SBUX","SCHW","SEE","SHW","SIVB","SJM","SLB","SNA","SNPS","SO","SPG","SPGI","SRE","STE",
    "STT","STX","STZ","SWK","SWKS","SYF","SYK","SYY","T","TAP","TDG","TDY","TECH","TEL","TER",
    "TFC","TFX","TGT","TMO","TMUS","TPR","TRGP","TRMB","TROW","TRV","TSCO","TSLA","TSN","TT",
    "TTWO","TXN","TXT","TYL","UAL","UDR","UHS","ULTA","UNH","UNP","UPS","URI","USB","V","VFC",
    "VICI","VLO","VMC","VNO","VRSK","VRSN","VRTX","VTR","VTRS","VZ","WAB","WAT","WBA","WBD","WDC",
    "WEC","WELL","WFC","WHR","WM","WMB","WMT","WRB","WRK","WST","WTW","WY","WYNN","XEL","XOM",
    "XRAY","XYL","YUM","ZBH","ZBRA","ZION","ZTS",
]

_STATIC_NASDAQ100 = [
    "AAPL","ABNB","ADBE","ADI","ADP","ADSK","AEP","AMAT","AMD","AMGN","AMZN","ANSS","ARM",
    "ASML","AVGO","AZN","BIIB","BKNG","BKR","CCEP","CDNS","CDW","CEG","CHTR","CMCSA","COST",
    "CPRT","CRWD","CSCO","CSGP","CSX","CTAS","CTSH","DASH","DDOG","DLTR","DXCM","EA","EXC",
    "FANG","FAST","FTNT","GEHC","GFS","GILD","GOOG","GOOGL","HON","IDXX","ILMN","INTC","INTU",
    "ISRG","KDP","KHC","KLAC","LIN","LRCX","LULU","MAR","MCHP","MDB","MDLZ","MELI","META",
    "MNST","MRNA","MRVL","MSFT","MU","NFLX","NVDA","NXPI","ODFL","ON","ORLY","PANW","PAYX",
    "PCAR","PDD","PEP","PYPL","QCOM","REGN","ROP","ROST","SBUX","SMCI","SNPS","SPLK","TEAM",
    "TMUS","TSLA","TTD","TTWO","TXN","VRSK","VRTX","WBD","WDAY","XEL","ZS",
]

_STATIC_DOW30 = [
    "AAPL","AMGN","AMZN","AXP","BA","CAT","CRM","CSCO","CVX","DIS",
    "DOW","GS","HD","HON","IBM","INTC","JNJ","JPM","KO","MCD",
    "MMM","MRK","MSFT","NKE","PG","SHW","TRV","UNH","V","VZ","WMT",
]

_STATIC_FTSE100 = [
    "AAF.L","AAL.L","ABF.L","ADM.L","AHT.L","ANTO.L","AUTO.L","AV.L","AZN.L","BA.L",
    "BARC.L","BATS.L","BDEV.L","BKG.L","BME.L","BNZL.L","BP.L","BRBY.L","BT-A.L","CCH.L",
    "CNA.L","CPG.L","CRDA.L","CRH.L","CTEC.L","DCC.L","DGE.L","EDV.L","ENT.L","EXPN.L",
    "FERG.L","FLTR.L","FRES.L","GLEN.L","GSK.L","HIK.L","HL.L","HLMA.L","HSBA.L","IHG.L",
    "III.L","IMB.L","INF.L","ITRK.L","ITV.L","JD.L","KGF.L","LAND.L","LGEN.L","LLOY.L",
    "LSEG.L","MNG.L","MRO.L","NG.L","NWG.L","NXT.L","OCDO.L","PHNX.L","PRU.L","PSH.L",
    "PSN.L","PSON.L","REL.L","RIO.L","RKT.L","RMV.L","RR.L","RS1.L","RTO.L","SBRY.L",
    "SDR.L","SGE.L","SGRO.L","SHEL.L","SKG.L","SMDS.L","SMIN.L","SMT.L","SN.L","SPX.L",
    "SSE.L","STAN.L","STJ.L","SVT.L","TSCO.L","TW.L","ULVR.L","UTG.L","UU.L","VOD.L",
    "WPP.L","WTB.L",
]

_STATIC_DAX = [
    "ADS.DE","AIR.DE","ALV.DE","BAS.DE","BAYN.DE","BEI.DE","BMW.DE","BNR.DE","CON.DE","1COV.DE",
    "DB1.DE","DBK.DE","DHL.DE","DTE.DE","DTG.DE","ENR.DE","FME.DE","FRE.DE","HEI.DE","HEN3.DE",
    "HNR1.DE","IFX.DE","LIN.DE","MBG.DE","MRK.DE","MTX.DE","MUV2.DE","P911.DE","PAH3.DE","QIA.DE",
    "RHM.DE","RWE.DE","SAP.DE","SHL.DE","SIE.DE","SRT3.DE","SY1.DE","TKA.DE","VNA.DE","VOW3.DE",
]

_STATIC_SMI = [
    "ABBN.SW","ADEN.SW","CSGN.SW","GEBN.SW","GIVN.SW",
    "HOLN.SW","KNIN.SW","LONN.SW","NESN.SW","NOVN.SW",
    "PGHN.SW","RIHN.SW","ROG.SW","SCMN.SW","SGSN.SW",
    "SIKA.SW","SLHN.SW","SREN.SW","UBSG.SW","ZURN.SW",
]

_STATIC_NIKKEI_SAMPLE = [
    "7203.T","6758.T","9984.T","6861.T","8306.T",
    "9433.T","6501.T","7267.T","4502.T","6902.T",
    "7751.T","8035.T","6954.T","4063.T","9432.T",
    "6367.T","7974.T","8058.T","2802.T","4503.T",
    "3382.T","4568.T","6301.T","6702.T","6752.T",
    "7741.T","8001.T","8031.T","8316.T","8411.T",
]

_STATIC_MSCI_EUROPE = [
    "ASML.AS","ROG.SW","NOVN.SW","NESN.SW","AZN.L","NOVO-B.CO","SHEL.L","SAP.DE","MC.PA",
    "HSBA.L","ULVR.L","SIE.DE","OR.PA","BP.L","ALV.DE","SAN.PA","DGE.L","AI.PA","BNP.PA",
    "RIO.L","GSK.L","BARC.L","DTE.DE","IBE.MC","CS.PA","BAS.DE","SU.PA","INGA.AS","MBG.DE",
    "LLOY.L","ABI.BR","EL.PA","PHIA.AS","ENEL.MI","ISP.MI","UCG.MI","TEF.MC","KER.PA",
    "NOKIA.HE","NESTE.HE","RACE.MI","DSY.PA","SGO.PA","BAYN.DE","ADS.DE","ENI.MI",
    "VOW3.DE","RI.PA","BMW.DE","IFX.DE",
]

_STATIC_MSCI_USA = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","BRK-B","UNH","JNJ",
    "JPM","V","XOM","PG","MA","HD","CVX","MRK","ABBV","LLY",
    "PEP","KO","COST","AVGO","TMO","WMT","MCD","CSCO","ACN","ABT",
    "CRM","DHR","CMCSA","TXN","NEE","PM","VZ","INTC","RTX","AMGN",
    "NFLX","HON","UNP","IBM","LOW","QCOM","BA","SBUX","GE","AMAT",
]

_STATIC_MSCI_EM = [
    "2330.TW","RELIANCE.NS","005930.KS","BABA","TSM","TCEHY","3690.HK","INFY.NS",
    "9988.HK","0700.HK","1211.HK","2317.TW","VALE3.SA","ITUB4.SA","PETR4.SA",
    "000660.KS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","2454.TW",
    "1810.HK","0939.HK","1398.HK","3988.HK","0388.HK","2318.HK","WEGE3.SA",
    "035420.KS","051910.KS","006400.KS","000858.SZ","600519.SS","601318.SS",
    "BBDC4.SA","B3SA3.SA","RENT3.SA","ASII.JK","BBCA.JK","TLKM.JK",
    "TOP.BK","PTT.BK","SHP.JO","NPN.JO","AMS.JO","WALMEX.MX","FEMSAUBD.MX",
    "2382.HK","9618.HK","1299.HK",
]

_STATIC_MSCI_WORLD_SC = [
    "SNDK","COHR","LUMN","CGNX","DECK","PNFP","RBC","EXLS","SKX","LNTH",
    "NOVT","MTSI","PLNT","ENSG","ORA","AIT","MOG-A","EHC","PIPR","EPAC",
    "6645.T","4911.T","6506.T","9613.T","6504.T","2801.T","4578.T","2413.T",
    "INA.L","BVIC.L","RWS.L","VCT.L","TRN.L","JDW.L","PMO.MI","ERG.MI",
    "NEM.DE","EVK.DE","SZU.DE","LEG.DE","FPE3.DE","RAA.DE",
    "CLW.AX","APE.AX","IEL.AX","ALX.AX","NHF.AX","SUL.AX",
    "PER.PA","GBT.PA",
]

_STATIC_MSCI_JAPAN = [
    "7203.T","6758.T","9984.T","6861.T","8306.T","9433.T","6501.T","7267.T",
    "4502.T","6902.T","7751.T","8035.T","6954.T","4063.T","9432.T","6367.T",
    "7974.T","8058.T","2802.T","4503.T","3382.T","4568.T","6301.T","6702.T",
    "6752.T","7741.T","8001.T","8031.T","8316.T","8411.T","4661.T","6326.T",
    "4519.T","6473.T","8766.T","4901.T","6098.T","9020.T","9022.T","2914.T",
    "6594.T","7733.T","3407.T","4543.T","7269.T","8002.T","8053.T","6981.T",
    "7832.T","9021.T",
]

_STATIC_MSCI_PACIFIC_EX_JP = [
    "BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX","WES.AX",
    "TLS.AX","WOW.AX","RIO.AX","FMG.AX","ALL.AX","GMG.AX","TCL.AX","REA.AX",
    "STO.AX","WDS.AX","JHX.AX","COL.AX","0005.HK","0941.HK","0016.HK","0001.HK",
    "0011.HK","0066.HK","0002.HK","0003.HK","1038.HK","0823.HK","0012.HK",
    "0006.HK","0883.HK","0027.HK","0688.HK","DBS.SI","OCBC.SI","UOB.SI",
    "SPH.NZ","FPH.NZ","ATM.NZ","AIA.NZ","MEL.NZ","SKC.NZ",
    "0017.HK","1113.HK","0267.HK","2688.HK","1928.HK","0175.HK",
]

_STATIC_UNIVERSES: dict[str, list[str]] = {
    "sp500": _STATIC_SP500,
    "nasdaq100": _STATIC_NASDAQ100,
    "dow30": _STATIC_DOW30,
    "ftse100": _STATIC_FTSE100,
    "dax": _STATIC_DAX,
    "smi": _STATIC_SMI,
    "nikkei225": _STATIC_NIKKEI_SAMPLE,
    "msci_europe": _STATIC_MSCI_EUROPE,
    "msci_usa": _STATIC_MSCI_USA,
    "msci_em": _STATIC_MSCI_EM,
    "msci_world_sc": _STATIC_MSCI_WORLD_SC,
    "msci_japan": _STATIC_MSCI_JAPAN,
    "msci_pacific_ex_jp": _STATIC_MSCI_PACIFIC_EX_JP,
}

_SCRAPERS: dict[str, callable] = {
    "sp500": _scrape_sp500,
    "nasdaq100": _scrape_nasdaq100,
    "dow30": _scrape_dow30,
    **{uid: _make_ishares_scraper(uid) for uid in _ISHARES_ETF_CONFIGS},
}


def get_constituents(universe_id: str, custom_tickers: Optional[list[str]] = None) -> list[str]:
    """Return list of ticker symbols for the given universe."""
    if universe_id == "custom" and custom_tickers:
        return custom_tickers

    if universe_id in _CONSTITUENT_CACHE:
        return _CONSTITUENT_CACHE[universe_id]

    scraper = _SCRAPERS.get(universe_id)
    if scraper:
        try:
            tickers = scraper()
            if tickers:
                _CONSTITUENT_CACHE[universe_id] = tickers
                logger.info(f"Loaded {len(tickers)} constituents for {universe_id} (scraped)")
                return tickers
        except Exception as e:
            logger.warning(f"Scraping failed for {universe_id}, using static list: {e}")

    if universe_id in _STATIC_UNIVERSES:
        tickers = _STATIC_UNIVERSES[universe_id]
        _CONSTITUENT_CACHE[universe_id] = tickers
        logger.info(f"Loaded {len(tickers)} constituents for {universe_id} (static)")
        return tickers

    return []


def clear_cache():
    _CONSTITUENT_CACHE.clear()
