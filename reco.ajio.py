import streamlit as st
import pandas as pd
import base64
import io

# --- यह फ़ंक्शन डाउनलोड लिंक बनाने के लिए है ---
def get_csv_download_link(df, filename="reconciliation_report.csv"):
    """
    Generates a link to download the DataFrame as a CSV file.
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Reconciliation Report डाउनलोड करें (.csv)</a>'
    return href

# --- मुख्य ऐप ---
st.set_page_config(layout="wide") # पेज को चौड़ा करने के लिए
st.title("🛍️ Ajio Seller Reconciliation Tool")
st.write("अपने तीनों रिपोर्ट (GST, RTV, Payment) अपलोड करें और यह टूल उन्हें रिकन्साइल (reconcile) कर देगा।")

# --- 1. फ़ाइल अपलोडर्स ---
st.header("1. अपनी रिपोर्ट्स अपलोड करें")
col1, col2, col3 = st.columns(3)

with col1:
    gst_file = st.file_uploader("1. GST Report", type=["csv", "xlsx"])

with col2:
    rtv_file = st.file_uploader("2. RTV Report", type=["csv", "xlsx"])

with col3:
    payment_file = st.file_uploader("3. Payment Report", type=["csv", "xlsx"])


# --- 2. रिकॉन्सिलिएशन प्रोसेस ---
if gst_file and rtv_file and payment_file:
    
    if st.button("🚀 रिकॉन्सिलिएशन शुरू करें", type="primary"):
        try:
            # --- डेटा पढ़ें (Excel या CSV) ---
            df_gst = pd.read_excel(gst_file) if gst_file.name.endswith('xlsx') else pd.read_csv(gst_file)
            df_rtv = pd.read_excel(rtv_file) if rtv_file.name.endswith('xlsx') else pd.read_csv(rtv_file)
            df_payment = pd.read_excel(payment_file) if payment_file.name.endswith('xlsx') else pd.read_csv(payment_file)

            st.success("तीनों फ़ाइलें सफलतापूर्वक लोड हो गईं!")

            # --- स्टेप 1: GST रिपोर्ट प्रोसेस करें ---
            # 'Cust Order No' से ग्रुप करें और 'Shipped QTY' व 'Total Price' का जोड़ निकालें
            st.write("Processing GST Report...")
            gst_summary = df_gst.groupby('Cust Order No').agg(
                Total_Shipped_QTY=('Shipped QTY', 'sum'),
                Total_Sales_Value=('Total Price', 'sum')
            ).reset_index().rename(columns={'Cust Order No': 'Order ID'})

            # --- स्टेप 2: RTV रिपोर्ट प्रोसेस करें ---
            # 'Cust Order No' से ग्रुप करें और 'Return QTY' व 'Return Value' का जोड़ निकालें
            st.write("Processing RTV Report...")
            rtv_summary = df_rtv.groupby('Cust Order No').agg(
                Total_Return_QTY=('Return QTY', 'sum'),
                Total_Return_Value=('Return Value', 'sum')
            ).reset_index().rename(columns={'Cust Order No': 'Order ID'})

            # --- स्टेप 3: Payment रिपोर्ट प्रोसेस करें (सबसे ज़रूरी) ---
            # यहां हम यह मान रहे हैं कि 'Payment' रिपोर्ट में 'Order No' कॉलम है
            # और 'Value' कॉलम में बिक्री के लिए पॉजिटिव (+) अमाउंट और रिटर्न के लिए नेगेटिव (-) अमाउंट है।
            st.write("Processing Payment Report...")
            payment_summary = df_payment.groupby('Order No').agg(
                Net_Payment_Received=('Value', 'sum')
            ).reset_index().rename(columns={'Order No': 'Order ID'})
            
            st.warning("""
            ** ज़रूरी नोट:** हमने यह माना है कि 'Payment Report' में:
            1.  `Order No` कॉलम सेल्स और रिटर्न दोनों के लिए इस्तेमाल होता है।
            2.  `Value` कॉलम में सेल्स के लिए पेमेंट (पॉजिटिव) और रिटर्न के लिए डिडक्शन (नेगेटिव) शामिल है।
            """)

            # --- स्टेप 4: तीनों डेटा को एक साथ मर्ज करें ---
            st.write("Merging all reports...")
            # GST समरी से शुरू करें (यह हमारा मास्टर है)
            df_recon = pd.merge(gst_summary, rtv_summary, on='Order ID', how='left')
            # पेमेंट समरी को मर्ज करें
            df_recon = pd.merge(df_recon, payment_summary, on='Order ID', how='left')

            # --- स्टेप 5: कैलकुलेशन और सफ़ाई ---
            # जो ऑर्डर RTV या Payment में नहीं मिले, उनके लिए 0 भरें
            df_recon = df_recon.fillna(0)

            # (मेरी तरफ़ से एडिशन) - असली रिकॉन्सिलिएशन
            # आपको कितना पैसा मिलना चाहिए था = (कुल बिक्री - कुल रिटर्न)
            df_recon['Expected_Net_Payment'] = df_recon['Total_Sales_Value'] - df_recon['Total_Return_Value']
            
            # कितना पैसा कम या ज़्यादा मिला = (कितना मिला - कितना मिलना चाहिए था)
            df_recon['Difference'] = df_recon['Net_Payment_Received'] - df_recon['Expected_Net_Payment']

            # --- स्टेप 6: फ़ाइनल रिपोर्ट दिखाएं ---
            st.header("📊 रिकॉन्सिलिएशन समरी (Summary)")
            
            # (मेरी तरफ़ से एडिशन) - मुख्य आंकड़े
            total_sales = df_recon['Total_Sales_Value'].sum()
            total_returns = df_recon['Total_Return_Value'].sum()
            expected_total = df_recon['Expected_Net_Payment'].sum()
            total_received = df_recon['Net_Payment_Received'].sum()
            total_difference = df_recon['Difference'].sum()

            sum_col1, sum_col2, sum_col3 = st.columns(3)
            sum_col1.metric("1. कुल बिक्री (GST Report)", f"₹ {total_sales:,.2f}")
            sum_col2.metric("2. कुल रिटर्न (RTV Report)", f"₹ {total_returns:,.2f}")
            sum_col3.metric("3. कुल मिली पेमेंट (Payment Report)", f"₹ {total_received:,.2f}")
            
            st.divider()

            sum_col4, sum_col5 = st.columns(2)
            sum_col4.metric("4. अपेक्षित पेमेंट (बिक्री - रिटर्न)", f"₹ {expected_total:,.2f}")
            sum_col5.metric("5. फ़ाइनल अंतर (Difference)", f"₹ {total_difference:,.2f}", 
                            help="यह बताता है कि आपको कितना पैसा कम (नेगेटिव) या ज़्यादा (पॉजिटिव) मिला है।")

            st.header("📄 फ़ाइनल रिकॉन्सिलिएशन रिपोर्ट")
            st.dataframe(df_recon)
            
            # डाउनलोड लिंक
            st.markdown(get_csv_download_link(df_recon), unsafe_allow_html=True)

        except Exception as e:
            st.error(f"एक एरर आया: {e}")
            st.error("कृपया अपनी फ़ाइलों के कॉलम नाम (Headers) दोबारा चेक करें।")
            st.error(f"GST में 'Cust Order No', 'Shipped QTY', 'Total Price' होना चाहिए।")
            st.error(f"RTV में 'Cust Order No', 'Return QTY', 'Return Value' होना चाहिए।")
            st.error(f"Payment में 'Order No', 'Value' होना चाहिए।")
