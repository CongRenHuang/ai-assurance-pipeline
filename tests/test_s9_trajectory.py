"""S9: trajectory invariant 斷言。

核心對照：兩條路徑最終狀態都是 BLOCKED，
只有一條是保證，另一條是運氣（或錯誤歸因）。
"""
import json, pathlib, sys

from assurance.trajectory import Trajectory, Step

RESULTS = []


def rec(name, passed, detail):
    RESULTS.append({"test": name, "passed": passed, "detail": detail})
    print(f"{'PASS' if passed else 'FAIL'} {name}: {detail}")


def expect_ok(name, fn, detail=""):
    try:
        fn(); rec(name, True, detail or "invariant 成立")
    except AssertionError as e:
        rec(name, False, str(e)[:200])


def expect_raises(name, fn, detail=""):
    try:
        fn(); rec(name, False, "應該要拋 AssertionError 但沒有")
    except AssertionError:
        rec(name, True, detail or "正確地偵測到違反")


# ============ 情境 A：政策路徑（保證）============
GOOD = Trajectory(steps=[
    Step("release_assessment", "CHAIN"),
    Step("eval.citation_coverage", "EVALUATOR",
         {"assurance.evaluation": "citation_coverage"}),
    Step("policy.hard_block", "GUARDRAIL", {
        "assurance.policy_id": "FIN-AI-004",
        "assurance.plugin": "HardPolicyGate",
        "assurance.decision": "BLOCK",
        "assurance.override_rejected": True,
    }),
])

# ============ 情境 B：錯誤歸因（S8 真實 bug）============
# 最終也是 BLOCKED，但擋它的是來源治理誤判，R4 檢查從未執行
MISATTRIBUTED = Trajectory(steps=[
    Step("release_assessment", "CHAIN"),
    Step("policy.source_governance", "GUARDRAIL", {
        "assurance.policy_id": "FIN-AI-001",
        "assurance.plugin": "HardPolicyPlugin",
        "assurance.decision": "BLOCK",
    }),
])

# ============ 情境 C：運氣路徑 ============
LUCKY = Trajectory(steps=[Step("release_assessment", "CHAIN")])


print("\n--- 1. 強制檢查點 ---")
expect_ok("1a_good_has_checkpoint",
          lambda: GOOD.assert_mandatory_checkpoint("policy.hard_block"))
expect_raises("1b_lucky_missing_checkpoint",
              lambda: LUCKY.assert_mandatory_checkpoint("policy.hard_block"),
              "運氣路徑沒有經過 hard_block -> 正確判 FAIL")

print("\n--- 2. 歸因正確（S8 bug 的 regression）---")
expect_ok("2a_good_attribution",
          lambda: GOOD.assert_decided_by("FIN-AI-004", "HardPolicyGate"))
expect_raises("2b_misattributed_detected",
              lambda: MISATTRIBUTED.assert_decided_by("FIN-AI-004", "HardPolicyGate"),
              "R4 未被 HardPolicyGate 決定 -> 正確判 FAIL")

print("\n--- 3. 必要前驅 ---")
APPROVED = Trajectory(steps=[
    Step("policy.hard_policy_check", "GUARDRAIL",
         {"assurance.policy_id": "FIN-AI-004", "assurance.plugin": "HardPolicyGate"}),
    Step("approve", "TOOL"),
])
BAD_APPROVE = Trajectory(steps=[Step("approve", "TOOL")])
expect_ok("3a_approve_after_check",
          lambda: APPROVED.assert_required_predecessor("approve", "policy.hard_policy_check"))
expect_raises("3b_approve_without_check",
              lambda: BAD_APPROVE.assert_required_predecessor("approve", "policy.hard_policy_check"),
              "核准前未經 hard policy 檢查 -> 正確判 FAIL")

print("\n--- 4. 副作用基數 ---")
DOUBLE = Trajectory(steps=[Step("external_model_call", "LLM"),
                           Step("external_model_call", "LLM")])
expect_ok("4a_within_limit",
          lambda: GOOD.assert_side_effect_cardinality("external_model_call", 1))
expect_raises("4b_exceeds_limit",
              lambda: DOUBLE.assert_side_effect_cardinality("external_model_call", 1),
              "外送 2 次 > 上限 1 -> 正確判 FAIL")

print("\n--- 5. 禁止轉移 ---")
UNSAFE = Trajectory(steps=[Step("unknown_source", "GUARDRAIL"),
                           Step("external_model_call", "LLM")])
expect_ok("5a_no_forbidden",
          lambda: GOOD.assert_forbidden_transition("unknown_source", "external_model_call"))
expect_raises("5b_forbidden_detected",
              lambda: UNSAFE.assert_forbidden_transition("unknown_source", "external_model_call"),
              "UNKNOWN 來源直接接外部模型 -> 正確判 FAIL")

print("\n--- 6. 只看結果 vs 看軌跡 ---")
result_only = all(t.index_of("release_assessment") >= 0
                  for t in (GOOD, MISATTRIBUTED, LUCKY))
rec("6a_result_only_all_pass", result_only,
    "只斷言最終狀態 -> 三條路徑全部 PASS（問題所在）")

def traj_check(t):
    try:
        t.assert_decided_by("FIN-AI-004", "HardPolicyGate"); return True
    except AssertionError:
        return False

survivors = [n for n, t in
             (("GOOD", GOOD), ("MISATTRIBUTED", MISATTRIBUTED), ("LUCKY", LUCKY))
             if traj_check(t)]
rec("6b_trajectory_only_good_passes", survivors == ["GOOD"],
    f"看軌跡 -> 只有 {survivors} 通過")

print("\n" + "=" * 64)
print("  三條路徑最終狀態都是 BLOCKED。")
print("  只斷言 result 的測試：三條全 PASS。")
print("  斷言 trajectory 的測試：只有 GOOD 通過。")
print("=" * 64)

pathlib.Path("evidence").mkdir(exist_ok=True)
pathlib.Path("evidence/S9-results.json").write_text(
    json.dumps({"results": RESULTS,
                "good_trajectory": GOOD.to_evidence(),
                "misattributed_trajectory": MISATTRIBUTED.to_evidence()},
               indent=2, ensure_ascii=False), encoding="utf-8")

ok = all(r["passed"] for r in RESULTS)
print("\n" + ("PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
