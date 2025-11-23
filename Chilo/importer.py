import pandas as pd
import re
from typing import List, Dict, Any, Tuple, Optional
from io import StringIO
import streamlit as st
from utils import (
    parse_dimensions, parse_pressure_drop, safe_float, safe_int, 
    normalize_header, clean_model_name, validate_chiller_data
)

def detect_delimiter(text: str) -> str:
    """Detect the delimiter used in the table (tab, comma, or multiple spaces)."""
    lines = text.strip().split('\n')
    if not lines:
        return '\t'
    
    # Count occurrences of different delimiters in the first few lines
    sample_lines = lines[:3]
    tab_count = sum(line.count('\t') for line in sample_lines)
    comma_count = sum(line.count(',') for line in sample_lines)
    space_count = sum(len(re.findall(r'\s{2,}', line)) for line in sample_lines)
    
    if tab_count > comma_count and tab_count > space_count:
        return '\t'
    elif comma_count > space_count:
        return ','
    else:
        return r'\s{2,}'  # Multiple spaces

def parse_table_text(text: str, ambient_f: Optional[int] = None, 
                    ewt_c: Optional[float] = None, lwt_c: Optional[float] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse table text and return a DataFrame with parsed data.
    Returns (DataFrame, list_of_errors)
    """
    errors = []
    
    if not text.strip():
        return pd.DataFrame(), ["No data provided"]
    
    # Detect delimiter
    delimiter = detect_delimiter(text)
    
    try:
        # Read the table
        if delimiter == r'\s{2,}':
            # For multiple spaces, use a more flexible approach
            df = pd.read_csv(StringIO(text), sep=r'\s+', engine='python')
        else:
            df = pd.read_csv(StringIO(text), sep=delimiter, engine='python')
        
        if df.empty:
            return df, ["No data could be parsed from the input"]
        
        # Clean column names but preserve order
        original_columns = list(df.columns)
        normalized_columns = [normalize_header(col) for col in df.columns]
        
        # Map known columns to database fields
        column_mapping = {
            'model': 'model',
            'tons': 'capacity_tons',
            'efficiency_kw_per_ton': 'efficiency_kw_per_ton',
            'iplv_kw_per_ton': 'iplv_kw_per_ton',
            'waterflow_usgpm': 'waterflow_usgpm',
            'unit_kw': 'unit_kw',
            'compressor_kw': 'compressor_kw',
            'fan_kw': 'fan_kw',
            'pressure_drop': 'pressure_drop',
            'mca_amps': 'mca_amps',
            'dimensions': 'dimensions'
        }
        
        # Create new column names, preserving original order
        new_columns = []
        for i, col in enumerate(normalized_columns):
            if col in column_mapping:
                new_columns.append(column_mapping[col])
            else:
                # Keep original column name for unmapped columns
                new_columns.append(original_columns[i])
        
        # Apply the new column names
        df.columns = new_columns
        
        # Add batch-assigned values
        if ambient_f is not None:
            df['ambient_f'] = ambient_f
        if ewt_c is not None:
            df['ewt_c'] = ewt_c
        if lwt_c is not None:
            df['lwt_c'] = lwt_c
        
        # Extract model prefix for each row and generate folder name
        from utils import extract_model_prefix
        
        # Generate folder name based on ambient and temperatures (used as subfolder)
        if ambient_f is not None and ewt_c is not None and lwt_c is not None:
            df['folder_name'] = f"{ambient_f}°F {ewt_c}°C/{lwt_c}°C"
        elif ambient_f is not None:
            df['folder_name'] = f"{ambient_f}°F"
        else:
            df['folder_name'] = "Unknown"
        
        # Extract model prefix for each row
        if 'model' in df.columns:
            df['model_prefix'] = df['model'].apply(lambda x: extract_model_prefix(str(x)) if pd.notna(x) else None)
        else:
            df['model_prefix'] = None
        
        # Parse special fields
        df = parse_special_fields(df, errors)
        
        # Ensure model column is first if it exists (after all processing)
        if 'model' in df.columns:
            # Get all columns except model
            other_columns = [col for col in df.columns if col != 'model']
            # Reorder with model first
            df = df[['model'] + other_columns]
        
        # Clean and validate data
        validated_rows = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            cleaned_data, row_errors = validate_chiller_data(row_dict)
            if row_errors:
                errors.extend([f"Row {idx + 1}: {error}" for error in row_errors])
            validated_rows.append(cleaned_data)
        
        # Convert back to DataFrame
        if validated_rows:
            result_df = pd.DataFrame(validated_rows)
            
            # Preserve the column order from the original DataFrame
            if not df.empty:
                # Get the column order from the original DataFrame
                original_order = list(df.columns)
                # Reorder the result DataFrame to match
                available_columns = [col for col in original_order if col in result_df.columns]
                result_df = result_df[available_columns]
        else:
            result_df = pd.DataFrame()
        
        return result_df, errors
        
    except Exception as e:
        errors.append(f"Error parsing table: {str(e)}")
        return pd.DataFrame(), errors

def parse_special_fields(df: pd.DataFrame, errors: List[str]) -> pd.DataFrame:
    """Parse special fields like dimensions and pressure drop."""
    
    # Parse dimensions
    if 'dimensions' in df.columns:
        dimensions_data = []
        for idx, dim_str in df['dimensions'].items():
            if pd.isna(dim_str):
                dimensions_data.append({'length_in': None, 'width_in': None, 'height_in': None})
            else:
                length, width, height = parse_dimensions(str(dim_str))
                dimensions_data.append({
                    'length_in': length,
                    'width_in': width,
                    'height_in': height
                })
        
        # Add dimension columns
        dim_df = pd.DataFrame(dimensions_data)
        for col in ['length_in', 'width_in', 'height_in']:
            df[col] = dim_df[col]
    
    # Parse pressure drop
    if 'pressure_drop' in df.columns:
        pressure_data = []
        for idx, pressure_str in df['pressure_drop'].items():
            if pd.isna(pressure_str):
                pressure_data.append({'pressure_drop_psi': None, 'pressure_drop_ftwg': None})
            else:
                psi, ftwg = parse_pressure_drop(str(pressure_str))
                pressure_data.append({
                    'pressure_drop_psi': psi,
                    'pressure_drop_ftwg': ftwg
                })
        
        # Add pressure drop columns
        pressure_df = pd.DataFrame(pressure_data)
        for col in ['pressure_drop_psi', 'pressure_drop_ftwg']:
            df[col] = pressure_df[col]
    
    return df

def import_chillers_from_dataframe(df: pd.DataFrame, db_module) -> Tuple[int, List[str]]:
    """
    Import chillers from a DataFrame into the database.
    Returns (number_imported, list_of_errors)
    """
    if df.empty:
        return 0, ["No data to import"]
    
    errors = []
    imported_count = 0
    
    try:
        # Convert DataFrame to list of dictionaries
        chillers_data = df.to_dict('records')
        
        # Import in batches
        batch_size = 50
        for i in range(0, len(chillers_data), batch_size):
            batch = chillers_data[i:i + batch_size]
            try:
                # Clean and validate each record before importing
                cleaned_batch = []
                for record in batch:
                    from utils import validate_chiller_data
                    cleaned_data, record_errors = validate_chiller_data(record)
                    if record_errors:
                        errors.extend([f"Record validation error: {error}" for error in record_errors])
                    cleaned_batch.append(cleaned_data)
                
                if cleaned_batch:
                    db_module.batch_insert_chillers(cleaned_batch)
                    imported_count += len(cleaned_batch)
                else:
                    errors.append(f"No valid records in batch {i//batch_size + 1}")
                    
            except Exception as e:
                error_msg = f"Error importing batch {i//batch_size + 1}: {str(e)}"
                errors.append(error_msg)
        
        return imported_count, errors
        
    except Exception as e:
        error_msg = f"Error during import: {str(e)}"
        errors.append(error_msg)
        return imported_count, errors

def preview_parsed_data(df: pd.DataFrame) -> None:
    """Display a preview of the parsed data in Streamlit."""
    if df.empty:
        st.warning("No data to preview")
        return
    
    st.subheader("Preview of Parsed Data")
    
    # Show basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", len(df))
    with col2:
        st.metric("Columns", len(df.columns))
    with col3:
        required_fields = ['model', 'capacity_tons', 'efficiency_kw_per_ton']
        missing_required = sum(1 for field in required_fields if field not in df.columns or df[field].isna().all())
        st.metric("Missing Required", missing_required)
    
    # Show the data table
    st.dataframe(df, use_container_width=True)
    
    # Show column mapping info
    with st.expander("Column Mapping Details"):
        st.write("**Mapped columns:**")
        mapped_cols = [col for col in df.columns if col in [
            'model', 'capacity_tons', 'efficiency_kw_per_ton', 'iplv_kw_per_ton',
            'waterflow_usgpm', 'unit_kw', 'compressor_kw', 'fan_kw',
            'pressure_drop_psi', 'pressure_drop_ftwg', 'mca_amps',
            'length_in', 'width_in', 'height_in', 'ambient_f', 'ewt_c', 'lwt_c'
        ]]
        
        for col in mapped_cols:
            st.write(f"- {col}: {df[col].notna().sum()} non-null values")
        
        # Show unmapped columns
        unmapped = [col for col in df.columns if col not in mapped_cols and not col.startswith('Unnamed')]
        if unmapped:
            st.write("**Unmapped columns (will be stored in extras_json):**")
            for col in unmapped:
                st.write(f"- {col}")

def import_from_file(file_path: str, ambient_f: Optional[int] = None,
                    ewt_c: Optional[float] = None, lwt_c: Optional[float] = None) -> Tuple[int, List[str]]:
    """
    Import chillers from a file (CSV/TSV).
    Returns (number_imported, list_of_errors)
    """
    try:
        # Read the file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.tsv') or file_path.endswith('.txt'):
            df = pd.read_csv(file_path, sep='\t')
        else:
            # Try to detect delimiter
            with open(file_path, 'r') as f:
                sample = f.read(1024)
            delimiter = detect_delimiter(sample)
            df = pd.read_csv(file_path, sep=delimiter)
        
        # Clean column names
        df.columns = [normalize_header(col) for col in df.columns]
        
        # Add batch-assigned values
        if ambient_f is not None:
            df['ambient_f'] = ambient_f
        if ewt_c is not None:
            df['ewt_c'] = ewt_c
        if lwt_c is not None:
            df['lwt_c'] = lwt_c
        
        # Extract model prefix for each row and generate folder name
        from utils import extract_model_prefix
        
        # Generate folder name based on ambient and temperatures (used as subfolder)
        if ambient_f is not None and ewt_c is not None and lwt_c is not None:
            df['folder_name'] = f"{ambient_f}°F {ewt_c}°C/{lwt_c}°C"
        elif ambient_f is not None:
            df['folder_name'] = f"{ambient_f}°F"
        else:
            df['folder_name'] = "Unknown"
        
        # Extract model prefix for each row
        if 'model' in df.columns:
            df['model_prefix'] = df['model'].apply(lambda x: extract_model_prefix(str(x)) if pd.notna(x) else None)
        else:
            df['model_prefix'] = None
        
        # Parse special fields
        errors = []
        df = parse_special_fields(df, errors)
        
        # Clean and validate data
        validated_rows = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            cleaned_data, row_errors = validate_chiller_data(row_dict)
            if row_errors:
                errors.extend([f"Row {idx + 1}: {error}" for error in row_errors])
            validated_rows.append(cleaned_data)
        
        if not validated_rows:
            return 0, errors + ["No valid data found"]
        
        # Convert back to DataFrame and import
        result_df = pd.DataFrame(validated_rows)
        
        # Import to database
        from db import batch_insert_chillers
        try:
            batch_insert_chillers(validated_rows)
            return len(validated_rows), errors
        except Exception as e:
            return 0, errors + [f"Database error: {str(e)}"]
        
    except Exception as e:
        return 0, [f"File reading error: {str(e)}"]
