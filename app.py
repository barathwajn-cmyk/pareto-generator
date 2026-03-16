import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import textwrap

# --- PAGE SETUP ---
st.set_page_config(page_title="Auto Pareto Generator", layout="centered", page_icon="📊")
st.title("📊 Auto Pareto Chart Generator")
st.write("Upload your defect data to instantly generate a clean Pareto chart.")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read the file
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("File uploaded successfully!")
        
        # --- CHART DETAILS & SETTINGS ---
        st.write("### 1. Chart Details")
        col_title1, col_title2 = st.columns(2)
        with col_title1:
            report_month = st.text_input("Month & Year", "Feb 2024")
        with col_title2:
            vendor_name = st.text_input("Vendor / Project Name", "Pricol")
            
        st.write("### 2. Data Settings")
        col1, col2 = st.columns(2)
        with col1:
            defect_col = st.selectbox("Column: Defect Names", df.columns)
        with col2:
            qty_col = st.selectbox("Column: Quantities", df.columns)
            
        # Slider to group the "long tail" of data
        top_n = st.slider("How many top defects to show before grouping into 'Others'?", min_value=5, max_value=30, value=15)
            
        # --- GENERATE CHART BUTTON ---
        if st.button("Generate Pareto Chart"):
            
            # 1. Data Processing
            # Group by defect and sum
            processed_df = df.groupby(defect_col)[qty_col].sum().reset_index()
            # Sort from highest to lowest
            processed_df = processed_df.sort_values(by=qty_col, ascending=False).reset_index(drop=True)
            
            # 2. Group into "Others" based on slider
            if len(processed_df) > top_n:
                top_df = processed_df.iloc[:top_n].copy()
                others_qty = processed_df.iloc[top_n:][qty_col].sum()
                others_df = pd.DataFrame({defect_col: ['Others (Combined)'], qty_col: [others_qty]})
                processed_df = pd.concat([top_df, others_df], ignore_index=True)
            
            # Extract data for plotting
            raw_labels = processed_df[defect_col].astype(str).tolist()
            counts = processed_df[qty_col].tolist()
            
            # TEXT WRAPPING: Break long labels into multiple lines (max 12 chars wide)
            labels = [textwrap.fill(label, width=12) for label in raw_labels]
            
            # Calculate cumulative percentages
            total_defects = sum(counts)
            cumulative_counts = np.cumsum(counts)
            cumulative_percent = (cumulative_counts / total_defects) * 100

            # 3. Chart Generation (Backend)
            fig, ax1 = plt.subplots(figsize=(16, 8)) # Made chart slightly wider

            # Bar Chart (Actual Quantity)
            bar_color = '#4285F4' 
            bars = ax1.bar(labels, counts, color=bar_color, width=0.6, label='Actual Quantity')
            ax1.set_ylabel('Quantity', color='black', fontsize=12)
            
            max_val = max(counts)
            ax1.set_ylim(0, max_val * 1.15) 
            ax1.set_xticks(range(len(labels)))
            
            # Apply the text-wrapped labels, rotated slightly for better fit
            ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)

            # Add values on top of bars
            for bar in bars:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval + (max_val*0.01), int(yval), 
                         ha='center', va='bottom', color=bar_color, fontweight='bold', fontsize=10)

            # Line Chart (Cumulative Percentage)
            ax2 = ax1.twinx()
            line_color = '#EA4335' 
            ax2.plot(labels, cumulative_percent, color=line_color, marker='o', linewidth=2.5, label='Cumm Rej %')
            ax2.set_ylim(0, 110)
            ax2.yaxis.set_major_formatter(mtick.PercentFormatter())

            # Add percentage labels to the line chart
            for i in range(len(labels)):
                ax2.text(i, cumulative_percent[i] + 2, f'{cumulative_percent[i]:.1f}%', 
                         ha='center', va='bottom', color=line_color, fontweight='bold', fontsize=9)

            # DYNAMIC TITLE
            chart_title = f"{vendor_name} - Defect Pareto Analysis ({report_month})"
            plt.title(chart_title, fontsize=18, fontweight='bold', pad=20)
            
            # Formatting
            ax1.grid(axis='y', linestyle='--', alpha=0.6)
            ax1.spines['top'].set_visible(False)
            ax2.spines['top'].set_visible(False)

            # Legend
            lines_1, labels_1 = ax1.get_legend_handles_labels()
            lines_2, labels_2 = ax2.get_legend_handles_labels()
            ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', bbox_to_anchor=(1.05, 1))

            plt.tight_layout()
            
            # 4. Display Chart
            st.pyplot(fig)
            
    except Exception as e:
        st.error(f"Oops! Something went wrong reading the file. Error: {e}")
