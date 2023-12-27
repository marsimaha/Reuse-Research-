import streamlit as st
import pandas as pd
from io import BytesIO
import ifcopenshell
import ast

def safe_eval(value):
    try:
        # Check if the value is the string 'None' and keep it as-is
        if value == 'None':
            return 'None'
        # Safely evaluate the string if it is not already a Python literal
        elif not isinstance(value, (int, float, bool)):
            return ast.literal_eval(value)
        return value
    except (ValueError, SyntaxError):
        # Return the value as-is if it cannot be safely evaluated
        return value

def parse_attributes(dict_):
    # Convert the attribute string to a Python list
    #dict_ = ast.literal_eval(dict_)
    evaluated_dict = {key: safe_eval(value) for key, value in dict_.items()}

    return evaluated_dict


def create_pset_door_common(ifc_file, door, properties):
    # Create property values
    property_values = []
    for name, value in properties.items():
        # Determine the type of the property and create accordingly
        if isinstance(value, bool):
            property_value = ifc_file.createIfcBoolean(value)
        elif isinstance(value, (float, int)):
            property_value = ifc_file.createIfcReal(value)
        else:  # Assuming default type is text
            property_value = ifc_file.createIfcText(value)
        
        # Create the property itself
        prop = ifc_file.createIfcPropertySingleValue(Name=name, NominalValue=property_value)
        property_values.append(prop)

    # Create the property set
    pset = ifc_file.createIfcPropertySet(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=None,  # Assuming no owner history
        Name="Pset_DoorCommon",
        Description=None,  # Assuming no description
        HasProperties=property_values
    )

    # Relate the property set to the door
    ifc_file.createIfcRelDefinesByProperties(
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=None,  # Assuming no owner history
        RelatedObjects=[door],
        RelatingPropertyDefinition=pset
    )

    return pset


def download_button(component):

    

    res = parse_attributes(component)
    properties = res['attributes']

    # Initialize an IFC file
    ifc_file = ifcopenshell.file(schema="IFC4")

    # Create an IfcDoor entity (example)
    door = ifc_file.create_entity(
        res['classification'],
        GlobalId=ifcopenshell.guid.new(),
        Name="Example",
    )


    # Create and associate Pset_DoorCommon with the door
    create_pset_door_common(ifc_file, door, properties)

    # Output the IFC file to a file on disk
    file_path = 'file.ifc'
    ifc_file.write(file_path)

    # Download button for the IFC file
    with open(file_path, 'rb') as file:
        st.download_button(
            label="Download IFC File",
            data=file,
            file_name=file_path,
            mime="application/octet-stream"
        )

    print(f"IFC file with Pset_DoorCommon written to {file_path}")