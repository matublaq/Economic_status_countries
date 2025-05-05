import pandas as pd
import numpy as np
import openpyxl
import sqlite3
import psycopg2
import shutil
from datetime import datetime, date, timedelta

###################### SQLITE3 ######################
#####################################################
################## CREATE DATABASE  #################
def create_inflation_database():
    #Connect/create database
    conn = sqlite3.connect("Inflation.db")
    cursor = conn.cursor()

    #Create Countries table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Countries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, 
            code TEXT NOT NULL
        )
    ''')

    #Create inflation table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Inflation(
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            country_id INTEGER NOT NULL, 
            year INTEGER NOT NULL, 
            inflation_rate REAL, 
            FOREIGN KEY (country_id) REFERENCES Countries(id)
        )
    ''')

    conn.commit()
    conn.close()

#####################################################
def delete_inflation_database():
    #Connect to the database
    conn = sqlite3.connect('Inflation.db')
    cursor = conn.cursor()

    #Drop tables
    cursor.execute("DROP TABLE IF EXISTS Countries")
    cursor.execute("DROP TABLE IF EXISTS Inflation")

    #Confirm change and close connection
    conn.commit()
    conn.close()

def delete_inflation_data():
    #Connect to the database
    conn = sqlite3.connect('Inflation.db')
    cursor = conn.cursor()

    #Delete all rows from the tables
    cursor.execute("DELETE FROM Countries")
    cursor.execute("DELETE FROM Inflation")

    #Confirm change and close connection
    conn.commit()
    conn.close()

#####################################################
def backup_inflation_database(file_path):
    shutil.copyfile(file_path, file_path[3:-3] + '_backup.db')

######################################################
def update_inflation_database(csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    ########################################################################
    try: 
        #Get countries and years from the database
        conn = sqlite3.connect("Inflation.db")
        cursor = conn.cursor()

        countries_db = cursor.execute("SELECT name FROM Countries").fetchall()
        countries_db_list = [ i[0] for i in countries_db]
        years_db = cursor.execute("SELECT year FROM Inflation").fetchall()
        years_db_list = list(set(i[0] for i in years_db))


        for country in countries_db_list:
            if (date.today().month >= 5): #Los datos se actualizan en mayo
                if (date.today().year - 1) in years_db_list:
                    return "Data is already up to date"
            else:
                if (date.today().year - 2) in years_db_list: 
                    return "Data is already up to date"
        
        delete_inflation_database()
        create_inflation_database()
        
        with sqlite3.connect("Inflation.db") as conn:
            cursor = conn.cursor()

            df = pd.read_csv("../info_extraction/inflation/Inflation_clean.csv")
            country_dict = {}
            for country in df['Country'].unique():

                country_df = df[df['Country'] == country]
                country_dict['Country'] = country_df['Country'].values[0]
                country_dict['Code'] = country_df['Code'].values[0]
                country_dict['year'] = country_df.columns[2:].tolist()
                country_dict['inflation_rate'] = country_df.iloc[0, 2:].tolist()

                #Insert countries
                cursor.execute("INSERT INTO Countries (name, code) VALUES (?, ?)", (country_dict['Country'], country_dict['Code']))
                
                #Get country id
                cursor.execute("SELECT id FROM Countries WHERE name = ?", (country_dict['Country'],))
                country_id = cursor.fetchone()[0]
                
                #Insert inflation data
                for i in range(len(country_dict['year'])):
                    year = country_dict['year'][i]
                    inflation_rate = country_dict['inflation_rate'][i]
                    cursor.execute('''
                            INSERT INTO Inflation (country_id, year, inflation_rate) 
                            VALUES (?, ?, ?)
                        ''', (country_id, country_dict['year'][i], country_dict['inflation_rate'][i]))
                    
            #Commit the transaction
            conn.commit()
            conn.close()
            return "Database updated successfully"

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")