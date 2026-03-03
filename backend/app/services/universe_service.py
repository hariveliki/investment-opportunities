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

# ---------------------------------------------------------------------------
# MSCI Europe — representative large+mid cap across 15 developed European
# countries. Tickers use yfinance conventions for their primary listings.
# ---------------------------------------------------------------------------
_STATIC_MSCI_EUROPE = [
    # United Kingdom
    "SHEL.L","AZN.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L","LSEG.L","BATS.L","DGE.L",
    "REL.L","CRH.L","GLEN.L","NXT.L","LLOY.L","BARC.L","AV.L","PRU.L","ABF.L","SSE.L",
    "BT-A.L","VOD.L","RR.L","IMB.L","WPP.L","EXPN.L","FERG.L","ANTO.L","HL.L","SMIN.L",
    "HLMA.L","IHG.L","FRES.L","SMT.L","STAN.L","NG.L","SGE.L","SKG.L","TSCO.L","KGF.L",
    "BRBY.L","AUTO.L","RKT.L","JD.L","AAL.L","BKG.L","BDEV.L","ADM.L","CCH.L","ITRK.L",
    # France
    "MC.PA","OR.PA","TTE.PA","SAN.PA","AIR.PA","SU.PA","AI.PA","BN.PA","CS.PA","DG.PA",
    "RI.PA","SAF.PA","BNP.PA","ACA.PA","EN.PA","EL.PA","DSY.PA","HO.PA","SGO.PA","CAP.PA",
    "KER.PA","VIV.PA","GLE.PA","ORA.PA","ML.PA","PUB.PA","ERA.PA","CA.PA","LR.PA","RMS.PA",
    "VIE.PA","STM.PA","STLAP.PA","WLN.PA","URW.PA",
    # Germany
    "SAP.DE","SIE.DE","ALV.DE","DTE.DE","MBG.DE","MUV2.DE","BAS.DE","BAYN.DE","BMW.DE","IFX.DE",
    "DB1.DE","DBK.DE","DHL.DE","HEN3.DE","ADS.DE","VOW3.DE","PAH3.DE","FRE.DE","CON.DE","MTX.DE",
    "RWE.DE","ENR.DE","HEI.DE","FME.DE","QIA.DE","SHL.DE","BNR.DE","P911.DE","1COV.DE","RHM.DE",
    # Switzerland
    "NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ABBN.SW","ZURN.SW","SIKA.SW","RIHN.SW","GIVN.SW",
    "SREN.SW","PGHN.SW","GEBN.SW","LONN.SW","HOLN.SW","SLHN.SW","SCMN.SW","KNIN.SW","ADEN.SW",
    # Netherlands
    "ASML.AS","INGA.AS","AD.AS","WKL.AS","PHIA.AS","DSM.AS","KPN.AS","NN.AS","HEIA.AS","UNA.AS",
    "AKZA.AS","RAND.AS","AGN.AS","BESI.AS","ASM.AS","PRX.AS",
    # Spain
    "SAN.MC","IBE.MC","ITX.MC","TEF.MC","BBVA.MC","AMS.MC","FER.MC","REP.MC","GRF.MC","ACS.MC",
    "CLNX.MC","MAP.MC","ENG.MC","ELE.MC","CABK.MC",
    # Italy
    "ISP.MI","UCG.MI","ENI.MI","ENEL.MI","RACE.MI","STLAM.MI","G.MI","TIT.MI","BAMI.MI",
    "PRY.MI","SRG.MI","SPM.MI","TEN.MI","AMP.MI","MB.MI","BGN.MI","UNI.MI",
    # Sweden
    "VOLV-B.ST","ATCO-A.ST","ERIC-B.ST","INVE-B.ST","HM-B.ST","SAND.ST","ASSA-B.ST",
    "HEXA-B.ST","ALFA.ST","ESSITY-B.ST","SKF-B.ST","TEL2-B.ST","SEB-A.ST","SHB-A.ST",
    "SWED-A.ST","SINCH.ST","ELUX-B.ST","NIBE-B.ST","GETI-B.ST","BOL.ST",
    # Denmark
    "NOVO-B.CO","DSV.CO","CARL-B.CO","ORSTED.CO","VWS.CO","MAERSK-B.CO","GN.CO","COLO-B.CO",
    "PNDORA.CO","DEMANT.CO","JYSK.CO","NZYM-B.CO","ISS.CO","TRYG.CO",
    # Finland
    "NOKIA.HE","SAMPO.HE","NESTE.HE","UPM.HE","KNEBV.HE","FORTUM.HE","STERV.HE","WRT1V.HE",
    "ELISA.HE","ORNBV.HE",
    # Norway
    "EQNR.OL","DNB.OL","TEL.OL","MOWI.OL","ORK.OL","SALM.OL","YAR.OL","AKRBP.OL","SUBC.OL",
    # Belgium
    "ABI.BR","UCB.BR","KBC.BR","SOLB.BR","ACKB.BR","PROX.BR",
    # Ireland
    "CRH","LSEG.L","RYA.L","FLT.L",
    # Portugal
    "EDP.LS","GALP.LS","JMT.LS",
    # Austria
    "VOE.VI","EBS.VI","OMV.VI","VER.VI",
]

# ---------------------------------------------------------------------------
# MSCI USA — broad US large+mid cap. Superset of S&P 500 with additional
# mid-cap names. Uses plain US tickers.
# ---------------------------------------------------------------------------
_STATIC_MSCI_USA = _STATIC_SP500 + [
    # Additional mid-caps not in S&P 500 list
    "CRWD","PANW","DDOG","SNOW","ZS","NET","BILL","MDB","TEAM","WDAY",
    "VEEV","OKTA","TWLO","COUP","DUOL","TTD","U","RBLX","DASH","COIN",
    "HOOD","SOFI","AFRM","PATH","APP","IOT","GTLB","CFLT","HUBS","PCOR",
    "CELH","SMCI","AXON","DECK","FICO","FIX","EME","TW","IBKR","LPLA",
    "RBA","HUBB","FNF","FND","NTNX","TOST","GDDY","LII","WSO","CACI",
    "SAIA","LSCC","EXLS","MANH","MEDP","NOVT","ENSG","TXRH","WING","CHDN",
    "WMS","CWST","TREX","SCI","KNSL","BWXT","MOD","RGEN","GGG","ITT",
    "WEX","MIDD","RPM","TTC","BRBR","IPAR","FHI","AIT","KBR","ESAB",
    "AZEK","ZWS","CSWI","SPSC","SWX","EVR","PJT","JEF","SF","HLI",
    "CG","ARES","OWL","STEP","BAM","BN","APO","KKR","BX","COKE",
]

# ---------------------------------------------------------------------------
# MSCI EM IMI — Emerging Markets Investable Market Index. Representative
# large+mid+small cap across ~24 EM countries. Uses ADRs and local tickers
# that yfinance supports.
# ---------------------------------------------------------------------------
_STATIC_MSCI_EM_IMI = [
    # China / Hong Kong ADRs & H-shares
    "BABA","JD","PDD","BIDU","NIO","LI","XPEV","NTES","BILI","ZTO",
    "YUMC","TCOM","GDS","MNSO","TAL","TME","IQ","VNET","FUTU","TIGR",
    "0700.HK","9988.HK","9618.HK","1211.HK","1810.HK","3690.HK","2318.HK","0939.HK",
    "1398.HK","3988.HK","0941.HK","0883.HK","0005.HK","0027.HK","0388.HK","0011.HK",
    "0016.HK","0002.HK","0003.HK","2628.HK","1928.HK","0688.HK","2020.HK","0960.HK",
    "2269.HK","9999.HK","0981.HK","1024.HK","6098.HK","0669.HK","1109.HK",
    # Taiwan
    "TSM","2330.TW","2317.TW","2454.TW","2412.TW","2308.TW","2882.TW","2881.TW",
    "2886.TW","1301.TW","1303.TW","2002.TW","2912.TW","3711.TW","2395.TW","4904.TW",
    "1216.TW","2207.TW","5880.TW","5871.TW","2382.TW","3008.TW","3034.TW","6505.TW",
    "2357.TW","1326.TW","2884.TW","2883.TW","2891.TW","2303.TW",
    # South Korea
    "005930.KS","000660.KS","035420.KS","005380.KS","051910.KS","006400.KS","035720.KS",
    "068270.KS","028260.KS","105560.KS","055550.KS","003670.KS","096770.KS","034730.KS",
    "012330.KS","066570.KS","032830.KS","086790.KS","030200.KS","033780.KS","009150.KS",
    "018260.KS","036570.KS","000270.KS","017670.KS","010130.KS",
    # India ADRs & local
    "INFY","WIT","HDB","IBN","SIFY","RDY","TTM","VEDL",
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","BHARTIARTL.NS","INFY.NS",
    "ITC.NS","SBIN.NS","LT.NS","BAJFINANCE.NS","HCLTECH.NS","WIPRO.NS",
    "MARUTI.NS","TITAN.NS","SUNPHARMA.NS","AXISBANK.NS","KOTAKBANK.NS","NTPC.NS",
    "ADANIENT.NS","TATAMOTORS.NS","ONGC.NS","POWERGRID.NS","TATASTEEL.NS","HINDALCO.NS",
    "INDUSINDBK.NS","ULTRACEMCO.NS","TECHM.NS","JSWSTEEL.NS","NESTLEIND.NS","APOLLOHOSP.NS",
    "DRREDDY.NS","DIVISLAB.NS",
    # Brazil
    "VALE","PBR","ITUB","BBD","ABEV","NU","SBS","GGB","EWZ","PAGS",
    "STNE","XP","BPAC11.SA","WEGE3.SA","RENT3.SA","EQTL3.SA","B3SA3.SA","RADL3.SA",
    "RAIL3.SA","SUZB3.SA","PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","BBAS3.SA",
    "MGLU3.SA","LREN3.SA","HAPV3.SA","CSAN3.SA","VIVT3.SA",
    # Mexico
    "AMX","CEMEX","FMX","BSMX","KOF",
    # South Africa
    "NPN.JO","SOL.JO","BTI.JO","AGL.JO","BHP.JO","FSR.JO","SBK.JO","ABG.JO","NED.JO",
    "MTN.JO","SHP.JO","DSY.JO","INP.JO","VOD.JO","AMS.JO",
    # Saudi Arabia
    "2222.SR","1180.SR","2010.SR","1010.SR","2350.SR","7010.SR","1150.SR","2020.SR",
    # Thailand
    "PTT.BK","AOT.BK","ADVANC.BK","CPALL.BK","SCB.BK","SCC.BK","GULF.BK","BDMS.BK",
    # Indonesia
    "BBCA.JK","BBRI.JK","BMRI.JK","TLKM.JK","ASII.JK","UNVR.JK","BBNI.JK","ICBP.JK",
    # Malaysia
    "MBBM.KL","PBBANK.KL","TENAGA.KL","CIMB.KL","PCHEM.KL","IHH.KL",
    # Chile
    "SQM","BCH","BSAC",
    # Poland
    "PKO.WA","PEO.WA","KGH.WA","PZU.WA","DNP.WA","CDR.WA","ALE.WA",
    # Turkey
    "THYAO.IS","ASELS.IS","BIMAS.IS","GARAN.IS","AKBNK.IS","EREGL.IS","TUPRS.IS","SISE.IS",
    # Philippines
    "SM.PS","ALI.PS","BDO.PS","TEL.PS","AC.PS","JFC.PS",
    # Qatar / UAE / Kuwait
    "QNB.QA","QEWS.QA","EMAAR.DU","FAB.AD","DIB.DU",
    # Others (Greece, Czech, Hungary, Egypt, Colombia, Peru)
    "OPAP.AT","HTO.AT","ETE.AT","CEZ.PR","MOL.BD","HRKG.BD","EC","BVN","CENCOSUD.SN",
]

# ---------------------------------------------------------------------------
# MSCI World Small Cap — representative developed-market small caps.
# ---------------------------------------------------------------------------
_STATIC_MSCI_WORLD_SC = [
    # US small caps
    "AXON","PCTY","PAYC","ENSG","MEDP","NOVT","TREX","SCI","CWST","KNSL",
    "BWXT","RGEN","CSWI","SPSC","FHI","AIT","AZEK","ZWS","IPAR","BRBR",
    "SWX","EVR","PJT","JEF","HLI","OWL","STEP","COKE","VRNS","PRGS",
    "KTOS","MGNI","IRTC","OLLI","BOOT","DOCS","GSHD","CARG","RELY","LNTH",
    "KRYS","TGTX","RVMD","ITCI","PCVX","ARWR","SRPT","RARE","XNCR","ALNY",
    "TNDM","NVCR","NVST","NEOG","HALO","RPRX","CYTK","CRNX","FOLD","DYN",
    "CORT","LGND","INSM","HRMY","AKRO","RCKT","GERN","APLS","BL","TENB",
    "RPD","FRSH","BRZE","ALTR","ESTC","DLO","PAYO","FLYW","SEMR","CWAN",
    "JAMF","NSIT","ALRM","CALX","VIAV","TTMI","CEVA","POWI","DIOD","FORM",
    "AEIS","LFUS","CXT","AMSC","ATKR","MBC","STRL","ROAD","PRIM","MYRG",
    # UK small caps
    "SHED.L","FOUR.L","BOKU.L","TET.L","JTC.L","GAMA.L","DPLM.L","BMY.L","WIZZ.L",
    # European small caps
    "MOR.ST","LIFCO-B.ST","BULTEN.ST","VIT.PA","GBT.MI","MASI.HE",
    # Japan small caps
    "6981.T","7735.T","6395.T","3774.T","4385.T","6920.T","7832.T","3088.T","2413.T",
    "6532.T","6191.T","7747.T","4684.T","3765.T","2371.T",
    # Australia small caps
    "NHF.AX","ILU.AX","ORA.AX","EVN.AX","OZL.AX","NIC.AX","IGO.AX","SFR.AX","PLS.AX",
    "LYC.AX","WAF.AX","NST.AX","GOR.AX","DVP.AX","DEG.AX",
    # Canada small caps
    "BYD.TO","TFII.TO","LUN.TO","ERO.TO","MTY.TO","CTC-A.TO","GIB-A.TO",
    "TIH.TO","AIF.TO","SJ.TO","PKI.TO","TVK.TO","MDA.TO",
]

# ---------------------------------------------------------------------------
# MSCI Japan — large+mid cap Japanese equities.
# ---------------------------------------------------------------------------
_STATIC_MSCI_JAPAN = [
    "7203.T","6758.T","9984.T","6861.T","8306.T","9433.T","6501.T","7267.T","4502.T","6902.T",
    "7751.T","8035.T","6954.T","4063.T","9432.T","6367.T","7974.T","8058.T","2802.T","4503.T",
    "3382.T","4568.T","6301.T","6702.T","6752.T","7741.T","8001.T","8031.T","8316.T","8411.T",
    "4661.T","6098.T","8766.T","9020.T","9022.T","6273.T","4519.T","6326.T","8591.T","4507.T",
    "8830.T","6594.T","3659.T","8725.T","8801.T","7269.T","4911.T","6988.T","6503.T","7270.T",
    "8802.T","6762.T","8630.T","4543.T","6981.T","8750.T","9531.T","3407.T","1925.T","1928.T",
    "7201.T","8015.T","4523.T","2502.T","4578.T","6971.T","6645.T","8053.T","5108.T","8267.T",
    "4901.T","6701.T","1605.T","2801.T","4689.T","5401.T","6506.T","7735.T","2914.T","8303.T",
    "3861.T","6479.T","8604.T","7011.T","5802.T","6857.T","4755.T","7733.T","8252.T","5713.T",
    "6724.T","1332.T","4452.T","2503.T","2269.T","9502.T","6752.T","1801.T","1803.T","9613.T",
    "2413.T","4704.T","2768.T","5020.T","5019.T","3289.T","1802.T","7202.T","7261.T","5411.T",
    "4902.T","7211.T","8354.T","7272.T","3086.T","7731.T","6305.T","7832.T","6963.T","9101.T",
    "9104.T","9107.T","8309.T","9301.T","4183.T","4188.T","1878.T","2501.T","3405.T","3401.T",
    "9021.T","5332.T","4151.T","2871.T","6841.T","5803.T","4631.T","6361.T","7276.T","5703.T",
    "4004.T","4005.T","5301.T","2432.T","9983.T","6504.T","8233.T","7752.T","6471.T","6770.T",
    "7012.T","3101.T","5714.T","3402.T","5706.T","9064.T","6473.T","6753.T","4042.T","4021.T",
    "7951.T","7013.T","6302.T","5232.T","5233.T","8601.T","8628.T","9735.T","4927.T","6460.T",
    "3099.T","2331.T","7186.T","4523.T","9766.T","6981.T","8876.T","7762.T","8795.T","4307.T",
    "6752.T","5631.T","2897.T","6952.T","8585.T","4272.T","3105.T","3436.T","6268.T","7912.T",
    "8053.T","6472.T","8331.T","4208.T","2229.T","9005.T","6752.T","4088.T","6674.T","9843.T",
]

# ---------------------------------------------------------------------------
# MSCI Pacific ex-Japan — Australia, Hong Kong, Singapore, New Zealand.
# ---------------------------------------------------------------------------
_STATIC_MSCI_PACIFIC_EX_JP = [
    # Australia
    "BHP.AX","CBA.AX","CSL.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX","WES.AX","WOW.AX","FMG.AX",
    "TLS.AX","RIO.AX","WDS.AX","ALL.AX","COL.AX","TCL.AX","GMG.AX","REA.AX","STO.AX","SHL.AX",
    "QBE.AX","ORG.AX","IAG.AX","MPL.AX","MIN.AX","S32.AX","NCM.AX","AGL.AX","JHX.AX","AMC.AX",
    "TWE.AX","ASX.AX","RMD.AX","CPU.AX","APA.AX","GPT.AX","MGR.AX","SGP.AX","DXS.AX","SCG.AX",
    "VCX.AX","SUN.AX","BEN.AX","BOQ.AX","AMP.AX","IFL.AX","PPT.AX","CGF.AX","ORI.AX","BXB.AX",
    "XRO.AX","SEK.AX","REH.AX","CAR.AX","NHF.AX","ILU.AX","ORA.AX","EVN.AX","NST.AX","IGO.AX",
    "PLS.AX","LYC.AX","WHC.AX","NWS.AX","ALQ.AX","TAH.AX","JBH.AX","PMV.AX","SUL.AX","WEB.AX",
    "CTD.AX","QAN.AX","SYD.AX","TPG.AX","APX.AX","BRG.AX","LOV.AX","APE.AX","DMP.AX","EDV.AX",
    # Hong Kong
    "0001.HK","0002.HK","0003.HK","0005.HK","0006.HK","0011.HK","0012.HK","0016.HK","0017.HK",
    "0019.HK","0027.HK","0066.HK","0083.HK","0101.HK","0175.HK","0241.HK","0267.HK","0288.HK",
    "0386.HK","0388.HK","0669.HK","0688.HK","0762.HK","0823.HK","0857.HK","0883.HK","0939.HK",
    "0941.HK","0960.HK","0968.HK","0981.HK","1038.HK","1044.HK","1093.HK","1109.HK","1113.HK",
    "1177.HK","1211.HK","1299.HK","1398.HK","1810.HK","1876.HK","1928.HK","1997.HK","2007.HK",
    "2018.HK","2020.HK","2269.HK","2313.HK","2318.HK","2319.HK","2382.HK","2388.HK","2628.HK",
    "3328.HK","3690.HK","3968.HK","3988.HK","6098.HK","6862.HK","9618.HK","9888.HK","9988.HK",
    "9999.HK",
    # Singapore
    "D05.SI","O39.SI","U11.SI","Z74.SI","C6L.SI","A17U.SI","C38U.SI","N2IU.SI","Y92.SI","F34.SI",
    "BN4.SI","S58.SI","S63.SI","V03.SI","H78.SI","G13.SI","BS6.SI","U96.SI","C09.SI","S68.SI",
    # New Zealand
    "FPH.NZ","ATM.NZ","SPK.NZ","MEL.NZ","RYM.NZ","AIA.NZ","CEN.NZ","MFT.NZ","SKC.NZ","EBO.NZ",
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
    "msci_em_imi": _STATIC_MSCI_EM_IMI,
    "msci_world_sc": _STATIC_MSCI_WORLD_SC,
    "msci_japan": _STATIC_MSCI_JAPAN,
    "msci_pacific_ex_jp": _STATIC_MSCI_PACIFIC_EX_JP,
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
