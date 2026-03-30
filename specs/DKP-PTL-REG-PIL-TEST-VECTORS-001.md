# **DKP-PTL-REG-PIL-TEST-VECTORS-001**

## **Deterministic PIL Extraction Test Vector Specification**

Version: 0.1  
Status: Draft – Validation Candidate  
Layer: Conformance and Reproducibility Validation Layer

Aligned with:

* DKP-PTL-REG-PIL-EXTRACTION-001 v0.3  
* DKP-PTL-REG-REFERENCE-001 v0.6  
* DKP-PTL-REG-CLIENT-001 v0.6

---

# **1\. Purpose**

This document defines the official conformance test vector format and mandatory validation corpus for deterministic Product Identity Layer extraction.

This specification exists to ensure that identical inputs produce identical extraction outputs across all compliant client implementations.

This specification:

* defines the test vector schema  
* defines normalization requirements for fixtures  
* defines pass/fail criteria  
* defines mandatory coverage categories  
* defines the initial official vector set

This specification does NOT:

* modify PIL extraction rules  
* redefine page parsing logic  
* introduce alternative outputs  
* permit probabilistic acceptance

---

# **2\. Deterministic Validation Principle**

For every official test vector:

* input fixture is immutable  
* execution order is fixed  
* expected output is unique  
* pass/fail decision is binary

A compliant implementation MUST produce exact expected output for every official vector.

No tolerance bands are permitted.

---

# **3\. Canonical Test Vector Schema**

Each test vector MUST be represented as a single JSON object with the following shape:

{  
  "test\_id": "pil\_tv\_0001",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "jsonld\_single\_product",  
  "description": "Single JSON-LD product object with explicit brand/model/sku and one visible price",  
  "input": {  
    "url": "https://example.com/product/bosch-rotak-32-1200w",  
    "utc\_year": 2026,  
    "html": "..."  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "bosch",  
      "model": "rotak 32 1200w",  
      "sku": "rotak32-1200",  
      "condition": "new",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "1200w",  
      "release\_year": ""  
    }  
  }  
}

All keys are mandatory.

If `pil_extraction_status != OK`, the `PIL` object MUST be omitted.

---

# **4\. Fixture Encoding Rules**

All official fixtures MUST:

* be stored as UTF-8  
* be normalized to NFC before publication  
* contain literal HTML text only  
* exclude network dependencies  
* exclude remote script execution  
* exclude shadow DOM  
* exclude browser extension state

The `html` field is the canonical serialized DOM fixture for the test.

The test harness MUST use the fixture exactly as published.

No implementation may fetch additional page resources.

---

# **5\. Execution Contract**

For each vector, the implementation MUST execute the PIL extraction runtime exactly once using:

* `input.url`  
* `input.utc_year`  
* `input.html`

The implementation MUST NOT:

* rewrite the fixture  
* repair invalid markup beyond browser-standard DOM parsing  
* add inferred metadata  
* substitute missing fields

The implementation MUST parse the fixture under standard browser DOM rules.

---

# **6\. Pass/Fail Rule**

A vector passes only if all of the following hold:

1. `pil_extraction_status` matches exactly  
2. if status is `OK`, every PIL field matches exactly  
3. no extra fields are emitted  
4. field values match exact normalized strings

Any mismatch is a failure.

There is no partial pass.

---

# **7\. Official Coverage Categories**

The official corpus MUST include vectors covering all of the following categories:

1. single JSON-LD product  
2. multiple JSON-LD products  
3. microdata-only product  
4. meta-only fallback  
5. DOM-title fallback  
6. URL fallback only  
7. listing page LCA selection  
8. invalid page unit due to multiple prices  
9. insufficient identity  
10. conflict blocked  
11. bundle detection  
12. storage\_or\_size extraction  
13. release year extraction  
14. condition mapping  
15. URL poisoning resistance  
16. structured-vs-DOM precedence  
17. no match  
18. deep nested card LCA  
19. duplicate title noise  
20. multilingual visible text with Latin product identifiers

No category may be omitted from the official corpus.

---

# **8\. Official Vector Set v0.1**

## **TV-0001 — Single JSON-LD Product**

{  
  "test\_id": "pil\_tv\_0001",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "jsonld\_single\_product",  
  "description": "Single JSON-LD product object with explicit brand/model/sku and one visible price",  
  "input": {  
    "url": "https://example.com/product/bosch-rotak-32-1200w",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<script type=\\"application/ld+json\\"\>{\\"@context\\":\\"https://schema.org\\",\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Bosch\\"},\\"model\\":\\"Rotak 32 1200W\\",\\"sku\\":\\"ROTAK32-1200\\",\\"itemCondition\\":\\"new\\",\\"size\\":\\"1200W\\"}\</script\>\</head\>\<body\>\<h1\>Bosch Rotak 32 1200W\</h1\>\<div class=\\"price\\"\>₪ 899\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "bosch",  
      "model": "rotak 32 1200w",  
      "sku": "rotak32-1200",  
      "condition": "new",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "1200w",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0002 — Multiple JSON-LD Products, Most Informative Wins**

{  
  "test\_id": "pil\_tv\_0002",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "jsonld\_multiple\_products",  
  "description": "Two Product objects present; object with more non-empty PIL fields must be selected",  
  "input": {  
    "url": "https://example.com/p/iphone-13-128gb",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<script type=\\"application/ld+json\\"\>{\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Apple\\"},\\"model\\":\\"iPhone 13\\"}\</script\>\<script type=\\"application/ld+json\\"\>{\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Apple\\"},\\"model\\":\\"iPhone 13 128GB\\",\\"sku\\":\\"A2633\\",\\"size\\":\\"128GB\\",\\"itemCondition\\":\\"new\\"}\</script\>\</head\>\<body\>\<h1\>Apple iPhone 13 128GB\</h1\>\<span\>₪ 2499\</span\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "apple",  
      "model": "iphone 13 128gb",  
      "sku": "a2633",  
      "condition": "new",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "128gb",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0003 — Microdata Only**

{  
  "test\_id": "pil\_tv\_0003",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "microdata\_only",  
  "description": "Microdata provides product identity without JSON-LD",  
  "input": {  
    "url": "https://example.com/lawn/bosch-universalrotak-34",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body itemscope itemtype=\\"https://schema.org/Product\\"\>\<h1 itemprop=\\"name\\"\>Bosch UniversalRotak 34\</h1\>\<span itemprop=\\"brand\\"\>Bosch\</span\>\<span itemprop=\\"model\\"\>UniversalRotak 34\</span\>\<span itemprop=\\"sku\\"\>UR34\</span\>\<span\>₪ 1099\</span\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "bosch",  
      "model": "universalrotak 34",  
      "sku": "ur34",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0004 — Meta Only Fallback**

{  
  "test\_id": "pil\_tv\_0004",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "meta\_only",  
  "description": "Meta tags supply brand and condition; title provides model",  
  "input": {  
    "url": "https://example.com/item/galaxy-s24-ultra-256gb",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<meta property=\\"og:title\\" content=\\"Samsung Galaxy S24 Ultra 256GB\\"\>\<meta property=\\"product:brand\\" content=\\"Samsung\\"\>\<meta property=\\"product:condition\\" content=\\"new\\"\>\</head\>\<body\>\<h1\>Samsung Galaxy S24 Ultra 256GB\</h1\>\<div\>₪ 4999\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "samsung",  
      "model": "galaxy s24 ultra 256gb",  
      "sku": "",  
      "condition": "new",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "256gb",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0005 — DOM Title Fallback**

{  
  "test\_id": "pil\_tv\_0005",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "dom\_title\_fallback",  
  "description": "No structured metadata; visible title and single price produce model-only valid extraction",  
  "input": {  
    "url": "https://example.com/tools/makita-hr2470",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<div class=\\"product\\"\>\<h1\>Makita HR2470 Rotary Hammer\</h1\>\<span class=\\"price\\"\>$ 159\</span\>\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "makita",  
      "model": "hr2470 rotary hammer",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0006 — URL Fallback Only, Valid**

{  
  "test\_id": "pil\_tv\_0006",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "url\_fallback\_only",  
  "description": "No structured metadata; URL tokens and DOM title permit valid extraction",  
  "input": {  
    "url": "https://example.com/product/dyson-v15-detect-2025",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<div\>\<h1\>Dyson V15 Detect 2025\</h1\>\<div\>£ 599\</div\>\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "dyson",  
      "model": "v15 detect 2025",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": "2025"  
    }  
  }  
}

## **TV-0007 — Listing Page LCA Selection**

{  
  "test\_id": "pil\_tv\_0007",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "listing\_page\_lca",  
  "description": "Product card boundary is derived by LCA of title and price",  
  "input": {  
    "url": "https://example.com/search?q=robot+vacuum",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<div class=\\"grid\\"\>\<div class=\\"card\\"\>\<a\>\<h2\>Xiaomi Robot Vacuum S10\</h2\>\</a\>\<span\>₪ 1299\</span\>\</div\>\<div class=\\"card\\"\>\<a\>\<h2\>Roborock Q8 Max\</h2\>\</a\>\<span\>₪ 1899\</span\>\</div\>\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "",  
      "model": "xiaomi robot vacuum s10",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0008 — Invalid Page Unit, Multiple Prices**

{  
  "test\_id": "pil\_tv\_0008",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "invalid\_multiple\_prices",  
  "description": "Card contains old price and current price; embedded contract requires exactly one price candidate",  
  "input": {  
    "url": "https://example.com/item/playstation-5",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<div class=\\"card\\"\>\<h1\>PlayStation 5 Console\</h1\>\<span class=\\"old\\"\>$ 599\</span\>\<span class=\\"new\\"\>$ 499\</span\>\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "INVALID\_PAGE\_UNIT"  
  }  
}

## **TV-0009 — Insufficient Identity**

{  
  "test\_id": "pil\_tv\_0009",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "insufficient\_identity",  
  "description": "Title too generic; model cannot be constructed",  
  "input": {  
    "url": "https://example.com/product/best-sale-item",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>New Best Sale Deal\</h1\>\<div\>€ 99\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "INSUFFICIENT\_IDENTITY"  
  }  
}

## **TV-0010 — Conflict Blocked**

{  
  "test\_id": "pil\_tv\_0010",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "conflict\_blocked",  
  "description": "Structured source and visible title create irreconcilable core identity conflict",  
  "input": {  
    "url": "https://example.com/p/canon-r6",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<script type=\\"application/ld+json\\"\>{\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Canon\\"},\\"model\\":\\"EOS R6\\"}\</script\>\</head\>\<body\>\<h1\>Canon EOS R5\</h1\>\<div\>$ 1999\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "CONFLICT\_BLOCKED"  
  }  
}

## **TV-0011 — Bundle Detection**

{  
  "test\_id": "pil\_tv\_0011",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "bundle\_detection",  
  "description": "Bundle markers must set bundle\_flag to bundle",  
  "input": {  
    "url": "https://example.com/p/gopro-hero12-kit",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>GoPro Hero12 Kit with Charger\</h1\>\<div\>$ 449\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "gopro",  
      "model": "hero12 kit with charger",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "bundle",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0012 — Storage Extraction**

{  
  "test\_id": "pil\_tv\_0012",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "storage\_extraction",  
  "description": "Storage token must normalize and populate storage\_or\_size",  
  "input": {  
    "url": "https://example.com/p/steam-deck-1tb",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>Steam Deck OLED 1TB\</h1\>\<div\>$ 649\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "",  
      "model": "steam deck oled 1tb",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "1tb",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0013 — Release Year Extraction**

{  
  "test\_id": "pil\_tv\_0013",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "release\_year\_extraction",  
  "description": "4-digit valid year must populate release\_year",  
  "input": {  
    "url": "https://example.com/p/tesla-model-y-2027",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>Tesla Model Y 2027\</h1\>\<div\>$ 39999\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "tesla",  
      "model": "model y 2027",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": "2027"  
    }  
  }  
}

## **TV-0014 — Condition Mapping**

{  
  "test\_id": "pil\_tv\_0014",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "condition\_mapping",  
  "description": "Condition synonyms must map to normalized condition",  
  "input": {  
    "url": "https://example.com/p/macbook-air-renewed",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>MacBook Air M2 Renewed\</h1\>\<div\>$ 799\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "",  
      "model": "macbook air m2 renewed",  
      "sku": "",  
      "condition": "refurbished",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0015 — URL Poisoning Resistance**

{  
  "test\_id": "pil\_tv\_0015",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "url\_poisoning\_resistance",  
  "description": "SEO noise in URL must not override structured identity",  
  "input": {  
    "url": "https://example.com/super-mega-deal-iphone-13-cheap-best-offer-2026",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<script type=\\"application/ld+json\\"\>{\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Apple\\"},\\"model\\":\\"iPhone 13\\",\\"sku\\":\\"A2633\\"}\</script\>\</head\>\<body\>\<h1\>Apple iPhone 13\</h1\>\<div\>$ 499\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "apple",  
      "model": "iphone 13",  
      "sku": "a2633",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0016 — Structured vs DOM Precedence**

{  
  "test\_id": "pil\_tv\_0016",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "structured\_vs\_dom\_precedence",  
  "description": "Structured source must win over lower-precedence DOM candidate",  
  "input": {  
    "url": "https://example.com/p/ninja-af500",  
    "utc\_year": 2026,  
    "html": "\<html\>\<head\>\<script type=\\"application/ld+json\\"\>{\\"@type\\":\\"Product\\",\\"brand\\":{\\"name\\":\\"Ninja\\"},\\"model\\":\\"AF500\\"}\</script\>\</head\>\<body\>\<h1\>Ninja AF500 Official Best Deal Edition\</h1\>\<div\>$ 229\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "ninja",  
      "model": "af500",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0017 — No Match**

{  
  "test\_id": "pil\_tv\_0017",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "no\_match",  
  "description": "Generic content page without product-bearing structure must return NO\_MATCH",  
  "input": {  
    "url": "https://example.com/blog/how-to-choose-a-drill",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<article\>\<h1\>How to Choose a Drill\</h1\>\<p\>No products listed here.\</p\>\</article\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "NO\_MATCH"  
  }  
}

## **TV-0018 — Deep Nested Card LCA**

{  
  "test\_id": "pil\_tv\_0018",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "deep\_nested\_lca",  
  "description": "Nested card structure must still resolve deterministic LCA within depth bound",  
  "input": {  
    "url": "https://example.com/search?q=headphones",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<div class=\\"grid\\"\>\<section\>\<div\>\<div\>\<article\>\<header\>\<a\>\<span\>\<h2\>Sony WH-1000XM5\</h2\>\</span\>\</a\>\</header\>\<footer\>\<div\>\<span\>€ 299\</span\>\</div\>\</footer\>\</article\>\</div\>\</div\>\</section\>\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "sony",  
      "model": "wh-1000xm5",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0019 — Duplicate Title Noise**

{  
  "test\_id": "pil\_tv\_0019",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "duplicate\_title\_noise",  
  "description": "Repeated marketing words must not dominate model parsing",  
  "input": {  
    "url": "https://example.com/p/logitech-mx-master-3s",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>Logitech MX Master 3S Best Best Best Deal\</h1\>\<div\>$ 89\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "logitech",  
      "model": "mx master 3s",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

## **TV-0020 — Multilingual Visible Text with Latin Identifier**

{  
  "test\_id": "pil\_tv\_0020",  
  "spec\_version": "0.1",  
  "pil\_extraction\_version": "0.3",  
  "category": "multilingual\_visible\_text",  
  "description": "Visible non-Latin text may coexist with Latin model identifier; extraction must preserve normalized Latin identity tokens",  
  "input": {  
    "url": "https://example.com/il/product/dreame-l10s-ultra",  
    "utc\_year": 2026,  
    "html": "\<html\>\<body\>\<h1\>שואב אבק Dreame L10S Ultra\</h1\>\<div\>₪ 2799\</div\>\</body\>\</html\>"  
  },  
  "expected": {  
    "pil\_extraction\_status": "OK",  
    "PIL": {  
      "brand": "dreame",  
      "model": "l10s ultra",  
      "sku": "",  
      "condition": "",  
      "bundle\_flag": "standalone",  
      "warranty\_type": "",  
      "region\_variant": "il",  
      "storage\_or\_size": "",  
      "release\_year": ""  
    }  
  }  
}

---

# **9\. Mandatory Harness Behavior**

The official validation harness MUST:

* load vectors in lexical `test_id` order  
* execute each vector independently  
* produce a machine-readable result log  
* stop only after all vectors complete  
* report full mismatch details per failed vector

Output schema:

{  
  "suite\_id": "pil\_vectors\_v0\_1",  
  "pil\_extraction\_version": "0.3",  
  "passed": 20,  
  "failed": 0,  
  "results": \[  
    {  
      "test\_id": "pil\_tv\_0001",  
      "status": "PASS"  
    }  
  \]  
}

---

# **10\. Conformance Requirement**

An implementation is conformant to this vector set only if:

* all official vectors pass  
* no vector is skipped  
* no expected output is modified locally

Selective conformance is prohibited.

---

# **11\. Version Governance**

Any modification to:

* vector input HTML  
* expected output  
* category definitions  
* harness contract

requires a new test vector specification version.

No silent mutation is permitted.

---

# **12\. Final Statement**

DKP-PTL-REG-PIL-TEST-VECTORS-001 v0.1 establishes:

* the official conformance schema for PIL extraction  
* a deterministic validation corpus  
* binary pass/fail behavior  
* mandatory category coverage  
* implementation reproducibility basis

This document is the validation companion to DKP-PTL-REG-PIL-EXTRACTION-001 v0.3.

