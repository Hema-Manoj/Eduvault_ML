# stages/aggregator.py

def aggregate_verdict(pdf_result, phash_result, cnn_result):
    """
    Combines PDF forensics, pHash, and CNN anomaly into a final trust score (0–100)
    """

    # ---------------- PDF NAME FORENSICS ----------------
    forensic_score = pdf_result.get("forensic_score", 0)
    pdf_verdict = pdf_result.get("verdict", "UNKNOWN")

    # Continuous risk: higher forensic_score → higher risk
    pdf_risk = forensic_score / (forensic_score + 4)

    # ---------------- pHASH ----------------
    phash_verdict = phash_result.get("phash_verdict", "")
    hamming_distance = phash_result.get("hamming_distance", 20)

    # Normalize hamming distance (cap at 20)
    phash_risk = min(hamming_distance / 20, 1.0)

    # ---------------- CNN ANOMALY ----------------
    cnn_score = cnn_result.get("cnn_anomaly_score", 0.0)
    cnn_verdict = cnn_result.get("cnn_anomaly_verdict", "")

    # Higher CNN score = more normal → invert to risk
    cnn_risk = max(0.0, 0.5 - cnn_score)
    cnn_risk = min(max(cnn_risk, 0.0), 1.0)

    # ---------------- WEIGHTED AGGREGATION ----------------
    final_risk = (
        0.50 * pdf_risk +
        0.35 * phash_risk +
        0.15 * cnn_risk
    )

    trust_score = round((1 - final_risk) * 100, 1)

    # ---------------- CONFIDENCE BOOST ----------------
    if (
        pdf_verdict == "LIKELY_ORIGINAL"
        and phash_verdict == "VISUALLY_MATCHING"
        and cnn_verdict == "NORMAL"
    ):
        trust_score = min(trust_score + 12, 95)

    # ---------------- FINAL VERDICT LABEL ----------------
    if trust_score >= 85:
        final_verdict = "HIGHLY_TRUSTED"
    elif trust_score >= 65:
        final_verdict = "MOSTLY_TRUSTED"
    elif trust_score >= 45:
        final_verdict = "NEEDS_REVIEW"
    else:
        final_verdict = "HIGH_RISK"

    return {
        "trust_score": trust_score,
        "final_verdict": final_verdict,
        "components": {
            "pdf_risk": round(pdf_risk, 3),
            "phash_risk": round(phash_risk, 3),
            "cnn_risk": round(cnn_risk, 3)
        }
    }
