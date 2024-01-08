import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import streamlit as st
import ast

class Component:
    def __init__(self):
        self.carbon = 0
        self.social = 0
        self.rvi = 0

    def calculate_social(self):
        self.social = 1

    def calculate_carbon(self):
        self.carbon = 1

    def calculate_rvi(self):
        self.calculate_social()
        self.calculate_carbon()
        self.rvi = self.carbon * 2 + self.social * 5
        return self.rvi

def fetch_component_from_neo4j(driver, component_name):
    with driver.session() as session:
        query = "MATCH (n:Component) WHERE n.name = $name RETURN n.name"
        result = session.run(query, name=component_name)
        components = [record["n.name"] for record in result]
        return components


def display_rvi_streamlit(driver):
    with st.form(key='component_form'):
        search_name = st.text_input('Enter Component Name:')
        submit_button = st.form_submit_button(label='Search')

    if submit_button:
        components = fetch_component_from_neo4j(driver, search_name)

        if components:
            component_rvi_list = []

            for component_name in components:
                comp = Component()
                rvi = comp.calculate_rvi()
                component_rvi_list.append((component_name, rvi))

            for component, rvi in component_rvi_list:
                st.write(f"Component: {component}, RVI: {rvi}")
        else:
            st.write("No components found with that name.")


def fetch_component_attributes_from_neo4j(driver, component_name):
    with driver.session() as session:
        query = """
        MATCH (n:Component {name: $name})
        RETURN n.attributes
        """
        results = session.run(query, name=component_name)
        components = [record.get("n.attributes", {}) for record in results]
        return components


def display_rvi_streamlit_att(driver):
    co2_mat = pd.read_excel("co2mat.xlsx", sheet_name="Sheet2")
    mat = co2_mat["Eng"].to_list()
    search_name = st.text_input('Enter Component Name:')
    if st.button('Search'):
        components_attributes = fetch_component_attributes_from_neo4j(driver, search_name)

        if components_attributes:
            component_rvi_list = []

            for component_att in components_attributes:
                material = ast.literal_eval(component_att)["Material"]
                # Search for rows in the DataFrame where 'Eng' matches the material name
                matching_rows = co2_mat[co2_mat['Eng'] == material]

                # If there are matching rows, extract the required data
                if not matching_rows.empty:
                    for _, row in matching_rows.iterrows():
                        total = row['Total']
                        fabrication = row['Fabrication']
                        elimination = row['Élimination']
                        contenu_dans_le_produit = row['Contenu dans le produit']
                        # Display the data in Streamlit
                        st.write(f"Material: {material}, Total: {total}, Fabrication: {fabrication}, Elimination: {elimination}, Contained: {contenu_dans_le_produit}")
                else:
                    st.write("No matching data found for Material:", material)
        else:
            st.write("No components found with that name.")



def display_rvi_streamlit_att2(driver):
    st.title('Env RVI Calculation')

    search_name = st.text_input('Enter Component Name:')
    co2_mat = pd.read_excel("co2mat.xlsx", sheet_name="Sheet2")
    mat = co2_mat["Eng"].to_list()

    if st.button('Search'):
        components_attributes = fetch_component_attributes_from_neo4j(driver, search_name)

        if components_attributes:
            results = []

            for component_att in components_attributes:
                material = ast.literal_eval(component_att)["Material"]
                # Search for rows in the DataFrame where 'Eng' matches the material name
                matching_rows = co2_mat[co2_mat['Eng'] == material]

                # If there are matching rows, append them to the results list
                if not matching_rows.empty:
                    results.append(matching_rows)
            
            # If there are results, concatenate them into a single DataFrame
            if results:
                result_df = pd.concat(results)
                # Display the DataFrame in Streamlit as a sortable table
                weight1 = (result_df['Fabrication']+result_df['Élimination'] - result_df['Contenu dans le produit'])  / (result_df['Fabrication']+result_df['Élimination']) * 100  # Normalized weights based on Total
                # Calculate the RVI for each row
                result_df['RVI(%)'] = (weight1) / 2
                result_df.columns = ['Total (kg CO2-eq)','Fabrication (kg CO2-eq)', 'Elimination (kg CO2-eq)', 'Reuse (kg CO2-eq)', 'Name FR', 'Name EN','RVI(%)' ]
                result_df = result_df.drop(columns=['Name FR', 'Name EN'])
                st.dataframe(result_df)
            else:
                st.write("No matching data found for Material:", material)
        else:
            st.write("No components found with that name.")