# Quick Start Guide - Chiller Picker

## 🚀 Getting Started

### Option 1: Double-click to run (Windows)
1. Double-click `launch.bat`
2. The application will open in your browser automatically
3. If it doesn't open, go to: http://localhost:8501

### Option 2: Command line
```bash
# Windows
python -m streamlit run app.py

# Or if streamlit is in PATH
streamlit run app.py
```

## 📋 First Time Setup

1. **Import Sample Data**:
   - Click "Import Data" in the sidebar
   - Go to "Paste & Parse" tab
   - Copy and paste the sample data from `sample_data.csv`
   - Set Ambient to 105°F, EWT to 12°C, LWT to 7°C
   - Click "Parse Data" then "Import to Database"

2. **Search for Chillers**:
   - Click "Search Chillers" in the sidebar
   - Enter your requirements:
     - Capacity: 100 tons
     - Ambient: 105°F
     - EWT: 12°C
     - LWT: 7°C
   - Click "Search Chillers"

## 🎯 Features

### Search Interface
- **Input Fields**: Capacity, Ambient, EWT, LWT
- **Smart Search**: Automatically widens capacity tolerance if no matches
- **Ranked Results**: Best option + alternatives
- **Expandable Details**: Click "View more details" for full specs

### Results Display
- **Best Option**: Highlighted in green
- **Alternatives**: Up to 2 neighbor chillers (above/below in capacity)
- **All Matches**: Collapsible table with all results
- **Search Summary**: Shows tolerance band and match count

### Data Import
- **Paste & Parse**: Paste table data directly
- **File Upload**: Upload CSV/TSV files
- **Batch Assignment**: Set ambient/temperatures for all rows
- **Preview**: See parsed data before importing

## 🔧 Troubleshooting

### Application won't start
- Make sure Python is installed
- Install dependencies: `pip install -r requirements.txt`
- Try: `python -m streamlit run app.py`

### No data found
- Import sample data first (see First Time Setup)
- Check ambient temperature selection
- Try different capacity values

### Browser doesn't open
- Manually go to: http://localhost:8501
- Check if port 8501 is available

## 📊 Sample Data

The application comes with sample data for testing:
- 16 chiller models (ACHX-B series)
- Capacity range: 77-369 tons
- Ambient: 105°F
- Full specifications included

## 🎨 UI Features

- **Clean Design**: Minimal, modern interface
- **Responsive**: Works on desktop and mobile
- **Color Coded**: Green for best option, yellow for alternatives
- **Expandable Cards**: Click to see full specifications
- **Search Summary**: Shows active filters and tolerance band
