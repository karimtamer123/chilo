import streamlit as st
import pandas as pd
import json
from typing import Optional, List, Dict
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import db
import importer
import selector
from utils import safe_float

# Page configuration
st.set_page_config(
    page_title="Chiller Picker Pro",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/chiller-picker',
        'Report a bug': 'https://github.com/your-repo/chiller-picker/issues',
        'About': 'Professional chiller selection and comparison tool'
    }
)

# Initialize database
@st.cache_resource
def init_app():
    """Initialize the application and database."""
    db.init_database()
    return True

init_app()

# Basic styling for clean appearance
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #0d5a8a;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Header
    st.title("❄️ Chiller Picker Pro")
    st.markdown("Professional chiller selection and comparison tool")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        
        page = st.radio(
            "Choose a page:",
            ["🔍 Search Chillers", "📥 Import Data", "📊 Database Stats", "⚙️ Manage Data"],
            index=0
        )
        
        st.info("Professional chiller selection tool with advanced filtering and comparison features.")
    
    # Route to appropriate page
    if page == "🔍 Search Chillers":
        search_page()
    elif page == "📥 Import Data":
        import_page()
    elif page == "📊 Database Stats":
        stats_page()
    elif page == "⚙️ Manage Data":
        manage_page()

# Initialize session state for search history
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

def add_to_search_history(capacity: float, ambient: int, ewt: float, lwt: float):
    """Add a search to history (keep last 5)."""
    search_entry = {
        'capacity': capacity,
        'ambient': ambient,
        'ewt': ewt,
        'lwt': lwt,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    # Remove duplicates (same search parameters)
    st.session_state.search_history = [
        s for s in st.session_state.search_history 
        if not (s['capacity'] == capacity and s['ambient'] == ambient and 
                s['ewt'] == ewt and s['lwt'] == lwt)
    ]
    # Add new search at the beginning
    st.session_state.search_history.insert(0, search_entry)
    # Keep only last 5
    st.session_state.search_history = st.session_state.search_history[:5]

def create_efficiency_comparison_chart(chillers: List[Dict]) -> go.Figure:
    """Create a side-by-side efficiency comparison chart."""
    if not chillers:
        return None
    
    models = [ch.get('model', f"Model {i+1}") for i, ch in enumerate(chillers)]
    efficiencies = [ch.get('efficiency_kw_per_ton') for ch in chillers]
    
    # Filter out None values
    valid_data = [(m, e) for m, e in zip(models, efficiencies) if e is not None]
    if not valid_data:
        return None
    
    models_clean, efficiencies_clean = zip(*valid_data)
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(models_clean),
            y=list(efficiencies_clean),
            marker_color='#1f77b4',
            text=[f'{e:.3f}' for e in efficiencies_clean],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title='Efficiency Comparison (kW/ton)',
        xaxis_title='Chiller Model',
        yaxis_title='Efficiency (kW/ton)',
        height=400,
        showlegend=False,
        xaxis={'tickangle': -45}
    )
    
    return fig

def export_comparison_report(chillers: List[Dict], search_params: Dict) -> str:
    """Generate a CSV comparison report."""
    if not chillers:
        return None
    
    # Prepare data for export
    export_data = []
    for ch in chillers:
        export_data.append({
            'Model': ch.get('model', ''),
            'Manufacturer': ch.get('manufacturer', ''),
            'Capacity (tons)': ch.get('capacity_tons', ''),
            'Efficiency (kW/ton)': ch.get('efficiency_kw_per_ton', ''),
            'Waterflow (USgpm)': ch.get('waterflow_usgpm', ''),
            'Ambient (°F)': ch.get('ambient_f', ''),
            'EWT (°C)': ch.get('ewt_c', ''),
            'LWT (°C)': ch.get('lwt_c', ''),
            'Unit kW': ch.get('unit_kw', ''),
            'Compressor kW': ch.get('compressor_kw', ''),
            'Fan kW': ch.get('fan_kw', ''),
            'IPLV (kW/ton)': ch.get('iplv_kw_per_ton', ''),
            'MCA (Amps)': ch.get('mca_amps', ''),
            'Pressure Drop (psi)': ch.get('pressure_drop_psi', ''),
            'Pressure Drop (ft.w.g)': ch.get('pressure_drop_ftwg', ''),
            'Length (in)': ch.get('length_in', ''),
            'Width (in)': ch.get('width_in', ''),
            'Height (in)': ch.get('height_in', '')
        })
    
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    return csv

def search_page():
    """Main search interface."""
    
    # Check if database has data
    stats = db.get_database_stats()
    if stats['total_chillers'] == 0:
        st.warning("No chiller model data found. Please import data first using the 'Import Data' page.")
        return
    
    st.header("Search for Chillers")
    
    # Quick Filters Section
    st.subheader("⚡ Quick Filters")
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    with col_f1:
        if st.button("50-100 tons", use_container_width=True, key="qf_50_100"):
            st.session_state.quick_filter_capacity = 75.0
            st.rerun()
    with col_f2:
        if st.button("100-200 tons", use_container_width=True, key="qf_100_200"):
            st.session_state.quick_filter_capacity = 150.0
            st.rerun()
    with col_f3:
        if st.button("200+ tons", use_container_width=True, key="qf_200_plus"):
            st.session_state.quick_filter_capacity = 250.0
            st.rerun()
    with col_f4:
        if st.button("Clear Filter", use_container_width=True, key="qf_clear"):
            if 'quick_filter_capacity' in st.session_state:
                del st.session_state.quick_filter_capacity
            st.rerun()
    
    # Search History Section
    if st.session_state.search_history:
        with st.expander("📚 Search History (Last 5 searches)", expanded=False):
            for i, hist in enumerate(st.session_state.search_history):
                col_h1, col_h2, col_h3 = st.columns([3, 1, 1])
                with col_h1:
                    st.write(f"**Search {i+1}:** {hist['capacity']:.1f} tons @ {hist['ambient']}°F, {hist['ewt']}/{hist['lwt']}°C")
                with col_h2:
                    st.caption(hist['timestamp'])
                with col_h3:
                    if st.button("Use", key=f"history_{i}", use_container_width=True):
                        st.session_state.history_capacity = hist['capacity']
                        st.session_state.history_ambient = hist['ambient']
                        st.session_state.history_ewt = hist['ewt']
                        st.session_state.history_lwt = hist['lwt']
                        st.rerun()
    
    st.divider()
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        # Determine initial values (from quick filter, history, or defaults)
        default_capacity = 50.0
        if 'quick_filter_capacity' in st.session_state:
            default_capacity = st.session_state.quick_filter_capacity
        elif 'history_capacity' in st.session_state:
            default_capacity = st.session_state.history_capacity
        
        default_ambient_idx = 1  # 105°F
        if 'history_ambient' in st.session_state:
            ambient_options = [95, 105, 115]
            try:
                default_ambient_idx = ambient_options.index(st.session_state.history_ambient)
            except:
                pass
        
        default_ewt_idx = 0  # 54°C
        if 'history_ewt' in st.session_state:
            ewt_options = [54, 55]
            try:
                default_ewt_idx = ewt_options.index(st.session_state.history_ewt)
            except:
                pass
        
        default_lwt_idx = 0  # 44°C
        if 'history_lwt' in st.session_state:
            lwt_options = [44, 45]
            try:
                default_lwt_idx = lwt_options.index(st.session_state.history_lwt)
            except:
                pass
        
        with col1:
            capacity_tons = st.number_input(
                "Capacity (tons)",
                min_value=0.1,
                max_value=1000.0,
                value=default_capacity,
                step=0.1,
                help="Required cooling capacity in tons"
            )
            
            ambient_f = st.selectbox(
                "Ambient Temperature (°F)",
                options=[95, 105, 115],
                index=default_ambient_idx,
                help="Ambient temperature for chiller operation"
            )
        
        with col2:
            ewt_c = st.selectbox(
                "Entering Water Temperature (°C)",
                options=[54, 55],
                index=default_ewt_idx,
                help="Entering water temperature in Celsius"
            )
            
            lwt_c = st.selectbox(
                "Leaving Water Temperature (°C)",
                options=[44, 45],
                index=default_lwt_idx,
                help="Leaving water temperature in Celsius"
            )
        
        search_button = st.form_submit_button("🔍 Search Chillers", use_container_width=True)
    
    if search_button:
        # Clear session state after form submission
        if 'quick_filter_capacity' in st.session_state:
            del st.session_state.quick_filter_capacity
        if 'history_capacity' in st.session_state:
            del st.session_state.history_capacity
            del st.session_state.history_ambient
            del st.session_state.history_ewt
            del st.session_state.history_lwt
        # Add to search history
        add_to_search_history(capacity_tons, ambient_f, ewt_c, lwt_c)
        
        # Perform search
        selector_obj = selector.ChillerSelector()
        results = selector_obj.find_best_chillers(capacity_tons, ambient_f, ewt_c, lwt_c)
        
        # Store results in session state for export
        all_best_options = [results['best_option']] + results['alternatives']
        all_best_options = [opt for opt in all_best_options if opt is not None]
        st.session_state.last_search_results = {
            'chillers': all_best_options,
            'all_matches': results['all_matches'],
            'search_params': {
                'capacity': capacity_tons,
                'ambient': ambient_f,
                'ewt': ewt_c,
                'lwt': lwt_c
            }
        }
        
        # Display search summary
        if not results['no_matches']:
            search_summary = selector_obj.get_search_summary(results['search_info'])
            st.info(f"**Search Results:** {search_summary}")
        
        # Display results
        if results['no_matches']:
            if results['fallback_available']:
                st.error("No chillers found for the specified ambient temperature.")
                st.info("Available ambient temperatures in database:")
                for fallback in results['fallback_available']:
                    st.write(f"- {fallback['ambient_f']}°F ({fallback['count']} chillers)")
            else:
                st.error("No chillers found matching your criteria. Try adjusting the capacity range or import more data.")
        else:
            # Efficiency Comparison Chart
            if all_best_options:
                st.subheader("📊 Efficiency Comparison")
                efficiency_chart = create_efficiency_comparison_chart(all_best_options)
                if efficiency_chart:
                    st.plotly_chart(efficiency_chart, use_container_width=True)
                else:
                    st.info("Efficiency data not available for comparison.")
                st.divider()
            
            # Best 3 Options
            if all_best_options:
                st.subheader("🏆 Best 3 Options")
                
                # Export button
                csv_data = export_comparison_report(all_best_options, {
                    'capacity': capacity_tons,
                    'ambient': ambient_f,
                    'ewt': ewt_c,
                    'lwt': lwt_c
                })
                if csv_data:
                    st.download_button(
                        label="📥 Export Comparison Report (CSV)",
                        data=csv_data,
                        file_name=f"chiller_comparison_{capacity_tons}tons_{ambient_f}F.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="export_btn"
                    )
                    st.divider()
                
                # Display the best option first
                if results['best_option']:
                    display_chiller_card(results['best_option'], "Best Match", "best-option")
                
                # Display alternatives
                if results['alternatives']:
                    for i, alt in enumerate(results['alternatives']):
                        if alt:
                            if i == 0 and len(results['alternatives']) >= 2:
                                display_chiller_card(alt, "Higher Capacity", "alternative")
                            elif i == 1 and len(results['alternatives']) >= 2:
                                display_chiller_card(alt, "Lower Capacity", "alternative")
                            else:
                                display_chiller_card(alt, f"Option {i+2}", "alternative")
            
            # All matches (collapsible)
            if len(results['all_matches']) > 3:
                with st.expander(f"View All {len(results['all_matches'])} Matches"):
                    display_all_matches_table(results['all_matches'])

def display_chiller_card(chiller_data: dict, title: str, card_class: str):
    """Display a chiller card with main metrics and expandable details."""
    
    formatted = selector.ChillerSelector().format_chiller_display(chiller_data)
    
    with st.container():
        # Chiller title and info
        chiller_name = formatted['details']['model']
        manufacturer = formatted['details']['manufacturer']
        
        st.subheader(f"{chiller_name} ({manufacturer})")
        st.caption(formatted['temp_info'])
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            capacity = formatted['capacity_tons']
            st.metric("Capacity", f"{capacity:.1f} tons")
        
        with col2:
            efficiency = formatted['efficiency_kw_per_ton']
            st.metric("Efficiency", f"{efficiency:.3f} kW/ton")
        
        with col3:
            waterflow = formatted['waterflow_usgpm']
            st.metric("Waterflow", f"{waterflow:.1f} USgpm")
        
        # Expandable details
        with st.expander("View more details", expanded=False):
            details = formatted['details']
            
            # Basic Info Section
            st.subheader("Basic Information")
            
            basic_info = [
                ("Model", details['model']),
                ("Manufacturer", details['manufacturer']),
                ("Model Prefix", details.get('model_prefix', 'N/A')),
                ("Folder", details.get('folder_name', 'N/A'))
            ]
            
            for label, value in basic_info:
                if value and value != 'N/A':
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.write(f"**{label}:**")
                    with col2:
                        st.write(value)
            
            # Performance Section
            st.subheader("Performance Data")
            
            perf_info = []
            if details['unit_kw']:
                perf_info.append(("Unit kW", f"{details['unit_kw']:.1f}"))
            if details['compressor_kw']:
                perf_info.append(("Compressor kW", f"{details['compressor_kw']:.1f}"))
            if details['fan_kw']:
                perf_info.append(("Fan kW", f"{details['fan_kw']:.1f}"))
            if details['iplv_kw_per_ton']:
                perf_info.append(("IPLV", f"{details['iplv_kw_per_ton']:.3f} kW/ton"))
            if details['mca_amps']:
                perf_info.append(("MCA", f"{details['mca_amps']:.0f} A"))
            
            for label, value in perf_info:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**{label}:**")
                with col2:
                    st.write(value)
            
            # Physical Specs Section
            st.subheader("Physical Specifications")
            
            if details['pressure_drop_psi'] and details['pressure_drop_ftwg']:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("**Pressure Drop:**")
                with col2:
                    st.write(f"{details['pressure_drop_psi']:.1f} psi / {details['pressure_drop_ftwg']:.1f} ft.w.g")
            
            dims = []
            if details['length_in']:
                dims.append(f"L: {details['length_in']:.1f}\"")
            if details['width_in']:
                dims.append(f"W: {details['width_in']:.1f}\"")
            if details['height_in']:
                dims.append(f"H: {details['height_in']:.1f}\"")
            
            if dims:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("**Dimensions:**")
                with col2:
                    st.write(' × '.join(dims))
            
            if details['notes']:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write("**Notes:**")
                with col2:
                    st.write(details['notes'])

def display_all_matches_table(all_matches: list):
    """Display all matches in a table format."""
    
    if not all_matches:
        st.write("No matches found.")
        return
    
    # Create DataFrame for display
    display_data = []
    for chiller in all_matches:
        formatted = selector.ChillerSelector().format_chiller_display(chiller)
        display_data.append({
            'Rank': chiller.get('_rank', ''),
            'Model': formatted['details']['model'],
            'Capacity (tons)': f"{formatted['capacity_tons']:.1f}" if formatted['capacity_tons'] else "—",
            'Efficiency (kW/ton)': f"{formatted['efficiency_kw_per_ton']:.3f}" if formatted['efficiency_kw_per_ton'] else "—",
            'Waterflow (USgpm)': f"{formatted['waterflow_usgpm']:.1f}" if formatted['waterflow_usgpm'] else "—",
            'Ambient': f"{chiller.get('ambient_f', '')}°F" if chiller.get('ambient_f') else "—",
            'Cap Delta': f"{chiller.get('_cap_delta', 0):.1f}" if chiller.get('_cap_delta') is not None else "—"
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, width='stretch')

def import_page():
    """Data import interface."""
    
    st.header("Import Chiller Data")
    
    # Tabs for different import methods
    tab1, tab2 = st.tabs(["📋 Paste & Parse", "📁 File Upload"])
    
    with tab1:
        st.subheader("Paste Table Data")
        st.write("Paste your chiller specification table below. The system will automatically detect the format.")
        
        # Batch assignment options
        with st.expander("Batch Assignment Options"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                batch_ambient = st.selectbox(
                    "Set Ambient for All Rows",
                    options=[None, 95, 105, 115],
                    help="Apply this ambient temperature to all imported rows"
                )
            
            with col2:
                batch_ewt = st.selectbox(
                    "Set EWT for All Rows (°C)",
                    options=[None, 54, 55],
                    index=0,
                    help="Apply this EWT to all imported rows"
                )
            
            with col3:
                batch_lwt = st.selectbox(
                    "Set LWT for All Rows (°C)",
                    options=[None, 44, 45],
                    index=0,
                    help="Apply this LWT to all imported rows"
                )
        
        # Text area for pasting
        pasted_data = st.text_area(
            "Paste your table here:",
            height=300,
            help="Paste tabular data with headers. Supports tab-separated or space-separated formats."
        )
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            parse_button = st.button("Parse Data", type="primary", width='stretch')
        
        with col2:
            # Check if we have parsed data ready to import
            if 'parsed_df' in st.session_state and not st.session_state['parsed_df'].empty:
                import_button = st.button("Import to Database", type="primary", width='stretch', key="import_btn")
            else:
                import_button = False
                st.button("Import to Database", disabled=True, width='stretch', key="import_btn_disabled")
                st.caption("Parse data first to enable import")
        
        # Handle parse button
        if parse_button:
            if pasted_data.strip():
                with st.spinner("Parsing data..."):
                    # Parse the data
                    df, errors = importer.parse_table_text(
                        pasted_data, 
                        ambient_f=batch_ambient,
                        ewt_c=batch_ewt,
                        lwt_c=batch_lwt
                    )
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                
                if not df.empty:
                    # Store parsed data in session state
                    st.session_state['parsed_df'] = df
                    st.session_state['parsed_errors'] = errors
                    st.success(f"✅ Successfully parsed {len(df)} records!")
                    
                    # Show preview
                    importer.preview_parsed_data(df)
                    st.rerun()
                else:
                    st.error("❌ No data could be parsed. Check the format and try again.")
            else:
                st.warning("⚠️ Please paste some data first.")
        
        # Handle import button
        if import_button and 'parsed_df' in st.session_state:
            df = st.session_state['parsed_df']
            with st.spinner(f"Importing {len(df)} records..."):
                imported_count, import_errors = importer.import_chillers_from_dataframe(df, db)
            
            if import_errors:
                for error in import_errors:
                    st.error(f"❌ {error}")
            
            if imported_count > 0:
                st.success(f"✅ Successfully imported {imported_count} chiller records!")
                st.balloons()  # Celebration animation!
                st.info("💡 Go to 'Database Stats' to see your imported data.")
                # Clear parsed data after import
                del st.session_state['parsed_df']
                if 'parsed_errors' in st.session_state:
                    del st.session_state['parsed_errors']
                st.rerun()
            else:
                st.error("❌ No records were imported. Check the errors above.")
            
        # Show parsed data if available
        if 'parsed_df' in st.session_state and not st.session_state['parsed_df'].empty:
            df = st.session_state['parsed_df']
            if not parse_button and not import_button:  # Only show if not just parsed/imported
                st.info("📋 Showing previously parsed data. You can import it or parse new data.")
                importer.preview_parsed_data(df)
    
    with tab2:
        st.subheader("Upload File")
        st.write("Upload a CSV or TSV file containing chiller specifications.")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'tsv', 'txt'],
            help="Upload a CSV, TSV, or text file with chiller data"
        )
        
        if uploaded_file:
            # Batch assignment options for file upload
            with st.expander("Batch Assignment Options"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    file_ambient = st.selectbox(
                        "Set Ambient for All Rows",
                        options=[None, 95, 105, 115],
                        key="file_ambient",
                        help="Apply this ambient temperature to all imported rows"
                    )
                
                with col2:
                    file_ewt = st.selectbox(
                        "Set EWT for All Rows (°C)",
                        options=[None, 54, 55],
                        index=0,
                        key="file_ewt",
                        help="Apply this EWT to all imported rows"
                    )
                
                with col3:
                    file_lwt = st.selectbox(
                        "Set LWT for All Rows (°C)",
                        options=[None, 44, 45],
                        index=0,
                        key="file_lwt",
                        help="Apply this LWT to all imported rows"
                    )
            
            if st.button("Import File", type="primary", width='stretch'):
                with st.spinner("Importing file..."):
                    # Save uploaded file temporarily
                    with open("temp_upload.csv", "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Import from file
                    imported_count, errors = importer.import_from_file(
                        "temp_upload.csv",
                        ambient_f=file_ambient,
                        ewt_c=file_ewt,
                        lwt_c=file_lwt
                    )
                
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                
                if imported_count > 0:
                    st.success(f"✅ Successfully imported {imported_count} chiller records!")
                    st.balloons()  # Celebration animation!
                    st.info("💡 Go to 'Database Stats' to see your imported data.")
                    st.rerun()
                else:
                    st.error("❌ No records were imported. Check the errors above.")

def stats_page():
    """Database statistics page."""
    
    st.header("Database Statistics")
    
    # Get database stats
    stats = db.get_database_stats()
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Chiller Types", len(db.get_organized_data()))
    
    with col2:
        st.metric("Total Models", stats['total_chillers'])
    
    with col3:
        st.metric("Temperature Folders", len(db.get_all_folders()))
    
    # Show organized data by manufacturer and folder
    if stats['total_chillers'] > 0:
        st.subheader("📁 Data Organization")
        
        organized_data = db.get_organized_data()
        all_folders = db.get_all_folders()
        
        if organized_data:
            for model_prefix, model_data in organized_data.items():
                manufacturer = model_data.get('manufacturer', 'Unknown')
                folders = model_data.get('folders', {})
                
                with st.expander(f"❄️ **{model_prefix}** Chiller ({manufacturer})", expanded=True):
                    for folder_name, folder_data in folders.items():
                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.write(f"📂 **{folder_name}**")
                            st.caption(f"Models: {', '.join(folder_data['models'][:5])}{'...' if len(folder_data['models']) > 5 else ''}")
                        
                        with col2:
                            st.metric("Models", folder_data['count'])
                        
                        with col3:
                            if st.button("View Details", key=f"view_{model_prefix}_{folder_name}"):
                                st.session_state[f"view_folder_{model_prefix}_{folder_name}"] = True
                        
                        # Show folder details if requested
                        if st.session_state.get(f"view_folder_{model_prefix}_{folder_name}", False):
                            folder_chillers = db.get_chillers_by_folder(model_prefix, folder_name)
                            if folder_chillers:
                                folder_df = pd.DataFrame(folder_chillers)
                                display_cols = ['model', 'capacity_tons', 'efficiency_kw_per_ton', 'waterflow_usgpm']
                                available_cols = [col for col in display_cols if col in folder_df.columns]
                                if available_cols:
                                    st.dataframe(folder_df[available_cols], width='stretch')
                            
                            if st.button("Close", key=f"close_{model_prefix}_{folder_name}"):
                                st.session_state[f"view_folder_{model_prefix}_{folder_name}"] = False
                                st.rerun()
        else:
            st.info("No organized data found. Import some data to see the folder structure.")
    
    # Show available ambients
    available_ambients = db.get_available_ambients()
    if available_ambients:
        st.subheader("🌡️ Available Ambient Temperatures")
        for ambient in available_ambients:
            count = len(db.get_chillers_by_criteria(1, ambient, None, None, 1.0))  # Get count for this ambient
            st.write(f"- {ambient}°F: {count} chillers")

def manage_page():
    """Data management page for editing folders and deleting records."""
    
    st.header("⚙️ Manage Data")
    
    # Check if database has data
    stats = db.get_database_stats()
    if stats['total_chillers'] == 0:
        st.warning("No chiller model data found. Please import data first using the 'Import Data' page.")
        return
    
    # Get organized data
    organized_data = db.get_organized_data()
    
    if not organized_data:
        st.info("No organized data found. Import some data first.")
        return
    
    # Display overview
    st.subheader("📁 Folder Overview")
    
    # Show each model prefix and its folders
    for model_prefix, model_data in organized_data.items():
        manufacturer = model_data.get('manufacturer', 'Unknown')
        folders = model_data.get('folders', {})
        
        st.markdown(f"### ❄️ **{model_prefix}** Chiller ({manufacturer})")
        
        for folder_name, folder_data in folders.items():
            with st.expander(f"📂 {folder_name} ({folder_data['count']} models)", expanded=False):
                # Show folder actions
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Folder:** {folder_name}")
                    st.caption(f"Models: {', '.join(folder_data['models'][:10])}{'...' if len(folder_data['models']) > 10 else ''}")
                
                with col2:
                    # Edit folder name button
                    if st.button("✏️ Edit Folder", key=f"edit_{model_prefix}_{folder_name}"):
                        st.session_state[f"editing_{model_prefix}_{folder_name}"] = True
                
                with col3:
                    # Delete folder button
                    if st.button("🗑️ Delete Folder", key=f"delete_folder_{model_prefix}_{folder_name}"):
                        st.session_state[f"confirm_delete_folder_{model_prefix}_{folder_name}"] = True
                
                # Edit folder name interface
                if st.session_state.get(f"editing_{model_prefix}_{folder_name}", False):
                    st.markdown("---")
                    new_folder_name = st.text_input(
                        "New Folder Name:",
                        value=folder_name,
                        key=f"new_name_{model_prefix}_{folder_name}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Save", key=f"save_{model_prefix}_{folder_name}"):
                            if new_folder_name and new_folder_name != folder_name:
                                if db.update_folder_name(model_prefix, folder_name, new_folder_name):
                                    st.success(f"Folder renamed successfully!")
                                    st.session_state[f"editing_{model_prefix}_{folder_name}"] = False
                                    st.rerun()
                                else:
                                    st.error("Failed to rename folder.")
                            else:
                                st.warning("Please enter a different folder name.")
                    with col2:
                        if st.button("✗ Cancel", key=f"cancel_{model_prefix}_{folder_name}"):
                            st.session_state[f"editing_{model_prefix}_{folder_name}"] = False
                            st.rerun()
                
                # Confirm delete folder
                if st.session_state.get(f"confirm_delete_folder_{model_prefix}_{folder_name}", False):
                    st.markdown("---")
                    st.warning(f"⚠️ Are you sure you want to delete the entire folder '{folder_name}'? This will delete {folder_data['count']} record(s).")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✓ Yes, Delete Folder", key=f"confirm_delete_{model_prefix}_{folder_name}", type="primary"):
                            deleted_count = db.delete_folder(model_prefix, folder_name)
                            st.success(f"Deleted folder '{folder_name}' ({deleted_count} records)")
                            st.session_state[f"confirm_delete_folder_{model_prefix}_{folder_name}"] = False
                            st.rerun()
                    with col2:
                        if st.button("✗ Cancel", key=f"cancel_delete_{model_prefix}_{folder_name}"):
                            st.session_state[f"confirm_delete_folder_{model_prefix}_{folder_name}"] = False
                            st.rerun()
                
                # Show individual records in this folder
                st.markdown("---")
                st.write("**Records in this folder:**")
                
                folder_chillers = db.get_chillers_by_folder(model_prefix, folder_name)
                if folder_chillers:
                    # Create a DataFrame for display
                    display_df = pd.DataFrame(folder_chillers)
                    
                    # Select columns to display
                    display_cols = ['id', 'model', 'capacity_tons', 'efficiency_kw_per_ton', 'waterflow_usgpm']
                    available_cols = [col for col in display_cols if col in display_df.columns]
                    
                    if available_cols:
                        # Display the table
                        st.dataframe(
                            display_df[available_cols],
                            width='stretch',
                            hide_index=True
                        )
                        
                        # Delete individual records
                        st.markdown("**Delete Individual Records:**")
                        delete_ids = st.multiselect(
                            f"Select records to delete from {folder_name}:",
                            options=display_df['id'].tolist(),
                            format_func=lambda x: f"{display_df[display_df['id']==x]['model'].iloc[0]} (ID: {x})",
                            key=f"delete_select_{model_prefix}_{folder_name}"
                        )
                        
                        if delete_ids:
                            if st.button(f"🗑️ Delete {len(delete_ids)} Selected Record(s)", key=f"delete_records_{model_prefix}_{folder_name}", type="primary"):
                                deleted_count = 0
                                for chiller_id in delete_ids:
                                    if db.delete_chiller(chiller_id):
                                        deleted_count += 1
                                
                                if deleted_count > 0:
                                    st.success(f"Successfully deleted {deleted_count} record(s)")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete records.")
                
                # Quick delete by ID
                st.markdown("---")
                st.write("**Quick Delete by ID:**")
                delete_id = st.number_input(
                    f"Enter record ID to delete from {folder_name}:",
                    min_value=1,
                    key=f"quick_delete_{model_prefix}_{folder_name}"
                )
                if st.button("Delete", key=f"quick_delete_btn_{model_prefix}_{folder_name}"):
                    # Verify the record belongs to this folder
                    chiller = db.get_chiller_by_id(delete_id)
                    if chiller and chiller.get('model_prefix') == model_prefix and chiller.get('folder_name') == folder_name:
                        if db.delete_chiller(delete_id):
                            st.success(f"Record ID {delete_id} deleted successfully")
                            st.rerun()
                        else:
                            st.error("Failed to delete record.")
                    else:
                        st.error(f"Record ID {delete_id} does not belong to this folder.")

if __name__ == "__main__":
    main()
