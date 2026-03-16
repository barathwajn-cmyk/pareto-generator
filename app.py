import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import textwrap
import time
from datetime import datetime
import re 

# --- PAGE SETUP ---
st.set_page_config(page_title="Auto Pareto Generator", layout="wide", page_icon="⚙️")

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
st.write("Connect live data or upload a file to instantly generate a crisp, high-definition Pareto chart.")

# --- DATA SOURCE TOGGLE ---
st.write("### Step 1: Choose Data Source")
data_source = st.radio("How do you want to import your data?", ["🔗 Live Google Sheet Link", "📁 Upload Excel/CSV File"], horizontal=True)

df = None 

try:
    if data_source == "🔗 Live Google Sheet Link":
        st.info("💡 **Instructions:** Go to your Google Sheet -> Click 'Share' -> Set to **'Anyone with the link can view'** -> Copy link and paste it below.")
        gsheet_url = st.text_input("Paste your live Google Sheet link here:")
        
        if gsheet_url:
            if "docs.google.com/spreadsheets" in gsheet_url:
                match = re.search(r'd/([a-zA-Z0-9-_]+)', gsheet_url)
                gid_match = re.search(r'gid=([0-9]+)', gsheet_url)
                
                if match:
                    sheet_id = match.group(1)
                    gid = gid_match.group(1) if gid_match else "0"
                    
                    csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                    
                    df = pd.read_csv(csv_export_url)
                    st.success("✅ Live Google Sheet connected successfully!")
                else:
                    st.error("🛑 That doesn't look like a valid Google Sheets link.")
            else:
                st.error("🛑 Please paste a valid Google Sheets URL.")

    else:
        uploaded_file = st.file_uploader("Upload your Excel or CSV file here", type=["csv", "xlsx", "xls"])
        
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                st.success("✅ CSV file loaded successfully!")
            else:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                
                if len(sheet_names) > 1:
                    selected_sheet = st.selectbox("📂 Your Excel file has multiple tabs. Select the one you want to use:", sheet_names)
                else:
                    selected_sheet = sheet_names[0]
                    
                df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
                st.success(f"✅ Excel Tab '{selected_sheet}' loaded successfully!")

    if df is not None:
        st.divider()
        
        # --- PARETO TYPE SELECTION ---
        st.write("### Step 2: Analysis Type & Pareto Title")
        pareto_category = st.text_input("What are you analyzing? This will become your Chart Title (e.g., Defect, Part, Machine, Scrap)", "Defect")
        
        st.divider()

        # --- OPTIONAL FILTERING ---
        st.write("### Step 3: Filter Data (Optional)")
        filter_col = st.selectbox("Filter by Column:", ["No Filter"] + list(df.columns))
        
        if filter_col != "No Filter":
            unique_values = df[filter_col].dropna().unique()
            filter_val = st.selectbox(f"Select the specific {filter_col} you want to look at:", unique_values)
            working_df = df[df[filter_col] == filter_val].copy()
            dynamic_prefix = str(filter_val)
        else:
            working_df = df.copy()
            dynamic_prefix = "Pricol" 
            
        # --- CHART DETAILS & SETTINGS ---
        st.write("### Step 4: Chart Settings")
        col_title, col_month = st.columns(2)
        with col_title:
            custom_title = st.text_input("Custom Title Prefix", dynamic_prefix)
        with col_month:
            current_date = datetime.now().strftime("%b %Y") 
            report_month = st.text_input("Month & Year", current_date) 
            
        col1, col2 = st.columns(2)
        with col1:
            category_col = st.selectbox(f"Column: {pareto_category} Names", working_df.columns)
        with col2:
            qty_col = st.selectbox("Column: Quantities (Must be numbers!)", working_df.columns)
            
        top_n = st.slider(f"How many top {pareto_category.lower()}s to show before grouping the rest into 'Others'?", min_value=5, max_value=40, value=25)
            
        # --- GENERATE CHART BUTTON ---
        if st.button("Generate Pareto Chart"):
            
            if working_df.empty:
                st.error("🛑 **Oops! There is no data for this specific filter.**")
            elif not pd.api.types.is_numeric_dtype(working_df[qty_col]):
                st.error(f"🛑 **Wait a second!** The column you chose for Quantities (`{qty_col}`) has text or words in it.")
            else:
                with st.spinner("Crunching the numbers and drawing the chart..."):
                    
                    working_df[qty_col] = working_df[qty_col].fillna(0).astype(int) 
                    processed_df = working_df.groupby(category_col)[qty_col].sum().reset_index()
                    processed_df = processed_df.sort_values(by=qty_col, ascending=False).reset_index(drop=True)
                    
                    if len(processed_df) > top_n:
                        top_df = processed_df.iloc[:top_n].copy()
                        others_qty = processed_df.iloc[top_n:][qty_col].sum()
                        others_df = pd.DataFrame({category_col: ['Others (Combined)'], qty_col: [others_qty]})
                        processed_df = pd.concat([top_df, others_df], ignore_index=True)
                    
                    raw_labels = processed_df[category_col].astype(str).tolist()
                    counts = processed_df[qty_col].tolist() 
                    labels = [textwrap.fill(label, width=25) for label in raw_labels]
                    
                    total_defects = sum(counts)
                    cumulative_counts = np.cumsum(counts)
                    cumulative_percent = (cumulative_counts / total_defects) * 100
                    
                    chart_title = f"{custom_title} - {report_month} {pareto_category.lower()} pareto"

                    def create_pareto_chart(highlight_80=False):
                        fig, ax1 = plt.subplots(figsize=(20, 7), dpi=300) 
                        
                        bar_colors = []
                        crossed_80 = False
                        for pct in cumulative_percent:
                            if highlight_80:
                                if not crossed_80:
                                    bar_colors.append('#4285F4') 
                                    if pct >= 80:
                                        crossed_80 = True
                                else:
                                    bar_colors.append('#CFD8DC') 
                            else:
                                bar_colors.append('#4285F4') 

                        bars = ax1.bar(labels, counts, color=bar_colors, width=0.6, label='SUM of Actual Quantity')
                        ax1.set_ylabel('') 
                        
                        max_val = max(counts) if counts else 10
                        ax1.set_ylim(0, max_val * 1.25) 
                        ax1.set_xticks(range(len(labels)))
                        ax1.set_xticklabels(labels, rotation=45, ha='right', rotation_mode='anchor', fontsize=13)
                        ax1.tick_params(axis='y', labelsize=13)

                        for idx, bar in enumerate(bars):
                            yval = int(bar.get_height())
                            text_color = bar_colors[idx]
                            if yval > 0:
                                ax1.text(bar.get_x() + bar.get_width()/2, yval + (max_val*0.02), f"{yval}", 
                                         ha='center', va='bottom', color=text_color, fontweight='bold', fontsize=12)

                        ax2 = ax1.twinx()
                        line_color = '#EA4335' 
                        ax2.plot(labels, cumulative_percent, color=line_color, linewidth=3, label='Cumm Rej %') 
                        
                        ax2.set_ylim(0, 115)
                        ax2.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
                        ax2.tick_params(axis='y', labelsize=13)

                        if highlight_80:
                            ax2.axhline(80, color='gray', linestyle='--', linewidth=1.5, alpha=0.6)
                            ax2.text(len(labels)-0.5, 82, "80% Cutoff", color='gray', ha='right', fontsize=12, style='italic')

                        for i in range(len(labels)):
                            pct_val = int(round(cumulative_percent[i]))
                            v_align = 'bottom' if pct_val > 90 else 'top'
                            y_offset = 2 if pct_val > 90 else -4 
                            ax2.text(i, cumulative_percent[i] + y_offset, f'{pct_val}%', 
                                     ha='center', va=v_align, color=line_color, fontweight='bold', fontsize=12)
                        
                        lines_1, labels_1 = ax1.get_legend_handles_labels()
                        lines_2, labels_2 = ax2.get_legend_handles_labels()
                        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False, fontsize=14)

                        plt.text(0.5, 1.25, chart_title, transform=ax1.transAxes, ha='center', fontsize=24, fontweight='bold')
                        
                        ax1.grid(axis='y', linestyle='-', alpha=0.3) 
                        ax1.spines['top'].set_visible(False)
                        ax2.spines['top'].set_visible(False)
                        ax1.yaxis.set_major_locator(mtick.MaxNLocator(integer=True))

                        plt.tight_layout()
                        return fig

                    fig_normal = create_pareto_chart(highlight_80=False)
                    fig_highlighted = create_pareto_chart(highlight_80=True)
                    
                    time.sleep(0.5) 
                    
                    tab1, tab2 = st.tabs(["📊 Normal View", "🎯 80% Highlighted View"])
                    
                    with tab1:
                        st.pyplot(fig_normal)
                        
                    with tab2:
                        st.pyplot(fig_highlighted)
                        st.info("💡 **Pro Tip:** In this view, the bars that contribute to the top 80% of your total volume are highlighted in blue. The 'trivial many' are grayed out.")
                    
                    st.toast(f"{pareto_category} Pareto generated successfully.", icon="✅")

except Exception as e:
    st.error("🛑 **Something went wrong while connecting to your data!**")
    st.warning(f"👉 **How to fix it:** If you are using a Google Sheet, make sure you clicked 'Share' and set it to 'Anyone with the link can view'. \n\n *(Technical error: {e})*")
