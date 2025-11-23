# Chiller Picker

A Python application for selecting the best chiller based on capacity, ambient temperature, and water temperatures. Built with Streamlit and SQLite.

## Features

- **Smart Search**: Find chillers by capacity, ambient temperature, and water temperatures
- **Progressive Tolerance**: Automatically widens capacity tolerance (±10% to ±20%) if no matches found
- **Ranked Results**: Results ranked by capacity delta, temperature match, and efficiency
- **Data Import**: Import chiller specifications from pasted tables or files
- **Fallback Handling**: Shows available ambient temperatures when no exact match found
- **Detailed Views**: Expandable details for each chiller option

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app.py
```

### 3. Import Sample Data

1. Go to the "Import Data" page
2. Copy and paste the sample data below into the "Paste Table Data" section
3. Set Ambient to 105°F, EWT to 12°C, LWT to 7°C
4. Click "Parse Data" then "Import to Database"

### 4. Search for Chillers

1. Go to the "Search Chillers" page
2. Enter your requirements (e.g., 50 tons, 105°F ambient, 12/7°C water temps)
3. View the ranked results

## Sample Data

```
Model	Tons	U. kW	C. kW	F. kW	Energy efficiency (kW/ton)	IPLV (kW/ton)	USgpm	psi/ft.w.g	MCA	Dimensions
ACHX-B 90S	80.10	119.52	104.40	15.12	1.492	0.973	191.56	3.4/7.7	265	152.0 L 89.0 W 89.0 H (in)
ACHX-B 90T	77.48	121.32	106.20	15.12	1.566	0.99	185.29	2.6/6.0	245	152.0 L 89.0 W 89.0 H (in)
ACHX-B 120S	108.20	145.42	130.30	15.12	1.344	0.924	258.76	3.8/8.7	323	152.0 L 89.0 W 89.0 H (in)
ACHX-B 120T	101.60	156.24	141.12	15.12	1.538	0.931	242.98	3.4/7.8	316	152.0 L 89.0 W 89.0 H (in)
ACHX-B 150S	140.97	186.84	166.68	20.16	1.325	0.896	337.13	10.2/23.5	415	197.3 L 89.0 W 96.0 H (in)
ACHX-B 150T	126.50	189.76	169.60	20.16	1.5	0.93	302.52	8.4/19.5	383	197.3 L 89.0 W 96.0 H (in)
ACHX-B 170S	141.60	200.16	180.00	20.16	1.414	1.019	338.64	7.7/17.8	445	197.3 L 89.0 W 96.0 H (in)
ACHX-B 180T	170.26	240.75	215.55	25.2	1.414	0.874	407.18	8.3/19.2	486	242.5 L 89.0 W 96.0 H (in)
ACHX-B 200S	188.91	261.00	235.80	25.2	1.382	0.922	451.78	10.0/23.1	580	242.5 L 89.0 W 89.0 H (in)
ACHX-B 200T	174.35	261.12	235.92	25.2	1.498	1.003	416.96	8.7/20.0	527	242.5 L 89.0 W 89.0 H (in)
ACHX-B 240T	215.70	292.64	262.40	30.24	1.357	0.858	515.85	10.3/23.7	591	287.8 L 89.0 W 96.0 H (in)
ACHX-B 270T	228.90	322.78	287.50	35.28	1.41	0.939	547.41	8.3/19.2	652	333.0 L 89.0 W 96.0 H (in)
ACHX-B 290T	246.00	351.78	316.50	35.28	1.43	0.941	588.31	9.5/21.8	711	333.0 L 89.0 W 96.0 H (in)
ACHX-B 330T	285.38	401.82	361.50	40.32	1.408	0.98	682.49	10.7/24.7	812	378.4 L 89.0 W 96.0 H (in)
ACHX-B 350T	328.01	447.92	402.56	45.36	1.366	0.896	784.44	8.2/18.8	905	423.6 L 89.0 W 96.0 H (in)
ACHX-B 400T	369.12	505.64	455.24	50.4	1.37	0.871	882.75	9.2/21.3	1021	468.9 L 89.0 W 96.0 H (in)
```

## CLI Import

You can also import data from the command line:

```bash
# Import from file
python import_from_file.py --file data.csv --ambient 105 --ewt 12 --lwt 7

# Import from clipboard
python import_from_file.py --clipboard --ambient 105 --ewt 12 --lwt 7

# Preview without importing
python import_from_file.py --file data.csv --preview
```

## Project Structure

```
chiller_picker/
├── app.py                 # Main Streamlit application
├── db.py                  # Database operations
├── importer.py            # Data parsing and import logic
├── selector.py            # Chiller selection and ranking
├── utils.py               # Utility functions
├── import_from_file.py    # CLI importer
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Search Logic

The application uses a sophisticated ranking system:

1. **Ambient Filter**: Only shows chillers matching the specified ambient temperature
2. **Capacity Tolerance**: Starts with ±10%, widens to ±20% if no matches
3. **Ranking Criteria** (in order):
   - Capacity delta (closer to target is better)
   - Temperature match (closer EWT/LWT is better)
   - Efficiency (lower kW/ton is better)
   - Waterflow (higher is better)

## Data Format

The importer expects tabular data with these columns (case-insensitive):

- **Model**: Chiller model name
- **Tons**: Cooling capacity in tons
- **Energy efficiency (kW/ton)**: Efficiency rating
- **IPLV (kW/ton)**: Integrated Part Load Value
- **USgpm**: Water flow rate
- **U. kW, C. kW, F. kW**: Unit, Compressor, Fan power
- **psi/ft.w.g**: Pressure drop (parsed into two fields)
- **MCA**: Minimum Circuit Amps
- **Dimensions**: Physical dimensions (parsed into L×W×H)

## Database Schema

The SQLite database stores chiller data with these key fields:

- `id`: Primary key
- `model`: Chiller model
- `capacity_tons`: Cooling capacity
- `ambient_f`: Ambient temperature (°F)
- `ewt_c`, `lwt_c`: Water temperatures (°C)
- `efficiency_kw_per_ton`: Energy efficiency
- `waterflow_usgpm`: Water flow rate
- Plus physical specs, electrical data, and dimensions

## Troubleshooting

### No Data Found
- Check that you've imported data first
- Verify ambient temperature selection
- Try widening the capacity range manually

### Import Errors
- Ensure table has proper headers
- Check that required fields (Model, Tons, Efficiency) are present
- Verify numeric data is properly formatted

### Performance
- Large datasets (>1000 chillers) may be slow to search
- Consider filtering by manufacturer or capacity range first

## License

This project is provided as-is for chiller selection and specification management.
