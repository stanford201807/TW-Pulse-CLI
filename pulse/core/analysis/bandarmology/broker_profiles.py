"""Broker profiling and classification for bandarmology analysis."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class BrokerProfile(str, Enum):
    """Broker profile classification."""

    SMART_MONEY_FOREIGN = "Smart Money Foreign"  # Institusi asing besar
    BANDAR_GORENGAN = "Bandar/Gorengan"  # Sering goreng saham
    RETAIL = "Retail"  # Platform retail
    LOCAL_INSTITUTIONAL = "Local Institutional"  # Institusi lokal
    MARKET_MAKER = "Market Maker"  # Biasa di 2 sisi
    UNKNOWN = "Unknown"


class BrokerInfo(BaseModel):
    """Information about a broker."""

    code: str
    name: str
    profile: BrokerProfile
    weight: float = 1.0  # Scoring weight
    description: Optional[str] = None


# Accurate Broker Profile Classification
# Based on market behavior and typical trading patterns

BROKER_PROFILES = {
    # =========================================================================
    # SMART MONEY FOREIGN - Institusi asing besar, biasanya directional
    # Follow big funds, pension funds, hedge funds
    # =========================================================================
    "SMART_MONEY_FOREIGN": {
        "codes": ["AK", "BK", "KZ", "MS", "GR", "LG", "CS", "DX", "ML", "DB"],
        "names": {
            "AK": "UBS Sekuritas",
            "BK": "J.P. Morgan Sekuritas",
            "KZ": "Credit Suisse Sekuritas",
            "MS": "Morgan Stanley Sekuritas",
            "GR": "Citi Sekuritas",
            "LG": "Deutsche Sekuritas",
            "CS": "CLSA Sekuritas",
            "DX": "BNP Paribas Sekuritas",
            "ML": "Merrill Lynch Sekuritas",
            "DB": "Deutsche Bank Sekuritas",
        },
        "weight": 1.5,  # Higher weight in scoring - most reliable signal
        "description": "Institusi asing besar, usually follow big funds. Strong directional signal.",
    },
    # =========================================================================
    # BANDAR / GORENGAN - Sering terlibat pump & dump
    # Hati-hati dengan pola distribusi terselubung
    # =========================================================================
    "BANDAR_GORENGAN": {
        "codes": ["SQ", "MG", "EP", "DR", "BZ", "AI"],
        "names": {
            "SQ": "Sinarmas Sekuritas",
            "MG": "Maybank Sekuritas",
            "EP": "MNC Sekuritas",
            "DR": "Danpac Sekuritas",
            "BZ": "Jasa Utama Capital",
            "AI": "Artha Sekuritas",
        },
        "weight": 0.8,  # Lower trust weight
        "description": "Sering terlibat gorengan. Watch for distribution patterns.",
    },
    # =========================================================================
    # RETAIL - Platform investor ritel
    # Biasanya late to the party, bisa jadi contrarian indicator
    # =========================================================================
    "RETAIL": {
        "codes": ["XA", "AZ", "KI", "YO", "ZP"],
        "names": {
            "XA": "Indo Premier (IPOT)",
            "AZ": "Stockbit Sekuritas",
            "KI": "Phintraco Sekuritas",
            "YO": "Yuanta Sekuritas",
            "ZP": "Ajaib Sekuritas",
        },
        "weight": 0.5,  # Contrarian indicator - retail often wrong
        "description": "Retail platforms. Often late, can be contrarian signal.",
    },
    # =========================================================================
    # LOCAL INSTITUTIONAL - Institusi lokal
    # Dana kelolaan besar, more informed than retail
    # =========================================================================
    "LOCAL_INSTITUTIONAL": {
        "codes": ["CC", "NI", "OD", "TP", "IF", "AG", "DH", "PG"],
        "names": {
            "CC": "Mandiri Sekuritas",
            "NI": "BNI Sekuritas",
            "OD": "Henan Putihrai Sekuritas",
            "TP": "Trimegah Sekuritas",
            "IF": "Sucor Sekuritas",
            "AG": "Panin Sekuritas",
            "DH": "Danareksa Sekuritas",
            "PG": "Mandiri Sekuritas (Retail)",
        },
        "weight": 1.0,  # Normal weight
        "description": "Local institutional brokers. Managed funds, pension, insurance.",
    },
    # =========================================================================
    # MARKET MAKER - Sering di kedua sisi
    # Net position matters more than gross volume
    # =========================================================================
    "MARKET_MAKER": {
        "codes": ["YU", "RX", "PD", "FG", "KK", "RG"],
        "names": {
            "YU": "Mirae Asset Sekuritas",
            "RX": "Macquarie Sekuritas",
            "PD": "CGS International Sekuritas",
            "FG": "Asia Kapitalindo Sekuritas",
            "KK": "Phillip Sekuritas",
            "RG": "RHB Sekuritas",
        },
        "weight": 0.7,  # Net position matters more
        "description": "Market makers. Often on both sides. Watch net position.",
    },
}


# Flat lookup: broker_code -> profile
BROKER_CODE_TO_PROFILE: dict[str, BrokerProfile] = {}
BROKER_CODE_TO_NAME: dict[str, str] = {}
BROKER_CODE_TO_WEIGHT: dict[str, float] = {}

# Build lookup tables from BROKER_PROFILES
_profile_mapping = {
    "SMART_MONEY_FOREIGN": BrokerProfile.SMART_MONEY_FOREIGN,
    "BANDAR_GORENGAN": BrokerProfile.BANDAR_GORENGAN,
    "RETAIL": BrokerProfile.RETAIL,
    "LOCAL_INSTITUTIONAL": BrokerProfile.LOCAL_INSTITUTIONAL,
    "MARKET_MAKER": BrokerProfile.MARKET_MAKER,
}

for profile_key, profile_data in BROKER_PROFILES.items():
    profile_enum = _profile_mapping.get(profile_key, BrokerProfile.UNKNOWN)

    for code in profile_data["codes"]:
        BROKER_CODE_TO_PROFILE[code] = profile_enum
        BROKER_CODE_TO_NAME[code] = profile_data["names"].get(code, code)
        BROKER_CODE_TO_WEIGHT[code] = profile_data["weight"]


class BrokerProfiler:
    """Utility class for broker profiling."""

    def __init__(self):
        self.profiles = BROKER_PROFILES
        self.code_to_profile = BROKER_CODE_TO_PROFILE
        self.code_to_name = BROKER_CODE_TO_NAME
        self.code_to_weight = BROKER_CODE_TO_WEIGHT

    def get_profile(self, broker_code: str) -> BrokerProfile:
        """Get profile for a broker code."""
        return self.code_to_profile.get(broker_code.upper(), BrokerProfile.UNKNOWN)

    def get_name(self, broker_code: str) -> str:
        """Get full name for a broker code."""
        return self.code_to_name.get(broker_code.upper(), broker_code)

    def get_weight(self, broker_code: str) -> float:
        """Get scoring weight for a broker code."""
        return self.code_to_weight.get(broker_code.upper(), 1.0)

    def get_broker_info(self, broker_code: str) -> BrokerInfo:
        """Get complete broker info."""
        code = broker_code.upper()
        return BrokerInfo(
            code=code,
            name=self.get_name(code),
            profile=self.get_profile(code),
            weight=self.get_weight(code),
        )

    def is_smart_money(self, broker_code: str) -> bool:
        """Check if broker is smart money foreign."""
        return self.get_profile(broker_code) == BrokerProfile.SMART_MONEY_FOREIGN

    def is_bandar(self, broker_code: str) -> bool:
        """Check if broker is bandar/gorengan."""
        return self.get_profile(broker_code) == BrokerProfile.BANDAR_GORENGAN

    def is_retail(self, broker_code: str) -> bool:
        """Check if broker is retail platform."""
        return self.get_profile(broker_code) == BrokerProfile.RETAIL

    def is_institutional(self, broker_code: str) -> bool:
        """Check if broker is local institutional."""
        return self.get_profile(broker_code) == BrokerProfile.LOCAL_INSTITUTIONAL

    def is_market_maker(self, broker_code: str) -> bool:
        """Check if broker is market maker."""
        return self.get_profile(broker_code) == BrokerProfile.MARKET_MAKER

    def get_codes_by_profile(self, profile: BrokerProfile) -> list[str]:
        """Get all broker codes for a specific profile."""
        profile_key_map = {
            BrokerProfile.SMART_MONEY_FOREIGN: "SMART_MONEY_FOREIGN",
            BrokerProfile.BANDAR_GORENGAN: "BANDAR_GORENGAN",
            BrokerProfile.RETAIL: "RETAIL",
            BrokerProfile.LOCAL_INSTITUTIONAL: "LOCAL_INSTITUTIONAL",
            BrokerProfile.MARKET_MAKER: "MARKET_MAKER",
        }
        key = profile_key_map.get(profile)
        if key and key in self.profiles:
            return self.profiles[key]["codes"]
        return []

    def classify_brokers(self, broker_codes: list[str]) -> dict[BrokerProfile, list[str]]:
        """Classify a list of broker codes by profile."""
        result: dict[BrokerProfile, list[str]] = {p: [] for p in BrokerProfile}
        for code in broker_codes:
            profile = self.get_profile(code)
            result[profile].append(code)
        return result
