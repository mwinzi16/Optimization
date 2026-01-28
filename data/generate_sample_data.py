"""
Generate sample return scenarios for portfolio optimization.
Creates 10,000 scenarios for 300 assets with realistic distributions.

Asset Universe:
- Peak risks: US Hurricane (80 assets), US Earthquake (50 assets)
- Diversifying perils: Japan Typhoon, EU Windstorm, AU Cyclone, etc.
- Diversifying regions: Multiple countries and perils with lower returns
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List

np.random.seed(42)

# Configuration
N_SCENARIOS = 10_000

# Define peril/region combinations with risk profiles
# Format: (prefix, count, coupon_range, exp_loss_range, attachment_range, exhaustion_range, correlation_group)
ASSET_CONFIGS = [
    # Peak Risks - US Hurricane (highest exposure, highest returns)
    ("US_Hurricane_FL", 25, (0.08, 0.12), (0.025, 0.045), (0.02, 0.04), (0.10, 0.20), "US_HU"),
    ("US_Hurricane_TX", 20, (0.07, 0.10), (0.020, 0.035), (0.02, 0.035), (0.08, 0.15), "US_HU"),
    ("US_Hurricane_LA", 15, (0.07, 0.11), (0.022, 0.040), (0.018, 0.035), (0.09, 0.18), "US_HU"),
    ("US_Hurricane_SE", 10, (0.06, 0.09), (0.018, 0.030), (0.015, 0.03), (0.07, 0.14), "US_HU"),
    ("US_Hurricane_NE", 10, (0.05, 0.08), (0.015, 0.025), (0.012, 0.025), (0.06, 0.12), "US_HU"),
    
    # Peak Risks - US Earthquake (second highest exposure)
    ("US_EQ_CA_North", 15, (0.06, 0.09), (0.018, 0.032), (0.015, 0.03), (0.08, 0.15), "US_EQ"),
    ("US_EQ_CA_South", 15, (0.07, 0.10), (0.020, 0.038), (0.018, 0.035), (0.09, 0.18), "US_EQ"),
    ("US_EQ_PNW", 10, (0.05, 0.08), (0.015, 0.028), (0.012, 0.025), (0.07, 0.14), "US_EQ"),
    ("US_EQ_NewMadrid", 10, (0.04, 0.07), (0.012, 0.022), (0.010, 0.020), (0.05, 0.10), "US_EQ"),
    
    # Diversifying - Japan
    ("JP_Typhoon", 20, (0.05, 0.07), (0.015, 0.025), (0.012, 0.022), (0.06, 0.11), "JP_TY"),
    ("JP_Earthquake", 15, (0.04, 0.06), (0.012, 0.020), (0.010, 0.018), (0.05, 0.10), "JP_EQ"),
    
    # Diversifying - Europe
    ("EU_Windstorm_UK", 15, (0.04, 0.06), (0.010, 0.018), (0.008, 0.015), (0.04, 0.08), "EU_WS"),
    ("EU_Windstorm_DE", 12, (0.035, 0.055), (0.009, 0.016), (0.007, 0.014), (0.035, 0.07), "EU_WS"),
    ("EU_Windstorm_FR", 10, (0.035, 0.05), (0.008, 0.015), (0.006, 0.012), (0.03, 0.06), "EU_WS"),
    ("EU_Flood", 10, (0.03, 0.045), (0.007, 0.013), (0.005, 0.010), (0.025, 0.05), "EU_FL"),
    
    # Diversifying - Australia/Pacific
    ("AU_Cyclone", 12, (0.045, 0.065), (0.012, 0.022), (0.010, 0.018), (0.05, 0.10), "AU_CY"),
    ("AU_Earthquake", 8, (0.035, 0.05), (0.008, 0.015), (0.006, 0.012), (0.03, 0.06), "AU_EQ"),
    ("NZ_Earthquake", 8, (0.04, 0.055), (0.010, 0.018), (0.008, 0.015), (0.04, 0.08), "NZ_EQ"),
    
    # Diversifying - Other Regions
    ("MX_Hurricane", 10, (0.05, 0.075), (0.015, 0.028), (0.012, 0.024), (0.06, 0.12), "MX_HU"),
    ("MX_Earthquake", 8, (0.045, 0.065), (0.012, 0.022), (0.010, 0.018), (0.05, 0.10), "MX_EQ"),
    ("CA_Earthquake", 8, (0.04, 0.06), (0.010, 0.018), (0.008, 0.015), (0.04, 0.08), "CA_EQ"),
    ("TW_Typhoon", 8, (0.045, 0.065), (0.012, 0.022), (0.010, 0.018), (0.05, 0.10), "TW_TY"),
    ("CL_Earthquake", 6, (0.05, 0.07), (0.015, 0.025), (0.012, 0.020), (0.06, 0.11), "CL_EQ"),
    ("TR_Earthquake", 6, (0.055, 0.08), (0.018, 0.030), (0.015, 0.025), (0.07, 0.14), "TR_EQ"),
    
    # Aggregate/Specialty
    ("Multi_Peril_NA", 10, (0.04, 0.06), (0.010, 0.018), (0.008, 0.015), (0.04, 0.08), "MULTI"),
    ("Multi_Peril_Global", 8, (0.035, 0.055), (0.008, 0.015), (0.006, 0.012), (0.03, 0.06), "MULTI"),
]

# Correlation within groups
CORRELATION_WITHIN_GROUP = 0.6


def generate_asset_params() -> Dict[str, Dict]:
    """Generate parameters for all assets based on ASSET_CONFIGS."""
    assets = {}
    
    for prefix, count, coupon_range, exp_loss_range, attach_range, exhaust_range, corr_group in ASSET_CONFIGS:
        for i in range(count):
            asset_name = f"{prefix}_{i+1:03d}"
            
            coupon = np.random.uniform(*coupon_range)
            exp_loss = np.random.uniform(*exp_loss_range)
            attachment = np.random.uniform(*attach_range)
            exhaustion = np.random.uniform(*exhaust_range)
            
            if exhaustion <= attachment:
                exhaustion = attachment + np.random.uniform(0.03, 0.08)
            
            assets[asset_name] = {
                "coupon": coupon,
                "exp_loss": exp_loss,
                "attachment": attachment,
                "exhaustion": exhaustion,
                "corr_group": corr_group,
            }
    
    return assets


def generate_correlated_factors(n_scenarios: int, corr_groups: List[str]) -> Dict[str, np.ndarray]:
    """Generate correlated random factors for each correlation group."""
    unique_groups = list(set(corr_groups))
    n_groups = len(unique_groups)
    
    base_factors = np.random.normal(0, 1, (n_scenarios, n_groups))
    global_factor = np.random.normal(0, 0.3, n_scenarios)
    
    factors = {}
    for i, group in enumerate(unique_groups):
        factors[group] = base_factors[:, i] + global_factor
    
    return factors


def generate_cat_losses(
    n_scenarios: int,
    exp_loss: float,
    attachment: float,
    exhaustion: float,
    corr_factor: np.ndarray,
    alpha: float = 1.5
) -> np.ndarray:
    """Generate losses using a compound Poisson-Pareto model."""
    base_prob = min(exp_loss / ((attachment + exhaustion) / 2), 0.12)
    
    prob_adjustment = 1 + 0.3 * corr_factor
    prob_adjustment = np.clip(prob_adjustment, 0.5, 2.0)
    adjusted_prob = np.clip(base_prob * prob_adjustment, 0, 0.25)
    
    event_occurs = np.random.binomial(1, adjusted_prob)
    
    losses = np.zeros(n_scenarios)
    event_indices = np.where(event_occurs == 1)[0]
    
    if len(event_indices) > 0:
        raw_severity = (np.random.pareto(alpha, len(event_indices)) + 1) * attachment
        
        for i, idx in enumerate(event_indices):
            industry_loss = raw_severity[i]
            if industry_loss <= attachment:
                losses[idx] = 0.0
            elif industry_loss >= exhaustion:
                losses[idx] = 1.0
            else:
                losses[idx] = (industry_loss - attachment) / (exhaustion - attachment)
    
    return losses


def generate_returns(assets: Dict[str, Dict], n_scenarios: int) -> pd.DataFrame:
    """Generate total return scenarios for all assets."""
    corr_groups = [params["corr_group"] for params in assets.values()]
    factors = generate_correlated_factors(n_scenarios, corr_groups)
    
    returns_data = {}
    
    for asset_name, params in assets.items():
        corr_group = params["corr_group"]
        corr_factor = factors[corr_group]
        
        asset_factor = corr_factor * np.sqrt(CORRELATION_WITHIN_GROUP) + \
                       np.random.normal(0, 1, n_scenarios) * np.sqrt(1 - CORRELATION_WITHIN_GROUP)
        
        losses = generate_cat_losses(
            n_scenarios,
            params["exp_loss"],
            params["attachment"],
            params["exhaustion"],
            asset_factor
        )
        
        total_returns = (1 + params["coupon"]) * (1 - losses) - 1
        returns_data[asset_name] = total_returns
    
    return pd.DataFrame(returns_data)


def main():
    print("=" * 60)
    print("PORTFOLIO OPTIMIZER - SAMPLE DATA GENERATION")
    print("=" * 60)
    print()
    
    assets = generate_asset_params()
    print(f"Generated {len(assets)} assets")
    
    # Count by category
    us_hu = sum(1 for k in assets if "US_Hurricane" in k)
    us_eq = sum(1 for k in assets if "US_EQ" in k)
    jp = sum(1 for k in assets if k.startswith("JP_"))
    eu = sum(1 for k in assets if k.startswith("EU_"))
    au_nz = sum(1 for k in assets if k.startswith("AU_") or k.startswith("NZ_"))
    other = len(assets) - us_hu - us_eq - jp - eu - au_nz
    
    print(f"\nAsset breakdown:")
    print(f"  US Hurricane (peak):    {us_hu:3d} assets")
    print(f"  US Earthquake (peak):   {us_eq:3d} assets")
    print(f"  Japan:                  {jp:3d} assets")
    print(f"  Europe:                 {eu:3d} assets")
    print(f"  Australia/NZ:           {au_nz:3d} assets")
    print(f"  Other diversifying:     {other:3d} assets")
    
    print(f"\nGenerating {N_SCENARIOS:,} scenarios...")
    returns_df = generate_returns(assets, N_SCENARIOS)
    
    returns_df.index = range(1, N_SCENARIOS + 1)
    returns_df.index.name = "Scenario"
    
    output_path = Path(__file__).parent / "scenario_returns.csv"
    returns_df.to_csv(output_path)
    print(f"\nSaved scenario returns to: {output_path}")
    
    asset_info = pd.DataFrame({
        name: {k: v for k, v in params.items() if k != "corr_group"}
        for name, params in assets.items()
    }).T
    asset_info.index.name = "Asset"
    asset_info_path = Path(__file__).parent / "asset_info.csv"
    asset_info.to_csv(asset_info_path)
    print(f"Saved asset info to: {asset_info_path}")
    
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    
    all_returns = returns_df.values.flatten()
    print(f"\nOverall:")
    print(f"  Mean return:     {np.mean(all_returns)*100:6.2f}%")
    print(f"  Std deviation:   {np.std(all_returns)*100:6.2f}%")
    print(f"  Min return:      {np.min(all_returns)*100:6.2f}%")
    print(f"  Max return:      {np.max(all_returns)*100:6.2f}%")


if __name__ == "__main__":
    main()
