import pathlib


def variant_dir(case_dir: pathlib.Path, variant: str) -> pathlib.Path:
    return case_dir / "applications" / variant


def application_path(case_dir: pathlib.Path, variant: str) -> pathlib.Path:
    return variant_dir(case_dir, variant) / "application.txt"


def true_verdicts_path(case_dir: pathlib.Path, variant: str) -> pathlib.Path:
    return variant_dir(case_dir, variant) / "true_verdicts.json"


def run_dir(
    case_dir: pathlib.Path, variant: str, run_label: str
) -> pathlib.Path:
    return variant_dir(case_dir, variant) / "runs" / run_label


def discover_variants(case_dir: pathlib.Path) -> list[str]:
    applications_dir = case_dir / "applications"
    if not applications_dir.is_dir():
        return []
    variants = []
    for entry in sorted(applications_dir.iterdir()):
        if entry.is_dir() and (entry / "application.txt").exists():
            variants.append(entry.name)
    return variants
