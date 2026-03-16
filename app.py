import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import textwrap
import time

# --- PAGE SETUP ---
st.set_page_config(page_title="Auto Pareto Generator", layout="centered", page_icon="⚙️")

# --- SECURITY GATE (PASSWORD) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Access Restricted")
    st.write("Please enter the access key to use the Pareto Generator.")
    pwd = st.text_input("Access Key:", type="password")
    
    if st.button("Login"):
        if pwd == "Pricol2024!": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect access key. Please try again.")
    st.stop() 

# --- MAIN APP LOGIC ---
st.title("⚙️ Auto Pareto Chart Generator")
st.write("Upload your data to instantly generate a clean Pareto chart.")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your Excel or CSV file here", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        # --- SHEET SELECTION LOGIC ---
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.success("CSV file loaded successfully!")
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox("📂 Your Excel file has multiple tabs. Select the one you want to use:", sheet_names)
            else:
                selected_sheet = sheet_names[0]
                
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            st.success(f"Excel Tab '{selected_sheet}' loaded successfully!")
        
        st.divider()
        
        # --- PARETO TYPE SELECTION ---
        st.write("### 1. Analysis Type")
        pareto_type = st.radio(
            "What type of Pareto are you generating?",
            ["Defect Pareto", "Part Pareto"],
            horizontal=True
        )
        
        category_label = "Defect" if pareto_type == "Defect Pareto" else "Part"
        
        st.divider()

        # --- OPTIONAL FILTERING (SECOND-LEVEL PARETO) ---
        st.write("### 2. Filter Data (Optional)")
        st.write("Want to look at just one specific vendor or part? Select a column here to filter the data.")
        
        filter_col = st.selectbox("Filter by Column:", ["No Filter"] + list(df.columns))
        
        if filter_col != "No Filter":
            unique_values = df[filter_col].dropna().unique()
            filter_val = st.selectbox(f"Select the specific {filter_col} you want to look at:", unique_values)
            working_df = df[df[filter_col] == filter_val].copy()
            dynamic_prefix = str(filter_val)
        else:
            working_df = df.copy()
            dynamic_prefix = "Overall"
            
        # --- CHART DETAILS & SETTINGS ---
        st.write("### 3. Chart Settings")
        col_title, col_month = st.columns(2)
        with col_title:
            custom_title = st.text_input("Custom Title (Shows at the top of the chart)", dynamic_prefix)
        with col_month:
            report_month = st.text_input("Month & Year", "Feb 2024")
            
        col1, col2 = st.columns(2)
        with col1:
            category_col = st.selectbox(f"Column: {category_label} Names", working_df.columns)
        with col2:
            qty_col = st.selectbox("Column: Quantities (Must be numbers!)", working_df.columns)
            
        top_n = st.slider(f"How many top {category_label.lower()}s to show before grouping the rest into 'Others'?", min_value=5, max_value=35, value=15)
            
        # --- GENERATE CHART BUTTON ---
        if st.button("Generate Pareto Chart"):
            
            if working_df.empty:
                st.error("🛑 **Oops! There is no data for this specific filter.**")
                st.warning("👉 **How to fix it:** Try selecting a different filter in Step 2, or change it back to 'No Filter'.")
            
            # --- LAYMAN-PROOF DATA VALIDATION ---
            elif not pd.api.types.is_numeric_dtype(working_df[qty_col]):
                st.error(f"🛑 **Wait a second!** The column you chose for Quantities (`{qty_col}`) has text or words in it.")
                st.warning("👉 **How to fix it:** Go to 'Step 3: Chart Settings' above. Change the **'Column: Quantities'** box to a column that only has numbers (like 1, 5, 144) so the chart can do the math.")
            
            else:
                with st.spinner("Crunching the numbers and drawing the chart..."):
                    
                    # 1. Data Processing
                    processed_df = working_df.groupby(category_col)[qty_col].sum().reset_index()
                    processed_df = processed_df.sort_values(by=qty_col, ascending=False).reset_index(drop=True)
                    
                    # 2. Group into "Others"
                    if len(processed_df) > top_n:
                        top_df = processed_df.iloc[:top_n].copy()
                        others_qty = processed_df.iloc[top_n:][qty_col].sum()
                        others_df = pd.DataFrame({category_col: ['Others (Combined)'], qty_col: [others_qty]})
                        processed_df = pd.concat([top_df, others_df], ignore_index=True)
                    
                    raw_labels = processed_df[category_col].astype(str).tolist()
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

                    chart_title = f"{custom_title} - {pareto_type} Analysis ({report_month})"
                    plt.title(chart_title, fontsize=18, fontweight='bold', pad=20)
                    
                    ax1.grid(axis='y', linestyle='--', alpha=0.6)
                    ax1.spines['top'].set_visible(False)
                    ax2.spines['top'].set_visible(False)

                    lines_1, labels_1 = ax1.get_legend_handles_labels()
                    lines_2, labels_2 = ax2.get_legend_handles_labels()
                    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', bbox_to_anchor=(1.05, 1))

                    plt.tight_layout()
                    
                    time.sleep(0.5) 
                    
                    # 4. Display Chart
                    st.pyplot(fig)
                    
                    st.toast(f"{pareto_type} generated successfully.", icon="✅")
                
    except Exception as e:
        st.error("🛑 **Something went wrong while reading your file!**")
        st.warning(f"👉 **How to fix it:** Make sure your Excel sheet doesn't have merged cells or completely blank rows at the very top. \n\n *(Technical error: {e})*")
