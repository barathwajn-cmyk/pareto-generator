import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import textwrap
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Auto Pareto Generator", layout="centered", page_icon="⚙️")
st.title("⚙️ Auto Pareto Chart Generator")
st.write("Upload your defect data to instantly generate a clean Pareto chart.")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        # --- SHEET SELECTION LOGIC ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.success("CSV file loaded.")
        else:
            # Read the Excel file metadata to find the sheets
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            
            # If there are multiple sheets, show a dropdown
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox("📂 Select Excel Tab/Sheet:", sheet_names)
            else:
                selected_sheet = sheet_names[0]
                
            # Load the specific sheet chosen by the user
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.success(f"Sheet '{selected_sheet}' loaded.")
        
        st.divider() # Adds a clean horizontal line
        
        # --- OPTIONAL FILTERING (SECOND-LEVEL PARETO) ---
        st.write("### 1. Filter Data (Optional)")
        st.write("Select a column to filter by a specific Vendor, Part, or Line.")
        
        filter_col = st.selectbox("Filter by Column:", ["No Filter"] + list(df.columns))
        
        if filter_col != "No Filter":
            unique_values = df[filter_col].dropna().unique()
            filter_val = st.selectbox(f"Select the specific {filter_col} to analyze:", unique_values)
            working_df = df[df[filter_col] == filter_val].copy()
            dynamic_prefix = str(filter_val)
        else:
            working_df = df.copy()
            dynamic_prefix = "Overall"
            
        # --- CHART DETAILS & SETTINGS ---
        st.write("### 2. Chart Settings")
        col_title, col_month = st.columns(2)
        with col_title:
            custom_title = st.text_input("Custom Title Prefix", dynamic_prefix)
        with col_month:
            report_month = st.text_input("Month & Year", "Feb 2024")
            
        col1, col2 = st.columns(2)
        with col1:
            defect_col = st.selectbox("Column: Defect Names", working_df.columns)
        with col2:
            qty_col = st.selectbox("Column: Quantities", working_df.columns)
            
        top_n = st.slider("Top defects to show before grouping into 'Others'", min_value=5, max_value=35, value=15)
            
        # --- GENERATE CHART BUTTON ---
        if st.button("Generate Pareto Chart"):
            
            if working_df.empty:
                st.warning("No data found for this selection! Please adjust your filters.")
            else:
                # Mechanical loading spinner
                with st.spinner("Processing data and generating chart..."):
                    
                    # 1. Data Processing
                    processed_df = working_df.groupby(defect_col)[qty_col].sum().reset_index()
                    processed_df = processed_df.sort_values(by=qty_col, ascending=False).reset_index(drop=True)
                    
                    # 2. Group into "Others"
                    if len(processed_df) > top_n:
                        top_df = processed_df.iloc[:top_n].copy()
                        others_qty = processed_df.iloc[top_n:][qty_col].sum()
                        others_df = pd.DataFrame({defect_col: ['Others (Combined)'], qty_col: [others_qty]})
                        processed_df = pd.concat([top_df, others_df], ignore_index=True)
                    
                    raw_labels = processed_df[defect_col].astype(str).tolist()
                    counts = processed_df[qty_col].tolist()
                    
                    labels = [textwrap.fill(label, width=18) for label in raw_labels]
                    
                    total_defects = sum(counts)
                    cumulative_counts = np.cumsum(counts)
                    cumulative_percent = (cumulative_counts / total_defects) * 100

                    # 3. Chart Generation 
                    fig, ax1 = plt.subplots(figsize=(18, 8)) 

                    bar_color = '#4285F4' 
                    bars = ax1.bar(labels, counts, color=bar_color, width=0.6, label='Actual Quantity')
                    ax1.set_ylabel('Quantity', color='black', fontsize=12)
                    
                    max_val = max(counts) if counts else 10
                    ax1.set_ylim(0, max_val * 1.15) 
                    ax1.set_xticks(range(len(labels)))
                    ax1.set_xticklabels(labels, rotation=65, ha='right', rotation_mode='anchor', fontsize=8)

                    for bar in bars:
                        yval = bar.get_height()
                        if yval > 0:
                            ax1.text(bar.get_x() + bar.get_width()/2, yval + (max_val*0.01), int(yval), 
                                     ha='center', va='bottom', color=bar_color, fontweight='bold', fontsize=9)

                    ax2 = ax1.twinx()
                    line_color = '#EA4335' 
                    ax2.plot(labels, cumulative_percent, color=line_color, marker='o', linewidth=2.5, label='Cumm Rej %')
                    ax2.set_ylim(0, 110)
                    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

                    for i in range(len(labels)):
                        ax2.text(i, cumulative_percent[i] + 2, f'{cumulative_percent[i]:.1f}%', 
                                 ha='center', va='bottom', color=line_color, fontweight='bold', fontsize=8)

                    chart_title = f"{custom_title} - Defect Pareto Analysis ({report_month})"
                    plt.title(chart_title, fontsize=18, fontweight='bold', pad=20)
                    
                    ax1.grid(axis='y', linestyle='--', alpha=0.6)
                    ax1.spines['top'].set_visible(False)
                    ax2.spines['top'].set_visible(False)

                    lines_1, labels_1 = ax1.get_legend_handles_labels()
                    lines_2, labels_2 = ax2.get_legend_handles_labels()
                    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', bbox_to_anchor=(1.05, 1))

                    plt.tight_layout()
                    
                    # Simulate a brief mechanical processing time if the data is very small
                    time.sleep(0.5) 
                    
                    # 4. Display Chart
                    st.pyplot(fig)
                    
                    # Subtle confirmation notification
                    st.toast("Pareto analysis complete.", icon="⚙️")
                
    except Exception as e:
        st.error(f"Error processing the file. Please check the data format. Error details: {e}")
