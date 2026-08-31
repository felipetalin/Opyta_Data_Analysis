from __future__ import annotations

import pandas as pd


EXPECTED_PHYLA = {
    "Charophyta": 96,
    "Bacillariophyta": 57,
    "Cyanobacteriota": 17,
    "Chlorophyta": 12,
    "Dinophyta": 5,
    "Euglenophyta": 5,
    "Ochrophyta": 4,
    "Cryptophyta": 1,
    "Rhodophyta": 1,
}

DESMIDIACEAE_TAXA = {
    "Cosmarium blyttii",
    "Cosmarium conatum",
    "Cosmarium lagoense",
    "Ichthyocercus longispinus var. tinhareensis",
    "Micrasterias crux-melitensis",
    "Staurastrum tentaculiferum",
    "Staurodesmus omearae",
    "Staurodesmus wandae",
}

PHYLUM_NORMALIZATION = {
    "bacillariophyta": "Bacillariophyta",
    "charophyta": "Charophyta",
    "chlorophyta": "Chlorophyta",
    "cryptophyta": "Cryptophyta",
    "cyanobacteria": "Cyanobacteriota",
    "cyanobacteriota": "Cyanobacteriota",
    "dinophyta": "Dinophyta",
    "euglenophyta": "Euglenophyta",
    "miozoa": "Dinophyta",
    "ochrophyta": "Ochrophyta",
    "rhodophyta": "Rhodophyta",
}


def apply_taxonomy_r01(source: pd.DataFrame) -> pd.DataFrame:
    df = source.copy()
    for col in ["nome_cientifico", "filo", "classe", "ordem", "familia", "genero"]:
        df[col] = df[col].astype("string").str.strip()

    df["filo"] = df["filo"].str.lower().map(PHYLUM_NORMALIZATION).fillna(df["filo"])
    diatoms = df["classe"].str.lower().isin({"bacillariophyceae", "coscinodiscophyceae"})
    df.loc[diatoms, "filo"] = "Bacillariophyta"
    conjugates = df["classe"].str.lower().isin({"conjugatophyceae", "zygnematophyceae"})
    df.loc[conjugates, "classe"] = "Zygnematophyceae"
    df.loc[df["nome_cientifico"].isin(DESMIDIACEAE_TAXA), "familia"] = "Desmidiaceae"
    df.loc[df["nome_cientifico"] == "Iconella constricta", "genero"] = "Iconella"
    df.loc[df["nome_cientifico"] == "Synura sp.", "ordem"] = "Synurales"
    df.loc[df["nome_cientifico"] == "Scytonemataceae", "nome_cientifico"] = "Scytonemataceae n.i."
    return df


def validate_taxonomy_r01(df: pd.DataFrame) -> dict:
    taxa = set(df["nome_cientifico"].dropna().astype(str))
    quant_mask = df["tipo_amostragem"].astype(str).str.contains("Quantitativa", case=False, na=False)
    quant_taxa = set(df.loc[quant_mask, "nome_cientifico"].dropna().astype(str))
    campaigns = {
        campaign: set(group["nome_cientifico"].dropna().astype(str))
        for campaign, group in df.groupby("nome_campanha")
    }
    shared = len(set.intersection(*campaigns.values()))
    exclusives = {
        campaign: len(values - set().union(*(other for key, other in campaigns.items() if key != campaign)))
        for campaign, values in campaigns.items()
    }
    phyla = df.groupby("filo")["nome_cientifico"].nunique().astype(int).to_dict()
    checks = {
        "rows_511": len(df) == 511,
        "taxa_198": len(taxa) == 198,
        "phyla_expected": phyla == EXPECTED_PHYLA,
        "campaign_richness": sorted(len(values) for values in campaigns.values()) == [123, 162],
        "shared_taxa_87": shared == 87,
        "exclusive_taxa_36_75": sorted(exclusives.values()) == [36, 75],
        "quantitative_taxa_58": len(quant_taxa) == 58,
        "qualitative_only_taxa_140": len(taxa - quant_taxa) == 140,
        "zygnematophyceae_96": df.loc[df["classe"] == "Zygnematophyceae", "nome_cientifico"].nunique() == 96,
        "desmidiaceae_8": DESMIDIACEAE_TAXA.issubset(set(df.loc[df["familia"] == "Desmidiaceae", "nome_cientifico"])),
        "iconella_genus": set(df.loc[df["nome_cientifico"] == "Iconella constricta", "genero"].dropna()) == {"Iconella"},
        "synura_order": set(df.loc[df["nome_cientifico"] == "Synura sp.", "ordem"].dropna()) == {"Synurales"},
        "scytonemataceae_ni": "Scytonemataceae n.i." in taxa and "Scytonemataceae" not in taxa,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError("Taxonomic validation R01 failed: " + ", ".join(failed))
    return {
        "status": "PASS",
        "checks": checks,
        "phyla": phyla,
        "campaign_richness": {key: len(value) for key, value in campaigns.items()},
        "shared_taxa": shared,
        "exclusive_taxa": exclusives,
    }
