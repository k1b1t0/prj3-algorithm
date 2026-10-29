"""
PhaseLogger cho Proposed H-CSM (Quotient-DP Matheuristic).
Xuat trace thuc thi ASCII ngan gon cho kiem toan chi tiet.
"""
from typing import Dict, Any
from models import SprintPlan


def print_phase_trace(plan: SprintPlan, trace: Dict[str, Any], detailed: bool = False):
    """Xuat trace kiem toan chi tiet 3 pha."""
    print("=" * 88)
    print(f"[H-CSM Execution Trace] Weight w: {trace['weight_w']:.2f} | Bounds: f1_max={trace['bounds']['f1_max']:.1f}, f2_max={trace['bounds']['f2_max']:.1f}")
    print("-" * 88)

    p1 = trace.get("phase1", {})
    print(f"[Phase 1: Quotient Space Reduction & 1D DP Profiling]")
    print(f"  * Input Tasks: {p1.get('input_task_count', 0)} | Equivalence Classes (Super-Nodes): {p1.get('cluster_count', 0)}")
    if detailed and "clusters" in p1:
        for cl in p1["clusters"][:8]:
            print(f"    - Cluster G{cl['id']} [{cl['repo']}:{cl['mod']}] (Effort: {cl['effort']} SP)")
        if len(p1["clusters"]) > 8:
            print(f"    ... and {len(p1['clusters']) - 8} more quotient clusters")

    p2 = trace.get("phase2", {})
    print(f"[Phase 2: Unified Multiple-Choice Quotient Allocation]")
    print(f"  * Remaining Capacity per Team: {p2.get('rem_cap', {})}")

    p3 = trace.get("phase3", {})
    print(f"[Phase 3: Inter-Team Consolidation & Bitmask DP Open-TSP]")
    routes = p3.get("team_routes", {})
    for tm_id, r_info in routes.items():
        print(f"  * Team {tm_id} ({r_info.get('num_blocks', 0)} blocks): Method: {r_info.get('method', 'DP')} | Cost: {r_info.get('cost', 0.0):.2f}")
        if detailed and "chain" in r_info:
            print(f"    Route: {' -> '.join(r_info['chain'])}")

    print("-" * 88)
    print(f"[H-CSM Summary] Assigned: {plan.total_risk_resolved:.1f} CVSS | f1: {plan.total_utility_resolved:.1f} | f2: {plan.total_switch_cost:.2f} | Time: {plan.execution_time_ms:.1f} ms")
    print("=" * 88)
