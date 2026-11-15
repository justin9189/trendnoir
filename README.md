# TrendNoir: Real trend, or illusion?

**Team:** TrendNoir
**Event:** 2026 NASA Space Apps Challenge, Seattle
**Challenge:** Be An Earth System Trend Detective! (Advanced)

TrendNoir is a detective kit for NASA Earth data, built for science journalists and fact-checkers,
students, and anyone curious about their region. Pick a variable and a place, and it walks the record
through four steps (pull the record, remove the seasons, measure the change, test the evidence), then
gives a plain-language verdict: a real trend, an unsteady one, not enough evidence yet, or no trend.
It then tries to break its own verdict, so users learn how a trend line can fool them.

The interface is styled as a case dossier: paper documents on a desk, cases in manila folders.

The whole app is one self-contained web page: `docs/index.html`. Open it in any modern browser,
or visit the GitHub Pages site for this repository.

## How TrendNoir answers the challenge

| The challenge asks | Where TrendNoir does it |
|---|---|
| Identify variables of interest | Investigate: two questions (kind of place, interest) suggest variables from MODIS, OMI, AIRS, GPM, MERRA-2 and GLDAS with plain definitions; any Giovanni variable can be searched; Case 004 ranks six variables over one region |
| Acquire data for a region | Draw a region on the globe; TrendNoir builds the Giovanni request and reads the downloaded CSV in the browser |
| Visualize the time series | Monthly record, seasons removed in an animated step, trend line with range, maps of every window of years |
| Rate of change and significance | Sen's slope with 95% range; Mann-Kendall corrected for autocorrelation; plain t-test for comparison; Hamed-Rao and seasonal Kendall; multiverse robustness |
| Opposite trends in different regions | Case 001 and two-region uploads |
| Definitions and demonstration examples | Definitions for every variable, three case files, a 30-second self-playing demo, live explainers |
| Not-yet-significant trends | "How long?" estimate; "no trend detected" versus "can't tell yet" |

## What it does

- **Check a claim.** The claim is built as a sentence from drop-down menus: *[measurement] in [place]
  [rose / fell / did not change] from [year] to [year]*, with about 60 places and 15 measurements. A claim
  can also be pasted in plain English; simple rules (no AI) read it and fill in the sentence, marking
  anything they could not read. If the record is on file, TrendNoir tests those years, checks whether
  they are extreme among all windows of the same length (cherry-picking), and asks how many reasonable
  analyses of the full record back the claim. If not, it sets up the NASA download on the globe and
  checks the claim once the CSV is dropped in. Verdicts: holds up, true for those years only, not
  supported, contradicted, misleading, unproven.
- **Evidence board.** On the home page, the four case files are pinned to a spinning desk globe and
  tied to their regions with red string; a magnifier follows the pointer over the globe.
- **Why it matters.** Three findings computed from the data on page load, for example that a careless
  test calls 64% of trend-free versions of Alaska's soil-wetness record significant.
- **Your call first.** Users make a call (rising, falling, no change) before seeing the evidence, then
  compare it with the verdict.
- **Variable finder.** Two questions (what kind of place, what interests you) suggest NASA variables
  from a fixed rule table, each with its source, a plain definition and why a trend might show there.
- **30-second demo.** A self-playing tour with captions: seasons hiding a trend, a claim check, opposite
  trends, and the globe.
- **Share links.** On a normal web host (for example GitHub Pages), claim checks and case files can be
  shared as links (`?claim=...`, `?case=c1&step=4`).
- **Investigate.** A four-step page with progress marks: what to investigate, where, getting the data,
  and dropping the file. The globe is an antique desk globe (d3 orthographic projection) with a brass
  meridian ring, lamp shading, pulsing case markers and drag inertia; places can be searched by name.
  It is draggable and zoomable. Draw a box anywhere,
  pick a measurement and years, and TrendNoir builds a NASA Giovanni link with the region, variable and
  dates filled in (split into parts for long daily records). Any other Giovanni variable can be used by
  typing a search word, a variable ID, or pasting a Giovanni link. Case regions are drawn on the globe and
  colored by trend direction; uploaded regions appear too.
- **Learn.** Four live explainers: a slider shows seasons hiding a trend, a draggable point shows why
  Sen's slope resists outliers, a vote tally shows what Mann-Kendall counts, and a simulation of 200
  trend-free records shows how memory fools a careless test. Plus a one-sentence glossary.
- **Case files.** Three worked cases built from NASA data: opposite NO₂ trends over Eastern China and
  Northern India (OMI on Aura), a warming in interior Alaska that is invisible until the seasons are
  removed (MERRA-2), and a "phantom" rainfall trend over the central United States (MERRA-2).
- **Four-step investigation** on one morphing chart, ending in a stamped verdict and a plain sentence.
- **Second opinions.** Every verdict is checked with Hamed and Rao's correction and the Hirsch-Slack
  seasonal Kendall test, plus a month-by-month view of when in the year the change happens.
- **Turning points.** A two-segment fit with a block bootstrap finds where an unsteady trend bends.
- **Try to break it.** A map of the trend for every window of eight or more years, and a button that
  finds the window most likely to fool you.
- **How hard is it to kill?** A multiverse analysis: every reasonable window times four defensible
  methods, summarized as a robustness grade and a specification curve.
- **How long until it's real?** A rough estimate of the record length needed to detect a trend.
- **Case 004: one place, six suspects.** Six variables over the same patch of interior Alaska, ranked
  by strength of evidence; any one can be opened in the four-step investigation.
- **Bring your own evidence.** Upload any Giovanni area-averaged time-series CSV (one region, or two
  regions to compare), from the Explore page. It is analyzed in the browser and never leaves the user's
  computer.

## Repository layout

```
data/raw/        Giovanni CSV downloads used for the case files (see data/README.md)
analysis/        Python analysis: monthly series, tests, windows, robustness  ->  web/data.json
web/             Page source (template.html), world map (geo.json) and build script
docs/index.html  The built, self-contained app (template + data.json + two sample files)
tests/           Check that the in-browser analysis reproduces the Python results
```

## Reproduce from scratch

```bash
pip install -r requirements.txt
python analysis/preprocess.py      # reads data/raw, writes web/data.json (about a minute)
python web/build.py                # writes docs/index.html
# optional: verify the browser analysis against Python
playwright install chromium
python tests/validate_browser_vs_python.py
```

GitHub Pages serves `docs/index.html` (Settings, Pages, deploy from the main branch, /docs folder).
Any other static host works too.
The page loads fonts from Google Fonts and d3 from cdnjs, and needs no other network access.

## Methods

1. Monthly means from the Giovanni series (daily data: months need at least ten valid days).
2. Seasons removed by subtracting each calendar month's long-term mean.
3. Rate of change: Sen's slope (median of all pairwise slopes).
4. Significance: Mann-Kendall test with a lag-1 effective-sample-size correction for autocorrelation.
   The "careless" comparison is an ordinary least-squares p-value that ignores autocorrelation.
5. Second opinions: Hamed and Rao modified Mann-Kendall (all significant lags of rank
   autocorrelation); Hirsch-Slack seasonal Kendall on the raw monthly record.
6. Verdicts: CONFIRMED (p < 0.01, interval excludes zero, both halves agree in sign); UNSTEADY
   (p < 0.05 but halves disagree); INCONCLUSIVE; NO TREND DETECTED (estimate far below the smallest
   trend the record could detect).
7. Turning point: continuous two-segment regression at every month, breakpoint uncertainty from a
   circular block bootstrap of residuals.
8. Robustness: every window of at least max(10 years, half the record) analyzed four ways; reported
   overall and for windows long enough to detect a trend of that size.
9. False alarms: 400 decoys per record from a circular block bootstrap of the trend-free residuals
   measure each test's false-positive rate (shown in "Why it matters").
10. Detection time: rule of thumb of Weatherhead et al. (1998).

Two common shortcuts, trend-free pre-whitening and the seasonal Kendall test without the
Hirsch-Slack correction, overstated significance badly on strongly autocorrelated series in our
tests (for land snow, p of 0.000004 and 0.00000001 against 0.26), so they are not used.

**Validation.** `tests/validate_browser_vs_python.py` feeds every raw file to the page's JavaScript
analysis. Verdicts and breakpoints match Python on all nine records, slopes agree within 0.05%,
and 99.9% of the robustness analyses agree (the rest are p-values at 0.05 rounded in data.json).

## Limitations

- Straight-line trends only. Curved changes are described by splitting the record, not modeled.
- MERRA-2 values are reanalysis (a model steered by observations), not direct measurements.
- OMI coverage changed after 2007 because of the row anomaly; we did not adjust for it.
- Window maps test hundreds of windows without a multiple-testing correction, by design: a window
  chosen after looking at the data is not a fair test.
- Giovanni CSVs do not carry units; users type them in when uploading.

## References

- Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*, 13, 245–259.
- Kendall, M. G. (1975). *Rank Correlation Methods*. Griffin.
- Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA*, 63, 1379–1389.
- Hamed, K. H., & Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *Journal of Hydrology*, 204, 182–196.
- Hirsch, R. M., Slack, J. R., & Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data. *Water Resources Research*, 18, 107–121.
- Hirsch, R. M., & Slack, J. R. (1984). A nonparametric trend test for seasonal data with serial dependence. *Water Resources Research*, 20, 727–732.
- Yue, S., Pilon, P., Phinney, B., & Cavadias, G. (2002). The influence of autocorrelation on the ability to detect trend in hydrological series. *Hydrological Processes*, 16, 1807–1829.
- Weatherhead, E. C., et al. (1998). Factors affecting the detection of trends: Statistical considerations and applications to environmental data. *Journal of Geophysical Research*, 103, 17149–17161.
- Steegen, S., Tuerlinckx, F., Gelman, A., & Vanpaemel, W. (2016). Increasing transparency through a multiverse analysis. *Perspectives on Psychological Science*, 11, 702–712.
- Gelaro, R., et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *Journal of Climate*, 30, 5419–5454.

## Data and tools

- NASA Giovanni (GES DISC) area-averaged time series. Datasets: OMI/Aura OMNO2d v4; MERRA-2
  collections M2TMNXSLV, M2TMNXFLX, M2TMNXLND, M2TMNXGLC, M2TMNXAER (v5.12.4). Details and the
  exact Giovanni settings for every file are in `data/README.md`.
- Python: NumPy, pandas, SciPy. Browser: plain JavaScript and SVG, plus d3 7.8.5 (loaded from cdnjs) for
  the globe. The page still works without it, except for the globe.
- World map: Natural Earth 1:110m land and borders (public domain), via the world-atlas package (ISC
  license), converted to compact coordinates in `web/geo.json`.
- Fonts: Special Elite and Source Serif 4, served by Google Fonts under open-source licenses.
- AI assistance: code and text were drafted with the help of Anthropic's Claude. All statistics are
  computed by the code in this repository, and no AI model produces or alters any number.

NASA does not endorse this project.
