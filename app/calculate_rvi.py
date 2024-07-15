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
                        fabrication = row['Fabrication']
                        # Display the data in Streamlit
                        st.write(f"Material: {material}, Fabrication: {fabrication}")
                else:
                    st.write("No matching data found for Material:", material)
        else:
            st.write("No components found with that name.")



"""def display_rvi_streamlit_att2(driver):
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
                matching_rows = co2_mat[co2_mat['Eng'] == material]

                if not matching_rows.empty:
                    results.append(matching_rows)
            
            if results:
                result_df = pd.concat(results)
                weight1 = (result_df['Fabrication']+result_df['Élimination'] - result_df['Contenu dans le produit'])  / (result_df['Fabrication']+result_df['Élimination']) * 100  # Normalized weights based on Total
                result_df['RVI(%)'] = (weight1) / 2
                result_df.columns = ['Total (kg CO2-eq)','Fabrication (kg CO2-eq)', 'Elimination (kg CO2-eq)', 'Reuse (kg CO2-eq)', 'Name FR', 'Name EN','RVI(%)' ]
                result_df = result_df.drop(columns=['Name FR'])
                st.dataframe(result_df)
            else:
                st.write("No matching data found for Material:", material)
        else:
            st.write("No components found with that name.")"""




def display_rvi_streamlit_att2(driver):
    st.title('Environmental RVI Calculation')
    #co2_mat = pd.read_excel("co2mat.xlsx", sheet_name="Sheet2")
    kbob_emb_co2 = pd.read_csv("kbob_res.csv")
    kbob_emb_co2_mass = pd.read_csv("kbob_res_mass.csv")
    fourth_level_list = pd.read_csv("kbob_res_fl.csv")["level"].unique()
    kbob_emb_co2_2 = pd.read_csv("fl_to_mat.csv")
    # Component selection
    selected_component = st.selectbox('Select Component:', options=[''] + fourth_level_list)

    if selected_component:
        # Material selection based on the component selected
        materials = kbob_emb_co2_2[kbob_emb_co2_2.fourth_level==selected_component]
        masses = kbob_emb_co2_mass[kbob_emb_co2_2.fourth_level==selected_component]

        selected_material = st.selectbox('Select Material for the Component:', options=[''] + list(materials["material_emb_2"]))

        if selected_material:
            # Input fields for dimensions
            length = st.number_input('Enter Length:', min_value=0.0, format="%.2f")
            width = st.number_input('Enter Width:', min_value=0.0, format="%.2f")
            height = st.number_input('Enter Height:', min_value=0.0, format="%.2f")

            if st.button('Calculate RVI'):
                # Perform calculation if all conditions are met
                if all([length, width, height]):  # Checking if dimensions are entered
                    # Placeholder for actual calculation based on material properties
                    co2_dict = {}
                    for _, row in materials.iterrows():
                        if row['material_emb_2'] not in co2_dict:
                            co2_dict[row['material_emb_2']] = {}
                        co2_dict[row['material_emb_2']][row['fourth_level']] = row['GES_Fabrication']
                    print(co2_dict)

                    mass_dict = {}
                    for _, row in masses.iterrows():
                        if row['material_emb_2'] not in mass_dict:
                            mass_dict[row['material_emb_2']] = {}
                        mass_dict[row['material_emb_2']][row['fourth_level']] = row['Masse/suface']

                    co2_value = co2_dict.get(selected_material, {}).get(selected_component, 0)
                    mass_value = mass_dict.get(selected_material, {}).get(selected_component, 0)
                    dimensions = [height* 0.01, length* 0.01, width* 0.01] 
                    dimensions.sort(reverse=True)
                    co2_fab = co2_value * np.prod(dimensions) * mass_value
                    rvi = co2_fab 
                    
                    st.write(f"Calculated CO2 for {selected_component} using {selected_material}: {rvi:.2f} eq.kg CO2")
                else:
                    st.error("Please enter all dimensions to calculate the RVI.")
        else:
            st.write("Please select a material to proceed with RVI calculations.")
    else:
        st.write("Please select a component to see available materials.")