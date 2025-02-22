# Xeon CPU Parser

Parse and analyze Intel Xeon CPU specifications from Wikipedia markup data.

## Data Source

The input files contain raw Wikipedia markup data extracted from CPU specification tables:

- `2025-02-21--xeon-scalable-v2-data.txt`: Cascade Lake Refresh (2nd Generation Scalable) data from February 21, 2025

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
