"""Constants for Indonesian Stock Market (IDX)."""


# IDX Sector Classifications (JASICA)
IDX_SECTORS: dict[str, list[str]] = {
    "FINANCE": [
        "BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BRIS", "MEGA", "NISP",
        "BTPN", "BDMN", "BNGA", "BNLI", "PNBN", "BJBR", "BJTM", "ARTO",
        "BBYB", "NOBU", "BINA", "MCOR", "SDRA", "AGRO", "BMAS", "BBHI",
    ],
    "BANKING": [
        "BBCA", "BBRI", "BMRI", "BBNI", "BBTN", "BRIS", "MEGA", "NISP",
        "BTPN", "BDMN", "BNGA", "BNLI", "PNBN", "BJBR", "BJTM", "ARTO",
    ],
    "MINING": [
        "ADRO", "PTBA", "ITMG", "BUMI", "BYAN", "INDY", "HRUM", "DOID",
        "ANTM", "INCO", "TINS", "MDKA", "NICL", "NCKL", "MBMA", "ADMR",
        "MEDC", "GEMS", "BSSR", "MYOH", "KKGI",
    ],
    "COAL": [
        "ADRO", "PTBA", "ITMG", "BUMI", "BYAN", "INDY", "HRUM", "DOID",
        "GEMS", "BSSR", "MYOH", "KKGI", "MBAP", "TOBA",
    ],
    "NICKEL": [
        "ANTM", "INCO", "NICL", "NCKL", "MBMA",
    ],
    "CONSUMER": [
        "UNVR", "ICBP", "INDF", "MYOR", "KLBF", "HMSP", "GGRM", "SIDO",
        "ULTJ", "CPIN", "JPFA", "MAIN", "GOOD", "CLEO", "ADES",
    ],
    "TELCO": [
        "TLKM", "EXCL", "ISAT", "TOWR", "TBIG", "MTEL",
    ],
    "PROPERTY": [
        "BSDE", "CTRA", "SMRA", "PWON", "LPKR", "DILD", "ASRI", "APLN",
        "KIJA", "DMAS", "JRPT", "MKPI", "PPRO", "BEST",
    ],
    "INFRASTRUCTURE": [
        "JSMR", "PGAS", "WIKA", "WSKT", "PTPP", "ADHI", "WTON", "ACST",
        "TOTL", "NRCA", "WSBP",
    ],
    "PLANTATION": [
        "LSIP", "AALI", "SSMS", "SIMP", "SGRO", "TBLA", "SMAR", "DSNG",
        "PALM", "BWPT",
    ],
    "AUTOMOTIVE": [
        "ASII", "AUTO", "SMSM", "GJTL", "IMAS", "INDS",
    ],
    "TECHNOLOGY": [
        "GOTO", "BUKA", "EMTK", "DCII", "CASH",
    ],
    "HEALTHCARE": [
        "KLBF", "SIDO", "MIKA", "HEAL", "SILO", "PRDA",
    ],
    "RETAIL": [
        "AMRT", "MAPI", "ACES", "RALS", "LPPF", "ERAA", "MIDI",
    ],
}

# Flatten all tickers
ALL_TICKERS: set[str] = set()
for sector_tickers in IDX_SECTORS.values():
    ALL_TICKERS.update(sector_tickers)

# Major IDX Broker Codes
BROKER_CODES: dict[str, str] = {
    # Foreign Brokers (Asing)
    "YU": "Mirae Asset Sekuritas",
    "PD": "CGS International Sekuritas",
    "MS": "Morgan Stanley Sekuritas",
    "CC": "Mandiri Sekuritas",
    "RX": "Macquarie Sekuritas",
    "LG": "Deutsche Sekuritas",
    "AK": "UBS Sekuritas",
    "KZ": "Credit Suisse Sekuritas",
    "CS": "CLSA Sekuritas",
    "DX": "BNP Paribas Sekuritas",
    "BK": "J.P. Morgan Sekuritas",
    "GR": "Citi Sekuritas",
    "ML": "Merrill Lynch Sekuritas",
    "FG": "Asia Kapitalindo Sekuritas",
    "KK": "Phillip Sekuritas",
    "DB": "Deutsche Bank Sekuritas",

    # Local Brokers (Lokal)
    "OD": "Henan Putihrai Sekuritas",
    "NI": "BNI Sekuritas",
    "EP": "MNC Sekuritas",
    "IF": "Sucor Sekuritas",
    "SQ": "Sinarmas Sekuritas",
    "AI": "Artha Sekuritas",
    "YP": "Samuel Sekuritas",
    "DR": "Danpac Sekuritas",
    "BZ": "Jasa Utama Capital Sekuritas",
    "AG": "Panin Sekuritas",
    "TP": "Trimegah Sekuritas",
    "ZP": "Ajaib Sekuritas",
    "AZ": "Stockbit Sekuritas",
    "KI": "Phintraco Sekuritas",
    "GI": "Kresna Sekuritas",
    "XA": "IPOT (Indo Premier)",
    "RG": "RHB Sekuritas",
    "PG": "Mandiri Sekuritas (Retail)",
    "DH": "Danareksa Sekuritas",
    "AO": "APERD Sekuritas",
    "LS": "Lautandhana Sekuritas",
    "YO": "Yuanta Sekuritas",
    "MG": "Maybank Sekuritas",
    "SK": "Shinhan Sekuritas",
    "KB": "KB Valbury Sekuritas",
    "NH": "NH Korindo Sekuritas",
}

# Major/Important Brokers to watch
MAJOR_BROKERS: dict[str, list[str]] = {
    "FOREIGN_BIG": ["YU", "PD", "MS", "CC", "RX", "LG", "BK", "GR", "ML"],
    "FOREIGN_MID": ["AK", "KZ", "CS", "DX", "FG", "KK", "DB"],
    "LOCAL_BIG": ["OD", "NI", "EP", "IF", "SQ", "AG", "TP"],
    "RETAIL": ["ZP", "AZ", "KI", "XA", "YO"],
}

# Broker type classification
BROKER_TYPES: dict[str, str] = {
    "YU": "Asing",
    "PD": "Asing",
    "MS": "Asing",
    "CC": "Lokal",
    "RX": "Asing",
    "LG": "Asing",
    "BK": "Asing",
    "GR": "Asing",
    "ML": "Asing",
    "AK": "Asing",
    "KZ": "Asing",
    "CS": "Asing",
    "DX": "Asing",
    "OD": "Lokal",
    "NI": "Lokal",
    "EP": "Lokal",
    "IF": "Lokal",
    "SQ": "Lokal",
    "ZP": "Lokal",
    "AZ": "Lokal",
    "KI": "Lokal",
    "XA": "Lokal",
    "TP": "Lokal",
}

# LQ45 Components (frequently updated)
LQ45_TICKERS: list[str] = [
    "ACES", "ADRO", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI",
    "BBTN", "BMRI", "BRPT", "BUKA", "CPIN", "EMTK", "EXCL", "GGRM",
    "GOTO", "HMSP", "ICBP", "INCO", "INDF", "INKP", "ISAT", "ITMG",
    "JPFA", "KLBF", "MAPI", "MDKA", "MEDC", "MIKA", "MNCN", "PGAS",
    "PTBA", "SMGR", "SRTG", "TBIG", "TINS", "TLKM", "TOWR", "TPIA",
    "UNTR", "UNVR", "WIKA", "WSKT",
]

# IDX30 Components
IDX30_TICKERS: list[str] = [
    "ADRO", "AMRT", "ANTM", "ASII", "BBCA", "BBNI", "BBRI", "BBTN",
    "BMRI", "BRPT", "CPIN", "EMTK", "EXCL", "GGRM", "ICBP", "INCO",
    "INDF", "ITMG", "KLBF", "MDKA", "PGAS", "PTBA", "SMGR", "TBIG",
    "TLKM", "TOWR", "TPIA", "UNTR", "UNVR",
]

# Trading hours (WIB - Jakarta time)
TRADING_HOURS = {
    "pre_opening": ("08:45", "09:00"),
    "session_1": ("09:00", "11:30"),
    "break": ("11:30", "13:30"),
    "session_2": ("13:30", "15:00"),
    "pre_closing": ("15:00", "15:10"),
    "post_trading": ("15:10", "16:00"),
}

# Price fractions (tick size) based on price level
PRICE_FRACTIONS: dict[tuple, int] = {
    (0, 200): 1,
    (200, 500): 2,
    (500, 2000): 5,
    (2000, 5000): 10,
    (5000, float("inf")): 25,
}

# Auto Rejection Limits (ARA/ARB)
AUTO_REJECTION = {
    "acceleration_board": {"up": 0.35, "down": 0.35},
    "development_board": {"up": 0.35, "down": 0.35},
    "main_board": {"up": 0.25, "down": 0.25},
    "ipo_day1": {"up": 0.50, "down": 0.50},
}
