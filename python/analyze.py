import csv
import math
import re
import statistics
from pathlib import Path

import matplotlib.pyplot as plt


def parse_p(path: Path):
    m = re.search(r"_p(\d+)\.csv$", path.name)
    if m:
        return int(m.group(1))
    return None


def read_csv(path: Path):
    rows = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "stream_id": int(row["stream_id"]),
                "step": int(row["step"]),
                "fraction": float(row["fraction"]),
                "processed": int(row["processed"]),
                "true_f0": int(row["true_f0"]),
                "estimate": float(row["estimate"]),
            })
    return rows


def group_by_step(rows):
    g = {}
    for x in rows:
        step = x["step"]
        if step not in g:
            g[step] = []
        g[step].append(x)
    return g


def rel_error(est: float, true_val: int):
    if true_val == 0:
        return 0.0
    return (est - float(true_val)) / float(true_val)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def plot_stream0(rows, p: int, out_dir: Path):
    stream0 = [x for x in rows if x["stream_id"] == 0]
    stream0.sort(key=lambda x: x["fraction"])

    xs = [x["fraction"] for x in stream0]
    ys_true = [x["true_f0"] for x in stream0]
    ys_est = [x["estimate"] for x in stream0]

    plt.figure()
    plt.plot(xs, ys_true, label="Истинное F0")
    plt.plot(xs, ys_est, label="Оценка HLL")
    plt.xlabel("Доля потока t")
    plt.ylabel("Число уникальных элементов")
    plt.title(f"График 1: поток #0 (p={p})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"1_поток0_p{p}.png", dpi=160)
    plt.close()


def plot_mean_sigma(rows, p: int, out_dir: Path):
    by_step = group_by_step(rows)
    steps = sorted(by_step.keys())

    xs = []
    mu = []
    sd = []

    for step in steps:
        items = by_step[step]
        frac = items[0]["fraction"]
        vals = [x["estimate"] for x in items]

        xs.append(frac)
        mu.append(statistics.mean(vals))
        sd.append(statistics.pstdev(vals))

    upper = [mu[i] + sd[i] for i in range(len(xs))]
    lower = [mu[i] - sd[i] for i in range(len(xs))]

    plt.figure()
    plt.plot(xs, mu, label="E(Nt)")
    plt.fill_between(xs, lower, upper, alpha=0.3, label="E(Nt) ± σ")
    plt.xlabel("Доля потока t")
    plt.ylabel("Оценка Nt")
    plt.title(f"График 2: среднее и разброс по потокам (p={p})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"2_среднее_сигма_p{p}.png", dpi=160)
    plt.close()


def plot_errors_and_theory(rows, p: int, out_dir: Path):
    by_step = group_by_step(rows)
    steps = sorted(by_step.keys())

    xs = []
    mean_err = []
    std_err = []

    for step in steps:
        items = by_step[step]
        frac = items[0]["fraction"]
        errs = [rel_error(x["estimate"], x["true_f0"]) for x in items]

        xs.append(frac)
        mean_err.append(statistics.mean(errs))
        std_err.append(statistics.pstdev(errs))

    m = 2 ** p
    theory = 1.04 / math.sqrt(m)

    plt.figure()
    plt.plot(xs, mean_err, label="Средняя относительная ошибка")
    plt.plot(xs, std_err, label="σ относительной ошибки")
    plt.axhline(theory, label="Теория: 1.04 / sqrt(m)")
    plt.xlabel("Доля потока t")
    plt.ylabel("Относительная ошибка")
    plt.title(f"График 3: ошибки и теория (p={p}, m={m})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"3_ошибки_теория_p{p}.png", dpi=160)
    plt.close()

    return {
        "p": p,
        "m": m,
        "theory_rse": theory,
        "mean_err_last": mean_err[-1] if len(mean_err) > 0 else 0.0,
        "std_err_last": std_err[-1] if len(std_err) > 0 else 0.0,
    }


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data"

    if not data_dir.exists():
        print("Ошибка: папка data не найдена:", str(data_dir))
        return

    files = sorted(list(data_dir.glob("results_p*.csv")))

    if len(files) == 0:
        print("Файлы не найдены:", str(data_dir / "results_p*.csv"))
        print("/data:")
        for x in sorted(data_dir.iterdir()):
            print(" -", x.name)
        return

    plots_dir = data_dir / "plots"
    ensure_dir(plots_dir)

    summary = []
    for path in files:
        p = parse_p(path)
        if p is None:
            continue

        rows = read_csv(path)

        plot_stream0(rows, p, plots_dir)
        plot_mean_sigma(rows, p, plots_dir)
        info = plot_errors_and_theory(rows, p, plots_dir)
        summary.append(info)

        print("Готово:", path.name)

    summary_path = data_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["p", "m", "theory_rse", "mean_err_last", "std_err_last"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in sorted(summary, key=lambda x: x["p"]):
            w.writerow(row)

    print("Все графики сохранены в:", str(plots_dir))
    print("Сводка сохранена в:", str(summary_path))


if __name__ == "__main__":
    main()
