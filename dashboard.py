import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import streamlit_authenticator as stauth


import streamlit as st
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
from geopy.geocoders import Nominatim
from PIL import Image
import datetime
import warnings
warnings.filterwarnings('ignore')

def display_map_with_sentiment(data, sentiment, geo_df):
    def get_most_positive_sentiment_per_location(data, sentiment):
        # Konversi data ke DataFrame pandas
        df = pd.DataFrame(data, columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Mengelompokkan data berdasarkan lokasi
        grouped = df.groupby('location')

        # Membuat DataFrame baru untuk hasil akhir
        result = pd.DataFrame(columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Loop melalui setiap grup lokasi
        for group_name, group_df in grouped:
            # Mengambil sentimen positif terbanyak
            max_positive_sentiment = group_df[group_df['Sentiment'] == sentiment].sort_values('jumlah', ascending=False).iloc[0]

            # Menambahkan hasil ke DataFrame akhir
            result = result.append(max_positive_sentiment)

        # Mengembalikan DataFrame akhir
        return result
    
    # Menggabungkan data dan menghitung jumlah sentimen per lokasi dan tokoh
    count_sentiment_tokoh_loc = data.groupby(['location', 'Sentiment', 'Tokoh'])['location'].count().reset_index(name="jumlah")
    merge2 = geo_df.merge(count_sentiment_tokoh_loc, on='location')
    merge2 = merge2[['location', 'Tokoh', 'Sentiment', 'jumlah']]

    # Mendapatkan sentimen positif terbanyak per lokasi
    fil = get_most_positive_sentiment_per_location(merge2, sentiment)

    # Menggabungkan dengan data geospasial
    fil = geo_df.merge(fil, on='location')
    fil = gpd.GeoDataFrame(fil, geometry='geometry')
    fil = fil[['location', 'Tokoh', 'Sentiment', 'jumlah', 'geometry']]

    # Membuat peta menggunakan folium
    map_indo = folium.Map(location=[-2.5489, 118.0149], tiles='cartodbpositron', zoom_start=4,
                          zoom_control=False,
                          scrollWheelZoom=False,
                          dragging=False)

    style_function = lambda x: {
        "fillColor": "#FF0000" if x["properties"]["Tokoh"] == "Ganjar Pranowo" else
                    "#0000FF" if x["properties"]["Tokoh"] == "Anies Baswedan" else
                    "#FFFF00",
        "fill": True,
        "fill_opacity": 0.7,
        "line_opacity": 0.2,
        "color": False
    }

    color = folium.GeoJson(fil, style_function=style_function)
    folium.GeoJsonTooltip(['location']).add_to(color)
    color.add_to(map_indo)

    st_map=folium_static(map_indo, width=800, height=450)
    return st_map

def display_map_with_sentiment_with_location(data, sentiment, geo_df, location):
    def get_most_positive_sentiment_per_location(data, sentiment):
        # Konversi data ke DataFrame pandas
        df = pd.DataFrame(data, columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Mengelompokkan data berdasarkan lokasi
        grouped = df.groupby('location')

        # Membuat DataFrame baru untuk hasil akhir
        result = pd.DataFrame(columns=['location', 'Tokoh', 'Sentiment', 'jumlah'])

        # Loop melalui setiap grup lokasi
        for group_name, group_df in grouped:
            # Mengambil sentimen positif terbanyak
            max_positive_sentiment = group_df[group_df['Sentiment'] == sentiment].sort_values('jumlah', ascending=False).iloc[0]

            # Menambahkan hasil ke DataFrame akhir
            result = result.append(max_positive_sentiment)

        # Mengembalikan DataFrame akhir
        return result
    
    # Menggabungkan data dan menghitung jumlah sentimen per lokasi dan tokoh
    count_sentiment_tokoh_loc = data.groupby(['location', 'Sentiment', 'Tokoh'])['location'].count().reset_index(name="jumlah")
    merge2 = geo_df.merge(count_sentiment_tokoh_loc, on='location')
    merge2 = merge2[['location', 'Tokoh', 'Sentiment', 'jumlah']]
    
    # Melakukan filter berdasarkan lokasi jika parameter location diberikan
    if location:
        merge2 = merge2[merge2['location'] == location]

    # Mendapatkan sentimen positif terbanyak per lokasi
    fil = get_most_positive_sentiment_per_location(merge2, sentiment)

    # Menggabungkan dengan data geospasial
    fil = geo_df.merge(fil, on='location')
    fil = gpd.GeoDataFrame(fil, geometry='geometry')
    fil = fil[['location', 'Tokoh', 'Sentiment', 'jumlah', 'geometry']]

    # Membuat peta menggunakan folium
    def center(location):
        address = f'{location}, ID'
        geolocator = Nominatim(user_agent="id_explorer")
        location = geolocator.geocode(address)
        latitude = location.latitude
        longitude = location.longitude
        return latitude, longitude
    centers = center(location)
    map_indo = folium.Map(location=[centers[0], centers[1]], 
                          tiles='cartodbpositron',
                          #zoom_start=4, 
                          zoom_control=False,
                          scrollWheelZoom=False,
                          dragging=False)

    style_function = lambda x: {
        "fillColor": "#FF0000" if x["properties"]["Tokoh"] == "Ganjar Pranowo" else
                    "#0000FF" if x["properties"]["Tokoh"] == "Anies Baswedan" else
                    "#FFFF00",
        "fill": True,
        "fill_opacity": 0.7,
        "line_opacity": 0.2,
        "color": False
    }

    color = folium.GeoJson(fil, style_function=style_function)
    folium.GeoJsonTooltip(['location']).add_to(color)
    color.add_to(map_indo)

    st_map=folium_static(map_indo, width=800, height=450)
    return st_map

def filters_lokasi(df_jkt):
    filters_desa_list = ['ALL']+list(df_jkt['location'].unique())
    filters_desa_list.sort()
    filters_desa = st.sidebar.selectbox('Pilih Daerah :', filters_desa_list, index=1)
    return filters_desa

def get_latest_date(df):

    # Mengambil tanggal terbaru
    tanggal_terbaru = df['date'].max()

    return tanggal_terbaru

def create_cumulative_line_chart(df, sentiment:int, region:str=None):
    # Filter data based on sentiment
    positive_df = df[df['Sentiment'] == sentiment]
    
    # Filter data based on region, if provided
    if region is not None:
        positive_df = positive_df[positive_df['location'] == region]

    # Calculate the count of positive sentiment occurrences per date and tokoh
    sentiment_counts = positive_df.groupby(['date', 'Tokoh']).size().reset_index(name='Count')

    # Calculate the cumulative count of previous values
    sentiment_counts['Cumulative_Count'] = sentiment_counts.groupby('Tokoh')['Count'].cumsum()

    # Create a line chart using Plotly
    fig = go.Figure()

    # Define colors for each tokoh
    colors = {'Ganjar Pranowo': 'darkred', 'Anies Baswedan': 'darkblue', 'Prabowo Subianto': 'darkgoldenrod'}

    # Loop through each tokoh in the dataframe
    for tokoh in sentiment_counts['Tokoh'].unique():
        data_tokoh = sentiment_counts[sentiment_counts['Tokoh'] == tokoh]
        fig.add_trace(go.Scatter(x=data_tokoh['date'], y=data_tokoh['Cumulative_Count'], mode='lines',
                                 name=tokoh, line=dict(color=colors[tokoh])))

    # Set the title and axis labels
    fig.update_layout(xaxis_title='Date',
                      yaxis_title='Cumulative Sentiment Count')

    # Display the line chart using Streamlit
    st.plotly_chart(fig)
    
def create_cumulative_line_chart_with_filtering_date(df, sentiment, start_date, end_date, region:str=None):
    # Filter data based on sentiment
    positive_df = df[df['Sentiment'] == sentiment]
    
    # Filter data based on region, if provided
    if region is not None:
        positive_df = positive_df[positive_df['location'] == region]

    # Convert start_date and end_date to strings
    start_date = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime.date) else start_date
    end_date = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime.date) else end_date

    # Filter data based on date range
    sentiment_counts = positive_df.groupby(['date', 'Tokoh']).size().reset_index(name='Count')
    sentiment_counts['date'] = pd.to_datetime(sentiment_counts['date'])  # Convert date column to datetime objects
    sentiment_counts = sentiment_counts[(sentiment_counts['date'] >= start_date) & (sentiment_counts['date'] <= end_date)]

    # Calculate the cumulative count of previous values
    sentiment_counts['Cumulative_Count'] = sentiment_counts.groupby('Tokoh')['Count'].cumsum()

    # Create a line chart using Plotly
    fig = go.Figure()

    # Define colors for each tokoh
    colors = {'Ganjar Pranowo': 'darkred', 'Anies Baswedan': 'darkblue', 'Prabowo Subianto': 'darkgoldenrod'}

    # Loop through each tokoh in the dataframe
    for tokoh in sentiment_counts['Tokoh'].unique():
        data_tokoh = sentiment_counts[sentiment_counts['Tokoh'] == tokoh]
        fig.add_trace(go.Scatter(x=data_tokoh['date'], y=data_tokoh['Cumulative_Count'], mode='lines',
                                 name=tokoh, line=dict(color=colors[tokoh])))

    # Set the title and axis labels
    fig.update_layout(xaxis_title='Date',
                      yaxis_title='Cumulative Sentiment Count')

    # Display the line chart on Streamlit
    st.plotly_chart(fig)

def create_stacked_barchart_combined(df, location=None):
    # Filter the DataFrame based on the provided location (if any)
    if location:
        df_filtered = df[df['location'] == location]
    else:
        df_filtered = df

    # Group the filtered DataFrame by 'Tokoh' and 'Sentiment', and calculate the count of each sentiment
    grouped_data = df_filtered.groupby(['Tokoh', 'Sentiment']).size().reset_index(name='Count')

    # Define labels for each sentiment
    sentiment_labels = {-1: 'Netral', 0: 'Negatif', 1: 'Positif'}

    # Define colors for each sentiment
    colors = {-1: 'darkgray', 0: 'darkred', 1: 'darkgreen'}

    # Create a stacked bar chart using Plotly Go
    fig = go.Figure()

    for sentiment, color in colors.items():
        data = grouped_data[grouped_data['Sentiment'] == sentiment]
        sentiment_label = sentiment_labels[sentiment]
        fig.add_trace(go.Bar(x=data['Tokoh'], y=data['Count'], name=sentiment_label, marker_color=color))

    # Customize the layout of the chart
    fig.update_layout(
        xaxis_title='Bakal Calon Presiden',
        yaxis_title='Jumlah',
        barmode='stack'
    )

    # Show the chart using Streamlit
    st.plotly_chart(fig)

def main():
    #TITLE
    APP_TITLE = "Klasifikasi Opini publik di Twitter terhadap bakal calon Presiden Indonesia Tahun 2024 secara Real Time"
    st.set_page_config(APP_TITLE, layout="wide")
    
    ## -- LOGIN ---
    names = ["Muhammad Rizki"]
    usernames = ["rizki11"]
    
    #LOAD HASH
    file_path = Path(__file__).parent / "hashed_pw.pkl"
    with file_path.open("rb") as file:
        hashed_passwords=pickle.load(file)
    
    authenticator = stauth.Authenticate(names, usernames, hashed_passwords, 
                                           "Ini APA", "abcd", cookie_expiry_days=365)
    
    name, authentication_status, username = authenticator.login("Login", "main")
    
    if authentication_status==False:
        st.error("Username/password salah")
    if authentication_status==None:
        st.warning("Please enter a username dan password")
    if authentication_status:    
        st.title(APP_TITLE)
        data_df = pd.read_csv("Dashboard Tanpa Filter/data/data.csv")
        replacement_mapping_dict = {
            "DIYOGYAKARTA" : "DI YOGYAKARTA",
            "DKIJAKARTA" : "DKI JAKARTA",
            "JAWABARAT" : "JAWA BARAT",
            "JAWATENGAH" : "JAWA TENGAH",
            "JAWATIMUR" : "JAWA TIMUR",
            "KALIMANTANBARAT" : "KALIMANTAN BARAT",
            "KALIMANTANSELATAN" : "KALIMANTAN SELATAN",
            "KALIMANTANTENGAH" : "KALIMANTAN TENGAH",
            "KALIMANTANTIMUR" : "KALIMANTAN TIMUR",
            "KALIMANTANUTARA" : "KALIMANTAN UTARA",
            "KEPULAUANBANGKABELITUNG" : "KEPULAUAN BANGKA BELITUNG",
            "KEPULAUANRIAU" : "KEPULAUAN RIAU",
            "MALUKUUTARA" : "MALUKU UTARA",
            "KALIMANTANBARAT" : "KALIMANTAN BARAT",
            "NUSATENGGARABARAT" : "NUSA TENGGARA BARAT",
            "NUSATENGGARATIMUR" : "NUSA TENGGARA TIMUR",
            "PAPUABARAT" : "PAPUA BARAT",
            "SULAWESIBARAT" : "SULAWESI BARAT",
            "SULAWESISELATAN" : "SULAWESI SELATAN",
            "SULAWESITENGAH" : "SULAWESI TENGAH",
            "SULAWESITENGGARA" : "SULAWESI TENGGARA",
            "SULAWESIUTARA" : "SULAWESI UTARA",
            "SUMATERABARAT" : "SUMATERA BARAT",
            "SUMATERASELATAN" : "SUMATERA SELATAN",
            "SUMATERAUTARA" : "SUMATERA UTARA"
            }
        data_df["location"] = data_df["location"].replace(replacement_mapping_dict)
        geo_df = gpd.read_file('indonesia-prov.geojson')
        #mengganti value Status
        replacement_mapping_dict = {
            "DI. ACEH" : "ACEH",
            "NUSATENGGARA BARAT" : "NUSA TENGGARA BARAT",
            "DAERAH ISTIMEWA YOGYAKARTA" : "DI YOGYAKARTA",
            "BANGKA BELITUNG" : "KEPULAUAN BANGKA BELITUNG"
        }
        geo_df["Propinsi"] = geo_df["Propinsi"].replace(replacement_mapping_dict)
        geo_df.rename(columns={'Propinsi': 'location'}, inplace=True)
        
        #MERGE
        merged_gdf = geo_df.merge(data_df, on='location')
        merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry')
        
        # FILTER  LOKASI
        authenticator.logout("logout", "sidebar")
        st.sidebar.title(f"Welcome {name}")
        st.sidebar.title("Filters")
        filters_desa = filters_lokasi(data_df)
            
        #st.write(merged_gdf)
        #display_map(gdf)
        st.markdown(f'<h3 style="color: gray;border-radius:50%;" >sumber: www.twitter.com</h3>',unsafe_allow_html=True)
        st.metric(label="Akurasi", value='75 %')
        latest_date = get_latest_date(data_df)
        st.markdown("Data Update = "+latest_date)
        # Using "with" notation
        with st.container():
            ganjar, anies, prabowo = st.columns(3)
            with ganjar:
                st.subheader("Ganjar Pranowo")
                image = Image.open('images/ganjar.png')
                width = 100
                height = 100
                resized_image = image.resize((width, height))
                st.image(resized_image)
                st.write("Nama : H. Ganjar Pranowo, S.H, M.IP")
                st.write("Lahir : 28 Oktober 1968, di Karanganyar, Jawa Tengah")
                
            with anies:
                st.subheader("Anies Baswedan")
                image = Image.open('images/anies.png')
                width = 100
                height = 100
                resized_image = image.resize((width, height))
                st.image(resized_image)            
                st.write("Nama : H. Anies Rasyid Baswedan, S.E., M.P.P., Ph.D")
                st.write("Lahir : 7 Mei 1969, di Kuningan, Jawa Barat")
                
            with prabowo:
                st.subheader("Prabowo Subianto")
                image = Image.open('images/prabowo.png')
                width = 100
                height = 100
                resized_image = image.resize((width, height))
                st.image(resized_image)
                st.write("Nama : Letnan Jenderal TNI (Purn.) H. Prabowo Subianto Djojohadikusumo")
                st.write("Lahir : 17 Oktober 1951, di Jakarta, Indonesia")
            
        if filters_desa=="ALL":
            with st.container():
                positif, negatif, netral = st.tabs(["Positif", "Negatif", "Netral"])
                with positif:                       
                    st.subheader("Jumlah Sentiment Positif terbanyak tiap Provinsi")
                    display_map_with_sentiment(merged_gdf, 1, geo_df)
                        
                with negatif:
                    st.subheader("Jumlah Sentiment Negatif terbanyak tiap Provinsi")
                    display_map_with_sentiment(merged_gdf, 0, geo_df)
                    
                with netral:
                    st.subheader("Jumlah Sentiment Netral terbanyak tiap Provinsi")
                    display_map_with_sentiment(merged_gdf, -1, geo_df)
            with st.container():
                st.subheader("Jumlah Seluruh Sentiment")
                create_stacked_barchart_combined(data_df)         
                    
            with st.container():
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])                       
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Positif Bakal Calon Presiden")
                    create_cumulative_line_chart(data_df, 1)
                with filter:
                    st.subheader("Grafik Sentimen Positif Bakal Calon Presiden")
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_pos = st.date_input("Pilih Tanggal Awal", value=None, key = 1)
                        end_date_pos = st.date_input("Pilih Tanggal Akhir", value=None, key = 2)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, 1, start_date_pos, end_date_pos)
            with st.container():
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Negatif Bakal Calon Presiden")
                    create_cumulative_line_chart(data_df, 0)
                with filter:
                    st.subheader("Grafik Sentimen Negatif Bakal Calon Presiden")
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_neg = st.date_input("Pilih Tanggal Awal", value=None, key = 3)
                        end_date_neg = st.date_input("Pilih Tanggal Akhir", value=None, key = 4)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, 0, start_date_neg, end_date_neg)
            with st.container():
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Netral Bakal Calon Presiden")
                    create_cumulative_line_chart(data_df, -1)
                with filter:
                    st.subheader("Grafik Sentimen Netral Bakal Calon Presiden")
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_net = st.date_input("Pilih Tanggal Awal", value=None, key = 5)
                        end_date_net = st.date_input("Pilih Tanggal Akhir", value=None, key = 6)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, -1, start_date_net, end_date_net)
        else:
            with st.container():
                positif, negatif, netral = st.tabs(["Positif", "Negatif", "Netral"])
                with positif:                            
                    st.subheader("Jumlah Sentiment Positif terbanyak Provinsi {}".format(filters_desa))
                    display_map_with_sentiment_with_location(merged_gdf, 1, geo_df, filters_desa)
                    
                with negatif:                            
                    st.subheader("Jumlah Sentiment Negatif terbanyak Provinsi {}".format(filters_desa))
                    display_map_with_sentiment_with_location(merged_gdf, 0, geo_df, filters_desa)
                    
                with netral:                            
                    st.subheader("Jumlah Sentiment netral terbanyak Provinsi {}".format(filters_desa))
                    display_map_with_sentiment_with_location(merged_gdf, -1, geo_df, filters_desa)
            with st.container():
                st.subheader(f"Jumlah Seluruh Sentiment provinsi {filters_desa}")
                create_stacked_barchart_combined(data_df, filters_desa)
            with st.container():
                st.subheader("Positif")
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Positif Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    create_cumulative_line_chart(data_df, 1, filters_desa)
                with filter:
                    st.subheader("Grafik Sentimen Positif Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_pos = st.date_input("Pilih Tanggal Awal", value=None, key = 7)
                        end_date_pos = st.date_input("Pilih Tanggal Akhir", value=None, key = 8)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, 1, start_date_pos, end_date_pos, filters_desa)
            with st.container():
                st.subheader("Negatif")
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Negatif Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    create_cumulative_line_chart(data_df, 0, filters_desa)
                with filter:
                    st.subheader("Grafik Sentimen Negatif Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_pos = st.date_input("Pilih Tanggal Awal", value=None, key = 9)
                        end_date_pos = st.date_input("Pilih Tanggal Akhir", value=None, key = 10)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, 0, start_date_pos, end_date_pos, filters_desa)
            with st.container():
                st.subheader("Netral")
                tanpa_filter,filter=st.tabs(["Tanpa Filter", "Filter"])
                with tanpa_filter:
                    st.subheader("Grafik Sentimen Netral Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    create_cumulative_line_chart(data_df, -1, filters_desa)
                with filter:
                    st.subheader("Grafik Sentimen Netral Bakal Calon Presiden Provinsi {}".format(filters_desa))
                    col1, col2 = st.columns((2, 8))
                    with col1:
                        start_date_pos = st.date_input("Pilih Tanggal Awal", value=None, key = 11)
                        end_date_pos = st.date_input("Pilih Tanggal Akhir", value=None, key = 12)
                    with col2:
                        create_cumulative_line_chart_with_filtering_date(data_df, -1, start_date_pos, end_date_pos, filters_desa)
if __name__ == "__main__":
    main()
    
    
    