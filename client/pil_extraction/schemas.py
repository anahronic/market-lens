"""
Typed schemas for PIL extraction.
All structures are explicit and version-locked per DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal

# PIL extraction status values per spec
PILExtractionStatus = Literal[
    "OK",
    "NO_MATCH",
    "INSUFFICIENT_IDENTITY",
    "CONFLICT_BLOCKED",
    "INVALID_PAGE_UNIT",
]


@dataclass(frozen=True)
class PILObject:
    """Product Identity Layer object per spec section 4."""
    brand: str
    model: str
    sku: str
    condition: str
    bundle_flag: str
    warranty_type: str
    region_variant: str
    storage_or_size: str
    release_year: str

    def to_dict(self) -> dict:
        return {
            "brand": self.brand,
            "model": self.model,
            "sku": self.sku,
            "condition": self.condition,
            "bundle_flag": self.bundle_flag,
            "warranty_type": self.warranty_type,
            "region_variant": self.region_variant,
            "storage_or_size": self.storage_or_size,
            "release_year": self.release_year,
        }


@dataclass(frozen=True)
class ExtractionResult:
    """Result of PIL extraction."""
    pil_extraction_status: PILExtractionStatus
    pil: Optional[PILObject] = None

    def to_dict(self) -> dict:
        result = {"pil_extraction_status": self.pil_extraction_status}
        if self.pil_extraction_status == "OK" and self.pil is not None:
            result["PIL"] = self.pil.to_dict()
        return result


@dataclass(frozen=True)
class TestVectorInput:
    """Input portion of a test vector."""
    url: str
    utc_year: int
    html: str


@dataclass(frozen=True)
class TestVectorExpected:
    """Expected output of a test vector."""
    pil_extraction_status: PILExtractionStatus
    pil: Optional[PILObject] = None

    @staticmethod
    def from_dict(d: dict) -> "TestVectorExpected":
        status = d["pil_extraction_status"]
        pil = None
        if status == "OK" and "PIL" in d:
            pil_dict = d["PIL"]
            pil = PILObject(
                brand=pil_dict["brand"],
                model=pil_dict["model"],
                sku=pil_dict["sku"],
                condition=pil_dict["condition"],
                bundle_flag=pil_dict["bundle_flag"],
                warranty_type=pil_dict["warranty_type"],
                region_variant=pil_dict["region_variant"],
                storage_or_size=pil_dict["storage_or_size"],
                release_year=pil_dict["release_year"],
            )
        return TestVectorExpected(pil_extraction_status=status, pil=pil)


@dataclass(frozen=True)
class TestVector:
    """A complete test vector per DKP-PTL-REG-PIL-TEST-VECTORS-001."""
    test_id: str
    spec_version: str
    pil_extraction_version: str
    category: str
    description: str
    input: TestVectorInput
    expected: TestVectorExpected

    @staticmethod
    def from_dict(d: dict) -> "TestVector":
        inp = d["input"]
        return TestVector(
            test_id=d["test_id"],
            spec_version=d["spec_version"],
            pil_extraction_version=d["pil_extraction_version"],
            category=d["category"],
            description=d["description"],
            input=TestVectorInput(
                url=inp["url"],
                utc_year=inp["utc_year"],
                html=inp["html"],
            ),
            expected=TestVectorExpected.from_dict(d["expected"]),
        )


@dataclass
class SourceContribution:
    """Tracks which source provided which field."""
    source: Literal["S1", "S2", "S3", "S4", "S5"]
    field: str
    value: str


@dataclass
class PageUnitResult:
    """Result of page unit selection."""
    success: bool
    title_node: Optional[object] = None  # DOM element (bs4 Tag)
    price_node: Optional[object] = None  # DOM element
    lca_root: Optional[object] = None    # LCA element
    failure_reason: Optional[str] = None


@dataclass
class ExtractedFields:
    """Intermediate extracted fields with source provenance."""
    brand: str = ""
    model: str = ""
    sku: str = ""
    condition: str = ""
    bundle_flag: str = "standalone"
    warranty_type: str = ""
    region_variant: str = ""
    storage_or_size: str = ""
    release_year: str = ""
    sources: dict = field(default_factory=dict)  # field -> source

    def to_pil(self) -> PILObject:
        return PILObject(
            brand=self.brand,
            model=self.model,
            sku=self.sku,
            condition=self.condition,
            bundle_flag=self.bundle_flag,
            warranty_type=self.warranty_type,
            region_variant=self.region_variant,
            storage_or_size=self.storage_or_size,
            release_year=self.release_year,
        )
