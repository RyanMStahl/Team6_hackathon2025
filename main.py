import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import time
import Image
import seaborn as sns


application_guide_introduction      = "Welcome to Essential Sustainability Visibility! This guide will help you understand how to use the application effectively. Whether you're a new user or need a refresher, this document covers all the essential features and workflows."
application_guide_part1_title       = "#### **Integrated Data Presentation**"
application_guide_part1_description = "This application brings together operational metrics like energy, batches, performance issue alerts, utility summary, and baseline performance in a single place."
application_guide_part2_title       = "#### **Dynamic Data Visualization**"
application_guide_part2_description = "By combining instrumental data from various sources and analyzing relationships between them, users can get a big picture overview of Sherwin-William's operations."
application_guide_part3_title       = "#### **Historical Data Comparison**"
application_guide_part3             = "This application enables comparison of data with data obtained from historical averages to facilitate early detection of divergence from optimal performance."
application_guide_part4_title       = "#### **Alerting**"
application_guide_part4             = "Get alerts when operational metrics differ significantly from the baseline average and reduce the time required to recover from operational failures."
application_usage_guide_1_title     = "#### **Energy**"
application_usage_guide_1_text      = "Users can get an overview of energy consumption metrics like Power, Voltage, and Ampere for a particular asset in a location."
application_usage_guide_1_markdown  = """1. Select **Site** (manufacturing location) in the left navigation bar
2. Select **Name** for the asset
3. Click on **Energy** radio button \n
##### Graphs Overview
* **Power (KwH)** over time - power usage
* **Voltage** over time - voltage measured
* **Amperage** over time - amperage reading"""


application_usage_guide_2_title    = "#### **Volume**"
application_usage_guide_2_text     = "Users can get an overview of volume of paint produced by the batch ID"
application_usage_guide_2_markdown = """1. Select **Site** (manufacturing location) in the left navigation bar
2. Select **Name** for the asset (or select "overview" to get information about all the assets)
3. Click on **Volume** radio button \n
##### Graphs Overview
* **Volume (in gallons)** per batch (overview) - volume of paint produced in a single batch for all assets in the location
* **Volume (in gallons)** per batch (per asset) - volume of paint produced in a single batch for a particular location 
"""


application_usage_guide_3_title    = "#### **Alerts**"
application_usage_guide_3_text     = "Users can get an overview of reported data versus current threshold limits. This provides visual evidence if an alert is triggered"
application_usage_guide_3_markdown = """1. Select **Site** (manufacturing location) in the left navigation bar
2. Select **Name** for the asset (or select "overview" to get information about all the assets)
3. Click on **Alerts** radio button \n
##### Graphs Overview
* **Alerts** per asset - alerts produced per asset"""
application_usage_guide_4_title    = "#### **Billing Info**"
application_usage_guide_4_text     = ""
application_usage_guide_4_markdown = ""


application_usage_guide_5_title    = "#### **Comparison**"
application_usage_guide_5_text     = "Users can compare energy data for two different assets to analyze performance differences between the assets"
application_usage_guide_5_markdown = """1. Select **Site** (manufacturing location) at the top of the left navigation bar
2. Select **Name** for the asset
3. Click on **Comparison** radio button
4. Select **Site Option 2** (second manufacturing location) at the bottom of the left navigation bar
5. Select **Name Option 2** for the second asset \n
##### Graphs Overview
* **Power (KwH)** over time - power usage
* **Voltage** over time - voltage measured
* **Ampere** over time - ampere reading """



application_usage_guide_6_title    = "#### **Billing (Utility Summary)**"
application_usage_guide_6_text     = "Users can analyze utility summary reports on specific sites and assets"
application_usage_guide_6_markdown = """1. Select **Billing Info** (manufacturing location) at the top of the left navigation bar
##### Graphs Overview
* **Total Kw/H** over time - total energy usage over time for all currently available sites
* **Peak Kw/H** over time - highest recorded energy usage for all currently available sides
* **Average Kw/H** over time - average energy usage over time for all currently available sites 
* **Billing Amount** over time - billing amounts over time for all currently available sites
"""


def extract_asset_suffix(asset_name):
    return asset_name[-1]


def display_utility_summary(conn):
    st.title('Utility Summary Section')
    st.subheader("The following utility data includes all sites and all billing periods")

    # Load all data from utility_summary table
    sql_query = "SELECT * FROM utility_summary"
    utility_data = pd.read_sql_query(sql_query, conn)

    # Convert billing_period_start to datetime
    utility_data['billing_period_start'] = pd.to_datetime(utility_data['billing_period_start'])

    # Set seaborn style
    sns.set(style="whitegrid")

    # Metrics to plot
    metrics = ["total_kwh", "peak_kw", "average_kw", "billing_amount"]

    # Create subplots
    fig, axes = plt.subplots(len(metrics), 1, figsize=(12, 16), sharex=True)

    # Plot each metric
    for i, metric in enumerate(metrics):
        sns.lineplot(data=utility_data, x="billing_period_start", y=metric, hue="site", marker="o", ax=axes[i])
        axes[i].set_title(f"{metric.replace('_', ' ').title()} Over Time by Site")
        axes[i].set_ylabel(metric.replace('_', ' ').title())
        axes[i].set_xlabel("Billing Period Start")

    plt.tight_layout()
    st.pyplot(fig)


def display_alerts(alert_data, target_asset, selected_site, conn, data):
    if (len(target_asset) == 1) and (len(alert_data) != 0):
        if alert_data is not None:
            asset1_data = alert_data.copy()
            asset1_data['timestamp'] = pd.to_datetime(asset1_data['timestamp'])
            asset1_data = asset1_data.sort_values('timestamp')

            asset_name_map = {extract_asset_suffix(row['name']): row['name'] for _, row in data.iterrows()}
            asset_id = str(asset1_data['asset_id'].iloc[0])
            asset_name = asset_name_map.get(asset_id, f'Asset {asset_id}')

            for alert_type in asset1_data['alert_type'].unique():
                st.subheader(f"{alert_type} - {asset_name}")
                subset = asset1_data[asset1_data['alert_type'] == alert_type]

                fig, ax = plt.subplots(figsize=(10, 4))
                timestamps = subset['timestamp']
                values = subset['value']
                thresholds = subset['threshold']

                for i in range(len(subset)):
                    ts = timestamps.iloc[i]
                    val = values.iloc[i]
                    thresh = thresholds.iloc[i]
                    delta = pd.Timedelta(minutes=30)

                    ax.hlines(y=val, xmin=ts - delta, xmax=ts + delta, colors='blue',
                              label='Alert Value' if i == 0 else "", linewidth=2)
                    ax.hlines(y=thresh, xmin=ts - delta, xmax=ts + delta, colors='red', linestyles='--',
                              label='Threshold' if i == 0 else "", linewidth=2)

                    if val > thresh:
                        ax.fill_between([ts - delta, ts + delta], thresh, val, color='orange', alpha=0.3,
                                        label='Exceeds Threshold' if i == 0 else "")

                    ax.axvline(x=ts, color='gray', linestyle=':', linewidth=0.5)

                ax.set_xlim(timestamps.min() - pd.Timedelta(hours=1), timestamps.max() + pd.Timedelta(hours=1))
                ax.set_xlabel("Timestamp")
                ax.set_ylabel("Value")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)
        else:
            st.error("❌ 'alerts' table not found in the database.")

    else:
        overview_sql_query = f"SELECT * from assets WHERE site='{selected_site}'"
        overview_asset_data = pd.read_sql(overview_sql_query, conn)
        overview_asset_ids = [extract_asset_suffix(row) for row in overview_asset_data['name']]

        if len(overview_asset_ids) != 0:
            overview_alert_data = []

            for asset_id in overview_asset_ids:
                overview_alert_query = f"SELECT * from alerts WHERE asset_id={asset_id}"
                overview_alert_data.append(pd.read_sql_query(overview_alert_query, conn))

            combined_df = pd.concat(overview_alert_data)
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            combined_df = combined_df.sort_values('timestamp')

            asset_name_map = {extract_asset_suffix(row['name']): row['name'] for _, row in data.iterrows()}
            combined_df['asset_name'] = combined_df['asset_id'].astype(str).map(asset_name_map)

            for alert_type in combined_df['alert_type'].unique():
                st.subheader(f"{alert_type} - {selected_site}")
                subset = combined_df[combined_df['alert_type'] == alert_type]

                fig, ax = plt.subplots(figsize=(10, 4))
                timestamps = subset['timestamp']
                values = subset['value']
                thresholds = subset['threshold']

                for i in range(len(subset)):
                    ts = timestamps.iloc[i]
                    val = values.iloc[i]
                    thresh = thresholds.iloc[i]
                    delta = pd.Timedelta(minutes=30)

                    ax.hlines(y=val, xmin=ts - delta, xmax=ts + delta, colors='blue',
                              label='Alert Value' if i == 0 else "", linewidth=3)
                    ax.hlines(y=thresh, xmin=ts - delta, xmax=ts + delta, colors='red', linestyles='--',
                              label='Threshold' if i == 0 else "", linewidth=3)

                    if val > thresh:
                        ax.fill_between([ts - delta, ts + delta], thresh, val, color='orange', alpha=0.3,
                                        label='Exceeds Threshold' if i == 0 else "")

                    ax.axvline(x=ts, color='gray', linestyle=':', linewidth=0.5)

                ax.set_xlim(timestamps.min() - pd.Timedelta(hours=1), timestamps.max() + pd.Timedelta(hours=1))
                ax.set_xlabel("Timestamp")
                ax.set_ylabel("Value")
                ax.grid(True)
                ax.legend()
                st.pyplot(fig)
        else:
            st.error("❌ No overview data to show")


def setup_home():
    st.title("_Sustainability Visibility_ :seedling:")
    st.subheader("Application Overview", divider="gray")
    st.text(application_guide_introduction)

    st.markdown(application_guide_part1_title)
    st.text(application_guide_part1_description)

    st.markdown(application_guide_part2_title)
    st.text(application_guide_part2_description)

    st.markdown(application_guide_part3_title)
    st.text(application_guide_part3)

    st.markdown(application_guide_part4_title)
    st.text(application_guide_part4)

    st.subheader("Application Guide", divider="gray")

    st.markdown(application_usage_guide_1_title)
    st.markdown(application_usage_guide_1_text)
    st.markdown(application_usage_guide_1_markdown)

    st.divider()

    st.markdown(application_usage_guide_2_title)
    st.markdown(application_usage_guide_2_text)
    st.markdown(application_usage_guide_2_markdown)

    st.divider()

    st.markdown(application_usage_guide_3_title)
    st.markdown(application_usage_guide_3_text)
    st.markdown(application_usage_guide_3_markdown)

    st.divider()

    st.markdown(application_usage_guide_5_title)
    st.markdown(application_usage_guide_5_text)
    st.markdown(application_usage_guide_5_markdown)

    st.divider()

    st.markdown(application_usage_guide_6_title)
    st.markdown(application_usage_guide_6_text)
    st.markdown(application_usage_guide_6_markdown)


@st.dialog("Login / SignUp", dismissible=False, on_dismiss="ignore")
def authenticate():
    st.markdown("Login")
    st.write("Please enter credentials.")
    email = st.text_input("Email")
    password = st.text_input("Password")
    if st.button("Enter"):
        if email == "admin" and password == "admin":
            st.success("✅ Logged in successfully!")
            time.sleep(3)
            st.session_state.show_authenticate = False
            st.rerun()
        else:
            st.error("❌ Invalid credentials")



def display_volume(batch_data, target_asset, selected_site, conn, data):
    if (len(target_asset) == 1) and (len(batch_data) != 0):
        if batch_data is not None:
            asset1_data = batch_data
            asset1_data = asset1_data.sort_values('batch_id')

            # Volume per Batch
            st.subheader("Volume (Gallons) per Batch")
            fig1, ax1 = plt.subplots()
            ax1.bar(asset1_data['batch_id'].astype(str), asset1_data['volume_gallons'], color='skyblue')
            ax1.set_xlabel("Batch ID")
            ax1.set_ylabel("Volume (Gallons)")
            ax1.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig1)

        else:
            st.error("❌ 'batches' table not found in the database.")
    else:
        overview_asset_ids = target_asset

        if len(overview_asset_ids) != 0:
            overview_batch_data = []

            for asset_id in overview_asset_ids:
                overview_sql_query = f'SELECT * from batches WHERE asset_id={asset_id}'
                overview_batch_data.append(pd.read_sql_query(overview_sql_query, conn))

            # Volume Overview per Batch
            st.subheader("Overview of Volume (Gallons) per Batch")

            asset_name_map = {
                extract_asset_suffix(row['name']): row['name']
                for _, row in data.iterrows()
            }

            fig1, ax1 = plt.subplots()
            for df in overview_batch_data:
                df = df.sort_values('batch_id')
                asset_id = str(df['asset_id'].iloc[0])
                asset_name = asset_name_map.get(asset_id, f'Asset {asset_id}')
                ax1.bar(df['batch_id'].astype(str), df['volume_gallons'], label=asset_name, alpha=0.6)
            ax1.set_xlabel("Batch ID")
            ax1.set_ylabel("Volume (Gallons)")
            ax1.grid(True)
            ax1.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig1)

        else:
            st.error("❌ No overview data to show")


def display_energy(energy_data, target_asset, selected_site, conn, data):
    if (len(target_asset) == 1) and (len(energy_data) != 0):
        # sql_query = f'SELECT * from energy_usage WHERE asset_id={target_asset}'
        # energy_data = pd.read_sql_query(sql_query, conn)
        # #st.write(energy_data)

        if energy_data is not None:

            asset1_data = energy_data
            asset1_data['timestamp'].sort_values = pd.to_datetime(asset1_data['timestamp'])

            # Power
            st.subheader("Power (kW) Over Time")
            fig1, ax1 = plt.subplots()

            asset1_data['timestamp'] = pd.to_datetime(asset1_data['timestamp'])
            asset1_data = asset1_data.sort_values('timestamp')

            ax1.plot(asset1_data['timestamp'], asset1_data['power_kw'], marker='o')
            ax1.set_xlabel("Timestamp")
            ax1.set_ylabel("Power (kW)")
            ax1.grid(True)
            plt.xticks(rotation=45)
            # ax1.xaxis.set_major_locator(plt.MaxNLocator(nbins=6))
            st.pyplot(fig1)

            # Voltage
            st.subheader("Voltage Over Time")
            fig2, ax2 = plt.subplots()

            asset1_data['timestamp'] = pd.to_datetime(asset1_data['timestamp'])
            asset1_data = asset1_data.sort_values('timestamp')

            ax2.plot(asset1_data['timestamp'], asset1_data['voltage'], marker='o', color='orange')
            ax2.set_xlabel("Timestamp")
            ax2.set_ylabel("Voltage")
            ax2.grid(True)
            plt.xticks(rotation=45)
            # ax2.xaxis.set_major_locator(plt.MaxNLocator(nbins=6))
            st.pyplot(fig2)

            # Amperage

            st.subheader("Amperage Over Time")
            fig3, ax3 = plt.subplots()

            # Convert and sort timestamps
            asset1_data['timestamp'] = pd.to_datetime(asset1_data['timestamp'])
            asset1_data = asset1_data.sort_values('timestamp')

            # Plot
            ax3.plot(asset1_data['timestamp'], asset1_data['amperage'], marker='o', color='green')
            ax3.set_xlabel("Timestamp")
            ax3.set_ylabel("Amperage")
            ax3.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig3)

        else:
            st.error("❌ 'energy_usage' table not found in the database.")
    else:

        overview_asset_ids = target_asset

        if len(overview_asset_ids) != 0:

            overview_energy_data = []

            for asset_id in overview_asset_ids:
                overview_sql_query = f'SELECT * from energy_usage WHERE asset_id={asset_id}'
                overview_energy_data.append(pd.read_sql_query(overview_sql_query, conn))

            # Power
            st.subheader("Overview of Power (kW) Over Time")

            # Create a mapping from asset_id to full pump name
            asset_name_map = {extract_asset_suffix(row['name']): row['name'] for _, row in data.iterrows()}

            # Plot Power (kW) Over Time
            fig1, ax1 = plt.subplots()
            for df in overview_energy_data:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                asset_id = str(df['asset_id'].iloc[0])
                asset_name = asset_name_map.get(asset_id, f'Asset {asset_id}')
                ax1.plot(df['timestamp'], df['power_kw'], marker='o', label=asset_name)
            ax1.set_xlabel("Timestamp")
            ax1.set_ylabel("Power (kW)")
            ax1.grid(True)
            ax1.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig1)

            # Voltage

            st.subheader("Overview of Voltage Over Time")
            fig2, ax2 = plt.subplots()
            for df in overview_energy_data:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                asset_id = str(df['asset_id'].iloc[0])
                asset_name = asset_name_map.get(asset_id, f'Asset {asset_id}')
                ax2.plot(df['timestamp'], df['voltage'], marker='o', label=asset_name)
            ax2.set_xlabel("Timestamp")
            ax2.set_ylabel("Voltage")
            ax2.grid(True)
            ax2.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig2)

            # Amperage

            st.subheader("Overview of Amperage Over Time")
            fig3, ax3 = plt.subplots()
            for df in overview_energy_data:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')
                asset_id = str(df['asset_id'].iloc[0])
                asset_name = asset_name_map.get(asset_id, f'Asset {asset_id}')
                ax3.plot(df['timestamp'], df['amperage'], marker='o', label=asset_name)
            ax3.set_xlabel("Timestamp")
            ax3.set_ylabel("Amperage")
            ax3.grid(True)
            ax3.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig3)

        else:
            st.error("❌ No overview data to show")


def select_site(selected_site):
    site = ''
    if selected_site == 'Houston':
        site = 'Houston'

    elif selected_site == 'Chicago':
        site = 'Chicago'

    elif selected_site == 'Orlando':
        site = 'Orlando'

    elif selected_site == 'Cleveland':
        site = 'Cleveland'

    query = f"SELECT * from assets WHERE site='{site}'"

    return query

def main():
    # Initialize session state
    if "show_authenticate" not in st.session_state:
        st.session_state.show_authenticate = True  # Start with authentication open

    # Only show authentication if it's open
    if st.session_state.show_authenticate:
        with st.container():
            authenticate()
    else:
        # Get data from sample database file
        conn = sqlite3.connect('sustainability_data.db')

        cursor = conn.cursor()

        asset_ids = []
        names = ["Overview"]

        # Set up web app starting with nav bar
        st.sidebar.image('Image/SW_Logo.jpg', use_container_width=True)
        selected_site = st.sidebar.selectbox('Site', (
            'Houston',
            'Orlando',
            'Chicago'
        ))

        # Read in selected site to find respective data
        query = select_site(selected_site)
        data = pd.read_sql(query, conn)

        for name in data['name']:
            asset_ids.append(extract_asset_suffix(name))
            names.append(name)

        # st.write(data)
        # st.write(asset_ids)

        # Retrieve all assets related to selected site
        selected_asset = st.sidebar.selectbox('Name', names)
        target_asset = extract_asset_suffix(selected_asset)

        # Build dashboard selection options
        dashboard_option = st.sidebar.radio('Dashboard View', (
            'Home',
            'Energy',
            'Volume',
            'Alerts',
            'Billing Info',
            'Comparison'
        ))

        # Nav bar choices: display different data depending on which view is selected
        match dashboard_option:

            # Home page: contains intro information for users about dashboard
            case 'Home':
                setup_home()

            # Energy page: shows energy consumption (overview or by specific asset) for a given site
            case 'Energy':
                st.subheader("Energy Section", divider="gray")

                # If specific asset is chosen, display energy data for that asset
                if target_asset.isdigit():
                    st.subheader(f"The following data is for {selected_site}: {selected_asset}")
                    sql_query = f'SELECT * from energy_usage WHERE asset_id={target_asset}'
                    energy_data = pd.read_sql_query(sql_query, conn)

                # Otherwise, show overview energy data for the chosen site
                else:
                    st.subheader(f"The following data is an overview of the {selected_site} location")
                    energy_data = []
                    overview_sql_query = f"SELECT * from assets WHERE site='{selected_site}'"
                    overview_energy_data = pd.read_sql(overview_sql_query, conn)

                    overview_asset_ids = []

                    for row in overview_energy_data['name']:
                        overview_asset_ids.append(extract_asset_suffix(row))

                    target_asset = overview_asset_ids

                # if energy_data is not None:

                display_energy(energy_data, target_asset, selected_site, conn, data)

            # Volume page:
            case 'Volume':
                st.subheader("Volume Section", divider="gray")
                if target_asset.isdigit():
                    sql_query = f'SELECT * from batches WHERE asset_id={target_asset}'
                    batch_data = pd.read_sql_query(sql_query, conn)
                else:
                    batch_data = []
                    overview_sql_query = f"SELECT * from assets WHERE site='{selected_site}'"
                    overview_batch_data = pd.read_sql(overview_sql_query, conn)

                    overview_asset_ids = []
                    for row in overview_batch_data['name']:
                        overview_asset_ids.append(extract_asset_suffix(row))

                    target_asset = overview_asset_ids

                display_volume(batch_data, target_asset, selected_site, conn, data)

            # Alerts page:
            case 'Alerts':
                st.subheader("Alerts Section", divider="gray")
                if target_asset.isdigit():
                    st.subheader(f"The following alert data is for {selected_site}: {selected_asset}")
                    sql_query = f'SELECT * from alerts WHERE asset_id={target_asset}'
                    alert_data = pd.read_sql_query(sql_query, conn)
                else:
                    st.subheader(f"The following alert data is an overview of the {selected_site} location")
                    overview_sql_query = f"SELECT * from assets WHERE site='{selected_site}'"
                    overview_asset_data = pd.read_sql(overview_sql_query, conn)

                    overview_asset_ids = [extract_asset_suffix(row) for row in overview_asset_data['name']]
                    target_asset = overview_asset_ids

                    alert_data = []
                    for asset_id in overview_asset_ids:
                        sql_query = f'SELECT * from alerts WHERE asset_id={asset_id}'
                        alert_data.append(pd.read_sql_query(sql_query, conn))
                    alert_data = pd.concat(alert_data)

                display_alerts(alert_data, target_asset, selected_site, conn, data)

            # Billing page:
            case 'Billing Info':
                st.subheader("Billing Section", divider="gray")
                display_utility_summary(conn)

            # Comparison page: compare two assets (same or different sites) side-by-side
            case 'Comparison':

                # Ensure specific asset is selected for valid comparison
                if target_asset.isdigit():
                    st.subheader("Comparison Section", divider="gray")
                    asset_ids_2 = []
                    names_2 = []

                    # Display second set of select boxes to choose secondary site and asset for comparison
                    selected_site_2 = st.sidebar.selectbox('Site Option 2', (
                        'Houston',
                        'Orlando',
                        'Chicago'
                    ))

                    site_2_query = select_site(selected_site_2)
                    data_site_2 = pd.read_sql(site_2_query, conn)

                    for name in data_site_2['name']:
                        asset_ids_2.append(extract_asset_suffix(name))
                        names_2.append(name)

                    # Split page into 2 columns for side-by-side energy data comparison
                    left_col, right_col = st.columns(2)

                    # Display first site/asset energy data on left side of page
                    with left_col:
                        st.subheader(f"The following data is for {selected_site}: {selected_asset}")
                        sql_query = f'SELECT * from energy_usage WHERE asset_id={target_asset}'
                        energy_data = pd.read_sql_query(sql_query, conn)
                        # st.write(energy_data)

                        if energy_data is not None:
                            display_energy(energy_data, target_asset, selected_site, conn, data)

                    # Display second site/asset energy data on right side of page
                    with right_col:
                        selected_asset_2 = st.sidebar.selectbox('Name Option 2', names_2)
                        target_asset_2 = extract_asset_suffix(selected_asset_2)

                        st.subheader(f"The following data is for {selected_site_2}: {selected_asset_2}")

                        sql_query_2 = f'SELECT * from energy_usage WHERE asset_id={target_asset_2}'
                        energy_data_2 = pd.read_sql_query(sql_query_2, conn)
                        # st.write(energy_data)

                        if energy_data_2 is not None:
                            display_energy(energy_data_2, target_asset_2, selected_site_2, conn, data_site_2)

                # If overview is chosen, prompt user to choose specific assets
                else:
                    st.subheader("Cannot compare on 'Overview'")
                    st.subheader("Please select an asset to compare")

if __name__ == "__main__":
    main()