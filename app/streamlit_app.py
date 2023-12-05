import streamlit as st
import pandas as pd
import logging
from numpy import random
from flask import jsonify

import numpy as np
from urllib.parse import urlencode

from neo4j import GraphDatabase
import search as sh
import json


URI = "neo4j+ssc://d4e7c69a.databases.neo4j.io"
AUTH = ("neo4j", "8gGwVhSx2-ycIPiPGOWejHAhufieq2XOOrkOAizxa1E")

def outputs(list, list_code, search_query):
    results, cos = sh.get_query_matches(search_query, list)
    cos = np.sort(cos)[[-1, -2, -3, -4, -5]]            
    similar_texts = list[results] 
    similar_codes = list_code[results]
    # Convert the list of tuples into a pandas DataFrame
    df_similar_texts = pd.DataFrame({
        'Name': similar_texts,
        'Relevance': cos[0:len(similar_texts)],
        "Code": similar_codes
    }) 
    df_similar_texts = df_similar_texts.drop_duplicates(subset='Code', keep='first')
    df_similar_texts = df_similar_texts.loc[df_similar_texts['Relevance'] != 0]
    df_similar_texts.reset_index()

    return df_similar_texts

def search():
    st.title("My Streamlit App")
    # Initialize the session state for checkboxes if not already set
    if 'checkbox_state' not in st.session_state:
        st.session_state.checkbox_state = [False, False, False]
    
    # Replace HTML form with Streamlit input widgets
    search_query = st.text_input("Enter your search query:")

    # Define a function to update checkboxes ensuring one is checked at a time
    def checkbox_callback(index):
        # When a checkbox is clicked, set all to False and then toggle the clicked one
        st.session_state.checkbox_state = [False, False, False]
        st.session_state.checkbox_state[index] = not st.session_state.checkbox_state[index]

    # Add checkboxes
    checkbox1 = st.checkbox('eBKP', value=st.session_state.checkbox_state[0], on_change=checkbox_callback, args=(0,))
    checkbox2 = st.checkbox('IFC', value=st.session_state.checkbox_state[1], on_change=checkbox_callback, args=(1,))
    checkbox3 = st.checkbox('MF', value=st.session_state.checkbox_state[2], on_change=checkbox_callback, args=(2,))


    if search_query:
        pass

    IFC = pd.read_csv("IFC_processed.csv") 
    eBKP = pd.read_csv("eBKP_processed.csv") 
    MF = pd.read_csv("MF_processed.csv") 

    # You can use buttons to trigger actions
    if st.button("Search"):
        # Perform action on click (similar to form submission in Flask)
        if checkbox1:
            st.write("eBKP")
            df_similar_texts = outputs(eBKP['Translated_Text'], eBKP['code'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)

        if checkbox2:
            st.write("IFC")
            df_similar_texts = outputs(IFC['IFC'], IFC['raw'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)

        if checkbox3:
            st.write("MF")
            df_similar_texts = outputs(MF['label'], MF['code'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)

        if not checkbox3 and not checkbox2 and not checkbox1 :
            st.write("eBKP")
            df_similar_texts = outputs(eBKP['Translated_Text'], eBKP['code'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)

            st.write("IFC")
            df_similar_texts = outputs(IFC['IFC'], IFC['raw'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)

            st.write("MF")
            df_similar_texts = outputs(MF['label'], MF['code'], search_query)
            # Display the DataFrame as a table in Streamlit
            st.table(df_similar_texts)




def get_attributes(classification):
    with open('IFC.json', 'r') as file:
        data = json.load(file)
    prop_name_list=[]
    for pset_name, pset_details in data["Domain"]["Classifications"][classification].get("Psets", {}).items():
        for prop_name, prop_details in pset_details.get("Properties", {}).items():
            if prop_details["type"] == "string" or prop_details["type"] == "real":
                prop_details = prop_details["type"]
            elif "values" in prop_details.keys():
                prop_details = str(prop_details["values"])
            else:
                prop_details = str(prop_details)

            prop_name_list.append((prop_name, prop_details))
    return prop_name_list

def upload_data(driver, component):
    # Flatten or serialize complex structures
    for key, value in component.items():
        if isinstance(value, list) and any(isinstance(i, (list, dict)) for i in value):
            # Serialize if the list contains nested structures
            component[key] = json.dumps(value)
        elif isinstance(value, dict):
            # Serialize nested dictionaries
            component[key] = json.dumps(value)

    with driver.session() as session:
        properties = ", ".join(f"{key}: ${key}" for key in component.keys())
        query = f"CREATE (a:Component {{{properties}}})"
        session.run(query, **component)

def db_upload():
    driver = GraphDatabase.driver(URI, auth=AUTH)

    st.title('Component Upload')

    if 'checkbox_state_upload' not in st.session_state:
        st.session_state.checkbox_state_upload = [False, False, False, False, False]

    def goto_level_2():
        st.session_state["stage"] = "level_2"


    # Define a function to update checkboxes ensuring one is checked at a time
    def checkbox_callback(index):

        st.session_state.checkbox_state_upload = [False, False, False, False, False]
        st.session_state.checkbox_state_upload[index] = not st.session_state.checkbox_state_upload[index]

    checkbox1 = st.checkbox('eBKP', value=st.session_state.checkbox_state_upload[0], on_change=checkbox_callback, args=(0,))
    checkbox2 = st.checkbox('IFC', value=st.session_state.checkbox_state_upload[1], on_change=checkbox_callback, args=(1,))
    checkbox3 = st.checkbox('MF', value=st.session_state.checkbox_state_upload[2], on_change=checkbox_callback, args=(2,))
    checkbox4 = st.checkbox('Uniclass_2015', value=st.session_state.checkbox_state_upload[3], on_change=checkbox_callback, args=(3,))
    checkbox5 = st.checkbox('No_Class', value=st.session_state.checkbox_state_upload[4], on_change=checkbox_callback, args=(4,))

    def insert_data(user, name):
        IFC = pd.read_csv("IFC_processed.csv")
        with open('IFC.json', 'r') as file:
            IFC_ATTRIBUTES = json.load(file)
        # Assuming sh.get_query_matches is a function you have defined elsewhere
        if checkbox2:
            results, _ = sh.get_query_matches(name, IFC['IFC'])
            results = [results]

            classification = IFC.raw[results[0][0]]

            prop_name_list= dict()
            for pset_name, pset_details in IFC_ATTRIBUTES["Domain"]["Classifications"][classification].get("Psets", {}).items():
                st.write(pset_details)

                for prop_name, prop_details in pset_details.get("Properties", {}).items():
                    if prop_details["type"] == "string" or prop_details["type"] == "real":
                        prop_details = prop_details["type"]
                    elif "values" in prop_details.keys():
                        prop_details = str(prop_details["values"])
                    else:
                        prop_details = str(prop_details)

                    prop_name_list[prop_name] = prop_details

        st.session_state["component"] = {"user":user, "name":name, "classification": classification, "attributes": prop_name_list}


    st.write("Enter component classification or click on no classification:")
    user = st.text_input("Username")
    name = st.text_input("Component name")
    if user:
        pass
    if name:
        pass
    if "stage" not in st.session_state:
        st.session_state["stage"] = "level_1"

    if st.button("Search"):
        st.session_state["stage"] = "level_1"
        # Add checkboxes
        # Every form must have a submit button
        if not (checkbox1 or checkbox2 or checkbox3 or checkbox4 or checkbox5):
            st.session_state.checkbox_state[4] = True
        insert_data(user, name)
        goto_level_2()

    if st.session_state["stage"] == "level_2":
        with st.form("my_form"):
            st.write("Enter component details : ")
            attribut = dict()
            for prop, place in st.session_state.component["attributes"].items():
                selectbox = False
                default_value = None
                try:
                    place = json.loads(place)
                    print("e")
                except json.JSONDecodeError as e:
                    print(f"Error converting string to dictionary: {e}")

                try:
                    evaluated_place = eval(place)
                    if isinstance(evaluated_place, list) and all(item in ['TRUE', 'FALSE'] for item in evaluated_place):
                        default_value = False
                        selectbox = True
                    if isinstance(place, dict) and 'type' in place:
                        evaluated_place = place['type']

                    elif isinstance(evaluated_place, list) and all(isinstance(item, str) for item in evaluated_place):
                        default_value = "OTHER"
                        selectbox = True
                    else:
                        default_value = place  # Default to the original value if none of the above conditions are met
                except:
                    evaluated_place = place
                
                widget_key = f"{prop}"
                if selectbox:
                    attribut[prop] = st.selectbox(prop, evaluated_place, key=widget_key)
                else:
                    attribut[prop] =  st.text_input(prop, placeholder=evaluated_place, key=widget_key)

            # Every form must have a submit button
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.component["attributes"] = attribut
                upload_data(driver, st.session_state.component)
                st.write(st.session_state.component)

                st.success("Data submitted!")
                st.session_state["component"] = dict()
                #st.session_state["stage"] = "level_1"


# Define a function to fetch components with the same user value
def get_components_with_same_user(driver, user_value):
    with driver.session() as session:
        query = (
            "MATCH (c:Component {user: $user}) "
            "RETURN c"
        )
        result = session.run(query, user=user_value)
        # Convert each record to a dictionary
        components = []
        for record in result:
            # Assuming the node properties are directly convertible to JSON
            component = dict(record['c'])
            components.append(component)

        return components
    

def get_component_by_id(component_id, driver):
        with driver.session() as session:
            query = (
                "MATCH (c:Component) "
                "WHERE ID(c) = $id "
                "RETURN c"
            )
            result = session.run(query, id=component_id)
            # Convert each record to a dictionary
            components = []
            for record in result:
                # Assuming the node properties are directly convertible to JSON
                component = dict(record['c'])
                components.append(component)

            return components


def get_components_with_same_name(driver, name):
    with driver.session() as session:  
        query = (
            "MATCH (c:Component {name: $name}) "
            "RETURN c"
        )
        result = session.run(query, name=name)
        components = [record['c'] for record in result]
        return components


def components_by_user():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    st.title('Component Viewer')
    # Input for the user
    name = st.text_input('Enter component name to find all the same components')
    # Button to fetch components
    if st.button('Fetch components'):
        if name:  # Check if user is not empty
            # Fetch components from the database
            components = get_components_with_same_name(driver, name)
            st.write(components)
            if components:
                # Display the components in the app
                st.write('Components for user:', name)
                for component in components:
                    st.json(component)  # Assuming the component is a dict or JSON-like object
            else:
                st.write('No components found for user:', name)
        else:
            st.warning('Please enter a user name.')
            

# Function to update the component in the database
def update_component(driver, component_id, updated_properties):
    with driver.session() as session:
        query = (
            "MATCH (c:Component) "
            "WHERE ID(c) = $id "
            "SET c += $props"
        )
        session.run(query, id=component_id, props=updated_properties)

def db_update():
    st.title('Edit Component')
    driver = GraphDatabase.driver(URI, auth=AUTH)

    # Get component ID from user input or a selection widget
    component_id = st.number_input('Enter component ID', min_value=0, step=1)

    # Fetch the component to be edited
    if st.button('Fetch Component'):
        component = get_component_by_id(component_id, driver)
        if component:
            # Assuming the component is a dictionary-like object
            st.json(component)
        else:
            st.error('Component not found.')

    # Form for editing the component
    with st.form(key='edit_component_form'):
        length = st.text_input('Length')
        name = st.text_input('Name')
        material = st.text_input('Material')
        width = st.text_input('Width')
        classification = st.text_input('Classification')

        submit_button = st.form_submit_button(label='Update Component')

        if submit_button:
            updated_properties = {
                'length': length,
                'name': name,
                'material': material,
                'width': width,
                'classification': classification
            }

            # Calculate the mean length and width for components with the same name in Neo4j
            if name:
                components_with_same_name = get_components_with_same_name(driver, name)
                if components_with_same_name:
                    lengths = [float(comp['length']) if comp['length'] != "" else np.nan for comp in components_with_same_name]
                    widths = [float(comp['width']) if comp['width'] != "" else np.nan for comp in components_with_same_name]
                    if lengths:
                        updated_properties['length'] = str(np.nanmean(lengths))
                    if widths:
                        updated_properties['width'] = str(np.nanmean(widths))

            if updated_properties:
                # Use a Cypher query to update the node's properties
                IFC = pd.read_csv("IFC_processed.csv")
                results, cos = sh.get_query_matches(name, IFC['IFC'])
                results = [results]
                updated_properties['classification'] = IFC.raw[results[0][0]]
                with driver.session() as session:
                    query = (
                        "MATCH (c:Component) "
                        "WHERE ID(c) = $id "
                        "SET c += $props"
                    )
                    session.run(query, id=component_id, props=updated_properties)
            # Update the component in the database
            update_component(driver, component_id, updated_properties)
            st.success('Component updated successfully.')



# Main function to control the app
def main():
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Choose a page", ["Search", "DB Upload", "DB Read", "DB Edit"])

    # Display the selected page
    if choice == "Search":
        search()
    elif choice == "DB Upload":
        db_upload()
    elif choice == "DB Read":
        components_by_user()
    elif choice == "DB Edit":
        db_update()
if __name__ == "__main__":
    main()