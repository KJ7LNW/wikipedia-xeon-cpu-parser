# Xeon CPU Parser

Parse and analyze Intel Xeon CPU specifications from Wikipedia markup data.

## Data Source

The input files contain raw Wikipedia markup data extracted from CPU specification tables:

- `2025-02-21--xeon-scalable-v2-data.txt`: Cascade Lake Refresh (2nd Generation Scalable) data from [Wikipedia](https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Cascade_Lake-based)#Xeon_Gold_(quad_processor)) as of February 21, 2025

The markup uses the `cpulist` template format which defines fields like:
- Model number, cores/threads
- Base frequency (calculated from FSB × multiplier)
- Turbo Boost frequencies (all-core/max)
- L2/L3 cache sizes
- TDP, socket, memory support, etc.

## Usage

```sh
./parse_sections.py [options] <datafile>

Options:
  -f/--min-base-ghz FLOAT  Minimum base frequency in GHz
  -w/--min-tdp INT         Minimum TDP in watts  
  -W/--max-tdp INT         Maximum TDP in watts
  -c/--min-cores INT       Minimum number of cores
  -s/--sort FIELD         Sort by field name (default: Frequency)
                          Special: corehz (base×cores), corehz-all (boost×cores)
  -t/--markdown-table     Output as markdown table
  -i/--include STR       Always include entries matching substring (multiple ok)
  --show-all            Show all available fields (default: key fields only)
```

Example:
```sh
# Show 24+ core CPUs between 150-205W TDP, sorted by all-core performance
./parse_sections.py -c 24 -w 150 -W 205 -f 3.0 -t -s corehz-all 2025-02-21--xeon-scalable-v2-data.txt
```

## Example Output

The following shows 16+ core CPUs between 150-205W TDP with base frequency ≥3.0 GHz, sorted by GHz-cores (base frequency × cores), including models 6234 and 6246R for reference:

```sh
./parse_sections.py -c 16 -w 150 -W 205 -f 3.0 -t -s corehz -i 6234 -i 6246r 2025-02-21--xeon-scalable-v2-data.txt
```

```
=== Xeon Gold (dual processor) ===

Matching Entries (3):
|Model number | Cores (threads) | Frequency | Turbo Boost all-core/2.0) | L2 cache | L3 cache | Total Cache | TDP | GHz-cores|
|--- | --- | --- | --- | --- | --- | --- | --- | ---|
|Xeon Gold 6248R | 24 (48) | 3.0 GHz | 3.6/4.0 GHz | 24 × 1.0 MB | 35.75 MB | 59.75 MB | 205 W | 72.0|
|Xeon Gold 6242R | 20 (40) | 3.1 GHz | 3.3/4.1 GHz | 20 × 1.0 MB | 35.75 MB | 55.75 MB | 205 W | 62.0|
|**Xeon Gold 6246R** | 16 (32) | 3.4 GHz | 3.6/4.1 GHz | 16 × 1.0 MB | 35.75 MB | 51.75 MB | 205 W | 54.4|

=== Xeon Gold (quad processor) ===

Matching Entries (9):
|Model number | Cores (threads) | Frequency | Turbo Boost all-core/2.0) | L2 cache | L3 cache | Total Cache | TDP | GHz-cores|
|--- | --- | --- | --- | --- | --- | --- | --- | ---|
|Xeon Gold 6261 | 22 (44) | 3.0 GHz | 3.2/3.4 GHz | 22 × 1.0 MB | 30.25 MB | 52.25 MB | 205 W | 66.0|
|Xeon Gold 6266C | 22 (44) | 3.0 GHz | 3.2/3.4 GHz | 22 × 1.0 MB | 30.25 MB | 52.25 MB | 205 W | 66.0|
|Xeon Gold 6253W | 18 (36) | 3.1 GHz | 4.1/4.4 GHz | 18 × 1.0 MB | 24.75 MB | 42.75 MB | 200 W | 55.8|
|Xeon Gold 6253CL | 18 (36) | 3.1 GHz | 3.8/3.9 GHz | 18 × 1.0 MB | 24.75 MB | 42.75 MB | 205 W | 55.8|
|Xeon Gold 6254 | 18 (36) | 3.1 GHz | 3.9/4.0 GHz | 18 × 1.0 MB | 24.75 MB | 42.75 MB | 200 W | 55.8|
|Xeon Gold 6231 | 16 (32) | 3.2 GHz | ?/3.9 GHz | 16 × 1.0 MB | 22 MB | 38.00 MB | 185 W | 51.2|
|Xeon Gold 6231C | 16 (32) | 3.2 GHz | 3.7/3.9 GHz | 16 × 1.0 MB | 22 MB | 38.00 MB | 185 W | 51.2|
|Xeon Gold 6241W | 16 (32) | 3.2 GHz | 4.2/4.4 GHz | 16 × 1.0 MB | 22 MB | 38.00 MB | 205 W | 51.2|
|**Xeon Gold 6234** | 8 (16) | 3.3 GHz | 4.0/4.0 GHz | 8 × 1.0 MB | 24.75 MB | 32.75 MB | 130 W | 26.4|

=== Xeon Platinum (octa processor) ===

Matching Entries (1):
|Model number | Cores (threads) | Frequency | Turbo Boost all-core/2.0) | L2 cache | L3 cache | Total Cache | TDP | GHz-cores|
|--- | --- | --- | --- | --- | --- | --- | --- | ---|
|Xeon Platinum 8222L | 18 (36) | 3.0 GHz | 3.4/3.5 GHz | 18 × 1.0 MB | 24.75 MB | 42.75 MB | 200 W | 54.0|
```

The output shows:
- Entries sorted by GHz-cores (base frequency × cores)
- Total Cache combining L2 + L3 cache sizes
- Included models in bold (6234, 6246R) even if they don't meet filters
