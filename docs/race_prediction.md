 1# Race Time Prediction Model — Task Plan

## Phase 1: Data Exploration & Cleaning

### 1.1 Load & Initial Profiling
- [ ] Load the dataset (CSV/Parquet) into a pandas DataFrame
- [ ] Run `df.info()`, `df.describe()`, `df.dtypes` to understand shape, types, and basic stats
- [ ] Check completeness: `df.isnull().sum()` per column — decide strategy per field:
  - `distance`/`duration` missing → drop row (these are essential)
  - `major` missing → likely means no marathon history, fill with empty string
  - `country`/`gender`/`age_group` missing → evaluate proportion; drop or impute with "Unknown"
- [ ] Generate an automated profile report for a quick visual overview
- **Tools**: `pandas`, `ydata-profiling` (formerly pandas-profiling)

### 1.2 Datetime Parsing & Temporal Features
- [ ] Parse `datetime` column to `pd.Timestamp` (`pd.to_datetime`)
- [ ] Handle timezone ambiguity — decide on UTC or local, be consistent
- [ ] Extract features: `year`, `month`, `day_of_week`, `week_of_year`
- [ ] Derive `season` from month (e.g., Dec-Feb=Winter, Mar-May=Spring, etc.)
- [ ] Sort all data by `(athlete, datetime)` — this ordering is critical for later rolling computations
- **Tools**: `pandas` (datetime accessors)

### 1.3 Parse the `major` Field
- [ ] Split the comma-separated `major` string into a list per row
- [ ] Extract individual marathon names and years (e.g., "Boston 2023" → name="Boston", year=2023)
- [ ] Derive: `marathon_count` (total marathons per athlete), `unique_marathons`, `years_racing`
- [ ] Handle edge cases: empty strings, inconsistent formatting, unknown marathon names
- **Tools**: `pandas` (string methods), `re` (regex for structured extraction)

### 1.4 Numeric Distributions & Outlier Detection
- [ ] Plot histograms for `distance` and `duration` — look for bimodal distributions (training vs race entries)
- [ ] Plot pace (`duration/distance`) distribution — flag values outside reasonable bounds (e.g., < 2.5 min/km or > 15 min/km)
- [ ] Box plots grouped by `age_group` and `gender` to see if distributions differ as expected
- [ ] Scatter plot `distance` vs `duration` — outliers far from the main cluster likely indicate data errors
- [ ] Decide on outlier strategy:
  - Hard caps (physiologically impossible values → remove)
  - Statistical (e.g., > 3 std from group mean → flag for review, don't auto-remove)
- **Tools**: `matplotlib`, `seaborn`, `scipy.stats` (for z-scores if needed)

### 1.5 Categorical Field Validation
- [ ] Check `gender` values — confirm only 'M' and 'F', flag unexpected entries
- [ ] Check `age_group` values — confirm only '18 - 34', '35 - 54', '55 +', flag others
- [ ] Check `country` — inspect cardinality (`df['country'].nunique()`), look for duplicates from inconsistent naming (e.g., "USA" vs "United States")
- [ ] Standardize country names if needed
- **Tools**: `pandas` (value_counts, unique)

### 1.6 Per-Athlete Sanity Checks
- [ ] Count activities per athlete — distribution of activity counts (are some athletes vastly over/under-represented?)
- [ ] Check for duplicate rows (same athlete, same datetime, same distance)
- [ ] Verify chronological consistency per athlete (no future-dated activities, no impossible gaps)
- [ ] Identify athletes with too few data points to be useful for modeling (set a minimum threshold, e.g., >= 10 activities)
- **Tools**: `pandas` (groupby, duplicated)

### 1.7 Output
- [ ] Save the cleaned DataFrame to a new file (e.g., `data/cleaned_activities.parquet`)
- [ ] Document any rows dropped and why (log counts: X rows removed for missing distance, Y for outlier pace, etc.)
- [ ] Produce a summary EDA notebook or report with the key charts and findings

### Phase 1 Recommended Setup
```
pip install pandas ydata-profiling matplotlib seaborn scipy
```
A **Jupyter notebook** is the ideal environment for this phase — it allows interactive exploration, inline plots, and easy documentation of findings as you go.

## Phase 2: Feature Engineering
- [ ] Derive pace: `duration / distance` (min/km)
- [ ] Compute rolling averages of distance and duration per athlete (7-day, 30-day, 90-day windows)
- [ ] Compute training consistency: frequency of runs per week/month, variance in pace
- [ ] Compute progression: pace trend over time per athlete (improving or declining)
- [ ] Compute experience: count of past marathons from `major`, total cumulative distance
- [ ] Encode demographics: `gender`, `age_group`, `country` as categorical features
- [ ] Flag race vs training entries (entries matching known race distances)

## Phase 3: Target Definition
- [ ] Define "race time" clearly — duration for a specific race distance (marathon, half, etc.)
- [ ] Filter dataset for race entries to use as prediction targets
- [ ] Use remaining entries as training history features

## Phase 4: Model Design
- [ ] Start with tabular ML approach: aggregate per-athlete features into one row per athlete-race
- [ ] Train a gradient boosting model (XGBoost or LightGBM) as baseline
- [ ] Evaluate whether a time-series approach (LSTM/transformer) is warranted based on data volume

## Phase 5: Training & Validation
- [ ] Split by athlete (not by row) to avoid data leakage
- [ ] Use time-aware splitting: train on earlier races, validate on later ones
- [ ] Evaluate with MAE, RMSE, and percentage error relative to finish time
- [ ] Use SHAP for feature importance and explainability

## Phase 6: Integrating Your Own Data
- [ ] Map Strava activity list to the same schema (distance, duration, datetime, etc.)
- [ ] Compute the same engineered features for your activities
- [ ] Feed your feature vector into the trained model to get a predicted race time

## Key Risks
- **Leakage**: race entries mixed with training entries in feature computation
- **Dataset bias**: model may extrapolate if your training patterns differ from the dataset's athletes
- **Distance specificity**: consider separate models per target distance or include target distance as a feature
- **Diminishing returns on complexity**: simple features (recent avg pace, weekly mileage) tend to dominate accuracy

## Tool Stack
- pandas (data wrangling)
- scikit-learn (baselines and pipelines)
- XGBoost / LightGBM (main model)
- SHAP (explainability)
- matplotlib / seaborn (EDA and visualization)