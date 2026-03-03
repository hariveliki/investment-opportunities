"""Universe service: provides index constituent lists."""

from __future__ import annotations

import io
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

_CONSTITUENT_CACHE: dict[str, list[str]] = {}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
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

_STATIC_UNIVERSES: dict[str, list[str]] = {
    "sp500": _STATIC_SP500,
    "nasdaq100": _STATIC_NASDAQ100,
    "dow30": _STATIC_DOW30,
    "ftse100": _STATIC_FTSE100,
    "dax": _STATIC_DAX,
    "smi": _STATIC_SMI,
    "nikkei225": _STATIC_NIKKEI_SAMPLE,
}

_SCRAPERS: dict[str, callable] = {
    "sp500": _scrape_sp500,
    "nasdaq100": _scrape_nasdaq100,
    "dow30": _scrape_dow30,
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
