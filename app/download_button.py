import streamlit as st
import pandas as pd
from io import BytesIO
import ifcopenshell
import ast

def create_ifc_file():
    return ifcopenshell.file()

def parse_attributes(attribute_str):
    # Convert the attribute string to a Python list
    return ast.literal_eval(attribute_str)

def create_and_add_entity(ifc_file, entity_type, attributes_dict):
    # Parse the attributes from the dictionary
    attributes = parse_attributes(attributes_dict['attributes'])

    # Check if attributes list is empty
    if not attributes:
        print("Error: Empty attributes list.")
        return None

    # Print the attributes for debugging
    print(f"Creating entity of type {entity_type} with attributes:")
    for attribute in attributes:
        print(f"{attribute[0]}: {attribute[1]}")

    try:
        # Create an IFC entity in the file
        entity = ifc_file.create_entity(entity_type, **dict(attributes))

        # Add the entity to the IFC file
        ifc_file.add(entity)

        return entity
    except Exception as e:
        print(f"Error creating entity: {e}")
        return None

def save_ifc_file(ifc_file):
    # Create a BytesIO object to store the IFC file
    ifc_buffer = BytesIO()
    ifc_buffer.write(ifc_file.wrapped_data)

    return ifc_buffer


# Streamlit app
def download_button(neo4j_node):
    # Example usage:
    ifc_file = create_ifc_file()

    # Add an IfcDoor entity to the file using the provided attributes
    create_and_add_entity(ifc_file, neo4j_node["classification"], neo4j_node)

    # Save the IFC file
    ifc_buffer = save_ifc_file(ifc_file)

    # Set up the download button for the IFC file
    st.download_button(
        label="Download IFC File",
        data=ifc_buffer,
        file_name='example.ifc',
        mime='application/octet-stream'
    )
