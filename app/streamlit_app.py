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
from nltk.stem import WordNetLemmatizer
from download_button import download_button
from search import *

import calculate_rvi as rvi

URI = "neo4j+s://aaf6defa.databases.neo4j.io:7687"
AUTH = ("neo4j", "LkoDag9gu-p8wEKa1EyyFrKsqpJWptJMk3OM0KV38Uo")

lemmatizer = WordNetLemmatizer()



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
        # Create the component node
        import re
        properties = ", ".join(f"{key}: ${key}" for key in component.keys())
        create_query = f"CREATE (a:Component {{{properties}}})"
        session.run(create_query, **component)

        # Assuming 'classification' is a property of the component
        classification = component.get('classification', None)
        parts = classification.split("lock")

        # Join the parts with an underscore
        joined_result = "_".join(parts)

        with driver.session() as session:
                properties = ", ".join(f"{key}: ${key}" for key in component.keys())
                query = f"CREATE (a:Component {{{properties}}})"
                session.run(query, **component)

def db_upload(driver):

    st.title('Component Upload')

    if 'checkbox_state_upload' not in st.session_state:
        st.session_state.checkbox_state_upload = [False, False, False, False, False]

    def goto_level_2():
        st.session_state["stage"] = "level_2"


    # Define a function to update checkboxes ensuring one is checked at a time
    def checkbox_callback(index):

        st.session_state.checkbox_state_upload = [False, False, False, False, False]
        st.session_state.checkbox_state_upload[index] = not st.session_state.checkbox_state_upload[index]

    checkbox1 = False#st.checkbox('eBKP', value=st.session_state.checkbox_state_upload[0], on_change=checkbox_callback, args=(0,))
    checkbox2 = st.checkbox('IFC', value=st.session_state.checkbox_state_upload[1], on_change=checkbox_callback, args=(1,))
    checkbox3 = False#st.checkbox('MF', value=st.session_state.checkbox_state_upload[2], on_change=checkbox_callback, args=(2,))
    checkbox4 = False#st.checkbox('Uniclass_2015', value=st.session_state.checkbox_state_upload[3], on_change=checkbox_callback, args=(3,))
    checkbox5 = False#st.checkbox('No_Class', value=st.session_state.checkbox_state_upload[4], on_change=checkbox_callback, args=(4,))

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
                for prop_name, prop_details in pset_details.get("Properties", {}).items():
                    if prop_details["type"] == "string" or prop_details["type"] == "real":
                        prop_details = prop_details["type"]
                        prop_name_list[prop_name] = prop_details

                    elif "values" in prop_details.keys():
                        prop_details = str(prop_details["values"])
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

    def is_valid_json(value):
        try:
            json.loads(value)
            return True
        except json.JSONDecodeError:
            return False

    def get_default_value(place):
        if place.strip().lower() == "real":
            # For "real", return 0 as the default
            return 0, False
        elif place.strip().lower() == "string":
            # For "real", return 0 as the default
            return "None", False
        try:
            # Safely evaluate the string representation of the list
            evaluated_place = ast.literal_eval(place)

            if isinstance(evaluated_place, list):
                # For a list, check if it's a list of booleans
                if all(item.upper() in ['TRUE', 'FALSE'] for item in evaluated_place):
                    # For a list of booleans, return the boolean False as the default
                    return False, True
                else:
                    # For other lists, return the first item in the list as the default
                    return evaluated_place[0], True
        except (ValueError, SyntaxError):
            # If there is an error during evaluation or the string is not a list,
            # it will fall back to the original value, which should be a string
            return place, False

        # If none of the above conditions are met, return the original place as the default value
        return place, False

    if st.session_state.get("stage") == "level_2":
        with st.form("my_form"):
            st.write("Enter component details:")
            attributes = dict()
            # Sample data: replace this with your actual options
            materials = pd.read_excel("co2mat.xlsx", sheet_name="Sheet2")
            materials = materials["Eng"].to_list()
            
            selected_option = st.selectbox("Select an option:", materials)

            attributes["Material"] = selected_option

            for prop, place in st.session_state.component["attributes"].items():
                default_value, use_selectbox = get_default_value(place)
                widget_key = f"{prop}"
                if use_selectbox:
                    # 'evaluated_place' must be a list obtained from 'ast.literal_eval'
                    # The first element of this list will be used as the default option
                    options = ast.literal_eval(place)
                    attributes[prop] = st.selectbox(prop, options, index=0, key=widget_key)
                else:
                    # For text inputs, 'default_value' is used as the default value
                    attributes[prop] = st.text_input(prop, default_value, key=widget_key)


            # Every form must have a submit button
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.session_state.component["attributes"] = attributes
                upload_data(driver, st.session_state.component)
                #st.write(st.session_state.component)

                st.success("Data submitted!")
                st.session_state["component"] = dict()




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
    
    

def components_by_user(driver):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    st.title('Component Viewer')
    # Input for the user
    name = st.text_input('Enter component name to find all the same components')
    # Button to fetch components
    if st.button('Fetch components'):
        if name:  # Check if user is not empty
            # Fetch components from the database
            components = get_components_with_same_name(driver, name)
            for component in components:
                st.write(component)
                download_button(dict(component))
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

def db_update(driver):
    st.title('Edit Component')

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
    driver = GraphDatabase.driver(URI, auth=AUTH)

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Choose a page", ["Search", "DB Upload", "DB Read", "RVI"])

    # Display the selected page
    if choice == "Search":
        search()
    elif choice == "DB Upload":
        db_upload(driver)
    elif choice == "DB Read":
        components_by_user(driver)
    #elif choice == "DB Edit":
    #    db_update(driver)

    elif choice == "RVI":
        rvi.display_rvi_streamlit_att2(driver)
if __name__ == "__main__":
    main()