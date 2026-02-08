import csv
import math
import re
import statistics
from pathlib import Path

import matplotlib.pyplot as plt


def parse_p(name: str):
    m = re.search(r"_p(\d+)\.csv$", name)
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


def pick_file(data_dir: Path, pattern: str):
    files = sorted(list(data_dir.glob(pattern)))
    if len(files) == 0:
        return None
    return files[0]


def find_baseline_file(data_dir: Path, p: int):
    f1 = data_dir / f"results_base_p{p}.csv"
    if f1.exists():
        return f1
    f2 = data_dir / f"results_p{p}.csv"
    if f2.exists():
        return f2
    return None


def find_improved_file(data_dir: Path, p: int):
    f = pick_file(data_dir, f"results_med*_p{p}.csv")
    if f is not None:
        return f
    f = pick_file(data_dir, f"results_improved*_p{p}.csv")
    if f is not None:
        return f
    f = pick_file(data_dir, f"results_k*_p{p}.csv")
    if f is not None:
        return f
    return None


def extract_k_from_name(name: str):
    m = re.search(r"med(\d+)", name)
    if m:
        return int(m.group(1))
    m = re.search(r"k(\d+)", name)
    if m:
        return int(m.group(1))
    return None


def stream0_series(rows):
    stream0 = [x for x in rows if x["stream_id"] == 0]
    stream0.sort(key=lambda x: x["fraction"])
    xs = [x["fraction"] for x in stream0]
    true0 = [x["true_f0"] for x in stream0]
    est0 = [x["estimate"] for x in stream0]
    return xs, true0, est0


def mean_sigma_estimate(rows):
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

    return xs, mu, sd


def mean_sigma_rel_error(rows):
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

    return xs, mean_err, std_err


def plot_graph1_compare(true_rows, base_rows, imp_rows, p: int, out_dir: Path):
    xs_t, true0, _ = stream0_series(true_rows)
    xs_b, _, est_b = stream0_series(base_rows)
    xs_i, _, est_i = stream0_series(imp_rows)

    plt.figure()
    plt.plot(xs_t, true0, label="Истинное F0 (поток #0)")
    plt.plot(xs_b, est_b, label="База HLL (поток #0)")
    plt.plot(xs_i, est_i, label="Улучшенный (поток #0)")
    plt.xlabel("Доля потока t")
    plt.ylabel("Число уникальных элементов")
    plt.title(f"График 1 (сравнение): поток #0, p={p}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"cmp_1_поток0_p{p}.png", dpi=160)
    plt.close()


def plot_graph2_compare(base_rows, imp_rows, p: int, out_dir: Path):
    xb, mub, sdb = mean_sigma_estimate(base_rows)
    xi, mui, sdi = mean_sigma_estimate(imp_rows)

    upper_b = [mub[i] + sdb[i] for i in range(len(xb))]
    lower_b = [mub[i] - sdb[i] for i in range(len(xb))]

    upper_i = [mui[i] + sdi[i] for i in range(len(xi))]
    lower_i = [mui[i] - sdi[i] for i in range(len(xi))]

    plt.figure()
    plt.plot(xb, mub, label="База: E(Nt)")
    plt.fill_between(xb, lower_b, upper_b, alpha=0.2, label="База: E(Nt) ± σ")
    plt.plot(xi, mui, label="Улучшенный: E(Nt)")
    plt.fill_between(xi, lower_i, upper_i, alpha=0.2, label="Улучшенный: E(Nt) ± σ")
    plt.xlabel("Доля потока t")
    plt.ylabel("Оценка Nt")
    plt.title(f"График 2 (сравнение): среднее и разброс, p={p}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"cmp_2_среднее_сигма_p{p}.png", dpi=160)
    plt.close()


def plot_graph3_compare(base_rows, imp_rows, p: int, out_dir: Path):
    xb, mean_b, std_b = mean_sigma_rel_error(base_rows)
    xi, mean_i, std_i = mean_sigma_rel_error(imp_rows)

    m = 2 ** p
    theory = 1.04 / math.sqrt(m)

    plt.figure()
    plt.plot(xb, std_b, label="База: σ относительной ошибки")
    plt.plot(xi, std_i, label="Улучшенный: σ относительной ошибки")
    plt.axhline(theory, linestyle="--", label="Теория базы: 1.04 / sqrt(m)")
    plt.xlabel("Доля потока t")
    plt.ylabel("σ относительной ошибки")
    plt.title(f"График 3 (сравнение): σ ошибки, p={p}, m={m}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"cmp_3_сигма_ошибки_p{p}.png", dpi=160)
    plt.close()

    return {
        "p": p,
        "m": m,
        "theory_rse_base": theory,
        "base_mean_err_last": mean_b[-1] if len(mean_b) > 0 else 0.0,
        "base_std_err_last": std_b[-1] if len(std_b) > 0 else 0.0,
        "imp_mean_err_last": mean_i[-1] if len(mean_i) > 0 else 0.0,
        "imp_std_err_last": std_i[-1] if len(std_i) > 0 else 0.0,
    }


def main():
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    data_dir = repo_root / "data"

    if not data_dir.exists():
        print("Ошибка: папка data не найдена:", str(data_dir))
        return

    out_dir = data_dir / "plots_compare"
    ensure_dir(out_dir)

    ps = []
    for f in data_dir.glob("results_p*.csv"):
        p = parse_p(f.name)
        if p is not None:
            ps.append(p)
    for f in data_dir.glob("results_base_p*.csv"):
        p = parse_p(f.name)
        if p is not None:
            ps.append(p)

    ps = sorted(list(set(ps)))

    if len(ps) == 0:
        print("Не нашёл базовые файлы results_p*.csv или results_base_p*.csv в папке data.")
        print("Что реально есть в data:")
        for x in sorted(data_dir.iterdir()):
            print(" -", x.name)
        return

    summary = []

    k = None
    any_improved = False

    for p in ps:
        base_file = find_baseline_file(data_dir, p)
        imp_file = find_improved_file(data_dir, p)

        if base_file is None:
            continue
        if imp_file is None:
            continue

        any_improved = True
        if k is None:
            k = extract_k_from_name(imp_file.name)

        base_rows = read_csv(base_file)
        imp_rows = read_csv(imp_file)

        plot_graph1_compare(base_rows, base_rows, imp_rows, p, out_dir)
        plot_graph2_compare(base_rows, imp_rows, p, out_dir)
        info = plot_graph3_compare(base_rows, imp_rows, p, out_dir)
        summary.append(info)

        print("Готово:", f"p={p}", "|", base_file.name, "vs", imp_file.name)

    if not any_improved:
        print("Не нашёл улучшенные файлы results_med*_p*.csv (или results_improved*_p*.csv) в папке data.")
        return

    summary_path = data_dir / "summary_compare.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "p",
            "m",
            "theory_rse_base",
            "base_mean_err_last",
            "base_std_err_last",
            "imp_mean_err_last",
            "imp_std_err_last",
            "std_improvement_factor",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for row in sorted(summary, key=lambda x: x["p"]):
            base_std = row["base_std_err_last"]
            imp_std = row["imp_std_err_last"]
            factor = 0.0
            if imp_std != 0.0:
                factor = base_std / imp_std

            out_row = dict(row)
            out_row["std_improvement_factor"] = factor
            w.writerow(out_row)

    if k is None:
        k = 5

    print("Все сравнительные графики сохранены в:", str(out_dir))
    print("Сводка сохранена в:", str(summary_path))
    print("Улучшенный алгоритм:", f"медиана из k={k} оценок")


if __name__ == "__main__":
    main()
