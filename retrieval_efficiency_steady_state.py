import asyncio
import json
import time
from pathlib import Path
from statistics import mean, variance

from benchmarks.common.mem0_client import Mem0Client


RESULT_DIR = Path("results/locomo")
INPUT_DIR = RESULT_DIR / "predicted_mem0-locomo-reproduction"

RAW_FILE = RESULT_DIR / "retrieval_efficiency_steady_state_raw.json"
SUMMARY_FILE = RESULT_DIR / "retrieval_efficiency_steady_state_summary.json"

NUM_TRIALS = 5
TOP_K_VALUES = [200, 50]

# Counterbalanced order to reduce time-order bias.
TRIAL_SCHEDULE = [
    (200, 1),
    (50, 1),
    (50, 2),
    (200, 2),
    (200, 3),
    (50, 3),
    (50, 4),
    (200, 4),
    (200, 5),
    (50, 5),
]


def percentile(values, p):
    """Linear interpolation percentile."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(ordered))
    weight = position - lower

    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def load_questions():
    files = sorted(
        INPUT_DIR.glob("conv0_q*.json"),
        key=lambda p: int(p.stem.split("q")[-1])
    )

    questions = [json.loads(p.read_text()) for p in files]

    if len(questions) != 152:
        raise ValueError(
            f"Expected 152 questions, found {len(questions)}"
        )

    if len({q["user_id"] for q in questions}) != 1:
        raise ValueError("Inconsistent user IDs")

    return questions


async def warm_up(client, questions, top_k):
    """Warm up using all 152 questions. Excluded from measurements."""
    print(f"\nWarm-up: Top-K={top_k}")

    for i, q in enumerate(questions, 1):
        await client.search(
            query=q["question"],
            user_id=q["user_id"],
            top_k=top_k,
            rerank=False,
        )

        if i % 25 == 0:
            print(f"Warm-up progress: {i}/152")

    print(f"Warm-up Top-K={top_k} complete")


async def run_trial(client, questions, top_k, trial):
    latencies = []

    print(f"\nStarting Top-K={top_k}, Trial {trial}")

    for i, q in enumerate(questions, 1):
        start = time.perf_counter()

        await client.search(
            query=q["question"],
            user_id=q["user_id"],
            top_k=top_k,
            rerank=False,
        )

        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

        if i % 25 == 0:
            print(f"Progress: {i}/152")

    result = {
        "trial": trial,
        "top_k": top_k,
        "questions": len(latencies),
        "mean_latency_ms": mean(latencies),
        "variance_latency_ms_squared": variance(latencies),
        "p50_latency_ms": percentile(latencies, 0.50),
        "p95_latency_ms": percentile(latencies, 0.95),
        "latencies_ms": latencies,
    }

    print(
        f"Trial {trial} Top-K={top_k}: "
        f"Mean={result['mean_latency_ms']:.2f} ms"
    )

    return result


async def main():
    if RAW_FILE.exists() or SUMMARY_FILE.exists():
        raise FileExistsError(
            "Steady-state result file already exists. "
            "Refusing to overwrite."
        )

    questions = load_questions()
    results = {"200": [], "50": []}

    async with Mem0Client(
        mode="oss",
        host="http://localhost:8888",
        rpm=100000,
    ) as client:

        # Phase 1: Full warm-up for both Top-K settings.
        # All 152 questions are used; no warm-up latency is recorded.
        for top_k in TOP_K_VALUES:
            await warm_up(client, questions, top_k)

        # Phase 2: Counterbalanced formal trials.
        for top_k, trial in TRIAL_SCHEDULE:
            result = await run_trial(
                client, questions, top_k, trial
            )
            results[str(top_k)].append(result)

    # Verify all trials are complete.
    for top_k in ["200", "50"]:
        if len(results[top_k]) != NUM_TRIALS:
            raise ValueError(f"Incomplete trials for Top-K={top_k}")

        for trial in results[top_k]:
            if trial["questions"] != 152:
                raise ValueError("Incomplete question measurements")

    raw_data = {
        "benchmark": "LOCOMO Conversation 0",
        "questions": 152,
        "trials_per_top_k": NUM_TRIALS,
        "top_k_values": TOP_K_VALUES,
        "measurement": "Steady-state retrieval latency (ms)",
        "warm_up": {
            "questions_per_top_k": 152,
            "top_k_values": TOP_K_VALUES,
            "included_in_measurements": False,
        },
        "trial_schedule": [
            {"top_k": k, "trial": t}
            for k, t in TRIAL_SCHEDULE
        ],
        "results": results,
    }

    summary = {}

    for top_k, trials in results.items():
        summary[top_k] = {}

        for metric in [
            "mean_latency_ms",
            "variance_latency_ms_squared",
            "p50_latency_ms",
            "p95_latency_ms",
        ]:
            values = [t[metric] for t in trials]

            summary[top_k][metric] = {
                "mean_across_trials": mean(values),
                "variance_across_trials": variance(values),
                "individual_trials": values,
            }

        # Pooled percentiles across all 760 individual measurements.
        all_latencies = [
            latency
            for trial in trials
            for latency in trial["latencies_ms"]
        ]

        summary[top_k]["pooled_p50_ms"] = percentile(
            all_latencies, 0.50
        )
        summary[top_k]["pooled_p95_ms"] = percentile(
            all_latencies, 0.95
        )

        summary[top_k]["total_questions"] = len(all_latencies)

    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)

    RAW_FILE.write_text(json.dumps(raw_data, indent=2))
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2))

    print("\n===== FINAL STEADY-STATE SUMMARY =====")

    for top_k, metrics in summary.items():
        print(f"\nTop-K={top_k}")

        print(
            "Mean:",
            round(metrics["mean_latency_ms"]["mean_across_trials"], 2)
        )
        print(
            "Variance:",
            round(metrics["mean_latency_ms"]["variance_across_trials"], 2)
        )
        print("Pooled P50:", round(metrics["pooled_p50_ms"], 2))
        print("Pooled P95:", round(metrics["pooled_p95_ms"], 2))

    print("\nSaved:", RAW_FILE)
    print("Saved:", SUMMARY_FILE)


if __name__ == "__main__":
    asyncio.run(main())
