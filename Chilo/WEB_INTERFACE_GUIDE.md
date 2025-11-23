# Chiller Picker - Web Interface Guide

## 🌐 Web Interface Features

The Chiller Picker application includes a comprehensive web interface built with Streamlit that provides all the functionality you requested:

### ✅ Input Fields (Top Section)
- **Capacity (tons)**: Number input with validation (0.1-1000 tons)
- **Ambient Temperature**: Dropdown with options 95°F, 105°F, 115°F
- **Entering Water Temperature (EWT)**: Number input in °C (0-50°C)
- **Leaving Water Temperature (LWT)**: Number input in °C (0-50°C)
- **Search Button**: Large, prominent search button

### ✅ Results Display
- **Best Option**: Highlighted in green with prominent display
- **Neighbor Chillers**: Shows up to 2 alternatives (one above, one below in capacity)
- **View More Details**: Expandable sections for full specifications
- **Search Summary**: Shows active filters and tolerance band used

### ✅ Additional Features
- **Progressive Tolerance**: Automatically widens from ±10% to ±20% if no matches
- **Fallback Handling**: Shows available ambient temperatures when no exact match
- **Data Import**: Built-in import functionality for pasting tables or uploading files
- **Database Stats**: View database statistics and sample data
- **Clean UI**: Modern, responsive design with color-coded results

## 🚀 How to Access

### Method 1: Double-click launcher (Windows)
1. Double-click `launch.bat`
2. Browser opens automatically to http://localhost:8501

### Method 2: Command line
```bash
python -m streamlit run app.py
```
Then open http://localhost:8501 in your browser

### Method 3: Direct streamlit command
```bash
streamlit run app.py
```

## 📋 Quick Test

1. **Start the application** using any method above
2. **Import sample data**:
   - Click "Import Data" in sidebar
   - Paste the sample data from `sample_data.csv`
   - Set Ambient to 105°F, EWT to 12°C, LWT to 7°C
   - Click "Parse Data" then "Import to Database"
3. **Search for chillers**:
   - Click "Search Chillers" in sidebar
   - Enter: 100 tons, 105°F, 12/7°C
   - Click "Search Chillers"
   - View the ranked results with best option and alternatives

## 🎯 Search Results Example

When you search for **100 tons, 105°F, 12/7°C**, you'll see:

### Best Option (Green highlight)
- **ACHX-B 120T**: 101.6 tons, 1.538 kW/ton, 242.98 USgpm
- Temperature: 105°F / EWT: 12.0°C / LWT: 7.0°C
- Click "View more details" for full specs

### Closest Alternatives (Yellow highlight)
- **ACHX-B 120S**: 108.2 tons, 1.344 kW/ton, 258.76 USgpm

### Search Summary
"Target capacity: 100.0 tons · Band: ±10.0% (90.0–110.0) · Ambient: 105°F · EWT/LWT: 12.0/7.0°C · Found: 2 matches"

## 🔧 Technical Details

- **Framework**: Streamlit (Python web framework)
- **Database**: SQLite (local file: `chillers.db`)
- **Port**: 8501 (default Streamlit port)
- **Browser**: Works in Chrome, Firefox, Safari, Edge
- **Responsive**: Works on desktop and mobile devices

## 🎨 UI Design

- **Clean Layout**: Minimal, modern interface
- **Color Coding**: Green for best option, yellow for alternatives
- **Expandable Cards**: Click to see detailed specifications
- **Search Summary**: Shows active filters and tolerance band
- **Error Handling**: Clear messages for no matches or missing data
- **Loading States**: Visual feedback during search operations

## 📊 Data Management

- **Import Methods**: Paste table data or upload CSV/TSV files
- **Batch Assignment**: Set ambient/temperatures for all imported rows
- **Data Validation**: Automatic parsing and validation of chiller specifications
- **Preview Mode**: See parsed data before importing
- **Database Stats**: View total chillers, manufacturers, ambient temperatures

The web interface provides everything you need to interact with the chiller selection tool visually in your browser!
