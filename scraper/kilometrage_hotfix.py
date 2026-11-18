

import pandas as pd

INPUT_PATH = "/home/axtch4/Projects/5eme//prix-de-voiture-occasion-maroc/data/raw/used_car_ads.csv"
OUTPUT_PATH = "/home/axtch4/Projects/5eme//prix-de-voiture-occasion-maroc/data/raw/used_car_ads_km_fixed.csv"

MIN_KM = 0
MAX_KM = 500_000  # sane upper bound for a used car's odometer


def recover_kilometrage(row):
    km = row["kilometrage"]
    year = row["annee"]

    if pd.isna(km):
        return pd.NA, "missing_originally"

    km_str = str(int(km))
    year_str = str(int(year)) if not pd.isna(year) else None

    # Case 1: looks like year-concatenation. Strip and validate.
    if year_str and km_str.startswith(year_str):
        remainder = km_str[len(year_str):]
        if remainder == "":
            return pd.NA, "concat_empty_remainder"
        remainder_val = int(remainder)
        if MIN_KM <= remainder_val <= MAX_KM:
            return remainder_val, "recovered_from_concat"
        else:
            return pd.NA, "concat_remainder_still_implausible"

    # Case 2: doesn't start with the year — check if it's just a normal,
    # already-valid value.
    km_val = int(km)
    if MIN_KM <= km_val <= MAX_KM:
        return km_val, "already_valid"

    # Case 3: doesn't start with year AND out of sane range — unknown
    # corruption, not recoverable by this method.
    return pd.NA, "unrecoverable"


def main():
    df = pd.read_csv(INPUT_PATH)
    print("Total rows (unchanged, nothing dropped):", len(df))

    results = df.apply(recover_kilometrage, axis=1, result_type="expand")
    df["kilometrage"] = results[0]
    df["km_recovery_status"] = results[1]

    print()
    print("km_recovery_status breakdown:")
    print(df["km_recovery_status"].value_counts())
    print()

    recovered_ok = df["km_recovery_status"].isin(["recovered_from_concat", "already_valid"])
    print(f"Rows with a trustworthy kilometrage: {recovered_ok.sum()} / {len(df)}")

    print()
    print("Sample of recovered_from_concat rows — VERIFY THESE AGAINST THE REAL PAGES:")
    pool = df[df["km_recovery_status"] == "recovered_from_concat"]
    sample = pool.sample(min(5, len(pool)), random_state=42)
    for _, row in sample.iterrows():
        print(f"  {row['marque']} {row['annee']} | recovered km = {row['kilometrage']} | {row['url_annonce']}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWritten to: {OUTPUT_PATH}  (same {len(df)} rows as input, only kilometrage + status column changed)")


if __name__ == "__main__":
    main()