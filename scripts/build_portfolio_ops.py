from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_SOURCE = PROJECT_ROOT / "data-source" / "portfolio-data.snapshot.json"
SCAN_SOURCE = PROJECT_ROOT / "data-source" / "folder-scan.snapshot.json"
TRIAGE_SOURCE = PROJECT_ROOT / "data-source" / "triage-recommendations.snapshot.json"
FAIR_SOURCE = PROJECT_ROOT / "data-source" / "fair-scores.snapshot.json"
OPS_JSON = PROJECT_ROOT / "ops-readiness.json"
DATA_JSON = PROJECT_ROOT / "data.json"
DATA_JS = PROJECT_ROOT / "data.js"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def triage_label(item: dict[str, object]) -> str:
    if item["recommendedStatus"] == "needs-triage":
        return "Needs triage"
    return f"Recommended {item['recommendedStatusLabel']}"


def status_resolution(project: dict[str, object], triage: dict[str, object] | None) -> tuple[str, bool, str]:
    if project["statusExplicit"]:
        return project["statusLabel"], True, "explicit"
    if triage and triage["recommendedStatus"] != "needs-triage" and triage["confidence"] in {"medium", "high"}:
        return triage["recommendedStatusLabel"], True, "triage"
    return "Needs triage", False, "unresolved"


def compute_readiness(project: dict[str, object], scan: dict[str, object] | None, triage: dict[str, object] | None, fair: dict[str, object] | None) -> dict[str, object]:
    fair_total = fair["scores"]["total"] if fair else 0
    fair_component = round(fair_total * 0.4)
    score = fair_component
    reasons: list[str] = [f"FAIR proxy contributes {fair_component}/40"]

    resolved_label, resolved, resolution_source = status_resolution(project, triage)
    if project["statusExplicit"]:
        score += 12
        reasons.append("Explicit lifecycle label present (+12)")
    elif triage and triage["recommendedStatus"] != "needs-triage" and triage["confidence"] in {"medium", "high"}:
        score += 8
        reasons.append(f"{triage['confidence'].title()} confidence triage recommendation (+8)")
    elif triage and triage["recommendedStatus"] != "needs-triage":
        score += 4
        reasons.append("Low confidence triage recommendation (+4)")

    has_specific_existing = bool(scan and scan.get("specificPath") and scan.get("exists"))
    if has_specific_existing:
        score += 8
        reasons.append("Specific live path exists (+8)")
    if scan and scan.get("hasGit"):
        score += 8
        reasons.append("Git repository detected (+8)")
        if not scan.get("gitDirty"):
            score += 4
            reasons.append("Git worktree appears clean (+4)")
    if scan and scan.get("hasTestsMarker"):
        score += 6
        reasons.append("Tests marker detected (+6)")
    if scan and scan.get("hasPaperArtifact"):
        score += 6
        reasons.append("Paper artifact detected (+6)")
    if scan and scan.get("hasProtocolArtifact"):
        score += 6
        reasons.append("Protocol artifact detected (+6)")
    if scan and (scan.get("hasIndexHtml") or scan.get("hasNoJekyll")):
        score += 6
        reasons.append("Pages-ready delivery signal (+6)")
    if scan and scan.get("activityBand") in {"fresh", "recent"}:
        score += 4
        reasons.append(f"{scan['activityBand'].title()} path activity (+4)")

    score = min(score, 100)

    publish_signal = bool(scan and (scan.get("hasIndexHtml") or scan.get("hasNoJekyll")) and scan.get("hasPaperArtifact") and scan.get("hasProtocolArtifact"))
    code_signal = bool(scan and scan.get("hasGit") and scan.get("hasTestsMarker"))
    operationally_backed = bool(resolved and code_signal and publish_signal and fair_total >= 60)

    if not has_specific_existing:
        primary_action = "Fix indexed path"
    elif not resolved:
        primary_action = "Freeze lifecycle status"
    elif not scan or not scan.get("hasGit"):
        primary_action = "Initialize or repair git"
    elif not scan.get("hasTestsMarker"):
        primary_action = "Add executable tests"
    elif not scan.get("hasPaperArtifact") or not scan.get("hasProtocolArtifact"):
        primary_action = "Complete manuscript bundle"
    elif not (scan.get("hasIndexHtml") or scan.get("hasNoJekyll")):
        primary_action = "Make Pages deliverable"
    elif fair_total < 60:
        primary_action = "Raise FAIR proxy maturity"
    elif scan.get("gitDirty"):
        primary_action = "Stabilize dirty worktree"
    else:
        primary_action = "Monitor and maintain"

    return {
        "name": project["name"],
        "id": project["id"],
        "path": project["path"],
        "tier": project["tierShortName"],
        "tierName": project["tierName"],
        "type": project["type"],
        "explicitStatus": project["statusLabel"],
        "resolvedStatus": resolved_label,
        "statusResolved": resolved,
        "resolutionSource": resolution_source,
        "triageLabel": triage_label(triage) if triage else "",
        "triageConfidence": triage["confidence"] if triage else "",
        "fairTotal": fair_total,
        "fairBand": fair["band"] if fair else "unknown",
        "readinessScore": score,
        "hasLivePath": has_specific_existing,
        "hasGit": bool(scan and scan.get("hasGit")),
        "gitDirty": bool(scan and scan.get("gitDirty")),
        "hasTests": bool(scan and scan.get("hasTestsMarker")),
        "hasPaper": bool(scan and scan.get("hasPaperArtifact")),
        "hasProtocol": bool(scan and scan.get("hasProtocolArtifact")),
        "pagesReady": bool(scan and (scan.get("hasIndexHtml") or scan.get("hasNoJekyll"))),
        "activityBand": scan.get("activityBand", "unknown") if scan else "unknown",
        "operationalSignals": scan.get("operationalSignals", 0) if scan else 0,
        "publishSignal": publish_signal,
        "codeSignal": code_signal,
        "operationallyBacked": operationally_backed,
        "primaryAction": primary_action,
        "reasons": reasons[:8],
    }


def build_payload() -> tuple[dict[str, object], dict[str, object]]:
    portfolio = load_json(PORTFOLIO_SOURCE)
    scan = load_json(SCAN_SOURCE)
    triage = load_json(TRIAGE_SOURCE)
    fair = load_json(FAIR_SOURCE)

    scan_by_path = {item["path"]: item for item in scan["scans"]}
    triage_by_id = {item["id"]: item for item in triage["recommendations"]}
    fair_by_id = {item["id"]: item for item in fair["scores"]}

    projects = [
        compute_readiness(
            project,
            scan_by_path.get(project["path"]),
            triage_by_id.get(project["id"]),
            fair_by_id.get(project["id"]),
        )
        for project in portfolio["portfolio"]
    ]

    readiness_scores = [item["readinessScore"] for item in projects]
    resolved_count = sum(1 for item in projects if item["statusResolved"])
    triage_resolved_count = sum(1 for item in projects if item["resolutionSource"] == "triage")
    code_signal_count = sum(1 for item in projects if item["codeSignal"])
    publish_signal_count = sum(1 for item in projects if item["publishSignal"])
    backed_count = sum(1 for item in projects if item["operationallyBacked"])
    high_readiness_count = sum(1 for item in projects if item["readinessScore"] >= 70)

    tier_scores: defaultdict[str, list[int]] = defaultdict(list)
    action_counts: Counter[str] = Counter()
    for item in projects:
        tier_scores[item["tier"]].append(item["readinessScore"])
        action_counts[item["primaryAction"]] += 1

    tier_means = [
        {"tier": tier, "meanReadiness": round(sum(scores) / len(scores), 1), "count": len(scores)}
        for tier, scores in tier_scores.items()
    ]

    ops_file = {
        "project": "PortfolioOps",
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "overview": {
            "trackedProjects": len(projects),
            "meanReadiness": round(sum(readiness_scores) / len(readiness_scores), 1),
            "medianReadiness": sorted(readiness_scores)[len(readiness_scores) // 2],
            "resolvedStatusCount": resolved_count,
            "resolvedStatusPercent": round((resolved_count / len(projects)) * 100, 1),
            "triageResolvedCount": triage_resolved_count,
            "triageResolvedPercent": round((triage_resolved_count / len(projects)) * 100, 1),
            "codeSignalCount": code_signal_count,
            "codeSignalPercent": round((code_signal_count / len(projects)) * 100, 1),
            "publishSignalCount": publish_signal_count,
            "publishSignalPercent": round((publish_signal_count / len(projects)) * 100, 1),
            "operationallyBackedCount": backed_count,
            "operationallyBackedPercent": round((backed_count / len(projects)) * 100, 1),
            "highReadinessCount": high_readiness_count,
            "highReadinessPercent": round((high_readiness_count / len(projects)) * 100, 1),
        },
        "projects": projects,
    }

    dashboard = {
        "project": {
            "name": "PortfolioOps",
            "version": "0.1.0",
            "generatedAt": ops_file["generatedAt"],
            "designBasis": [
                "Portfolio registry merged with live folder telemetry",
                "Triage recommendations and FAIR proxy scores folded into one readiness model",
                "Static GitHub Pages dashboard and E156 bundle",
            ],
        },
        "metrics": ops_file["overview"],
        "actionBreakdown": [
            {"action": action, "count": count}
            for action, count in sorted(action_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "bestTiers": sorted(tier_means, key=lambda item: (-item["meanReadiness"], item["tier"]))[:6],
        "weakestTiers": sorted(tier_means, key=lambda item: (item["meanReadiness"], item["tier"]))[:6],
        "topProjects": sorted(projects, key=lambda item: (-item["readinessScore"], item["name"]))[:12],
        "backedProjects": [item for item in sorted(projects, key=lambda item: (-item["readinessScore"], item["name"])) if item["operationallyBacked"]][:12],
        "priorityQueue": sorted(
            [item for item in projects if item["primaryAction"] != "Monitor and maintain"],
            key=lambda item: (item["readinessScore"], item["name"]),
        )[:16],
    }

    return ops_file, dashboard


def write_outputs(ops_file: dict[str, object], dashboard: dict[str, object]) -> None:
    OPS_JSON.write_text(json.dumps(ops_file, indent=2), encoding="utf-8")
    DATA_JSON.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
    DATA_JS.write_text("window.PORTFOLIO_OPS_DATA = " + json.dumps(dashboard, indent=2) + ";\n", encoding="utf-8")


def main() -> None:
    ops_file, dashboard = build_payload()
    write_outputs(ops_file, dashboard)
    metrics = dashboard["metrics"]
    print(
        "Built PortfolioOps "
        f"({metrics['trackedProjects']} projects, "
        f"{metrics['operationallyBackedCount']} operationally backed, "
        f"{metrics['highReadinessPercent']}% readiness >= 70)."
    )


if __name__ == "__main__":
    main()
