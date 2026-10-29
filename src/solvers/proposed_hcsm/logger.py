"""
PhaseLogger for Proposed H-CSM.
Formats clean ASCII execution trace for detailed auditing.
"""
from typing import Dict, Any
from models import SprintPlan


def print_phase_trace(plan: SprintPlan, trace: Dict[str, Any], detailed: bool = False):
    """Format clean concise ASCII debug trace."""
    print("=" * 88)
    print(f"[H-CSM Execution Trace] Weight w: {trace['weight_w']:.2f} | Bounds: f1_max={trace['bounds']['f1_max']:.1f}, f2_max={trace['bounds']['f2_max']:.1f}")
    print("-" * 88)

    p1 = trace["phase1"]
    print(f"[Phase 1: Coarsening & Chunking]")
    print(f"  * Input Tasks: {p1['input_task_count']} | Created {p1['chunk_count']} Chunks (E_chunk = 15 SP)")
    if detailed:
        for ch in p1["chunks"][:8]:
            print(f"    - Chunk B{ch['chunk_id']} [{ch['repo']}:{ch['module']}:{ch['skill']}] ({ch['effort']} SP): Tasks {ch['task_ids']}")
        if len(p1["chunks"]) > 8:
            print(f"    ... and {len(p1['chunks']) - 8} more chunks")

    p2 = trace["phase2"]
    print(f"[Phase 2: Multi-Cluster Packing]")
    print(f"  * Packed {len(p2['packing_steps'])} Chunks | Rem Cap: {p2['rem_cap_after_packing']}")
    if detailed:
        for step in p2["packing_steps"]:
            print(f"    - Team {step['team_id']} <- Chunk B{step['chunk_id']} ({step['effort']} SP) | Tasks: {step['task_ids']} | Gain: {step['gain']:+.4f}")

    p3 = trace["phase3"]
    print(f"[Phase 3: Residual Backfill & Hard Guardrail (S > 0)]")
    print(f"  * Accepted: {len(p3['accepted_backfills'])} tasks | Blocked by Guardrail: {len(p3['blocked_guardrail'])} tasks | Final Rem Cap: {p3['final_rem_cap']}")
    if detailed:
        for acc in p3["accepted_backfills"]:
            print(f"    - ACCEPTED: Task {acc['task_id']} ({acc['effort']} SP) -> Team {acc['team_id']} | S: {acc['score_s']:.5f} > 0 (Delta Z: {acc['delta_z']:+.4f})")
        for blk in p3["blocked_guardrail"][:5]:
            print(f"    - BLOCKED:  Task {blk['task_id']} ({blk['effort']} SP) -> Team {blk['team_id']} | Reason: {blk['reason']}")

    p4 = trace["phase4"]
    print(f"[Phase 4: Super-Node Block-Level Open-TSP]")
    for tm_id, r_info in p4["team_routes"].items():
        print(f"  * Team {tm_id} ({r_info['num_blocks']} blocks): Method: {r_info['method']} | Route Cost: {r_info['cost']:.2f}")
        if detailed and "chain" in r_info:
            print(f"    Route: {' -> '.join(r_info['chain'])}")

    print("-" * 88)
    print(f"[H-CSM Summary] Assigned: {plan.total_risk_resolved:.1f} CVSS | f1: {plan.total_utility_resolved:.1f} | f2: {plan.total_switch_cost:.2f} | Time: {plan.execution_time_ms:.1f} ms")
    print("=" * 88)

