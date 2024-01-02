import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import streamlit as st

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


