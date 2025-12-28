import os
from bs4 import BeautifulSoup
import requests
import time
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import io

#paso 2: desacarga HTML
url = "https://en.wikipedia.org/wiki/List_of_most-streamed_songs_on_Spotify" 
headers = { 
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
    "AppleWebKit/537.36 (KHTML, like Gecko) " 
    "Chrome/120.0.0.0 Safari/537.36" } 
response = requests.get(url, headers=headers)
print("Estado:", response.status_code)

print("Estado:", response.status_code) 
html_content = response.text

html = io.StringIO(response.text)

tables = pd.read_html(html)
print(f"Se encontraron {len(tables)} tablas.")

df = tables[0]
print(df.head())

#limpieza de datos
df.columns = ["Rank", "Song", "Artist", "Streams", "Release_Date", "Ref"]

df["Streams"] = (
    df["Streams"]
    .astype(str)               
    .str.replace("billions", "", regex=False)
    .str.replace("B", "", regex=False)
    .str.replace("$", "", regex=False)
    .str.strip()
)

df = df[df["Streams"].str.match(r"^\d+(\.\d+)?$")]

df.loc[:,"Streams"] = df["Streams"].astype(float)

df["Streams"] = pd.to_numeric(df["Streams"], errors="coerce")

df["Release_Date"] = pd.to_datetime(df["Release_Date"], errors="coerce")

df = df.dropna(subset=["Streams", "Release_Date"])

print(df.dtypes)
print(df.head())

#Almacena los datos en sqlite
conn = sqlite3.connect("spotify_songs.db")

df.to_sql("most_streamed", conn, if_exists="replace", index=False)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM most_streamed")
print("Rows inserted:", cursor.fetchone()[0])

conn.commit()
conn.close()

#Visualiza los Datos

top10 = df.nlargest(10, "Streams")
plt.figure(figsize=(10,6))
sns.barplot(data=top10, x="Streams", y="Song", hue="Song", palette="viridis", legend=False)
plt.title("Top 10 canciones más reproducidas en Spotify")
plt.xlabel("Streams (billions)")
plt.ylabel("Canción")
plt.tight_layout()
plt.savefig("grafico_top10.png")
plt.show()

#Número de canciones por año

df["Year"] = df["Release_Date"].dt.year
plt.figure(figsize=(10, 5))
sns.countplot(data=df, x="Year", order=sorted(df["Year"].dropna().unique()))
plt.title("Number of Songs in the Ranking by Release Year")
plt.xlabel("Year")
plt.ylabel("Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("songs_by_year.png")
plt.show()

# Artistas que aprecen más veces en la lista de canciones más reproducidas

artists = df["Artist"].value_counts().nlargest(10)
artists_df = artists.reset_index() 
artists_df.columns = ["Artist", "Count"]
plt.figure(figsize=(10, 6))
sns.barplot(x=artists.values, y=artists.index, hue=artists.index, palette="coolwarm", legend=False)
plt.title("Artists with the Most Songs in the Ranking")
plt.xlabel("Number of Songs")
plt.ylabel("Artist")
plt.tight_layout()
plt.savefig("chart3_artists.png")
plt.show()