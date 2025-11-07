import streamlit as st
import pandas as pd
import base64
import io

# --- Function to create a download link ---
def get_csv_download_link(df, filename="reconciliation_report.csv"):
    """
    Generates a link to download the DataFrame as a CSV file.
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download Reconciliation Report (.csv)</a>'
    return href

# --- Main App ---
st.set_page_config(layout="wide") 
st.title("🛍️ Ajio Seller Reconciliation Tool")
st.write("Upload your three reports (GST, RTV, Payment). This tool will find all records and reconcile them.")

# --- 1. File Uploaders ---
st.header("1. Upload Your Reports")
col1, col2, col3 = st.columns(3)

with col1:
    gst_file = st.file_uploader("1. GST Report", type=["csv", "xlsx"])

with col2:
    rtv_file = st.file_uploader("2. RTV Report", type=["csv", "xlsx"])

with col3:
    payment_file = st.file_uploader("3. Payment Report", type=["csv", "xlsx"])


# --- 2. Reconciliation Process ---
if gst_file and rtv_file and payment_file:
    
    if st.button("🚀 Start Reconciliation", type="primary"):
        try:
            # --- Read Data (Excel or CSV) ---
            df_gst = pd.read_excel(gst_file) if gst_file.name.endswith('xlsx') else pd.read_csv(gst_file)
            df_rtv = pd.read_excel(rtv_file) if rtv_file.name.endswith('xlsx') else pd.read_csv(rtv_file)
            df_payment = pd.read_excel(payment_file) if payment_file.name.endswith('xlsx') else pd.read_csv(payment_file)

            st.success("All three files loaded successfully!")

            # --- Step 1: Process GST Report ---
            st.write("Processing GST Report...")
            
            # --- *** CHANGE HERE: Using 'Invoice Value' instead of 'Total Price' *** ---
            gst_summary = df_gst.groupby('Cust Order No').agg(
                Total_Shipped_QTY=('Shipped QTY', 'sum'),
                Total_Sales_Value=('Invoice Value', 'sum') 
            ).reset_index().rename(columns={'Cust Order No': 'Order ID'})

            # --- Step 2: Process RTV Report ---
            st.write("Processing RTV Report...")
            rtv_summary = df_rtv.groupby('Cust Order No').agg(
                Total_Return_QTY=('Return QTY', 'sum'),
                Total_Return_Value=('Return Value', 'sum')
            ).reset_index().rename(columns={'Cust Order No': 'Order ID'})

            # --- Step 3: Process Payment Report ---
            st.write("Processing Payment Report...")
            payment_summary = df_payment.groupby('Order No').agg(
                Net_Payment_Received=('Value', 'sum')
            ).reset_index().rename(columns={'Order No': 'Order ID'})
            
            st.warning("""
            **Important Note:** We have assumed that in the 'Payment Report':
            1.  The `Order No` column is used for both sales and returns.
            2.  The `Value` column includes payments for sales (positive) and deductions for returns (negative).
            """)

            # --- Step 4: Merge all three datasets ---
            st.write("Merging all reports...")
            # Use 'outer' merge to keep all records from GST and RTV
            df_recon = pd.merge(gst_summary, rtv_summary, on='Order ID', how='outer')
            # Use 'outer' merge again to include all payment records
            df_recon = pd.merge(df_recon, payment_summary, on='Order ID', how='outer')

            # --- Step 5: Calculations and Cleanup ---
            # Fill 0 for orders not found in other reports
            df_recon = df_recon.fillna(0)

            # (My Addition) - The actual reconciliation
            df_recon['Expected_Net_Payment'] = df_recon['Total_Sales_Value'] - df_recon['Total_Return_Value']
            df_recon['Difference'] = df_recon['Net_Payment_Received'] - df_recon['Expected_Net_Payment']

            # --- Step 6: Display the Final Report ---
            st.header("📊 Reconciliation Summary")
            
            total_sales = df_recon['Total_Sales_Value'].sum()
            total_returns = df_recon['Total_Return_Value'].sum()
            expected_total = df_recon['Expected_Net_Payment'].sum()
            total_received = df_recon['Net_Payment_Received'].sum()
            total_difference = df_recon['Difference'].sum()

            sum_col1, sum_col2, sum_col3 = st.columns(3)
            sum_col1.metric("1. Total Sales (from GST Report)", f"₹ {total_sales:,.2f}")
            sum_col2.metric("2. Total Returns (from RTV Report)", f"₹ {total_returns:,.2f}")
            sum_col3.metric("3. Total Payment Received (from Payment Report)", f"₹ {total_received:,.2f}")
            
            st.divider()

            sum_col4, sum_col5 = st.columns(2)
            sum_col4.metric("4. Expected Net Payment (Sales - Returns)", f"₹ {expected_total:,.2f}")
            sum_col5.metric("5. Final Difference", f"₹ {total_difference:,.2f}", 
                            help="This shows how much you were underpaid (negative) or overpaid (positive).")

            st.header("📄 Final Reconciliation Report")
            st.info("This report now includes all Order IDs found in any of the three files.")
            st.dataframe(df_recon)
            
            # Download link
            st.markdown(get_csv_download_link(df_recon), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error("Please double-check your file column names (Headers).")
            # --- *** CHANGE HERE: Updated error message *** ---
            st.error("GST report must contain 'Cust Order No', 'Shipped QTY', and 'Invoice Value'.")
            st.error("RTV report must contain 'Cust Order No', 'Return QTY', and 'Return Value'.")
            st.error("Payment report must contain 'Order No' and 'Value'.")
